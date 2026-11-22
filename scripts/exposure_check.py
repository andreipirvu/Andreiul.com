"""Record what Shodan already knows about your own public IP (RISK-REGISTER R-05).

Query only an address you own or are authorised to assess. One host() call per
run; the free tier rate-limits loops. Lab 7 diffs these snapshots and alerts.
"""
import json
import os
from datetime import date
from pathlib import Path


def snapshot(host):
    """Keep the fields that tell you whether your exposure changed."""
    return {
        "ip": host["ip_str"],
        "ports": sorted(host.get("ports", [])),
        "org": host.get("org"),
        "last_update": host.get("last_update"),
    }


def main():
    import shodan

    api = shodan.Shodan(os.environ["SHODAN_KEY"])
    try:
        host = api.host(os.environ["OWN_PUBLIC_IP"])
    except shodan.APIError as err:
        raise SystemExit(f"Shodan: {err}")
    snap = snapshot(host)
    out = Path("exposure") / f"{date.today()}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(snap, indent=2) + "\n")
    print(json.dumps(snap, indent=2))


if __name__ == "__main__":
    main()
