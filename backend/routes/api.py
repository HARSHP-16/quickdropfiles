import hashlib
import mimetypes
from datetime import timezone
from pathlib import Path
from flask import Blueprint, Response, current_app, jsonify, request, send_file
from werkzeug.utils import secure_filename
from backend.extensions import db, limiter
from backend.models import StoredFile
from backend.services.share_service import ShareUnavailable, create_share, get_active_share, remove_share

api = Blueprint("api", __name__, url_prefix="/api")


def _share_data(share, include_text=True):
    frontend_url = current_app.config.get("PUBLIC_FRONTEND_URL", "").rstrip("/")
    share_url = f"{frontend_url}/s/{share.token}" if frontend_url else f"/s/{share.token}"
    return {
        "token": share.token, "code": share.code, "url": share_url,
        "share_type": share.share_type, "created_at": share.created_at.replace(tzinfo=timezone.utc).isoformat(),
        "expires_at": share.expires_at.replace(tzinfo=timezone.utc).isoformat(), "download_count": share.download_count,
        "delete_after_download": share.delete_after_download,
        "text_content": share.text_content if include_text and share.share_type == "text" else None,
        "files": [{"id": f.id, "name": f.original_filename, "size": f.file_size, "content_type": f.content_type,
                   "download_url": f"/api/download/{share.token}/{f.id}"} for f in share.files],
    }


@api.post("/upload")
@limiter.limit("10 per hour")
def upload():
    files = request.files.getlist("files")
    if not files or not any(f.filename for f in files):
        return jsonify(error="Choose at least one file."), 400
    if len(files) > current_app.config["MAX_FILES_PER_SHARE"]:
        return jsonify(error=f"Maximum {current_app.config['MAX_FILES_PER_SHARE']} files per share."), 400
    if request.content_length and request.content_length > current_app.config["MAX_FILE_SIZE_MB"] * 1024 * 1024 * len(files):
        return jsonify(error="The upload is too large."), 413
    expires_in = request.form.get("expires_in", current_app.config["DEFAULT_EXPIRATION_SECONDS"])
    delete_after = request.form.get("delete_after_download", "false").lower() == "true"
    share, delete_secret = create_share("file", expires_in, delete_after)
    storage = current_app.extensions["storage"]
    try:
        for incoming in files:
            display_name = secure_filename(incoming.filename) or "download"
            incoming.stream.seek(0, 2)
            size = incoming.stream.tell()
            incoming.stream.seek(0)
            if size > current_app.config["MAX_FILE_SIZE_MB"] * 1024 * 1024:
                raise ValueError(f"{display_name} exceeds the {current_app.config['MAX_FILE_SIZE_MB']} MB limit.")
            blob_name = storage.save(incoming)
            content_type = mimetypes.guess_type(display_name)[0] or "application/octet-stream"
            db.session.add(StoredFile(share_id=share.id, original_filename=display_name, blob_name=blob_name,
                                      content_type=content_type, file_size=size))
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Upload failed")
        return jsonify(error=str(exc) if isinstance(exc, ValueError) else "Something went wrong while creating the share."), 400 if isinstance(exc, ValueError) else 500
    payload = _share_data(share, include_text=False)
    payload.update(success=True, delete_secret=delete_secret)
    return jsonify(payload), 201


@api.post("/text")
@limiter.limit("20 per hour")
def text_share():
    data = request.get_json(silent=True) or {}
    content = data.get("content", "")
    if not isinstance(content, str) or not content.strip():
        return jsonify(error="Paste some text to share."), 400
    if len(content.encode("utf-8")) > current_app.config["MAX_TEXT_SIZE_MB"] * 1024 * 1024:
        return jsonify(error=f"Text exceeds the {current_app.config['MAX_TEXT_SIZE_MB']} MB limit."), 413
    share, delete_secret = create_share("text", data.get("expires_in", current_app.config["DEFAULT_EXPIRATION_SECONDS"]),
                                        bool(data.get("delete_after_download")), content)
    db.session.commit()
    payload = _share_data(share)
    payload.update(success=True, delete_secret=delete_secret)
    return jsonify(payload), 201


@api.get("/share/<token>")
def get_share(token):
    try:
        return jsonify(_share_data(get_active_share(token)))
    except ShareUnavailable as exc:
        return jsonify(error=str(exc), expired="expired" in str(exc).lower()), 410


@api.get("/qr/<token>")
def qr(token):
    try:
        get_active_share(token)
    except ShareUnavailable as exc:
        return jsonify(error=str(exc)), 410
    import qrcode
    import qrcode.image.svg
    frontend_url = current_app.config.get("PUBLIC_FRONTEND_URL", "").rstrip("/")
    base_url = frontend_url if frontend_url else request.url_root.rstrip("/")
    image = qrcode.make(f"{base_url}/s/{token.upper()}", image_factory=qrcode.image.svg.SvgPathImage)
    output = __import__('io').BytesIO()
    image.save(output)
    return Response(output.getvalue(), mimetype="image/svg+xml")


@api.get("/lookup/<code>")
@limiter.limit("30 per hour")
def lookup(code):
    normalized = code.replace("-", "").upper()
    try:
        share = get_active_share(normalized)
        frontend_url = current_app.config.get("PUBLIC_FRONTEND_URL", "").rstrip("/")
        share_url = f"{frontend_url}/s/{share.token}" if frontend_url else f"/s/{share.token}"
        return jsonify(token=share.token, url=share_url)
    except ShareUnavailable:
        return jsonify(error="Invalid or expired share code."), 404


@api.get("/download/<token>/<int:file_id>")
@limiter.limit("60 per hour")
def download(token, file_id):
    try:
        share = get_active_share(token)
    except ShareUnavailable as exc:
        return jsonify(error=str(exc)), 410
    file = next((f for f in share.files if f.id == file_id), None)
    if not file:
        return jsonify(error="File not found."), 404
    try:
        handle = current_app.extensions["storage"].open(file.blob_name)
        response = send_file(handle, mimetype=file.content_type, as_attachment=True, download_name=file.original_filename)
        share.download_count += 1
        if share.delete_after_download:
            # An open local file handle remains readable for this response; cleanup runs immediately.
            remove_share(share, current_app.extensions["storage"])
        else:
            db.session.commit()
        return response
    except Exception:
        current_app.logger.exception("Download failed")
        return jsonify(error="The file could not be downloaded."), 500


@api.post("/consume/<token>")
def consume_text(token):
    try:
        share = get_active_share(token)
    except ShareUnavailable as exc:
        return jsonify(error=str(exc)), 410
    if share.share_type != "text":
        return jsonify(error="This endpoint only handles text shares."), 400
    share.download_count += 1
    if share.delete_after_download:
        remove_share(share, current_app.extensions["storage"])
    else:
        db.session.commit()
    return jsonify(success=True)


@api.delete("/share/<token>")
def delete_share(token):
    supplied = request.headers.get("X-Delete-Secret", "")
    try:
        share = get_active_share(token)
    except ShareUnavailable as exc:
        return jsonify(error=str(exc)), 410
    if not supplied or hashlib.sha256(supplied.encode()).hexdigest() != share.delete_secret_hash:
        return jsonify(error="Not authorized to delete this share."), 403
    remove_share(share, current_app.extensions["storage"])
    return jsonify(success=True)
