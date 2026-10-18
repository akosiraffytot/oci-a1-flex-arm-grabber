# oci-arm-catcher (Docker / CasaOS edition)

Dockerized fork of [alexpua/oci-arm-catcher](https://github.com/alexpua/oci-arm-catcher) that runs 24/7 on a home server (CasaOS, any Docker host), pings you on Telegram the moment free Oracle Cloud ARM capacity appears, and serves a live status/log page in your browser.

The original is a single PowerShell/bash script for a desktop machine. This fork wraps the same proven retry loop in a container so you can start it, close the browser tab, and let it hunt for days until it catches an `A1.Flex` instance.

> Use the [upstream project](https://github.com/alexpua/oci-arm-catcher) directly if you want the native Windows (PowerShell) or macOS/Linux script without Docker.

## Features

- **24/7 container** — survives reboots (`restart: unless-stopped`), survives closed browser tabs
- **Telegram push** notification on success *and* on fatal error
- **Web UI** at a mapped port: dark terminal page with a live status badge (`RUNNING` / `CAUGHT` / `FAILED`) and the full auto-scrolling log, refreshed every 5s
- **CasaOS one-compose install** — or any Docker host
- **Two auth options**: mount your existing `~/.oci/config`, or paste credentials into `.env` (no files to mount)
- **Two SSH key options**: inline public key content, or mounted key file
- Multi-AD rotation, polite retry interval, retry-only-on-capacity-errors (same smart loop as upstream)

## Quick start (CasaOS)

1. Copy this repo onto your CasaOS server (git clone, or upload the folder).
2. Create your config:

   ```bash
   cp .env.example .env
   nano .env        # fill in your OCIDs, SSH key, Telegram, auth
   ```

   See [Configuration](#configuration) below. To discover your OCIDs, run `scripts/get-config.sh` on any machine that already has the OCI CLI configured.

3. Build and start:

   ```bash
   docker compose up -d --build
   ```

   Or in CasaOS: **App Store → + → Custom** → paste the contents of `docker-compose.yml`, then edit `.env` and restart the app.

4. Open the status page: `http://<casaos-ip>:8090` (or `WEB_PORT` if you changed it). Close the tab — the container keeps running.
5. When it catches an instance you get a Telegram message. The page flips to **CAUGHT** and shows the instance OCID in the log. Stop the app from CasaOS (or `docker compose down`) when you're done.

## Configuration

All settings live in `.env` (never commit it — already gitignored).

| Variable | Required | Notes |
|---|---|---|
| `COMPARTMENT_ID` | yes | Tenancy root OCID, or a child compartment |
| `DISPLAY_NAME` | yes | Instance name in the OCI console |
| `AVAILABILITY_DOMAIN` | yes\* | Single AD |
| `AVAILABILITY_DOMAINS` | yes\* | Comma-separated ADs to rotate; overrides the single AD |
| `SUBNET_ID` | yes | Public subnet OCID in your VCN |
| `IMAGE_ID` | yes | An **aarch64/ARM** image OCID |
| `OCPUS` | yes | Always Free max is **2** total |
| `MEMORY_GB` | yes | Always Free max is **12** total |
| `RETRY_INTERVAL` | no | Seconds between attempts (default `300`) |
| `SSH_PUBLIC_KEY` | one of | Inline SSH **public** key content |
| `SSH_KEY_FILE` | one of | Path to a mounted `.pub` file |
| `WEB_PORT` | no | Host port for the web UI (default `8090`) |
| `TELEGRAM_BOT_TOKEN` | no | Enables Telegram notifications |
| `TELEGRAM_CHAT_ID` | no | Your Telegram chat id |

\* Set **either** `AVAILABILITY_DOMAIN` **or** `AVAILABILITY_DOMAINS`. If both are set, the rotating list wins.

The Always Free Ampere allowance is **2 OCPU / 12 GB total** (Oracle halved it from 4/24 in June 2026). Asking for more fails fast with `LimitExceeded`, which the catcher stops on.

## Authentication

Pick **one**. The OCI CLI supports both natively — no code differences.

**Option A — mount your existing config** (no extra env vars). Uncomment the two mounts in `docker-compose.yml`:

```yaml
volumes:
  - ~/.oci/config:/root/.oci/config:ro
  - ~/.oci/oci_api_key.pem:/root/.oci/oci_api_key.pem:ro
```

The CLI finds them at its default location (`/root/.oci`). Keep the key filename in your config pointing at the mounted path.

**Option B — env auth** (no file mounts; paste from your `~/.oci/config` into `.env`):

```bash
OCI_CLI_TENANCY="ocid1.tenancy.oc1..xxxx"
OCI_CLI_USER="ocid1.user.oc1..xxxx"
OCI_CLI_FINGERPRINT="aa:bb:cc:..."
OCI_CLI_KEY_CONTENT="-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
OCI_CLI_REGION="eu-amsterdam-1"
# OCI_CLI_PASSPHRASE="..."   # only if your key has a passphrase
```

## SSH access

Pick **one**:

- **Inline content** (easiest on CasaOS): set `SSH_PUBLIC_KEY` in `.env` to the full contents of your `.pub` file.
- **Mounted file**: uncomment the `~/.ssh/...pub` mount in `docker-compose.yml` and set `SSH_KEY_FILE=/keys/ssh.pub`.

## Telegram setup

1. Message [@BotFather](https://t.me/BotFather) → `/newbot` → copy the token.
2. Get your chat id (e.g. message [@userinfobot](https://t.me/userinfobot)).
3. Put both in `.env` and restart.

The catcher notifies on **success** (instance created) and on **fatal error** (bad OCID, auth failure, quota exceeded), so you know if it dies overnight.

## How it works

Same loop as upstream:

```
loop:
  oci compute instance launch  --shape VM.Standard.A1.Flex ...
  ├─ success            → parse instance OCID, Telegram + web badge = CAUGHT, keep UI up
  ├─ "out of capacity"  → wait RETRY_INTERVAL, rotate AD, retry
  │   InternalError / LimitExceeded / TooManyRequests / timeout
  └─ any other error    → Telegram + web badge = FAILED, stop (fix your config)
```

It only retries on "come back later" errors and stops on real problems instead of looping forever. The web UI reads `/data/status` and `/data/catcher.log`, which the entrypoint keeps updated.

## Security

- The web UI is **unauthenticated**. It is meant for your LAN only — **do not port-forward it to the internet**.
- `.env` contains your OCI key material. Keep it out of git (already ignored) and out of shared folders.

## Development

Tests run entirely in Docker (bats + shellcheck + a Python web-server test):

```bash
./scripts/test.sh
```

The bash script is covered by [bats](https://github.com/bats-core/bats-core) tests that mock the `oci` CLI. The web server has a small Python `unittest`-style check.

## Disclaimer

This tool only calls the official OCI CLI on a polite retry interval — it doesn't bypass any limits. You're responsible for staying within your account's terms and free-tier limits. Provided as-is under the MIT License.

## Credits

- Original project: [alexpua/oci-arm-catcher](https://github.com/alexpua/oci-arm-catcher) (MIT)
- This fork adds Docker/CasaOS packaging, the web UI, and Telegram notifications.
