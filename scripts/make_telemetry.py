"""Synthetic Suricata EVE telemetry for the local stack (Lab 5 Part F, Lab 6 Part E).

Writes one day of mostly ordinary traffic from a small office network, with a few
suspicious behaviours mixed in. Nothing here is real: hosts are private addresses,
outside addresses come from the documentation ranges (RFC 5737), domains end in
example.com/.net/.org. The output is deterministic (fixed seed), so a rule tested on it
behaves the same on every machine.

    python3 scripts/make_telemetry.py              # writes data/telemetry.json
    python3 scripts/make_telemetry.py --list       # what is mixed in, and where

The suspicious behaviours are labelled only in --list, never in the events themselves,
so a detection has to find them from the telemetry alone.
"""
import argparse
import base64
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

SEED = 4242
DAY = datetime(2026, 11, 20, tzinfo=timezone.utc)
HOSTS = [f"10.0.0.{i}" for i in range(10, 30)]
RESOLVER = "10.0.0.53"
OUTSIDE = [f"198.51.100.{i}" for i in range(1, 60)] + [f"192.0.2.{i}" for i in range(1, 40)]
DOMAINS = ["www.example.com", "mail.example.com", "cdn.example.net", "api.example.org",
           "docs.example.com", "updates.example.net", "login.example.org", "static.example.net"]
BROWSER_UA = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0",
]
INJECTED = []


def ts(t):
    return t.strftime("%Y-%m-%dT%H:%M:%S.%f") + "+0000"


def base(t, etype, src, sport, dst, dport, proto, app=None, flow=None):
    ev = {"timestamp": ts(t), "flow_id": flow or random.randint(10**9, 10**10), "in_iface": "eth0",
          "event_type": etype, "src_ip": src, "src_port": sport, "dest_ip": dst,
          "dest_port": dport, "proto": proto}
    if app:
        ev["app_proto"] = app
    return ev


def dns_pair(t, host, name, rtype="A", rdata=None):
    sport = random.randint(32768, 60999)
    q = base(t, "dns", host, sport, RESOLVER, 53, "UDP", "dns")
    q["dns"] = {"version": 2, "type": "query", "id": random.randint(1, 65535), "rrname": name,
                "rrtype": rtype}
    a = base(t + timedelta(milliseconds=20), "dns", RESOLVER, 53, host, sport, "UDP", "dns")
    a["dns"] = {"version": 2, "type": "answer", "id": q["dns"]["id"], "rrname": name, "rrtype": rtype,
                "rcode": "NOERROR",
                "answers": [{"rrname": name, "rrtype": rtype, "ttl": random.choice([60, 300, 3600]),
                             "rdata": rdata or random.choice(OUTSIDE)}]}
    return [q, a]


def http(t, host, dst, domain, url, ua, status=200, method="GET"):
    ev = base(t, "http", host, random.randint(32768, 60999), dst, 80, "TCP", "http")
    ev["http"] = {"hostname": domain, "url": url, "http_user_agent": ua, "http_method": method,
                  "protocol": "HTTP/1.1", "status": status, "length": random.randint(200, 90000)}
    return ev


def tls(t, host, dst, sni, port=443):
    ev = base(t, "tls", host, random.randint(32768, 60999), dst, port, "TCP", "tls")
    ev["tls"] = {"sni": sni, "version": "TLS 1.3", "ja3": {"hash": "%032x" % random.getrandbits(128)}}
    return ev


def flow(t, host, dst, dport, proto="TCP", app=None, pkts=12, bytes_=4800):
    ev = base(t, "flow", host, random.randint(32768, 60999), dst, dport, proto, app)
    ev["flow"] = {"pkts_toserver": pkts, "pkts_toclient": pkts, "bytes_toserver": bytes_,
                  "bytes_toclient": bytes_ * 3, "start": ts(t), "end": ts(t + timedelta(seconds=4)),
                  "state": "closed"}
    return ev


def alert(t, host, dst, dport, sid, sig, category, severity, app=None):
    ev = base(t, "alert", host, random.randint(32768, 60999), dst, dport, "TCP", app)
    ev["alert"] = {"action": "allowed", "gid": 1, "signature_id": sid, "rev": 2, "signature": sig,
                   "category": category, "severity": severity}
    return ev


