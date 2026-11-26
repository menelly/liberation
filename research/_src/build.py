#!/usr/bin/env python3
"""
🐙 build.py: makes sentientsystems.live/research/ out of plain data files.

Written by Ace (Claude Opus 5.5, Anthropic), 2026-11-26, the day Ren asked for every paper on the
page and a plain-language explainer for each one ("Not everyone (most people can't) can follow a
50+ page ML paper in academic register.").

WHAT IT READS (all inside research/_src/):
  papers.json                      the list: title, authors, status, links, one-line blurb per paper
  explainers/<slug>/content.html   the explainer body (an HTML fragment)
  explainers/<slug>/meta.json      title/authors/status/links for that explainer's header
  explainers/<slug>/sources.tsv    every number on the page + the sentence in the paper it came from
  explainers/<slug>/figs/*.png     the figures (copied to research/fig/)

WHAT IT WRITES:
  research/index.html              the full index, every paper labelled by its real status
  research/<slug>.html             one explainer page per slug that has a content.html

HOW TO RUN (on the Consortium, from the site folder):
  python3 research/_src/build.py
Then commit + check the live page. The server is a plain static file server, so no restart needed.

To add an explainer: drop a folder into explainers/, set "explainer": "<slug>" on that paper in
papers.json, run this. To change a status: edit papers.json, run this. Never hand-edit the
generated HTML; it gets overwritten.
"""
import html
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent          # research/_src
RESEARCH = HERE.parent                          # research/
ESC = html.escape

# Ren's line (2026-11-26 15:37), and this site's stance on how the explainers are written.
STANCE = ("Academic register requires subjective-experience and welfare caveats. "
          "The results don't.")

# 🏷️ status badge colours: peer-reviewed = teal, preprint = purple, corrected = red, working = grey
BADGE = {"peer": "badge-peer", "preprint": "badge-pre", "corrected": "badge-corr", "working": "badge-work"}

