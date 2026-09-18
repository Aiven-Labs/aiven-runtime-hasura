# Hasura starter for Aiven Runtime

Standalone **Hasura GraphQL Engine Community Edition v2.50.3**, its native **Hasura Console**, and **Aiven for PostgreSQL**. Turn PostgreSQL tables into GraphQL queries, mutations and subscriptions.

This template deploys the open-source v2 GraphQL Engine. It does not deploy Hasura DDN or require a Hasura Cloud account, enterprise license, Valkey, or object storage. The official Hasura image is pinned by version and multi-platform registry digest.

## What starts up

```text
Browser / GraphQL client --HTTPS--> Aiven Runtime :8080
                                           |
                                  Hasura engine + Console
                                           |
                                      verified TLS
                                           |
                                    Aiven PostgreSQL
                                metadata + application data
```

One dedicated PostgreSQL database stores both Hasura metadata (`hdb_catalog`) and your application tables. The starter supplies it as Hasura's initial `default` data source. Tables become available through GraphQL after you track them in Console.

Deployment is vanilla Hasura: no sample tables or rows are created automatically. An optional notes example is included in `examples/`. No custom frontend or authentication service is bundled.

The startup wrapper validates the admin secret and database configuration, enforces certificate and hostname verification for PostgreSQL, and starts Hasura as a non-root user. Hasura performs its own metadata migrations and serves Console assets from the container.

## Local demo

Requires Docker Compose v2 and a working container engine.

1. Copy `.env.example` to `.env`.
2. Run `openssl rand -hex 32` twice and put independent generated values into `POSTGRES_PASSWORD` and `HASURA_GRAPHQL_ADMIN_SECRET`.
3. Run `docker compose up --build -d`.
4. Open <http://localhost:8080/console> and enter your admin secret.
5. Under **Data**, select the `default` source and create or track tables, or try the optional example below.

Only Hasura's port 8080 is published, bound to loopback. Local PostgreSQL uses the private Compose network without TLS. `LOCAL_DEVELOPMENT=true` is only for this local setup; never set it on Runtime. Use hexadecimal local passwords so they are safe in a URI.

`docker compose down` preserves PostgreSQL data. `docker compose down -v` permanently removes local database data, including Hasura metadata.

## Deploy on Aiven Runtime

1. Commit and push the repo so Runtime can build it.
2. In Aiven Console, create a Runtime application from the repository and select **compose.aiven.yaml**. Review the detected PostgreSQL dependency and credential integration: its connection string must populate `DATABASE_URL`.
3. Use a dedicated, initially empty PostgreSQL database owned by the supplied account. Select PostgreSQL 16 explicitly: Runtime's scanner uses the image name to identify the service but ignores its version tag.
4. Select the plans below, one Runtime replica, and HTTP port **8080**. Add the required settings before starting the application.
5. Once startup completes, open the generated HTTPS URL with `/console` appended and enter the admin secret. Test an authenticated query; a healthy process alone does not prove your data source is usable.

For Aiven MCP/API deployment, build the root Dockerfile and create the `application_service_credential` integration explicitly. MCP/API deployment does not process Compose manifests.

### Suggested demo sizes

| Service | Starting point | Purpose |
| --- | --- | --- |
| Runtime | One replica, 2 GiB RAM (`startup-100-2048` where available) | Hasura engine and Console |
| PostgreSQL | `startup-4` or equivalent 4 GiB plan, PostgreSQL 16 | Metadata and application data |

These are conservative starting suggestions, not benchmarked minimums or production sizing. They are documented in the Runtime manifest as comments; plans are selected in Console/API and are not enforced by Compose. Review available internal/free plans and current pricing before creating services. Live validation is pending; see [VALIDATION.md](VALIDATION.md).

### Required Runtime settings

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | Integration-provided PostgreSQL URI with credentials, database and port |
| `HASURA_GRAPHQL_ADMIN_SECRET` | Unique random secret, at least 32 printable ASCII characters without spaces; generate with `openssl rand -hex 32` |
| `AIVEN_CA_CERT_BASE64` | Aiven project CA PEM encoded as one line with `openssl base64 -A -in ca.pem` |

Store credentials and the admin secret as Runtime secrets, outside Git. Download the project CA from Aiven Console. The wrapper writes it to a private temporary file and sets `sslmode=verify-full`; all original URI query parameters are discarded so they cannot override TLS or redirect the connection. Credentials containing reserved characters must be percent-encoded in the URI. The integration normally handles this.

