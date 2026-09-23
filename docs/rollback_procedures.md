# Rollback Procedures Runbook

## Overview
When a production deployment experiences elevated error rates (HTTP 5xx > 1%), health check failures, or severe performance degradation, immediately execute a rollback.

## Cloud Run Rollback Procedure
1. Identify the last known stable revision ID:
   `gcloud run revisions list --service=<SERVICE_NAME> --region=us-central1`
2. Instantly redirect 100% traffic back to the stable revision:
   `gcloud run services update-traffic <SERVICE_NAME> --to-revisions=<STABLE_REVISION_ID>=100 --region=us-central1`
3. Verify traffic routing:
   `gcloud run services describe <SERVICE_NAME> --region=us-central1`

## Kubernetes (GKE) Rollback Procedure
1. Check rollout history:
   `kubectl rollout history deployment/<DEPLOYMENT_NAME> -n <NAMESPACE>`
2. Undo the rollout to revert to the previous revision:
   `kubectl rollout undo deployment/<DEPLOYMENT_NAME> -n <NAMESPACE>`
3. To revert to a specific historical revision:
   `kubectl rollout undo deployment/<DEPLOYMENT_NAME> --to-revision=<REVISION_NUMBER> -n <NAMESPACE>`

## Critical Safety Rules During Rollback
- **Do NOT attempt database schema rollbacks during an active outage** unless schema migrations were explicitly written as dual-write capable.
- Reverting code to a previous version while a database schema is incompatible will cause complete service failure.
- Notify `#incidents-prod` immediately whenever a production rollback is triggered.