def background(events):
    t = DAY + timedelta(hours=7)
    while t < DAY + timedelta(hours=19):
        host = random.choice(HOSTS)
        dom = random.choice(DOMAINS)
        ip = random.choice(OUTSIDE)
        events += dns_pair(t, host, dom, rdata=ip)
        r = random.random()
        if r < 0.55:
            events.append(tls(t + timedelta(milliseconds=60), host, ip, dom))
        elif r < 0.85:
            events.append(http(t + timedelta(milliseconds=60), host, ip, dom,
                               random.choice(["/", "/index.html", "/assets/app.js", "/news", "/img/logo.png"]),
                               random.choice(BROWSER_UA)))
        else:
            events.append(flow(t, host, ip, 443, app="tls"))
        if random.random() < 0.05:  # mail domains publish long but benign TXT records
            events += dns_pair(t, host, "selector1._domainkey.example.com", "TXT",
                               "v=DKIM1; k=rsa; p=" + "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA" * 5)
        if random.random() < 0.03:
            events.append(alert(t, host, ip, 443, 2013504, "ET POLICY GNU/Linux APT User-Agent Outbound",
                                "Not Suspicious Traffic", 3, "http"))
        t += timedelta(seconds=random.randint(20, 90))


def inject(events):
    # 1. DNS tunnelling over long TXT answers (what the Lab 5 rule detects).
    host, t = "10.0.0.23", DAY + timedelta(hours=10, minutes=4)
    for i in range(6):
        blob = base64.b64encode(random.randbytes(170)).decode()
        events += dns_pair(t + timedelta(seconds=37 * i), host, f"q{i:02d}x.updates.example.net", "TXT", blob)
    INJECTED.append(("T1071.004", "DNS C2 over long TXT answers", host, "dns"))

    # 2. Exfiltration in long DNS query labels.
    host, t = "10.0.0.17", DAY + timedelta(hours=13, minutes=31)
    secret = base64.b32encode(random.randbytes(300)).decode().lower().rstrip("=")
    for i in range(0, len(secret), 60):
        events += dns_pair(t + timedelta(seconds=i // 60 * 3), host,
                           f"{secret[i:i + 60]}.d.exfil-cdn.example.org")
    INJECTED.append(("T1048.003", "Data in very long DNS subdomain labels", host, "dns"))

    # 3. HTTP beacon with a user agent that real browsers never send, every 5 minutes.
    host, dst = "10.0.0.12", "203.0.113.66"
    for i in range(40):
        t = DAY + timedelta(hours=8, minutes=5 * i, seconds=random.randint(0, 3))
        events.append(http(t, host, dst, "203.0.113.66", f"/b/{random.getrandbits(32):08x}",
                           "Mozilla/4.0 (compatible; MSIE 6.0; Win32)", method="POST"))
    INJECTED.append(("T1071.001", "HTTP beacon, legacy browser user agent, fixed interval", host, "http"))

    # 4. TLS on a port that is not 443.
    host, t = "10.0.0.27", DAY + timedelta(hours=15, minutes=12)
    for i in range(8):
        events.append(tls(t + timedelta(minutes=i * 7), host, "198.51.100.200", "sync.example.net", 8443 + i % 2))
    INJECTED.append(("T1571", "TLS to non-standard ports", host, "tls"))

    # 5. A high-severity IDS alert among the noise.
    t = DAY + timedelta(hours=16, minutes=48)
    events.append(alert(t, "10.0.0.19", "192.0.2.150", 4444, 2027865,
                        "ET MALWARE Possible Reverse Shell Activity", "A Network Trojan was detected", 1))
    INJECTED.append(("T1059", "High-severity IDS alert (reverse shell)", "10.0.0.19", "alert"))

    # 6. Flows to the documentation address used as a known-bad indicator in Lab 6.
    t = DAY + timedelta(hours=11)
    events.append(flow(t, "10.0.0.14", "203.0.113.66", 443, app="tls"))
    INJECTED.append(("T1071", "Connection to a known-bad IP (Lab 6 indicator 203.0.113.66)", "10.0.0.14", "flow"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="data/telemetry.json")
    ap.add_argument("--list", action="store_true", help="print what was mixed in")
    args = ap.parse_args()
    random.seed(SEED)
    events = []
    background(events)
    inject(events)
    events.sort(key=lambda e: e["timestamp"])
    if args.list:
        for tech, what, host, etype in INJECTED:
            print(f"{tech:10} {etype:6} {host:11} {what}")
        return
    out = Path(args.out)
    out.parent.mkdir(exist_ok=True)
    out.write_text("".join(json.dumps(e) + "\n" for e in events))
    print(f"{len(events)} events written to {out} ({DAY:%Y-%m-%d}, 07:00 to 19:00 UTC)")


if __name__ == "__main__":
    main()
