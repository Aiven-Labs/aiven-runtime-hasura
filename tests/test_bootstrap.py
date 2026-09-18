import base64
from pathlib import Path
import subprocess
import tempfile
import unittest
from urllib.parse import parse_qs, urlsplit

from bootstrap import database_uri, prepare


class BootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.certdir = tempfile.TemporaryDirectory()
        root = Path(cls.certdir.name)
        subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
            "-keyout", str(root / "key.pem"), "-out", str(root / "ca.pem"),
            "-days", "1", "-subj", "/CN=Hasura starter test CA",
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cls.ca = base64.b64encode((root / "ca.pem").read_bytes()).decode()

    @classmethod
    def tearDownClass(cls):
        cls.certdir.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name) / "startup"
        self.env = {
            "DATABASE_URL": "postgres://demo:p%40ssword@db.example.com:5432/defaultdb",
            "HASURA_GRAPHQL_ADMIN_SECRET": "a" * 64,
            "AIVEN_CA_CERT_BASE64": self.ca,
        }

    def test_runtime_verifies_ca_and_hostname_and_ignores_uri_overrides(self):
        self.env["DATABASE_URL"] += "?sslmode=disable&sslrootcert=/wrong&host=other.example.com"
        prepare(self.env, self.directory)
        uri = urlsplit(self.env["HASURA_GRAPHQL_METADATA_DATABASE_URL"])
        self.assertEqual(uri.hostname, "db.example.com")
        self.assertEqual(uri.password, "p%40ssword")
        self.assertEqual(parse_qs(uri.query), {
            "sslmode": ["verify-full"], "sslrootcert": [str(self.directory / "aiven-ca.pem")],
            "connect_timeout": ["10"],
        })
        self.assertEqual(self.env["HASURA_GRAPHQL_DATABASE_URL"], uri.geturl())
        self.assertEqual((self.directory / "aiven-ca.pem").stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.directory.stat().st_mode & 0o777, 0o700)

    def test_local_tls_opt_out_is_explicit(self):
        self.env.pop("AIVEN_CA_CERT_BASE64")
        with self.assertRaisesRegex(ValueError, "valid PEM"):
            prepare(self.env, self.directory)
        self.env["LOCAL_DEVELOPMENT"] = "true"
        prepare(self.env, self.directory)
        self.assertEqual(parse_qs(urlsplit(self.env["DATABASE_URL"]).query)["sslmode"], ["disable"])
        self.assertFalse((self.directory / "aiven-ca.pem").exists())

    def test_invalid_ca_fails_closed(self):
        for ca in ("", "not-base64!", base64.b64encode(b"not a certificate").decode()):
            with self.subTest(ca=ca):
                self.env["AIVEN_CA_CERT_BASE64"] = ca
                with self.assertRaisesRegex(ValueError, "valid PEM"):
                    prepare(self.env, self.directory)

    def test_secret_required_and_header_safe(self):
        for secret in ("", "short", "a" * 31, "a" * 32 + "\n", "é" * 32, "a" * 32 + " "):
            with self.subTest(length=len(secret)):
                self.env["HASURA_GRAPHQL_ADMIN_SECRET"] = secret
                with self.assertRaisesRegex(ValueError, "HASURA_GRAPHQL_ADMIN_SECRET"):
                    prepare(self.env, self.directory)

    def test_invalid_uris_fail_without_disclosing_credentials(self):
        password = "sensitive-test-password"
        uris = [
            f"postgres://u:{password}@db:bad/name",
            f"postgres://u:{password}@[broken:5432/name",
            f"postgres://u:{password}@db/name",
            f"postgres://u:{password}@db:5432/",
            f"https://u:{password}@db:5432/name",
            f"postgres://u:{password}@db:5432/name#fragment",
            "postgres://db:5432/name",
        ]
        for uri in uris:
            with self.subTest(uri=uri):
                with self.assertRaises(ValueError) as error:
                    database_uri(uri, False, Path("/tmp/ca.pem"))
                self.assertNotIn(password, str(error.exception))

    def test_auth_and_mode_misconfiguration_rejected(self):
        for key, value in (("LOCAL_DEVELOPMENT", "yes"),
                           ("HASURA_GRAPHQL_UNAUTHORIZED_ROLE", "anonymous"),
                           ("HASURA_GRAPHQL_ADMIN_SECRETS", '["other"]')):
            with self.subTest(key=key):
                env = dict(self.env, **{key: value})
                with self.assertRaises(ValueError):
                    prepare(env, self.directory)

    def test_startup_targets_persistent_db_and_native_console(self):
        self.env["HASURA_GRAPHQL_DEV_MODE"] = "true"
        prepare(self.env, self.directory)
        self.assertEqual(self.env["HASURA_GRAPHQL_DATABASE_URL"], self.env["HASURA_GRAPHQL_METADATA_DATABASE_URL"])
        self.assertEqual(self.env["HASURA_GRAPHQL_ENABLE_CONSOLE"], "true")
        self.assertEqual(self.env["HASURA_GRAPHQL_SERVER_PORT"], "8080")
        self.assertEqual(self.env["HASURA_GRAPHQL_DEV_MODE"], "false")
        self.assertEqual(self.env["HASURA_GRAPHQL_ADMIN_INTERNAL_ERRORS"], "false")
        self.assertEqual(self.env["HASURA_GRAPHQL_ENABLE_TELEMETRY"], "false")


if __name__ == "__main__":
    unittest.main()