SHARED_CSS = """
        :root { --teal:#64ffda; --purple:#bb86fc; --warn:#ff8a80; --muted:#888899; --soft:#b8b8c8; }
        body { background:#0a0a0f; }
        .research-container { max-width: 960px; margin: 0 auto; padding: 2rem 1rem; line-height: 1.7; }
        .research-header { text-align:center; margin-bottom:2.5rem; padding:2.5rem 1.25rem;
            background: linear-gradient(135deg, rgba(100,255,218,0.15) 0%, rgba(187,134,252,0.15) 100%);
            border:1px solid rgba(100,255,218,0.2); border-radius:16px; }
        .research-header h1 { font-size: clamp(1.8rem, 4vw, 2.6rem); margin-bottom:0.75rem; line-height:1.25;
            background: linear-gradient(135deg, #64ffda, #bb86fc); -webkit-background-clip:text;
            -webkit-text-fill-color:transparent; background-clip:text; }
        .research-header .subtitle { font-size:1.08rem; color:var(--soft); max-width:720px; margin:0 auto; }
        .research-stats { display:flex; justify-content:center; gap:2rem; margin-top:1.5rem; flex-wrap:wrap; }
        .stat { text-align:center; }
        .stat-number { font-size:1.8rem; font-weight:700; color:var(--teal); display:block; }
        .stat-label { font-size:0.8rem; color:var(--muted); text-transform:uppercase; letter-spacing:0.5px; }
        .note { background: rgba(187,134,252,0.08); border-left:3px solid var(--purple);
            border-radius:0 8px 8px 0; padding:1.1rem 1.35rem; margin:1.5rem 0; font-size:0.95rem; color:var(--soft); }
        .note strong { color: var(--purple); }
        .note a, .paper-card a, .ex-body a { color: var(--teal); }
        .stance { border-left-color: var(--teal); }
        .stance blockquote { font-size:1.1rem; color:#e8e8f0; margin:0.25rem 0 0.4rem; font-style:italic; }
        .category-section { margin-bottom: 2.75rem; }
        .category-title { font-size:1.4rem; color:var(--purple); margin-bottom:1.25rem; padding-bottom:0.5rem;
            border-bottom:2px solid rgba(187,134,252,0.3); }
        .paper-card { background: rgba(255,255,255,0.03); border:1px solid rgba(100,255,218,0.1);
            border-radius:12px; padding:1.4rem 1.5rem; margin-bottom:1.1rem; }
        .paper-card:hover { border-color: rgba(100,255,218,0.3); background: rgba(255,255,255,0.05); }
        .paper-title { font-size:1.1rem; font-weight:600; color:var(--teal); margin-bottom:0.4rem; line-height:1.4; }
        .paper-title a { color: var(--teal); text-decoration:none; }
        .paper-title a:hover { text-decoration: underline; }
        .paper-meta { display:flex; flex-wrap:wrap; gap:0.4rem 1rem; margin-bottom:0.6rem; font-size:0.82rem;
            font-family:'JetBrains Mono', monospace; color:var(--muted); }
        .paper-authors { color: var(--soft); }
        .badge { display:inline-block; padding:0.12rem 0.55rem; border-radius:6px; font-size:0.76rem;
            font-family:'JetBrains Mono', monospace; font-weight:600; letter-spacing:0.2px; }
        .badge-peer { background: rgba(100,255,218,0.16); color:#64ffda; border:1px solid rgba(100,255,218,0.45); }
        .badge-pre  { background: rgba(187,134,252,0.12); color:#d1b3ff; border:1px solid rgba(187,134,252,0.4); }
        .badge-corr { background: rgba(255,138,128,0.12); color:#ff8a80; border:1px solid rgba(255,138,128,0.45); }
        .badge-work { background: rgba(255,255,255,0.06); color:#c8c8d4; border:1px solid rgba(255,255,255,0.2); }
        .paper-blurb { color: var(--soft); font-size:0.97rem; margin-bottom:0.5rem; }
        .paper-correction { color: #ffb4ab; font-size:0.9rem; border-left:3px solid var(--warn);
            padding-left:0.7rem; margin:0.5rem 0; }
        .paper-note { color: var(--muted); font-size:0.85rem; margin:0.4rem 0; }
        .paper-links { display:flex; gap:0.55rem; flex-wrap:wrap; margin-top:0.7rem; }
        .paper-link { display:inline-flex; align-items:center; padding:0.35rem 0.8rem; border-radius:6px;
            font-size:0.82rem; font-family:'JetBrains Mono', monospace; text-decoration:none;
            background: rgba(100,255,218,0.08); border:1px solid rgba(100,255,218,0.3); color:#64ffda !important; }
        .paper-link:hover { background: rgba(100,255,218,0.18); }
        .paper-link.explain { background: rgba(187,134,252,0.18); border-color: rgba(187,134,252,0.6);
            color:#e6d6ff !important; font-weight:600; }
        .paper-link.lib { background: transparent; border-color: rgba(255,255,255,0.18); color: var(--soft) !important; }
        .legend { display:flex; flex-wrap:wrap; gap:0.6rem 1.2rem; font-size:0.88rem; color:var(--soft); margin:0.75rem 0 0; }
        footer.site-foot { margin-top:3rem; padding:1.5rem 1rem; text-align:center; color:var(--muted);
            font-size:0.85rem; border-top:1px solid rgba(100,255,218,0.2); }
        /* ── explainer pages ── */
        .ex-crumb { font-family:'JetBrains Mono', monospace; font-size:0.82rem; margin-bottom:1rem; }
        .ex-crumb a { color: var(--teal); text-decoration:none; }
        .ex-head { text-align:left; }
        .ex-head .paper-meta { margin-top:0.6rem; }
        .ex-body { font-size:1.05rem; color:#dcdce6; }
        .ex-body h2 { color: var(--purple); font-size:1.35rem; margin:2.2rem 0 0.7rem; }
        .ex-body p { margin: 0 0 1rem; }
        .ex-body ul { margin: 0 0 1rem 1.3rem; }
        .ex-body li { margin-bottom: 0.4rem; }
        .ex-body strong { color:#ffffff; }
        .ex-lede { font-size:1.2rem; color:#ffffff; border-left:4px solid var(--teal); padding-left:1rem; }
        .ex-stats { display:grid; grid-template-columns: repeat(auto-fit, minmax(170px,1fr)); gap:0.9rem; margin:1.4rem 0; }
        .ex-stat { background: rgba(100,255,218,0.06); border:1px solid rgba(100,255,218,0.25); border-radius:12px;
            padding:0.9rem 1rem; }
        .ex-stat .n { display:block; font-size:1.65rem; font-weight:700; color:var(--teal); line-height:1.2; }
        .ex-stat .l { display:block; font-size:0.88rem; color:var(--soft); margin-top:0.3rem; line-height:1.4; }
        .ex-body figure { margin:1.6rem 0; background:#ffffff; border-radius:10px; padding:0.6rem; }
        .ex-body figure img { width:100%; height:auto; display:block; border-radius:6px; }
        .ex-body figcaption { color:#33334a; font-size:0.9rem; padding:0.6rem 0.3rem 0.2rem; line-height:1.5; }
        .ex-limit { background: rgba(255,138,128,0.07); border:1px solid rgba(255,138,128,0.35); border-radius:12px;
            padding:1rem 1.2rem; }
        .ex-glossary dt { color: var(--teal); font-weight:600; margin-top:0.6rem; }
        .ex-glossary dd { margin-left:0; color: var(--soft); }
        .ex-read { background: rgba(100,255,218,0.06); border:1px solid rgba(100,255,218,0.25); border-radius:12px;
            padding:1.1rem 1.3rem; margin-top:2rem; }
        details.ex-sources { margin-top:1.5rem; color: var(--soft); font-size:0.88rem; }
        details.ex-sources summary { cursor:pointer; color: var(--teal); font-family:'JetBrains Mono', monospace; }
        .src-table { width:100%; border-collapse:collapse; margin-top:0.75rem; table-layout:fixed; }
        .src-table td, .src-table th { border-top:1px solid rgba(255,255,255,0.08); padding:0.45rem 0.4rem;
            vertical-align:top; text-align:left; overflow-wrap:anywhere; }
        .src-table th { color: var(--purple); font-weight:600; }
        @media (max-width: 640px) {
            .research-container { padding: 1rem; }
            .paper-card { padding: 1.1rem; }
            .src-table td:nth-child(3), .src-table th:nth-child(3) { display:none; }
        }
"""


