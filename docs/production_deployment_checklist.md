# Production Deployment Checklist Runbook

## Overview
This checklist governs the operational sequence for executing deployments to the Production environment.

## Pre-Deployment Sequence
- [ ] Confirm all Release Prerequisites are MET and verified.
- [ ] Open a Slack/Teams deployment thread in `#ops-releases`.
- [ ] Check Cloud Monitoring and Datadog dashboards for baseline metrics (HTTP 5xx rate < 0.05%, P99 latency < 250ms).
- [ ] Take a manual backup or verify point-in-time recovery (PITR) for relational databases (Cloud SQL/Spanner).

## Deployment Execution Sequence
1. **Canary / Progressive Traffic Shift**:
   - Deploy new container image revision to Cloud Run / Kubernetes cluster.
   - Route 10% traffic to the new revision for a 10-minute canary bake period.
2. **Health & Error Metric Verification**:
   - Verify health check endpoints return HTTP 200 OK across all canary pods/instances.
   - Monitor error logs in Cloud Logging for unhandled exceptions or panic traces.
3. **Full Traffic Shift**:
   - If error rate remains < 0.1% after 10 minutes, shift 100% traffic to the new revision.
   - Scale down previous revision after 15 minutes of zero traffic.

## Post-Deployment Sequence
- [ ] Run automated post-deploy smoke tests against public API endpoints.
- [ ] Update release status in Jira/GitHub Release notes.
- [ ] Announce completion in `#ops-releases`.