The wrapper sets both `HASURA_GRAPHQL_METADATA_DATABASE_URL` and `HASURA_GRAPHQL_DATABASE_URL` from the normalized `DATABASE_URL`; do not configure those separately. Using the latter is Hasura's supported compatibility mechanism for adding the initial `default` source. Once you manage additional sources through Console, configure their verified TLS connections individually: this wrapper only configures the initial database.

Hasura needs permission to create and maintain `hdb_catalog` and the `pgcrypto` extension in the metadata database. The supplied database owner also needs permission to create application tables for the optional example. If extension creation is restricted, have a database administrator install `pgcrypto` in the public schema first; do not disable TLS or use an unrelated production database to work around startup errors.

## Try the optional notes example

1. In **Console > Data > default > SQL**, run [examples/notes.sql](examples/notes.sql). Leave table tracking enabled, or track `public.starter_notes` afterwards.
2. Open **API > GraphiQL** and paste [examples/queries.graphql](examples/queries.graphql). Select one operation at a time to list, create, update or watch notes.
3. For `WatchNotes`, keep the subscription running in one tab and run a mutation in another. The subscription should update over WebSocket.

The SQL intentionally fails if `starter_notes` already exists. It is a one-time example, not a startup migration or a seed that overwrites data on each restart. The examples use admin access and create no anonymous role.

For a server-side API call, set `HASURA_URL` to the application origin and `HASURA_GRAPHQL_ADMIN_SECRET` in your shell:

```sh
curl "$HASURA_URL/v1/graphql" \
  -H "x-hasura-admin-secret: $HASURA_GRAPHQL_ADMIN_SECRET" \
  -H 'Content-Type: application/json' \
  -d '{"query":"query { starter_notes(order_by: {id: asc}) { id title completed } }"}'
```

GraphQL can return HTTP 200 with an `errors` field. Check the response body as well as the status code. Restart Runtime and confirm the tracked table and inserted rows remain available.

## Authentication and shared use

Console uses Hasura's native admin-secret prompt; there is no separate username or application password. The Console shell, static assets and health endpoint may load without credentials. Data and metadata operations require the secret. An already-authorized browser may remember it and skip the prompt. Use a private browser window to check anonymous access.

**The admin secret grants unrestricted database and metadata access through Hasura.** Keep it for trusted administrators and server-side testing. Never embed it in a public frontend or distribute it to application end users. Before exposing a user-facing API, configure JWT or webhook authentication and explicit Hasura role, row and column permissions. Authentication providers and end-user account management are not part of this starter. The wrapper rejects an anonymous-role setting and alternate admin-secret lists.

For a frontend on another origin, configure `HASURA_GRAPHQL_CORS_DOMAIN` with its exact origin(s). Upstream's default allows all origins, but requests still require authentication. CORS is not an authorization system. Restrict query complexity, rate limits and access through your chosen API gateway as appropriate; this demo does not provide a gateway or custom rate limiter.

## Operations and validation

Run the configuration tests with Python 3.10+ and OpenSSL; no Python packages are required:

```sh
python3 -m unittest discover -s tests -v
```

The Docker health check uses `/healthz?strict=true`. Runtime may ignore Dockerfile health checks, so validate startup, authenticated queries and persistence separately. Do not treat this endpoint as an end-to-end test of every connected source.

Keep one replica for the initial demo. Before scaling, size database connection pools, load-test queries and subscriptions, configure backups and monitoring, and review event-trigger side effects. The container filesystem is disposable; persistent state belongs in PostgreSQL. Back up PostgreSQL and export Hasura metadata before upgrades. Do not downgrade a migrated metadata database without the upstream migration procedure.

Console metadata changes persist in PostgreSQL, but are not automatically written to this repository. Export/version metadata and introduce Hasura CLI migrations when developing a reusable application schema. The base image is digest-pinned; Ubuntu packages installed during build receive the current repository versions. Refresh the image deliberately and review scan results when upgrading.

See [VALIDATION.md](VALIDATION.md) for completed checks and remaining live tests.

## References

- [Hasura v2.50.3 release](https://github.com/hasura/graphql-engine/releases/tag/v2.50.3)
- [Hasura server configuration](https://hasura.io/docs/2.0/deployment/graphql-engine-flags/reference/)
- [PostgreSQL requirements](https://hasura.io/docs/2.0/deployment/postgres-requirements/)
- [Hasura authentication and authorization](https://hasura.io/docs/2.0/auth/overview/)
- [Aiven Runtime Compose manifests](https://aiven.io/docs/products/runtime/manifest-files/compose-files)
