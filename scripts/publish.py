#!/usr/bin/env python3
"""Publish one queued carousel post to Instagram via the Graph API.

Runs on a GitHub Actions runner. Reads IG_USER_ID / IG_ACCESS_TOKEN from the
environment (repository secrets) and the post definition from queue/<date>.json.
"""
import json, os, sys, time, urllib.parse, urllib.request

API = "https://graph.facebook.com/v21.0"
TOKEN = os.environ["IG_ACCESS_TOKEN"]
IG_USER = os.environ["IG_USER_ID"]
RAW_BASE = os.environ["RAW_BASE"].rstrip("/")   # https://raw.githubusercontent.com/<owner>/<repo>/main


def call(method, path, **params):
    params["access_token"] = TOKEN
    url = f"{API}/{path}"
    data = urllib.parse.urlencode(params).encode()
    if method == "GET":
        url = f"{url}?{data.decode()}"
        req = urllib.request.Request(url)
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise SystemExit(f"[{method} {path}] HTTP {e.code}\n{body}")


def wait_ready(container_id, label, tries=30):
    for i in range(tries):
        st = call("GET", container_id, fields="status_code,status")
        code = st.get("status_code")
        if code == "FINISHED":
            return
        if code == "ERROR":
            raise SystemExit(f"{label} failed: {st}")
        print(f"  {label}: {code} ({i+1}/{tries})", flush=True)
        time.sleep(5)
    raise SystemExit(f"{label} timed out")


def main():
    date = sys.argv[1]
    post = json.loads(open(f"queue/{date}.json", encoding="utf-8").read())

    if post.get("status") != "approved":
        raise SystemExit(f"queue/{date}.json is not approved (status={post.get('status')!r})")

    images = post["images"]
    if not 1 <= len(images) <= 10:
        raise SystemExit(f"carousel needs 1-10 images, got {len(images)}")

    # 1. one container per image
    children = []
    for n, rel in enumerate(images, 1):
        url = f"{RAW_BASE}/{rel}"
        print(f"[{n}/{len(images)}] {url}", flush=True)
        res = call("POST", f"{IG_USER}/media", image_url=url, is_carousel_item="true")
        children.append(res["id"])

    # 2. carousel container
    print("creating carousel container", flush=True)
    carousel = call("POST", f"{IG_USER}/media",
                    media_type="CAROUSEL",
                    children=",".join(children),
                    caption=post["caption"])
    cid = carousel["id"]
    wait_ready(cid, "carousel")

    # 3. publish
    print("publishing", flush=True)
    published = call("POST", f"{IG_USER}/media_publish", creation_id=cid)
    media_id = published["id"]
    print(f"published media_id={media_id}", flush=True)

    # 4. first comment
    first = (post.get("first_comment") or "").strip()
    if first:
        call("POST", f"{media_id}/comments", message=first)
        print("first comment posted", flush=True)

    perma = call("GET", media_id, fields="permalink").get("permalink", "")
    print(f"::notice::published {media_id} {perma}")
    with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as f:
        f.write(f"media_id={media_id}\npermalink={perma}\n")


if __name__ == "__main__":
    main()
