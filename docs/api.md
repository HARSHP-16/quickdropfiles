# API

`POST /api/upload` accepts multipart `files`, optional `expires_in`, and `delete_after_download`. `POST /api/text` accepts JSON with `content` and the same options. Successful creation returns `token`, formatted `code`, `url`, `expires_at`, and a one-time `delete_secret`.

`GET /api/share/<token>` returns safe share metadata and text content. `GET /api/download/<token>/<file_id>` serves standard file shares, while one-time (`delete_after_download=true`) shares require `POST /api/download/<token>/<file_id>` to prevent unintended consumption by crawlers and prefetchers. `POST /api/consume/<token>` records successful text copying. `GET /api/lookup/<code>` resolves a formatted code. Explicit deletion requires `X-Delete-Secret` from the creation response.
