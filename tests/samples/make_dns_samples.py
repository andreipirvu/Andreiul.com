"""Write the DNS TXT samples for Lab 5: raw Suricata EVE and the ECS it becomes."""
import base64
import json
from pathlib import Path

samples = Path("tests/samples")
blob = base64.b64encode(bytes(range(180))).decode()  # 240 characters, looks like encoded data
dkim = "v=DKIM1; k=rsa; p=" + "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA" * 5  # long but benign


def eve(name, rtype, data=None, kind="answer"):
    dns = {"version": 2, "type": kind, "id": 4242, "rrname": name, "rrtype": rtype, "rcode": "NOERROR"}
    if kind == "answer":
        dns["answers"] = [{"rrname": name, "rrtype": rtype, "ttl": 60, "rdata": data}]
    return {"timestamp": "2026-11-09T10:00:00.000000+0000", "flow_id": 1, "in_iface": "eth0",
            "event_type": "dns", "src_ip": "10.0.0.53", "src_port": 53, "dest_ip": "10.0.0.5",
            "dest_port": 40000, "proto": "UDP", "dns": dns}


def ecs(rec):
    """The fields the rule reads, as pipelines/suricata.conf writes them."""
    d = rec["dns"]
    out = {"type": d["type"], "question": {"name": d["rrname"], "type": d["rrtype"]}}
    if "answers" in d:
        out["answers"] = [{"name": a["rrname"], "type": a["rrtype"], "ttl": a["ttl"],
                           "data": a["rdata"]} for a in d["answers"]]
    return {"event": {"module": "suricata", "dataset": "suricata.eve"}, "dns": out}


positive = [eve("a1b2c3.updates.example.net", "TXT", blob)]
negative = [
    eve("example.com", "TXT", "v=spf1 include:_spf.example.com ~all"),  # short TXT
    eve("a1b2c3.updates.example.net", "TXT", kind="query"),             # query, no answer
    eve("selector1._domainkey.example.com", "TXT", dkim),                # long but benign
]
for name, records in [("positive", positive), ("negative", negative)]:
    lines = lambda f: "".join(json.dumps(f(r)) + "\n" for r in records)
    (samples / f"eve_dns_txt_{name}.json").write_text(lines(lambda r: r))
    (samples / f"ecs_dns_txt_{name}.json").write_text(lines(ecs))
print("4 sample files written to", samples)
