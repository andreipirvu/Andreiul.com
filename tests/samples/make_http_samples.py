"""Write the HTTP samples for my own rule (Lab 5 Part F): raw Suricata EVE and the ECS it becomes.

Positive: the beacon from the synthetic telemetry, an Internet Explorer 6 user agent posting
to a bare IP. Negative, the near misses the rule must ignore:
  - an old intranet client that still sends MSIE 6.0, but only GETs from a named server;
  - a current browser posting a login form to a router at a bare IP.
"""
import json
from pathlib import Path

samples = Path("tests/samples")
IE6 = "Mozilla/4.0 (compatible; MSIE 6.0; Win32)"
CHROME = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"


def eve(src, dst, host, url, ua, method, status=200):
    return {"timestamp": "2026-11-20T08:00:02.000000+0000", "flow_id": 7, "in_iface": "eth0",
            "event_type": "http", "src_ip": src, "src_port": 50123, "dest_ip": dst, "dest_port": 80,
            "proto": "TCP", "app_proto": "http",
            "http": {"hostname": host, "url": url, "http_user_agent": ua, "http_method": method,
                     "protocol": "HTTP/1.1", "status": status, "length": 512}}


def ecs(rec):
    """The fields the rule reads, as pipelines/suricata.conf writes them."""
    h = rec["http"]
    return {"event": {"module": "suricata", "dataset": "suricata.eve"},
            "http": {"request": {"method": h["http_method"]}, "response": {"status_code": h["status"]}},
            "user_agent": {"original": h["http_user_agent"]},
            "url": {"domain": h["hostname"], "original": h["url"]},
            "destination": {"ip": rec["dest_ip"]}}


positive = [eve("10.0.0.12", "203.0.113.66", "203.0.113.66", "/b/ccad50db", IE6, "POST")]
negative = [
    eve("10.0.0.30", "198.51.100.40", "intranet.example.com", "/reports/daily.html", IE6, "GET"),
    eve("10.0.0.31", "192.168.1.1", "192.168.1.1", "/cgi-bin/login", CHROME, "POST"),
]
for name, records in [("positive", positive), ("negative", negative)]:
    lines = lambda f: "".join(json.dumps(f(r)) + "\n" for r in records)
    (samples / f"eve_http_ie_post_{name}.json").write_text(lines(lambda r: r))
    (samples / f"ecs_http_ie_post_{name}.json").write_text(lines(ecs))
print("4 sample files written to", samples)
