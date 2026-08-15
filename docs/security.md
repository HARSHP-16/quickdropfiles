# Security notes

- Public identifiers are generated with `secrets` and have approximately 60 bits of entropy.
- Uploaded filenames are sanitised only for download display; random IDs name stored objects.
- Flask enforces an aggregate request cap, per-file cap, number-of-files cap, and text cap. Flask-Limiter protects creation, lookup, and downloads by IP.
- The app never returns storage credentials. HTTPS-only must be enabled in App Service.
- Explicit deletion requires the randomly generated deletion secret returned once to the creator. This secret is stored only as a SHA-256 digest.
- Treat uploaded content as untrusted: the app only renders user text and image files are downloaded rather than embedded on share pages.

For a multi-instance deployment, configure Flask-Limiter with Redis instead of its default in-memory store. Use managed identity and Key Vault/App Service settings for production secrets.
