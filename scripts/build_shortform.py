#!/usr/bin/env python3
"""Build the /writing/shortform.html "Notes" page from curated LessWrong takes.

Renders a hand-picked subset of Daniel's LessWrong shortform takes into a single
styled page — a stream of short notes, newest-first, grouped by year. Each note
links back to its original LessWrong comment (canonical source).

Source of truth is `writing/shortform/shortform.json` (written by
fetch_lesswrong.py), specifically each take's **htmlBody** — same faithful,
already-rendered HTML we build the post pages from. Stdlib only.

Curation lives in CURATED below: (comment id, display title). To add/remove a
note, edit that list. Order is derived from postedAt, so only id+title matter.

Usage: python3 scripts/build_shortform.py
"""
import html as html_lib
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
ARCHIVE = ROOT / "writing" / "shortform" / "shortform.json"
OUT = ROOT / "writing" / "shortform.html"

# Curated takes, by LessWrong comment id → display title. Daniel-approved.
# Order on the page is by date (newest first), derived from the archive.
CURATED = {
    "nmC7XBEZvdnjNvDmi": "Adapting research plans on the fly",
    "khXqEEbssMPtHTXkK": "Fake prerequisites",
    "aYQzaxJperZFi4yc8": "When to deduplicate work with others",
    "CuHnKee6GL8rsGaXp": "Labs' unpublishable alignment science",
    "YRcSDJxXBivZGWtzH": "Alignment affordances of model-persona research",
    "nebMYhZvN7GXkvSyX": "On dropping things that aren't excellent",
    "eB55D8uGASyM4ypBx": "Functional interpretability",
    "3pSKqjZss6sKPZNDX": "A theory of impact for research outside the labs",
    "zJRWriQjbEoaWW52Z": "Learn to ask for help earlier",
    "iYsCbHJhT7CuBGvdb": "Research engineering tips for SWEs",
    "6Q7WvmD7jWoY8STHK": "Don't write survey papers on techniques",
    "4zDMdTKxKoXNt9KfJ": "Writing papers in two phases",
    "fn9YyziLj5jmBcrAJ": "Library code vs experiment code",
    "EesNATHbknuEviXDG": "The last-mile problem in delegating to AI",
    "p8jEWLKfPgNMxDDQW": "Superhuman latent knowledge",
    "mvyWJWWzbCoiYafBX": "Strategies in social deduction games",
    "X8hzrHzpduez2DrdK": "Writing all my notes in public",
    "rv3veoLsBhdp69tLy": "The five whys, in Todoist",
    "433pv5ojHcuAWyDJu": "Taste as a hard-to-automate skill",
    "bHmNL3FAwGETAmnrD": "Create handles for knowledge",
    "cAc2ujatmjEYzBqsb": "Imposter syndrome is a positive signal",
    "vKavCHHQYnqZpPvWc": "Why anthropomorphise LLMs?",
    "LqefzJMn7HTRthMit": "Inference-time compute will be hard to govern",
    "Dc8GytgHMn85uBiRB": "Explaining AGI to a layperson",
}

MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# LessWrong server-renders LaTeX as bulky MathJax spans. The few used in these
# takes are trivial inline symbols, so swap them for the Unicode equivalent
# rather than pulling in MathJax (the site ships none).
TEX = {r"\to": "→", r"\rightarrow": "→", r"\times": "×", r"\leq": "≤",
       r"\geq": "≥", r"\in": "∈", r"\cdot": "·", r"\approx": "≈"}

esc = lambda s: html_lib.escape(s, quote=False)
escq = lambda s: html_lib.escape(s, quote=True)

# --- minimal markdown for local drafts (preview only; --draft) ---
LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
BOLD = re.compile(r"\*\*(.+?)\*\*")
ITALIC = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")


def md_inline(text):
    text = esc(text)
    text = LINK.sub(r'<a href="\2">\1</a>', text)
    text = BOLD.sub(r"<strong>\1</strong>", text)
    text = ITALIC.sub(r"<em>\1</em>", text)
    return text


