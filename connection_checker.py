import json
from pathlib import Path
from datetime import datetime
import logging

try:
    import requests
except Exception:  # requests may not be installed
    requests = None

SYSTEM_LOG = Path(__file__).resolve().parent / "logs" / "system.log"


def _log(message: str) -> None:
    SYSTEM_LOG.parent.mkdir(exist_ok=True)
    timestamp = datetime.now().isoformat()
    with SYSTEM_LOG.open("a") as log_file:
        log_file.write(f"{timestamp} - {message}\n")


def _load_json(path: Path) -> dict:
    try:
        with path.open("r") as f:
            return json.load(f)
    except Exception as exc:
        _log(f"Failed to load {path.name}: {exc}")
        return {}


def check_all_connections() -> dict:
    base = Path(__file__).resolve().parent
    config = _load_json(base / "config.json")
    secrets = _load_json(base / "secrets.json")

    results = {}

    # HyperHDR
    try:
        if requests is None:
            raise RuntimeError("requests not available")
        ip = config.get("hyperhdr_ip", "localhost")
        port = config.get("hyperhdr_port", 8090)
        resp = requests.get(f"http://{ip}:{port}/json-rpc", timeout=5)
        results["hyperhdr"] = "online" if resp.ok else "offline"
    except Exception as exc:
        _log(f"HyperHDR check failed: {exc}")
        results["hyperhdr"] = "offline"

    # ESP32
    try:
        if requests is None:
            raise RuntimeError("requests not available")
        ip = config.get("esp32_ip", "")
        resp = requests.get(f"http://{ip}/ping", timeout=5)
        results["esp32"] = "online" if resp.ok else "offline"
    except Exception as exc:
        _log(f"ESP32 check failed: {exc}")
        results["esp32"] = "offline"

    # Philips Hue
    try:
        if requests is None:
            raise RuntimeError("requests not available")
        ip = config.get("hue_ip", "")
        token = secrets.get("hue_token", "")
        resp = requests.get(f"http://{ip}/api/{token}/config", timeout=5)
        results["hue"] = "online" if resp.ok else "offline"
    except Exception as exc:
        _log(f"Hue check failed: {exc}")
        results["hue"] = "offline"

    # SSH to Raspberry Pi
    try:
        import paramiko
    except Exception as exc:
        _log(f"Paramiko import failed: {exc}")
        results["ssh"] = "missing paramiko"
    else:
        try:
            host = config.get("raspberry_ip", "")
            username = secrets.get("ssh_user", "")
            password = secrets.get("ssh_password", "")

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=host, username=username, password=password, timeout=5)
            stdin, stdout, stderr = ssh.exec_command("echo online")
            output = stdout.read().decode().strip()
            results["ssh"] = output if output else "unknown"
            ssh.close()
        except paramiko.AuthenticationException:
            results["ssh"] = "auth failed"
            _log("SSH authentication failed")
        except Exception as exc:
            results["ssh"] = "offline"
            _log(f"SSH check failed: {exc}")

    _log(f"Connection summary: {results}")
    return results


if __name__ == "__main__":
    summary = check_all_connections()
    print(summary)
