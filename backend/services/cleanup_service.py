from datetime import datetime, timezone
from backend.extensions import db
from backend.models import Share
from backend.services.share_service import remove_share


def cleanup_expired(storage):
    expired = Share.query.filter(Share.status == "active", Share.expires_at <= datetime.now(timezone.utc)).all()
    for share in expired:
        share.status = "expired"
        remove_share(share, storage)
    return len(expired)
