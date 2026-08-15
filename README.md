# QuickDrop

Temporary, account-free sharing for files and text. Drop or paste content, then open the generated link, scan its QR code, or enter its short code on another device. Content expires automatically after one hour by default.

## What is implemented

- Multiple file uploads (default: up to five, 100 MB each) and text shares
- Cryptographically random 60-bit public tokens and formatted access codes
- Share links, server-generated QR SVGs, mobile-responsive UI, and expiry countdowns
- Download/copy counters; optional delete after first successful download/copy
- Expiration validated on every request, plus an Azure Functions timer cleanup app
- Local storage + SQLite for development; Azure Blob Storage and PostgreSQL-compatible configuration for production
- IP rate limiting, request/text/file limits, sanitised display filenames, internal object names, and protected explicit deletion

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt pytest
flask --app backend.app run --debug
```

Open `http://127.0.0.1:5000`. Copy `.env.example` to `.env` and set environment values for non-default settings. Run tests with `pytest -q`.

## Architecture

```text
Browser → Flask / Azure App Service → PostgreSQL (share metadata)
                                  └→ Azure Blob Storage (files)
Azure Function (every 5 minutes) → deletes expired blobs and metadata state
```

For local development, SQLite and `data/uploads` replace the cloud services. Do not use SQLite/local storage for production.

## Azure deployment

1. Create an Azure Storage account/container and Azure Database for PostgreSQL.
2. Deploy the Flask app to App Service (Dockerfile is included) and configure `DATABASE_URL`, `STORAGE_BACKEND=azure`, Azure storage variables, `SECRET_KEY`, and limits through App Service Configuration.
3. Deploy `functions/cleanup` as a separate Function App with the same database/storage configuration.
4. Use managed identity/RBAC for Blob access where your hosting setup permits it; never commit credentials. Enable HTTPS-only on App Service.

The Azure Blob adapter uses `DefaultAzureCredential`: Azure CLI/developer credentials work locally, while App Service uses its system-assigned managed identity. Set only the non-secret Azure storage account and container names in App Service configuration.

## API

`POST /api/upload`, `POST /api/text`, `GET /api/share/<token>`, `GET /api/download/<token>/<file_id>`, `GET /api/lookup/<code>`, and `DELETE /api/share/<token>` (requires the creation-only `X-Delete-Secret`). See [docs/api.md](docs/api.md).

## Limits and roadmap

The app deliberately has short, configurable limits to control anonymous-storage abuse and Azure cost. It does not provide accounts, permanent storage, or P2P transfers. WebRTC direct transfers are planned for V2.
