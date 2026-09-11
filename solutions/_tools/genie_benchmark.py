#!/usr/bin/env python3
"""
Benchmark / regression-test the 4 workshop Genie Agents against a fixed question set
with known-correct answers. For each question it starts a Genie conversation, waits for
the answer + query result, and checks that every expected token (a number or a name)
appears in the answer text or the returned rows. Prints a per-agent pass/fail table and
an overall score, and writes a JSON results file.

This is both (a) a facilitator pre-flight check that each Genie Agent is answering
correctly before the onsite, and (b) a regression test to re-run after pointing the
agents at real St. Luke's data (update the expected answers if the real numbers differ).

Usage:
  # benchmark every agent defined in the benchmarks file
  GENIE_PROFILE=stlukes-workshop uv run --with requests --python 3.11 \
      python genie_benchmark.py solutions/_tools/genie_benchmarks.json

  # benchmark a single use case
  GENIE_PROFILE=stlukes-workshop uv run --with requests --python 3.11 \
      python genie_benchmark.py solutions/_tools/genie_benchmarks.json --only ckd

Auth: host + bearer token come from the Databricks CLI profile in GENIE_PROFILE
(default kk_test). The benchmarks file carries each use case's space_id + question set.
"""
import json, os, subprocess, sys, time
import requests

PROFILE = os.environ.get("GENIE_PROFILE", "kk_test")


def get_host():
    import configparser
    cp = configparser.ConfigParser()
    cp.read(os.path.expanduser("~/.databrickscfg"))
    return cp[PROFILE]["host"].rstrip("/")


def get_token():
    r = subprocess.run(["databricks", "auth", "token", "--profile", PROFILE],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout)["access_token"]
    except Exception:
        sys.exit(f"could not get token: {r.stdout}\n{r.stderr}")


def ask(host, tok, space_id, question):
    """Ask one question; return (answer_text, sql, rows_as_text)."""
    h = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
    base = f"{host}/api/2.0/genie/spaces/{space_id}"
    r = requests.post(f"{base}/start-conversation", headers=h,
                      json={"content": question}, timeout=30)
    r.raise_for_status()
    j = r.json()
    cid = j.get("conversation_id") or j["conversation"]["id"]
    mid = j.get("message_id") or j["message"]["id"]
    m, status = {}, None
    for _ in range(75):  # up to ~5 min
        m = requests.get(f"{base}/conversations/{cid}/messages/{mid}", headers=h, timeout=30).json()
        status = m.get("status")
        if status in ("COMPLETED", "FAILED", "CANCELLED"):
            break
        time.sleep(4)
    atts = m.get("attachments", []) or []
    text = " ".join(a.get("text", {}).get("content", "") for a in atts if a.get("text"))
    sql_att = next((a for a in atts if a.get("query")), None)
    sql, rows_text = "", ""
    if sql_att:
        sql = sql_att["query"].get("query", "").strip()
        aid = sql_att.get("attachment_id")
        try:
            qr = requests.get(f"{base}/conversations/{cid}/messages/{mid}/attachments/{aid}/query-result",
                              headers=h, timeout=60).json()
            rows = qr.get("statement_response", {}).get("result", {}).get("data_array", []) or []
            rows_text = " ".join(str(c) for row in rows for c in row)
        except Exception as e:
            rows_text = f"(result fetch error: {e})"
    return status, text, sql, rows_text


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: genie_benchmark.py <benchmarks.json> [--only <key>]")
    bench = json.load(open(sys.argv[1]))
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]
    host, tok = get_host(), get_token()
    results, n_pass, n_total = {}, 0, 0
    for key, spec in bench.items():
        if key.startswith("_") or not isinstance(spec, dict):
            continue
        if only and key != only:
            continue
        space_id = spec["space_id"]
        if not space_id or space_id.startswith("<"):
            print(f"\n## {key}: SKIPPED (no space_id set yet)")
            continue
        print(f"\n## {key}  (space {space_id})")
        results[key] = []
        for q in spec["questions"]:
            status, text, sql, rows = ask(host, tok, space_id, q["question"])
            haystack = (text + " " + rows).lower()
            hay_nc = haystack.replace(",", "")  # so "1,524" matches expected "1524"
            expect = q.get("expect_all", [])
            missing = [e for e in expect
                       if str(e).lower() not in haystack
                       and str(e).lower().replace(",", "") not in hay_nc]
            ok = status == "COMPLETED" and not missing
            n_total += 1
            n_pass += 1 if ok else 0
            results[key].append({"question": q["question"], "pass": ok,
                                 "status": status, "missing": missing})
            mark = "PASS" if ok else "FAIL"
            print(f"  [{mark}] {q['question']}")
            if not ok:
                print(f"         status={status} missing={missing}")
                if text:
                    print(f"         answer: {text[:200]}")
    print(f"\n=== OVERALL: {n_pass}/{n_total} passed ===")
    out = sys.argv[1].replace(".json", "_results.json")
    json.dump({"pass": n_pass, "total": n_total, "results": results}, open(out, "w"), indent=2)
    print(f"wrote {out}")
    sys.exit(0 if n_pass == n_total else 1)


if __name__ == "__main__":
    main()
