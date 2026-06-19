#!/usr/bin/env python3
"""Download Daniel's LessWrong posts as Markdown with YAML frontmatter.

Pulls every post for the user via the LessWrong GraphQL API and writes one
`YYYY-MM-DD-slug.md` file per post into `writing/lesswrong/`. Idempotent:
re-running overwrites the files with fresh content. No dependencies beyond the
Python 3 stdlib.

Usage: python3 scripts/fetch_lesswrong.py
"""
import json
import sys
import urllib.request
from pathlib import Path

ENDPOINT = "https://www.lesswrong.com/graphql"
USER_SLUG = "daniel-tan"
SHORTFORM_POST_ID = "4mtqQKvmHpQJ4dgj7"  # "Daniel Tan's Shortform"
ROOT = Path(__file__).parent.parent
OUT_DIR = ROOT / "writing" / "lesswrong"
SHORTFORM_DIR = ROOT / "writing" / "shortform"


def gql(query):
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps({"query": query}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if payload.get("errors"):
        sys.exit(f"GraphQL error: {payload['errors']}")
    return payload["data"]


def resolve_user_id(slug):
    data = gql('{ user(input:{selector:{slug:"%s"}}){ result{ _id displayName } } }' % slug)
    user = data["user"]["result"]
    print(f"User: {user['displayName']} ({user['_id']})")
    return user["_id"]


def fetch_posts(user_id):
    # htmlBody is the FAITHFUL source: LW's markdown export silently drops some
    # footnote definitions, so the site is built from htmlBody (see build_writing.py).
    # The markdown is kept too, as a readable/grep-able archive.
    query = """
    { posts(input:{terms:{view:"userPosts", userId:"%s", limit:100}}){
        results{ _id title slug postedAt baseScore commentCount pageUrl
                 htmlBody contents{ markdown wordCount } } } }
    """ % user_id
    return gql(query)["posts"]["results"]


def yaml_escape(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_post(p):
    contents = p.get("contents") or {}
    body = contents.get("markdown") or ""
    date = (p.get("postedAt") or "")[:10]
    slug = p.get("slug") or p["_id"]
    fname = f"{date}-{slug}.md"
    frontmatter = "\n".join([
        "---",
        f"title: {yaml_escape(p['title'])}",
        f"date: {date}",
        f"slug: {slug}",
        f"lw_id: {p['_id']}",
        f"lw_url: {p.get('pageUrl', '')}",
        f"karma: {p.get('baseScore', 0)}",
        f"comments: {p.get('commentCount', 0)}",
        f"word_count: {contents.get('wordCount', 0)}",
        "---",
        "",
    ])
    (OUT_DIR / fname).write_text(frontmatter + body + "\n", encoding="utf-8")
    return fname, contents.get("wordCount", 0)


def fetch_shortform(user_id):
    """Top-level comments on the user's own shortform post = their 'takes'."""
    # htmlBody, like posts, is the faithful source the site build reads; markdown
    # is kept as a readable/grep-able archive (see build_shortform.py).
    query = """
    { comments(input:{terms:{view:"postCommentsTop", postId:"%s", limit:500}}){
        results{ _id userId baseScore postedAt parentCommentId pageUrl
                 htmlBody contents{ markdown } } } }
    """ % SHORTFORM_POST_ID
    rows = gql(query)["comments"]["results"]
    takes = [c for c in rows if c.get("userId") == user_id and not c.get("parentCommentId")]
    takes.sort(key=lambda c: c.get("postedAt", ""), reverse=True)
    return takes


def write_shortform(takes):
    """One archive file: all takes newest-first with score, date, and LW link."""
    SHORTFORM_DIR.mkdir(parents=True, exist_ok=True)
    out = ["---", "title: Shortform takes (from LessWrong)",
           f"source: https://www.lesswrong.com/posts/{SHORTFORM_POST_ID}",
           f"count: {len(takes)}", "---", ""]
    for c in takes:
        date = (c.get("postedAt") or "")[:10]
        out.append(f"## {date} · {c.get('baseScore', 0)} karma")
        out.append(f"<!-- id:{c['_id']} url:{c.get('pageUrl', '')} -->")
        out.append("")
        out.append((c.get("contents") or {}).get("markdown", "").strip())
        out.append("")
    (SHORTFORM_DIR / "shortform.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    # Canonical structured archive (incl. htmlBody) — the site build reads this.
    (SHORTFORM_DIR / "shortform.json").write_text(
        json.dumps(takes, indent=2, ensure_ascii=False), encoding="utf-8")
    return len(takes)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    user_id = resolve_user_id(USER_SLUG)
    posts = fetch_posts(user_id)
    # Sort newest first; the shortform container has an empty body — keep it but flag.
    posts.sort(key=lambda p: p.get("postedAt", ""), reverse=True)
    print(f"Fetched {len(posts)} posts. Writing to {OUT_DIR}/\n")
    for p in posts:
        fname, wc = write_post(p)
        print(f"  {fname}  ({wc} words)")
    # Canonical structured archive (incl. htmlBody) — the site build reads this.
    (OUT_DIR / "posts.json").write_text(
        json.dumps(posts, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {OUT_DIR}/posts.json ({len(posts)} posts, with htmlBody)")
    print(f"\nFetching shortform takes...")
    takes = fetch_shortform(user_id)
    n = write_shortform(takes)
    print(f"Wrote {n} shortform takes to {SHORTFORM_DIR}/shortform.md")
    print(f"\nDone: {len(posts)} posts + {n} shortform takes.")


if __name__ == "__main__":
    main()
