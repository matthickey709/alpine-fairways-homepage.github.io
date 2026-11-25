#!/usr/bin/env python3
"""Stamp the shared site header and footer into every page, then rebuild sitemap.xml.

The site is plain static HTML (works with JavaScript off), so the shared header and
footer are copied into each page between marker comments:

    <!-- site-header:start --> ... <!-- site-header:end -->
    <!-- site-footer:start --> ... <!-- site-footer:end -->

Edit HEADER / FOOTER below, then run from the repo root:

    python3 _tools/stamp.py

sitemap.xml lists every stamped page that has a <link rel="canonical">.
(This folder starts with "_", so GitHub Pages does not publish it.)
"""
from __future__ import annotations

import datetime
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://alpinefairways.ca"

NAV = [
    ("/ventures/", "Ventures"),
    ("/notes/", "Notes"),
    ("/about/", "About"),
    ("/contact/", "Contact"),
]

HEADER = """<a class="skip-link" href="#main">Skip to content</a>
  <header class="site-header">
    <div class="site-header__inner">
      <a class="brand" href="/"><img src="/assets/favicon.svg" alt="" width="28" height="28">Alpine Fairways</a>
      <nav class="site-nav" aria-label="Main">
{links}
      </nav>
    </div>
  </header>"""

FOOTER = """<footer class="site-footer">
    <div class="site-footer__inner">
      <div class="footer-cols">
        <div>
          <h2>Site</h2>
          <ul>
            <li><a href="/">Home</a></li>
            <li><a href="/ventures/">Ventures</a></li>
            <li><a href="/notes/">Notes</a></li>
            <li><a href="/about/">About</a></li>
            <li><a href="/contact/">Contact</a></li>
          </ul>
        </div>
        <div>
          <h2>Ventures</h2>
          <ul>
            <li><a href="/game-night-trivia.html">Game Night Trivia</a></li>
            <li><a href="/proper-drop.html">Proper Drop</a></li>
          </ul>
        </div>
        <div>
          <h2>Legal</h2>
          <ul>
            <li><a href="/privacy/">Privacy</a></li>
            <li><a href="/terms/">Terms</a></li>
          </ul>
        </div>
      </div>
      <p class="footer-legal">&copy; {year} Alpine Fairways Holdings Inc. &middot; St. John&rsquo;s, Newfoundland &amp; Labrador</p>
    </div>
  </footer>"""

HEADER_RE = re.compile(r"(<!-- site-header:start -->).*?(<!-- site-header:end -->)", re.S)
FOOTER_RE = re.compile(r"(<!-- site-footer:start -->).*?(<!-- site-footer:end -->)", re.S)
CANON_RE = re.compile(r'<link rel="canonical" href="([^"]+)">')


def url_path(page: pathlib.Path) -> str:
    rel = page.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("index.html")]
    return "/" + rel


def section_of(path: str) -> str | None:
    """Which top-level nav item a page belongs to."""
    if path in ("/game-night-trivia.html", "/proper-drop.html"):
        return "/ventures/"
    for href, _ in NAV:
        if path.startswith(href):
            return href
    return None


def render_header(path: str) -> str:
    current = section_of(path)
    links = []
    for href, label in NAV:
        attr = ""
        if href == path:
            attr = ' aria-current="page"'
        elif href == current:
            attr = ' aria-current="true"'
        links.append(f'        <a href="{href}"{attr}>{label}</a>')
    return HEADER.format(links="\n".join(links))


def main() -> None:
    year = datetime.date.today().year
    footer = FOOTER.replace("{year}", str(year))
    urls = []
    for page in sorted(ROOT.rglob("*.html")):
        rel = page.relative_to(ROOT)
        if any(part.startswith((".", "_")) for part in rel.parts):
            continue
        text = page.read_text(encoding="utf-8")
        if "<!-- site-header:start -->" not in text:
            continue
        path = url_path(page)
        new = HEADER_RE.sub(lambda m: f"{m[1]}\n  {render_header(path)}\n  {m[2]}", text)
        new = FOOTER_RE.sub(lambda m: f"{m[1]}\n  {footer}\n  {m[2]}", new)
        if new != text:
            page.write_text(new, encoding="utf-8")
            print(f"stamped {rel}")
        canon = CANON_RE.search(new)
        if canon:
            urls.append(canon[1])

    today = datetime.date.today().isoformat()
    def key(u: str) -> tuple:
        return (u != f"{SITE}/", u)
    body = "\n".join(
        f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{today}</lastmod>\n  </url>" for u in sorted(urls, key=key)
    )
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n"
        "</urlset>\n"
    )
    (ROOT / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    print(f"sitemap.xml: {len(urls)} URLs")


if __name__ == "__main__":
    main()
