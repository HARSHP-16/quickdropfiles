import io
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from backend.extensions import db
from backend.models import Share
from backend.services.storage import AzureBlobStorage, create_storage

def test_text_share_lookup_and_consume(client):
    response = client.post('/api/text', json={'content':'hello QuickDrop', 'delete_after_download': True})
    assert response.status_code == 201
    data = response.json
    assert data['code'].count('-') == 2
    assert client.get('/api/lookup/' + data['code']).status_code == 200
    assert client.get('/api/share/' + data['token']).json['text_content'] == 'hello QuickDrop'
    assert client.post('/api/consume/' + data['token']).status_code == 200
    assert client.get('/api/share/' + data['token']).status_code == 410

def test_file_upload_download_and_filename_safety(client):
    response = client.post('/api/upload', data={'files': (io.BytesIO(b'contents'), '../../unsafe.txt')}, content_type='multipart/form-data')
    assert response.status_code == 201
    file = response.json['files'][0]
    assert file['name'] == 'unsafe.txt'
    download = client.get(file['download_url'])
    assert download.status_code == 200 and download.data == b'contents'

def test_expired_share_rejected(client, app):
    created = client.post('/api/text', json={'content':'bye'}).json
    with app.app_context():
        share = Share.query.filter_by(token=created['token']).first()
        share.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.session.commit()
    assert client.get('/api/share/' + created['token']).status_code == 410

def test_empty_and_large_text_rejected(client, app):
    assert client.post('/api/text', json={'content':'   '}).status_code == 400
    app.config['MAX_TEXT_SIZE_MB'] = 0
    assert client.post('/api/text', json={'content':'x'}).status_code == 413


def test_azure_storage_uses_managed_identity_and_private_blob_endpoint():
    with patch("azure.identity.DefaultAzureCredential") as credential, \
         patch("azure.storage.blob.BlobServiceClient") as client:
        storage = AzureBlobStorage("quickdropstoragehp", "quickdrop-files")

    credential.assert_called_once_with()
    client.assert_called_once_with(
        account_url="https://quickdropstoragehp.blob.core.windows.net",
        credential=credential.return_value,
    )
    client.return_value.get_container_client.assert_called_once_with("quickdrop-files")
    assert storage.container is client.return_value.get_container_client.return_value


def test_azure_backend_requires_account_name():
    try:
        create_storage({"STORAGE_BACKEND": "azure", "AZURE_STORAGE_ACCOUNT_NAME": None,
                        "AZURE_STORAGE_CONTAINER": "quickdrop-files"})
    except RuntimeError as exc:
        assert "AZURE_STORAGE_ACCOUNT_NAME" in str(exc)
    else:
        raise AssertionError("Azure backend must require an account name")


def test_public_frontend_url_and_qr(client, app):
    app.config["PUBLIC_FRONTEND_URL"] = "https://quickdropfiles.vercel.app"
    response = client.post('/api/text', json={'content': 'test frontend url'})
    assert response.status_code == 201
    data = response.json
    assert data['url'] == f"https://quickdropfiles.vercel.app/s/{data['token']}"
    assert "azurewebsites.net" not in data['url']

    lookup_res = client.get('/api/lookup/' + data['code'])
    assert lookup_res.status_code == 200
    assert lookup_res.json['url'] == f"https://quickdropfiles.vercel.app/s/{data['token']}"

    qr_res = client.get('/api/qr/' + data['token'])
    assert qr_res.status_code == 200
    assert qr_res.mimetype == "image/svg+xml"


def test_cors_configuration(client):
    # Allowed origin
    res = client.get('/api/lookup/test', headers={'Origin': 'https://quickdropfiles.vercel.app'})
    assert res.headers.get('Access-Control-Allow-Origin') == 'https://quickdropfiles.vercel.app'
    assert 'Access-Control-Allow-Credentials' not in res.headers

    # Disallowed origin
    res_unauth = client.get('/api/lookup/test', headers={'Origin': 'https://malicious-site.com'})
    assert res_unauth.headers.get('Access-Control-Allow-Origin') is None

    # Preflight OPTIONS
    res_options = client.options('/api/share/test', headers={
        'Origin': 'https://quickdropfiles.vercel.app',
        'Access-Control-Request-Method': 'DELETE',
        'Access-Control-Request-Headers': 'X-Delete-Secret,Content-Type'
    })
    assert res_options.status_code == 200
    assert res_options.headers.get('Access-Control-Allow-Origin') == 'https://quickdropfiles.vercel.app'
    assert 'X-Delete-Secret' in res_options.headers.get('Access-Control-Allow-Headers', '')