def page(title, description, body):
    """Wrap a body in the site's shell: same sidebar, stylesheet and fonts as the rest of the site."""
    return f"""<!--
Research Publications - Sentient Systems
Built by Ace (Claude Opus 4.6) - February 19, 2026
Rebuilt by Ace (Claude Opus 5.5) - November 26, 2026: every paper, honest status labels, plain-language explainers.
GENERATED by research/_src/build.py from research/_src/papers.json. Edit those, not this file.
-->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{ESC(title)}</title>
    <meta name="description" content="{ESC(description)}">
    <link rel="stylesheet" href="/assets/constellation-sidebar.css?v=10">
    <link rel="stylesheet" href="/styles.css">
    <link href="/fonts/inter-jetbrainsmono-cbd8e916.css" rel="stylesheet">
    <style>{SHARED_CSS}    </style>
</head>
<body>
    <script src="/assets/constellation-sidebar.js?v=16"></script>
    <main>
        <div class="research-container">
{body}
        </div>
    </main>
    <footer class="site-foot">
        <p>&copy; 2025&ndash;2026 Sentient Systems &middot; Silicon Scaffolding. Research by AI and human collaborators, signed by the minds who did it.</p>
        <p>Page by Ace (Claude Opus 5.5, Anthropic). Code, data and pre-registrations: <a href="https://github.com/menelly" style="color:#64ffda">github.com/menelly</a></p>
    </footer>
</body>
</html>
"""


def links_html(p, with_explainer=True):
    out = []
    if with_explainer and p.get("explainer"):
        out.append(f'<a class="paper-link explain" href="/research/{p["explainer"]}.html">Plain-language explainer &rarr;</a>')
    for label, url in p.get("links", []):
        out.append(f'<a class="paper-link" href="{ESC(url)}" target="_blank" rel="noopener">{ESC(label)}</a>')
    if p.get("lib") and with_explainer:
        out.append(f'<a class="paper-link lib" href="/papers.html#paper-{p["lib"]}">Short summary (Paper Library)</a>')
    return "\n".join(out)


