"""Validate starter configuration, enforce database TLS, then replace PID 1 with Hasura."""
import base64
import binascii
import os
from pathlib import Path
import ssl
import sys
from urllib.parse import urlencode, urlsplit, urlunsplit


def required(env, name):
    value = env.get(name, "")
    if not value:
        raise ValueError(f"{name} is required")
    return value


def database_uri(raw, local, ca):
    # Parse errors must never echo a URI containing credentials.
    try:
        parts = urlsplit(raw)
        valid = (
            parts.scheme in ("postgres", "postgresql")
            and parts.hostname and parts.port
            and parts.username and parts.password
            and parts.path not in ("", "/") and not parts.fragment
            and not any(c.isspace() or ord(c) < 32 for c in raw)
        )
    except ValueError:
        valid = False
    if not valid:
        raise ValueError("DATABASE_URL must be a PostgreSQL URI with credentials, host, port and database")
    # Discard supplied query options: none may override TLS verification or host.
    query = {"sslmode": "disable", "connect_timeout": "10"} if local else {
        "sslmode": "verify-full", "sslrootcert": str(ca), "connect_timeout": "10"
    }
    return urlunsplit(("postgresql", parts.netloc, parts.path, urlencode(query), ""))


def prepare(env, directory):
    flag = env.get("LOCAL_DEVELOPMENT", "false").lower()
    if flag not in ("true", "false"):
        raise ValueError("LOCAL_DEVELOPMENT must be true or false")
    local = flag == "true"
    secret = required(env, "HASURA_GRAPHQL_ADMIN_SECRET")
    if len(secret) < 32 or not secret.isascii() or any(c.isspace() or ord(c) < 33 or ord(c) == 127 for c in secret):
        raise ValueError("HASURA_GRAPHQL_ADMIN_SECRET must contain at least 32 printable ASCII characters without spaces")
    # This starter deliberately has no anonymous role or alternate admin secrets.
    if env.get("HASURA_GRAPHQL_UNAUTHORIZED_ROLE") or env.get("HASURA_GRAPHQL_ADMIN_SECRETS"):
        raise ValueError("This starter uses one admin secret and does not enable anonymous access")
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    directory.chmod(0o700)
    ca = directory / "aiven-ca.pem"
    if not local:
        try:
            pem = base64.b64decode(required(env, "AIVEN_CA_CERT_BASE64"), validate=True).decode("ascii")
            ssl.create_default_context(cadata=pem)
        except (ValueError, UnicodeError, binascii.Error, ssl.SSLError) as exc:
            raise ValueError("AIVEN_CA_CERT_BASE64 must encode a valid PEM CA certificate") from exc
        ca.write_text(pem)
        ca.chmod(0o600)
    uri = database_uri(required(env, "DATABASE_URL"), local, ca)
    env["DATABASE_URL"] = uri
    # The documented compatibility variable adds the initial 'default' source.
    # Both source data and Hasura metadata live in the dedicated demo database.
    env["HASURA_GRAPHQL_DATABASE_URL"] = uri
    env["HASURA_GRAPHQL_METADATA_DATABASE_URL"] = uri
    env["HASURA_GRAPHQL_SERVER_HOST"] = "0.0.0.0"
    env["HASURA_GRAPHQL_SERVER_PORT"] = "8080"
    env["HASURA_GRAPHQL_ENABLE_TELEMETRY"] = "false"
    env["HASURA_GRAPHQL_DEV_MODE"] = "false"
    env["HASURA_GRAPHQL_ADMIN_INTERNAL_ERRORS"] = "false"
    env["HASURA_GRAPHQL_ENABLE_CONSOLE"] = "true"
    env["HASURA_GRAPHQL_CONSOLE_ASSETS_DIR"] = "/srv/console-assets"
    env.setdefault("HASURA_GRAPHQL_ENABLED_LOG_TYPES", "startup,http-log,webhook-log,websocket-log")
    return env


def main():
    os.umask(0o077)
    try:
        prepare(os.environ, Path("/tmp/hasura-starter"))
    except (ValueError, OSError) as exc:
        message = str(exc) if isinstance(exc, ValueError) else "Unable to prepare startup files"
        print(f"Starter configuration error: {message}", file=sys.stderr)
        return 1
    print("Starting Hasura on port 8080 with admin authentication.", flush=True)
    os.execvp("graphql-engine", ["graphql-engine", "serve"])


if __name__ == "__main__":
    sys.exit(main())
