#!/usr/bin/env python3
"""
Ask a Databricks Genie space a question and print the answer + SQL + result rows.
Robust polling client used to verify Genie Agents live during the workshop build.

Usage:
  uv run --with requests --python 3.11 python genie_ask.py <space_id> "<question>" [conversation_id]

Auth: pulls host + bearer token from the Databricks CLI (profile kk_test).
"""
import json, os, subprocess, sys, time
import requests

# Override with GENIE_PROFILE for other workspaces (e.g. the SLHS workshop workspace).
PROFILE = os.environ.get("GENIE_PROFILE", "kk_test")


def cli(*args):
    return subprocess.run(["databricks", *args, "--profile", PROFILE],
                          capture_output=True, text=True)


def get_host():
    # ~/.databrickscfg host for the profile
    import configparser, os
    cp = configparser.ConfigParser()
    cp.read(os.path.expanduser("~/.databrickscfg"))
    return cp[PROFILE]["host"].rstrip("/")


def get_token():
    r = cli("auth", "token")
    try:
        return json.loads(r.stdout)["access_token"]
    except Exception:
        sys.exit(f"could not get token: {r.stdout}\n{r.stderr}")


def main():
    space_id = sys.argv[1]
    question = sys.argv[2]
    conv_id = sys.argv[3] if len(sys.argv) > 3 else None
    host = get_host()
    tok = get_token()
    h = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
    base = f"{host}/api/2.0/genie/spaces/{space_id}"

    if conv_id:
        r = requests.post(f"{base}/conversations/{conv_id}/messages",
                          headers=h, json={"content": question}, timeout=30)
    else:
        r = requests.post(f"{base}/start-conversation",
                          headers=h, json={"content": question}, timeout=30)
    r.raise_for_status()
    j = r.json()
    cid = j.get("conversation_id") or j["conversation"]["id"]
    mid = j.get("message_id") or j["message"]["id"]

    status = None
    for _ in range(60):  # up to ~4 min
        m = requests.get(f"{base}/conversations/{cid}/messages/{mid}", headers=h, timeout=30).json()
        status = m.get("status")
        if status in ("COMPLETED", "FAILED", "CANCELLED"):
            break
        time.sleep(4)

    print(f"Q: {question}")
    print(f"conversation_id: {cid}")
    print(f"status: {status}")
    atts = m.get("attachments", []) or []
    for a in atts:
        if a.get("text", {}).get("content"):
            print("TEXT:", a["text"]["content"])
    sql_att = next((a for a in atts if a.get("query")), None)
    if sql_att:
        print("SQL:", sql_att["query"].get("query", "").strip()[:1500])
        aid = sql_att.get("attachment_id")
        try:
            qr = requests.get(f"{base}/conversations/{cid}/messages/{mid}/attachments/{aid}/query-result",
                              headers=h, timeout=60).json()
            rows = qr.get("statement_response", {}).get("result", {}).get("data_array", [])
            cols = [c["name"] for c in qr.get("statement_response", {}).get("manifest", {}).get("schema", {}).get("columns", [])]
            print("COLUMNS:", cols)
            for row in rows[:15]:
                print("ROW:", row)
        except Exception as e:
            print("result fetch error:", e)


if __name__ == "__main__":
    main()
