from datetime import datetime, timezone
from backend.extensions import db


class Share(db.Model):
    __tablename__ = "shares"
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(32), unique=True, nullable=False, index=True)
    code = db.Column(db.String(16), unique=True, nullable=False, index=True)
    share_type = db.Column(db.String(16), nullable=False)  # file or text
    text_content = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    download_count = db.Column(db.Integer, nullable=False, default=0)
    delete_after_download = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.String(16), nullable=False, default="active")
    delete_secret_hash = db.Column(db.String(64), nullable=False)
    files = db.relationship("StoredFile", backref="share", cascade="all, delete-orphan", lazy="select")

    def is_expired(self):
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) >= expires


class StoredFile(db.Model):
    __tablename__ = "share_files"
    id = db.Column(db.Integer, primary_key=True)
    share_id = db.Column(db.Integer, db.ForeignKey("shares.id"), nullable=False, index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    blob_name = db.Column(db.String(255), unique=True, nullable=False)
    content_type = db.Column(db.String(127), nullable=False, default="application/octet-stream")
    file_size = db.Column(db.Integer, nullable=False)
