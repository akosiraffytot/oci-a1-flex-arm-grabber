import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


def main():
    tmp = tempfile.mkdtemp()
    log_file = os.path.join(tmp, "catcher.log")
    status_file = os.path.join(tmp, "status")
    Path(log_file).write_text("[test] Attempt #1\n")
    Path(status_file).write_text("running\n")

    server_py = Path(__file__).parent.parent / "web" / "server.py"
    env = dict(os.environ, LOG_FILE=log_file, STATUS_FILE=status_file, WEB_PORT="18090")
    server = subprocess.Popen([sys.executable, str(server_py)], env=env)
    time.sleep(1)
    try:
        html = urllib.request.urlopen("http://127.0.0.1:18090/").read().decode()
        assert "oci-arm-catcher" in html, "index page missing app name"

        log = urllib.request.urlopen("http://127.0.0.1:18090/log").read().decode()
        assert "Attempt #1" in log, "log endpoint missing content"

        status = json.load(urllib.request.urlopen("http://127.0.0.1:18090/status"))
        assert status == {"status": "running"}, f"bad status: {status}"

        Path(status_file).write_text("caught\n")
        status = json.load(urllib.request.urlopen("http://127.0.0.1:18090/status"))
        assert status == {"status": "caught"}, f"status not live: {status}"

        missing_env = dict(
            os.environ,
            LOG_FILE=os.path.join(tmp, "nope.log"),
            STATUS_FILE=os.path.join(tmp, "nope.status"),
            WEB_PORT="18091",
        )
        server2 = subprocess.Popen([sys.executable, str(server_py)], env=missing_env)
        time.sleep(1)
        try:
            log = urllib.request.urlopen("http://127.0.0.1:18091/log").read().decode()
            assert "waiting" in log, "missing log file not handled"
            status = json.load(urllib.request.urlopen("http://127.0.0.1:18091/status"))
            assert status == {"status": "starting"}, f"missing status file not handled: {status}"
        finally:
            server2.kill()

        try:
            urllib.request.urlopen("http://127.0.0.1:18090/nope")
            raise AssertionError("404 not returned")
        except urllib.error.HTTPError as e:
            assert e.code == 404
    finally:
        server.kill()
    print("web_server_test: OK")


if __name__ == "__main__":
    main()
