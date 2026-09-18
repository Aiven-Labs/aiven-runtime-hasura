# Validation

## Local checks — 18 September 2026

- Seven standard-library configuration tests passed (`python3 -m unittest discover -s tests -v`).
- Checked required admin secret, invalid/unsafe header values, anonymous-role rejection, malformed connection URIs and credential-safe validation errors.
- Verified mandatory CA validation, certificate/hostname verification settings, discarded URI overrides, private CA file permissions and explicit local-only TLS opt-out.
- Verified metadata and initial source receive the same persistent database URI, with native Console enabled and development/error-detail modes disabled.
- Confirmed the official v2.50.3 registry manifest and pinned its multi-platform digest; Linux amd64 and arm64 variants are available. Inspected the upstream image configuration for its existing user (UID/GID 1001) and engine startup command.
- Checked the strict health endpoint against the versioned upstream documentation.
- Git whitespace validation passed.

No Docker or Podman engine is installed in the current local environment. Container build and application checks were therefore performed on Aiven Runtime.

## Aiven Runtime — 18 September 2026

Deployed commit `f6bcac4f955e06f403194475314b24317cc519fd` unchanged using Aiven MCP, the root Dockerfile and an explicit PostgreSQL credential integration in AWS Ireland (`aws-eu-west-1`).

| Service | Tested plan | Listed base price/hour |
| --- | --- | --- |
| Runtime | `startup-100-2048`, one replica, 2 GiB RAM | $0.06849 |
| PostgreSQL | `startup-4`, PostgreSQL 16.15 | $0.151 |

Combined listed base price: **$0.21949/hour**, approximately **$5.27/day** while running, before additional charges or account-specific discounts. Pricing was checked for the test project and region on this date.

Passed:

- Container build, artifact scan and deployment from the pushed commit. Non-root image configuration started successfully; native Console assets loaded.
- Hasura metadata initialization, initial `default` source, and strict health endpoint returning `200 OK`.
- Configured verified-TLS database connection; an independent client confirmed certificate and hostname verification with TLS 1.3.
- No sample tables existed on initial startup.
- Missing and incorrect secrets rejected by GraphQL and metadata APIs. GraphQL authentication failures can return HTTP 200 with an `access-denied` error, so checks inspected response bodies.
- Browser Console displayed its login prompt, rejected an incorrect secret, and accepted the generated admin secret.
- Loaded the optional notes SQL, tracked the table, queried rows and inserted a fourth row through GraphQL.
- Authenticated WebSocket subscription received initial rows and a subsequent mutation update through Runtime ingress.
- Powered Runtime off and on; logs confirmed the old process shut down and a different runtime instance started. Strict health recovered and the tracked table plus inserted row remained available.

The live test database contains the optional notes example and a persistence-test row. The repository still creates no sample data automatically. No implementation changes were required during deployment.

## Remaining validation

- Console Compose scanner path and local Docker Compose startup (MCP deployed the Dockerfile directly).
- Application-user JWT/webhook authentication, permission policies and real application schemas.
- Production load, sizing benchmarks, high availability, event-trigger delivery and multi-replica operation.

Runtime's OCI build ignored Dockerfile HEALTHCHECK, so health and functional checks were performed externally. The upstream health endpoint alone does not validate all data-source operations.
