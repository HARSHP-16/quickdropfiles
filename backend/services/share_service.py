import hashlib
from datetime import datetime, timedelta, timezone
from backend.extensions import db
from backend.models import Share
from backend.services.token_service import format_code, generate_delete_secret, generate_token


class ShareUnavailable(Exception):
    pass


def create_share(share_type, expires_in, delete_after_download=False, text_content=None):
    seconds = min(max(int(expires_in), 60), int(__import__('flask').current_app.config["MAX_EXPIRATION_SECONDS"]))
    while True:
        token = generate_token()
        if not Share.query.filter_by(token=token).first():
            break
    secret = generate_delete_secret()
    share = Share(token=token, code=format_code(token), share_type=share_type, text_content=text_content,
                  expires_at=datetime.now(timezone.utc) + timedelta(seconds=seconds),
                  delete_after_download=delete_after_download,
                  delete_secret_hash=hashlib.sha256(secret.encode()).hexdigest())
    db.session.add(share)
    db.session.flush()
    return share, secret


def get_active_share(token):
    share = Share.query.filter_by(token=token.upper()).first()
    if not share or share.status != "active":
        raise ShareUnavailable("This share is no longer available.")
    if share.is_expired():
        share.status = "expired"
        db.session.commit()
        raise ShareUnavailable("This share has expired.")
    return share


def remove_share(share, storage):
    for item in share.files:
        try:
            storage.delete(item.blob_name)
        except Exception:
            __import__('flask').current_app.logger.exception("Could not delete blob for share %s", share.id)
    share.status = "deleted"
    db.session.commit()
