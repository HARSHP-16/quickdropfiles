# Deployment checklist

1. Provision a Storage account, private Blob container, PostgreSQL database, App Service, and Function App in one low-cost Azure region.
2. Set App Service configuration values from `.env.example`; use a PostgreSQL `DATABASE_URL`, `STORAGE_BACKEND=azure`, and a unique `SECRET_KEY`.
3. Give the runtime identity Blob Data Contributor access, then migrate the storage adapter from connection-string authentication to managed identity if desired.
4. Deploy the Function App using the same configuration and confirm its five-minute timer runs.
5. Turn on HTTPS-only, health monitoring, log retention limits, and cost budgets/alerts. Test expiry before inviting users.

Keep the default 1-hour expiry and conservative anonymous upload limits during the student-credit phase. Review current Azure Student terms and regional pricing in the Azure portal immediately before provisioning; they change over time.
