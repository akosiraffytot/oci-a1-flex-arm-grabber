#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker run --rm -v "$PWD":/repo -w /repo --entrypoint sh bats/bats:latest \
    -c 'apk add -q python3 && bats tests/'
docker run --rm -v "$PWD":/repo -w /repo koalaman/shellcheck:stable \
    shellcheck oci-arm-catcher.sh entrypoint.sh scripts/get-config.sh scripts/test.sh
docker run --rm -v "$PWD":/repo -w /repo python:3.12-slim python tests/web_server_test.py
