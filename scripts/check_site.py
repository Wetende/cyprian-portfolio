#!/usr/bin/env python3
"""Check generated routes, fragments, metadata and bundled asset references."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"


class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.references = []
        self.h1 = 0
        self.canonical = None
        self.description = False
        self.title = False
        self.json_ld = False

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if data.get("id"):
            assert data["id"] not in self.ids, "Duplicate element ID"
            self.ids.add(data["id"])
        self.h1 += tag == "h1"
        self.title |= tag == "title"
        self.description |= tag == "meta" and data.get("name") == "description" and bool(data.get("content"))
        self.json_ld |= tag == "script" and data.get("type") == "application/ld+json"
        if tag == "link" and data.get("rel") == "canonical":
            self.canonical = data.get("href")
        for name in ("href", "src"):
            if data.get(name):
                self.references.append(data[name])


documents = {}
for path in DIST.rglob("*.html"):
    doc = Document()
    doc.feed(path.read_text())
    assert doc.h1 == 1 and doc.title and doc.description and doc.json_ld, path
    assert doc.canonical and doc.canonical.startswith("https://"), path
    documents[path.resolve()] = doc

references = 0
for path, doc in documents.items():
    for value in doc.references:
        parsed = urlsplit(value)
        assert parsed.scheme in ("", "https", "mailto", "tel"), value
        if parsed.scheme or parsed.netloc:
            continue
        assert not parsed.path.startswith("/"), "Use relative paths for GitHub project-site compatibility."
        destination = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
        assert destination.is_relative_to(DIST.resolve()), value
        if destination.is_dir():
            destination /= "index.html"
        assert destination.is_file(), (path, value)
        if parsed.fragment:
            assert destination in documents and unquote(parsed.fragment) in documents[destination].ids, (path, value)
        references += 1

css = DIST / "assets/style.css"
for value in re.findall(r'url\(["\x27]?([^\)"\x27]+)', css.read_text()):
    assert (css.parent / value).is_file(), value

projects = json.loads((ROOT / "content/portfolio.json").read_text())["projects"]
assert len(documents) == len(projects) + 2
assert (DIST / "robots.txt").is_file() and (DIST / "sitemap.xml").is_file()
assert not any(path.name == ".cache" for path in DIST.rglob("*"))
print(f"Verified {len(documents)} pages, {references} local references, both fonts and SEO files.")
