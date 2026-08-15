import io
from datetime import datetime, timedelta, timezone
from backend.extensions import db
from backend.models import Share

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
