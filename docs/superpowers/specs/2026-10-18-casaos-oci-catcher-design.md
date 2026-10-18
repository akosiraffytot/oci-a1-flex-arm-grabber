# CasaOS OCI ARM Catcher — Design Spec

Dockerized fork of [alexpua/oci-arm-catcher](https://github.com/alexpua/oci-arm-catcher) that runs 24/7 on CasaOS, notifies via Telegram, and serves a web log/status page.

## Decisions

- **Script**: fork upstream bash version (not PowerShell) — Linux container. Patches:
  1. `notify()` gains Telegram branch (`TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` via curl) — fires on success and fatal error
  2. `SSH_PUBLIC_KEY` env (inline key content) accepted as alternative to mounted `SSH_KEY_FILE`
  3. `set_status` helper writes `running|caught|failed` to `STATUS_FILE` (no-op when unset)
  4. `.env` file optional when required vars already present in environment (container/compose case)
- **Auth**: OCI CLI native dual support — mounted config (`OCI_CLI_CONFIG_FILE` or default `/root/.oci/config`) OR env vars `OCI_CLI_TENANCY`, `OCI_CLI_USER`, `OCI_CLI_FINGERPRINT`, `OCI_CLI_KEY_CONTENT`, `OCI_CLI_REGION`. Zero custom code.
- **Container processes**: entrypoint starts catcher in background (stdout tee'd to `/data/catcher.log`), web server in foreground. Catcher exit (caught/failed) does NOT stop container — UI keeps serving final state. `docker stop` trap kills catcher.
- **Web UI**: Python stdlib `http.server` on `0.0.0.0:8090`. Endpoints: `GET /` (static dark-terminal `index.html`), `GET /log` (plain text), `GET /status` (`{"status": "..."}`), else 404. Page polls both endpoints every 5s, badge RUNNING/CAUGHT/FAILED, auto-scroll log. No auth — LAN only.
- **Status lifecycle**: entrypoint writes `running`; script writes `caught` on success, `failed` on validation or fatal error.
- **Compose**: `env_file: .env`, host port `${WEB_PORT:-8090}:8090`, bind mount `./data:/data`, `restart: unless-stopped`. Commented examples for config/key/SSH mounts.
- **Tests**: fork upstream bats suite (11 tests must stay passing) + 7 new bats cases (telegram mock curl ×2, SSH_PUBLIC_KEY, env-only config, status caught/failed/failed-validation) + `tests/web_server_test.py` + shellcheck — all run via Docker (`scripts/test.sh`), no host toolchain needed.
- **Out of scope**: log rotation (~6 MB/year), UI auth, GHCR prebuilt multi-arch images, PowerShell port (upstream covers Windows).

## Constraints

- MIT license: keep upstream attribution, credit in README
- LF line endings enforced via `.gitattributes` (Windows dev host)
- Runtime deps only: oci-cli, curl, jq, bash, python3 stdlib
