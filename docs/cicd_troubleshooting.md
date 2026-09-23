# CI/CD Troubleshooting Runbook

## Common Pipeline Failures & Resolutions

### 1. Container Image Scan Failures (Trivy / Artifact Analysis / Clair)
- **Symptom**: Pipeline fails at `container-scan` step with critical CVE warnings.
- **Root Cause**: Base Docker image contains outdated system packages or vulnerable software libraries.
- **Resolution**:
  - Update `Dockerfile` base image tag to the latest patch release (e.g. `python:3.11-slim-bookworm`).
  - Upgrade application dependencies in `requirements.txt` or `package.json`.
  - If no patch exists and risk is low, file a Security Exception with InfoSec.

### 2. Secret Manager / Permission Denied Errors
- **Symptom**: Cloud Build or GitHub Actions fails with `403 Permission Denied on SecretManager`.
- **Root Cause**: The Cloud Build Service Account lacks `roles/secretmanager.secretAccessor`.
- **Resolution**: Grant `roles/secretmanager.secretAccessor` to `PROJECT_NUMBER@cloudbuild.gserviceaccount.com`.

### 3. Database Migration Lock Timeout
- **Symptom**: Deployment hangs at `flyway migrate` or `alembic upgrade head` and times out after 10 minutes.
- **Root Cause**: An active long-running transaction holds an exclusive table lock in production.
- **Resolution**: Identify blocking queries via `pg_stat_activity` / `SHOW PROCESSLIST` and terminate idle locks before retrying pipeline.
