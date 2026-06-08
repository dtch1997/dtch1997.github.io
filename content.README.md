# Editing the site's words

The prose on `index.html` lives in **`content.md`**, separate from the HTML. To
change wording:

1. Edit the text under the relevant `### key` in `content.md`.
2. Run `python3 build.py` (no dependencies — plain Python 3).
3. Commit `content.md` + the regenerated `index.html`, then push.

That's it. `index.html` is **generated** — don't edit it by hand; the next build
overwrites it.

## What you can write

Each field is one paragraph. Inline markdown:

- `[link text](https://url)` → a link
- `**bold**`, `*italic*`
- raw HTML works too (e.g. the hero headline keeps its `<span class="accent">`)

## Layout vs. words — the split

- **Words** → `content.md` (this is yours to edit freely).
- **Layout, classes, styling, structure** (adding a paragraph, changing a CSS
  class, the papers list, the nav, the dev kit) → `index.template.html`. Editing
  that safely means touching HTML — ask Claude if you'd rather not.

`build.py` cross-checks the two: it errors if a `{{placeholder}}` in the template
has no matching field in `content.md`, or vice-versa, so they can't drift.

## Scope

Currently wired up: the prose sections of `index.html` (hero, about, work intro,
now, contact). Headings, the papers list, chips, and the other pages
(`now.html`, `fun/*.html`) are still plain HTML — say the word to extend the same
pattern to them.
