"""
Probe whatever is listening on localhost (default port 5000) and print markers
so you can see if it is *this* repo's SSR app or an old process / wrong folder.

Usage (from repo root, with Flask already running):

    python scripts/diagnose_live_server.py
    python scripts/diagnose_live_server.py http://127.0.0.1:5001
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from urllib.parse import urljoin


def _fetch(url: str) -> tuple[int, dict[str, str], bytes]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read()
            headers = {k.lower(): v for k, v in resp.headers.items()}
            return resp.status, headers, body
    except urllib.error.HTTPError as e:
        body = e.read()
        headers = {k.lower(): v for k, v in e.headers.items()} if e.headers else {}
        return e.code, headers, body


def main() -> int:
    base = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000").rstrip("/")
    print(f"Probing: {base}\n")

    try:
        status, headers, body = _fetch(base + "/")
    except urllib.error.URLError as e:
        print("Connection failed:", e)
        print()
        print(
            "Nothing is listening on that host/port, or a firewall blocked it.\n"
            "Start this repo's app from the repo root:  python run.py\n"
            "Then run this script again (or try http://127.0.0.1:5000)."
        )
        return 1

    loc = headers.get("location")
    chain = [f"GET / -> {status}"]
    final_url = base + "/"
    if status in (301, 302, 303, 307, 308) and loc:
        next_url = urljoin(base + "/", loc)
        chain.append(f"redirect -> {next_url}")
        status, headers, body = _fetch(next_url)
        final_url = next_url
        chain.append(f"GET redirect target -> {status}")

    text = body.decode("utf-8", errors="replace")
    print("Redirect chain:", " | ".join(chain))
    print(f"Final URL: {final_url}")
    print(f"Content-Length (bytes): {len(body)}")
    print(f"X-Mzansi-Template header: {headers.get('x-mzansi-template', '(none)')}")
    print()
    print("--- Markers (this repo's SSR feed should match the LEFT column) ---")
    print(f"  MZANSI_TEMPLATE_V2 in HTML: {'MZANSI_TEMPLATE_V2' in text}")
    print(f"  ssr-nav in HTML:            {'ssr-nav' in text}")
    print(f"  mzansi-assets CSS link:     {'mzansi-assets' in text}")
    print(f"  'Celebration' in HTML:      {'Celebration' in text}  (should be False)")
    print(f"  'topbar' in HTML:           {'topbar' in text}  (should be False)")
    print()

    wrong = ("topbar" in text or "Celebration Wall" in text) and "MZANSI_TEMPLATE_V2" not in text
    if wrong:
        print("*** CONCLUSION: This is NOT the current MzansiBuilds repo on Git/Cursor. ***")
        print(
            "    Another program is using this port (old Flask clone, different project, or IDE preview).\n"
            "    This repo serves GET / with 302 -> /ssr/feed and has /__mzansi-ui-check JSON.\n"
            "    Windows:  netstat -ano | findstr :5000   then   taskkill /PID <pid> /F\n"
            "    Then:     cd <this-repo-root> && python run.py\n"
        )
    elif status == 200 and "MZANSI_TEMPLATE_V2" not in text:
        print("*** WARNING: GET / returned 200 without the MZANSI_TEMPLATE_V2 marker. ***")
        print("    Wrong app on this port, or templates not from this repo.\n")

    print("--- First 600 characters of body ---")
    print(text[:600])
    print()

    # JSON probe
    try:
        st, _, raw = _fetch(base + "/__mzansi-ui-check")
        raw_txt = raw.decode("utf-8", errors="replace").strip()
        if st != 200:
            print(f"--- GET /__mzansi-ui-check -> HTTP {st} ---")
            print(raw_txt[:500])
        else:
            data = json.loads(raw_txt)
            print("--- GET /__mzansi-ui-check ---")
            print(json.dumps(data, indent=2))
    except json.JSONDecodeError:
        print("--- GET /__mzansi-ui-check (not JSON) ---")
        try:
            _, _, raw = _fetch(base + "/__mzansi-ui-check")
            print(raw.decode("utf-8", errors="replace")[:500])
        except urllib.error.URLError as e:
            print(e)
    except urllib.error.URLError as e:
        print("Could not read /__mzansi-ui-check:", e)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