def md_to_html(text):
    """Tiny block renderer: #/##/### headings (demoted to h3/h4 to sit under the
    note title), `- ` bullets, and paragraphs. Enough for a draft preview."""
    blocks, para, items = [], [], []

    def flush_para():
        if para:
            blocks.append("<p>" + md_inline(" ".join(para)) + "</p>")
            para.clear()

    def flush_list():
        if items:
            blocks.append("<ul>" + "".join(f"<li>{md_inline(i)}</li>" for i in items) + "</ul>")
            items.clear()

    for line in text.splitlines():
        s = line.strip()
        if not s:
            flush_para(); flush_list()
        elif s.startswith("### "):
            flush_para(); flush_list(); blocks.append(f"<h4>{md_inline(s[4:])}</h4>")
        elif s.startswith(("## ", "# ")):
            flush_para(); flush_list()
            blocks.append(f"<h3>{md_inline(s.lstrip('# '))}</h3>")
        elif s.startswith("- "):
            flush_para(); items.append(s[2:])
        else:
            flush_list(); para.append(s)
    flush_para(); flush_list()
    return "\n".join(blocks)


def parse_draft(path):
    """Read a drafts/YYYY-MM-DD-slug.md file into a preview note."""
    from pathlib import Path as _P
    p = _P(path)
    raw = re.sub(r"<!--.*?-->", "", p.read_text(encoding="utf-8"), flags=re.DOTALL)
    title, body = None, []
    for ln in raw.splitlines():
        if title is None and ln.startswith("# "):
            title = ln[2:].strip()
        else:
            body.append(ln)
    name = p.stem
    return {
        "title": title or name,
        "date": name[:10] if re.match(r"\d{4}-\d{2}-\d{2}", name) else "",
        "slug": re.sub(r"^\d{4}-\d{2}-\d{2}-", "", name),
        "html": md_to_html("\n".join(body)),
    }


def strip_mathjax(html):
    """Replace each <span class="math-tex">…</span> with its Unicode symbol."""
    out, i = [], 0
    marker = '<span class="math-tex">'
    while True:
        j = html.find(marker, i)
        if j == -1:
            out.append(html[i:])
            break
        out.append(html[i:j])
        # walk balanced <span>/</span> from the math-tex span to its close
        k, depth = j, 0
        while k < len(html):
            if html.startswith("<span", k):
                depth += 1
                k = html.index(">", k) + 1
            elif html.startswith("</span>", k):
                depth -= 1
                k += len("</span>")
                if depth == 0:
                    break
            else:
                k += 1
        span = html[j:k]
        m = re.search(r'aria-label="([^"]*)"', span)
        label = (m.group(1).strip() if m else "")
        out.append(TEX.get(label, esc(label)))
        i = k
    return "".join(out)


def prepare_body(html):
    """Touch up LW's htmlBody for a note card — no structural rewriting."""
    html = strip_mathjax(html)
    html = html.strip()
    # a take that opens with its own <h1> title duplicates the card title — drop it
    html = re.sub(r"^\s*<h1>.*?</h1>", "", html, count=1, flags=re.DOTALL).strip()
    # demote in-body section headings so the card's <h2> title stays dominant
    html = html.replace("<h1>", "<h3>").replace("</h1>", "</h3>")
    html = html.replace("<h2>", "<h4>").replace("</h2>", "</h4>")
    html = re.sub(r"<img\b", '<img loading="lazy"', html)
    return html


def date_long(d):
    y, m, day = d.split("-")
    return f"{MONTHS[int(m)]} {int(day)}, {y}"