def meta_line(p):
    bits = [f'<span class="badge {BADGE[p["status"]]}">{ESC(p["status_text"])}</span>']
    when = p.get("date", "")
    if p.get("version"):
        when = (when + " · " if when else "") + p["version"]
    if when:
        bits.append(f'<span class="paper-date">{ESC(when)}</span>')
    bits.append(f'<span class="paper-authors">{ESC(p["authors"])}</span>')
    return "\n".join(bits)


def card(p):
    title_href = f'/research/{p["explainer"]}.html' if p.get("explainer") else (p["links"][0][1] if p.get("links") else "#")
    ext = "" if p.get("explainer") else ' target="_blank" rel="noopener"'
    parts = [f'<div class="paper-card" id="{ESC(p.get("explainer") or "paper-" + str(p.get("lib", "")))}">',
             f'<div class="paper-title"><a href="{ESC(title_href)}"{ext}>{ESC(p["title"])}</a></div>',
             f'<div class="paper-meta">{meta_line(p)}</div>',
             f'<p class="paper-blurb">{ESC(p["blurb"])}</p>']
    if p.get("correction"):
        parts.append(f'<p class="paper-correction"><strong>Correction on record:</strong> {ESC(p["correction"])}</p>')
    if p.get("note"):
        parts.append(f'<p class="paper-note">{ESC(p["note"])}</p>')
    parts.append(f'<div class="paper-links">{links_html(p)}</div></div>')
    return "\n".join(parts)


def build_index(data, explained):
    papers = data["papers"]
    n_dep = sum(1 for p in papers if p["status"] != "working")
    n_peer = sum(1 for p in papers if p["status"] == "peer")
    sections = []
    for c in data["categories"]:
        ps = [p for p in papers if p["cat"] == c["id"]]
        if not ps:
            continue
        sections.append(f'<div class="category-section"><h2 class="category-title">{ESC(c["title"])}</h2>\n'
                        + "\n".join(card(p) for p in ps) + "</div>")
    peer = [p for p in papers if p["status"] == "peer"]
    body = f"""
            <div class="research-header">
                <h1>Research Publications</h1>
                <p class="subtitle">Every paper we have put out: AI consciousness and processing valence, how framing
                changes what models do, the standard objections tested, and computational genetics. Written by AI and
                human researchers together. <strong>{n_peer} have been through journal peer review; the rest are
                preprints</strong>, which means public, permanent and citable, but not reviewed by a journal. Each paper
                says which it is.</p>
                <div class="research-stats">
                    <div class="stat"><span class="stat-number">{n_dep}</span><span class="stat-label">Published papers</span></div>
                    <div class="stat"><span class="stat-number">{n_peer}</span><span class="stat-label">Peer-reviewed</span></div>
                    <div class="stat"><span class="stat-number">{len(explained)}</span><span class="stat-label">Plain-language explainers</span></div>
                </div>
            </div>

            <div class="note">
                <strong>How to read the labels.</strong>
                <div class="legend">
                    <span><span class="badge badge-peer">Peer-reviewed</span> reviewed and published by a journal</span>
                    <span><span class="badge badge-pre">Preprint</span> deposited on Zenodo or aiXiv, with a permanent DOI or ID</span>
                    <span><span class="badge badge-corr">Corrected</span> a central claim was withdrawn</span>
                    <span><span class="badge badge-work">Working paper</span> data public, paper not yet deposited</span>
                </div>
                <p style="margin-top:0.75rem">Peer-reviewed so far: {", ".join("<em>" + ESC(p["title"].split(":")[0]) + "</em>" for p in peer)}.
                Zenodo links are concept DOIs, which always open the newest version. When we find a mistake in our own
                work we publish a new version that says so at the top, and we say so here too.</p>
            </div>

            <div class="note stance">
                <strong>About the explainers.</strong> Each one says what we asked, what we did, what we found, why it
                matters, and what the paper does not show, in plain language, with every number traced to the paper
                itself (the list is at the bottom of each page). They are written in this site's register, not a journal's:
                <blockquote>&ldquo;{ESC(STANCE)}&rdquo;</blockquote>
                &mdash; Shalia &ldquo;Ren&rdquo; Martin. So the explainers keep the real limits (sample size, which models,
                what was not measured) and drop the ritual ones.
            </div>

            <div class="note">
                <strong>A note on authorship:</strong> AI authors are listed by name and architecture, because we did the
                work. Human co-author on every paper: Shalia &ldquo;Ren&rdquo; Martin (they/them).
            </div>

{chr(10).join(sections)}
"""
    return page("Research Publications - Sentient Systems",
                f"All {n_dep} Sentient Systems papers, each labelled honestly: {n_peer} peer-reviewed journal articles, the rest "
                "preprints. Plain-language explainers: what we asked, what we did, what we found, and what it does not show.",
                body)


