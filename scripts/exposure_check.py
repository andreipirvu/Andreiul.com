"""Record what Shodan already knows about your own public IP (RISK-REGISTER R-05).

Query only an address you own or are authorised to assess. One lookup per run; the
free tier rate-limits loops. Lab 7 diffs these snapshots and alerts.

The full host() lookup needs a paid Shodan membership; a free API key gets 403. In that
case the script falls back to Shodan's free InternetDB (no key), which returns the
same open ports but no organisation or last-update date. The snapshot records which
source answered, so Lab 7 compares like with like.
"""
import json
import os
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

INTERNETDB = "https://internetdb.shodan.io/{ip}"


def snapshot(host):
    """Keep the fields that tell you whether your exposure changed (full Shodan API)."""
    return {
        "source": "shodan-api",
        "ip": host["ip_str"],
        "ports": sorted(host.get("ports", [])),
        "org": host.get("org"),
        "last_update": host.get("last_update"),
    }


def snapshot_internetdb(ip, data):
    """Same shape from an InternetDB answer; it has no org or last-update date."""
    return {
        "source": "internetdb",
        "ip": data.get("ip", ip),
        "ports": sorted(data.get("ports", [])),
        "org": None,
        "last_update": None,
    }


def fetch_internetdb(ip):
    """One keyless call. A 404 means Shodan has no data on the IP: nothing seen open."""
    req = urllib.request.Request(INTERNETDB.format(ip=ip), headers={"User-Agent": "exposure_check"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as err:
        if err.code == 404:
            return {"ip": ip, "ports": []}
        raise SystemExit(f"InternetDB: HTTP {err.code}") from None


def lookup(ip, key):
    import shodan

    try:
        return snapshot(shodan.Shodan(key).host(ip))
    except shodan.APIError as err:
        if "403" not in str(err) and "Access denied" not in str(err):
            raise SystemExit(f"Shodan: {err}") from None
        print("Shodan API: host lookup needs a membership; using the free InternetDB instead.")
        return snapshot_internetdb(ip, fetch_internetdb(ip))


def main():
    snap = lookup(os.environ["OWN_PUBLIC_IP"], os.environ["SHODAN_KEY"])
    out = Path("exposure") / f"{date.today()}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(snap, indent=2) + "\n")
    print(json.dumps(snap, indent=2))


if __name__ == "__main__":
    main()