PAGE = """<!DOCTYPE html>
<html lang="en-GB">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Notes — Daniel Tan</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="stylesheet" href="../sleeper.css">
    <link rel="stylesheet" href="writing.css">
</head>
<body>
    <div class="atmos" aria-hidden="true"><div class="stars"></div><div class="lamp"></div></div>
    <div class="page page-wide">
        <div class="topbar">
            <a href="../index.html" class="wordmark">Daniel Tan</a>
            <a href="index.html" class="backlink"><span class="arr">←</span> Writing</a>
        </div>
        <header class="pagehead">
            <p class="eyebrow">notes</p>
            <h1>Notes</h1>
        </header>
        <p class="lede-line">Shorter takes — on research, craft, and how to do
        good work — selected from my <a href="{shortform_url}">LessWrong
        shortform</a>.</p>
        <div class="sf-layout">
            <div class="notes">
{notes}
            </div>
            <nav class="sf-toc" aria-label="All notes">
                <p class="sf-toc-head">All notes</p>
                <ol>
{toc}
                </ol>
            </nav>
        </div>
    </div>
</body>
</html>
"""

NOTE = """            <article class="note" id="{cid}">
                <h2 class="note-title"><a href="#{cid}">{title}</a></h2>
                <p class="note-meta">{date_long} · {karma} karma · <a href="{lw_url}">On LessWrong ↗</a></p>
                <div class="prose note-body">
{body}
                </div>
            </article>"""

NOTE_DRAFT = """            <article class="note note-draft" id="draft-{slug}">
                <h2 class="note-title"><a href="#draft-{slug}">{title}</a><span class="note-badge">draft</span></h2>
                <p class="note-meta">Draft · {date_long} · not yet published</p>
                <div class="prose note-body">
{body}
                </div>
            </article>"""

SHORTFORM_URL = "https://www.lesswrong.com/posts/4mtqQKvmHpQJ4dgj7/daniel-tan-s-shortform"


def build(draft_paths=()):
    archive = {t["_id"]: t for t in json.loads(ARCHIVE.read_text(encoding="utf-8"))}
    takes = []
    for cid, title in CURATED.items():
        if cid not in archive:
            raise SystemExit(f"curated id not in archive: {cid}")
        t = archive[cid]
        t["title"] = title
        t["date"] = (t.get("postedAt") or "")[:10]
        takes.append(t)
    takes.sort(key=lambda t: t["date"], reverse=True)

    blocks, toc, cur_year = [], [], None

    # local drafts (preview only) sit above the published notes
    drafts = [parse_draft(p) for p in draft_paths]
    if drafts:
        toc.append('                    <li class="sf-toc-year">in review</li>')
        for d in drafts:
            blocks.append(NOTE_DRAFT.format(
                slug=escq(d["slug"]), title=esc(d["title"]),
                date_long=date_long(d["date"]) if d["date"] else "draft",
                body=d["html"]))
            toc.append(
                f'                    <li><a href="#draft-{escq(d["slug"])}">'
                f'<span class="sf-toc-date">✎</span>'
                f'<span class="sf-toc-title">{esc(d["title"])}</span></a></li>'
            )

    for t in takes:
        year = t["date"][:4]
        if year != cur_year:
            blocks.append(f'            <div class="wyear">{year}</div>')
            toc.append(f'                    <li class="sf-toc-year">{year}</li>')
            cur_year = year
        blocks.append(NOTE.format(
            cid=escq(t["_id"]),
            title=esc(t["title"]),
            date_long=date_long(t["date"]),
            karma=t.get("baseScore", 0),
            lw_url=escq(t.get("pageUrl", SHORTFORM_URL)),
            body=prepare_body(t["htmlBody"]),
        ))
        y, m, _ = t["date"].split("-")
        toc.append(
            f'                    <li><a href="#{escq(t["_id"])}">'
            f'<span class="sf-toc-date">{MONTHS[int(m)]}</span>'
            f'<span class="sf-toc-title">{esc(t["title"])}</span></a></li>'
        )
    OUT.write_text(
        PAGE.format(notes="\n".join(blocks), toc="\n".join(toc),
                    shortform_url=SHORTFORM_URL),
        encoding="utf-8")
    extra = f" + {len(drafts)} draft(s)" if drafts else ""
    print(f"Built {OUT} with {len(takes)} curated notes{extra} (+ sidebar).")


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Build the Notes (shortform) page.")
    ap.add_argument("--draft", action="append", default=[], metavar="PATH",
                    help="include a local markdown draft as a preview note (repeatable)")
    build(ap.parse_args().draft)


if __name__ == "__main__":
    main()
