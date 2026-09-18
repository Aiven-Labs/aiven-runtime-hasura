# Validation

## Local checks — 18 September 2026

- Seven standard-library configuration tests passed (`python3 -m unittest discover -s tests -v`).
- Checked required admin secret, invalid/unsafe header values, anonymous-role rejection, malformed connection URIs and credential-safe validation errors.
- Verified mandatory CA validation, certificate/hostname verification settings, discarded URI overrides, private CA file permissions and explicit local-only TLS opt-out.
- Verified metadata and initial source receive the same persistent database URI, with native Console enabled and development/error-detail modes disabled.
- Confirmed the official v2.50.3 registry manifest and pinned its multi-platform digest; Linux amd64 and arm64 variants are available. Inspected the upstream image configuration for its existing user (UID/GID 1001) and engine startup command.
- Checked the strict health endpoint against the versioned upstream documentation.
- Git whitespace validation passed.

These are configuration tests, not evidence that the Hasura container has run. No Docker or Podman engine is installed in the current local environment.

## Pending after the repository is pushed

- Build and image scan on Aiven Runtime; verify non-root startup and locally served Console assets.
- PostgreSQL 16 schema/extension initialization and verified-TLS connectivity.
- Console admin-secret prompt; missing/wrong secrets rejected by data and metadata APIs.
- Initial `default` data source, optional notes SQL, tracked table, authenticated query and mutation.
- WebSocket subscription through Runtime ingress.
- Metadata, tracked tables and inserted rows survive a Runtime restart.
- Record actual tested plans, usage and displayed pricing. Suggested sizes are one 2 GiB Runtime replica and PostgreSQL `startup-4`; they are not yet benchmarked or live-tested.
- Console Compose scanner path and local Docker Compose startup.

No Hasura cloud services have been provisioned for this template yet. No application-user JWT/webhook provider, anonymous API, production load, high availability, event triggers or multi-replica deployment has been tested.
