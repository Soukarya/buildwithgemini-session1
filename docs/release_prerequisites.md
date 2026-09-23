# Release Prerequisites Runbook

## Overview
All application services targeting staging or production environments must satisfy these prerequisite gates prior to initiating deployment.

## Required Verification Gates

1. **Automated Test Coverage**:
   - Unit test code coverage must be **>= 85%**.
   - All integration tests in the CI pipeline must complete with **0 failures**.

2. **Security Vulnerability Scanning**:
   - Zero **CRITICAL** or **HIGH** severity security vulnerabilities (CVEs) in base container images or third-party dependencies.
   - Any unfixable or false-positive vulnerabilities must have a formally approved Security Exception signed by the InfoSec Lead.

3. **Approvals & Sign-Offs**:
   - Staging releases require automated pipeline pass.
   - Production releases require explicit sign-off from the designated SRE Lead and Product Engineering Manager.

4. **Change Freeze Compliance**:
   - Verify no active Change Freeze window is in place (e.g., major holiday freezes, end-of-quarter blackout periods).
   - If a freeze is active, only approved Emergency Releases are permitted.

5. **Database Migration Checks**:
   - Schema migrations must be backward-compatible with the currently running application version.
   - Destructive migrations (dropping columns, changing types) must be split into a two-phase release cycle.