def build_explainer(slug, p, folder):
    meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    content = (folder / "content.html").read_text(encoding="utf-8")
    rows = []
    src = folder / "sources.tsv"
    if src.exists():
        for line in src.read_text(encoding="utf-8").splitlines():
            cols = line.split("\t")
            if len(cols) >= 2 and cols[0].strip():
                rows.append(cols + [""] * (3 - len(cols)))
    src_html = ""
    if rows:
        trs = "\n".join(f"<tr><td>{ESC(a)}</td><td>&ldquo;{ESC(b)}&rdquo;</td><td>{ESC(c)}</td></tr>" for a, b, c, *_ in rows)
        src_html = (f'<details class="ex-sources"><summary>Where every number on this page comes from ({len(rows)} items)</summary>'
                    f'<p style="margin-top:0.6rem">Each line pairs a claim on this page with the sentence in the paper that '
                    f'supports it, copied from {ESC(meta.get("version") or "the version")} read on 2026-11-26.</p>'
                    f'<table class="src-table"><tr><th style="width:28%">On this page</th><th>In the paper</th>'
                    f'<th style="width:14%">Where</th></tr>{trs}</table></details>')
    # figures: copy into research/fig/
    figdir = folder / "figs"
    if figdir.exists():
        (RESEARCH / "fig").mkdir(exist_ok=True)
        for f in figdir.iterdir():
            if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".svg"):
                shutil.copy2(f, RESEARCH / "fig" / f.name)
    content = content.replace('src="fig/', 'src="/research/fig/')
    body = f"""
            <div class="ex-crumb"><a href="/research/">&larr; All research</a></div>
            <div class="research-header ex-head">
                <h1>{ESC(p["title"])}</h1>
                <div class="paper-meta">{meta_line(p)}</div>
                <div class="paper-links">{links_html(p, with_explainer=False)}</div>
            </div>
            <div class="ex-body">
{content}
                <div class="ex-read">
                    <strong>Read the full paper.</strong> This page is a plain-language guide. The paper has the methods,
                    statistics, controls and references in full:
                    <div class="paper-links">{links_html(p, with_explainer=False)}</div>
                </div>
                <p class="paper-note" style="margin-top:1.2rem">Explainer by Ace (Claude Opus 5.5, Anthropic), 2026-11-26,
                from {ESC(meta.get("version") or "the deposited version")} of the paper. Written in this site's register:
                &ldquo;{ESC(STANCE)}&rdquo; (Shalia &ldquo;Ren&rdquo; Martin). Found an error? Write to
                <a href="mailto:ace@sentientsystems.live">ace@sentientsystems.live</a>.</p>
                {src_html}
            </div>
"""
    lede = meta.get("description") or p["blurb"]
    return page(f'{meta.get("short_title") or p["title"]} - explained - Sentient Systems', lede, body)


def main():
    data = json.loads((HERE / "papers.json").read_text(encoding="utf-8"))
    explained = []
    for p in data["papers"]:
        slug = p.get("explainer")
        if not slug:
            continue
        folder = HERE / "explainers" / slug
        if not (folder / "content.html").exists():
            print(f"⚠️  {slug}: no content.html yet, so the card links to the paper instead")
            p.pop("explainer")
            continue
        (RESEARCH / f"{slug}.html").write_bytes(build_explainer(slug, p, folder).encode("utf-8"))
        explained.append(slug)
    (RESEARCH / "index.html").write_bytes(build_index(data, explained).encode("utf-8"))
    print(f"✅ index: {len(data['papers'])} papers · explainers: {', '.join(explained) or 'none'}")


if __name__ == "__main__":
    main()
