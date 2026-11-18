#!/usr/bin/env python3
"""Build a small, pre-rendered portfolio without runtime dependencies."""
import argparse
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urljoin, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
DATA = json.loads((ROOT / "content/portfolio.json").read_text())
CONFIG = json.loads((ROOT / "site-config.json").read_text())
ASSET_VERSIONS = {
    name: sha256((ROOT / "assets" / name).read_bytes()).hexdigest()[:12]
    for name in ("style.css", "site.js")
}
parser = argparse.ArgumentParser()
parser.add_argument("--base-url", default=CONFIG["base_url"])
args = parser.parse_args()
BASE = args.base_url.rstrip("/") + "/"
parts = urlsplit(BASE)
if parts.scheme != "https" or not parts.netloc or parts.query or parts.fragment:
    raise SystemExit("The canonical base URL must be an HTTPS URL without query or fragment.")
if CONFIG.get("custom_domain") and parts.hostname != CONFIG["custom_domain"]:
    raise SystemExit("The canonical base URL must match the configured custom domain.")
slugs = [row["slug"] for row in DATA["projects"]]
retired_slugs = DATA.get("retired_project_slugs", [])
all_slugs = slugs + retired_slugs
if len(set(all_slugs)) != len(all_slugs) or not all(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) for slug in all_slugs):
    raise SystemExit("Project slugs must be unique URL-safe names.")
if DIST.is_symlink():
    raise SystemExit("Refusing to replace a symlinked build directory.")
if DIST.exists():
    shutil.rmtree(DIST)
DIST.mkdir()
shutil.copytree(ROOT / "assets", DIST / "assets")


def e(value):
    return escape(str(value), quote=True)


def person():
    return {
        "@context": "https://schema.org", "@type": "Person", "@id": BASE + "#person",
        "name": DATA["name"], "jobTitle": DATA["role"], "url": BASE,
        "image": urljoin(BASE, "assets/cyprian-wetende.webp"),
        "worksFor": {"@type": "Organization", "name": DATA["company"], "url": DATA["company_url"]},
        "sameAs": [DATA["linkedin"], DATA["github"], DATA["personal_portfolio"]],
        "knowsAbout": DATA["expertise_topics"],
    }


def head(title, description, path="", prefix="", noindex=False):
    canonical = urljoin(BASE, path)
    structured = json.dumps(person(), ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e")
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{e(title)}</title>
  <meta name="description" content="{e(description)}">
  <meta name="referrer" content="strict-origin-when-cross-origin">
  <meta name="theme-color" content="#073e30">
  {('<meta name="robots" content="noindex">' if noindex else '')}
  <link rel="canonical" href="{e(canonical)}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{e(title)}">
  <meta property="og:description" content="{e(description)}">
  <meta property="og:url" content="{e(canonical)}">
  <meta property="og:image" content="{e(urljoin(BASE, 'assets/cyprian-wetende.webp'))}">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" href="{e(prefix)}assets/favicon.svg" type="image/svg+xml">
  <link rel="preload" href="{e(prefix)}assets/fonts/montserrat-latin.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="{e(prefix)}assets/style.css?v={ASSET_VERSIONS['style.css']}">
  <script src="{e(prefix)}assets/site.js?v={ASSET_VERSIONS['site.js']}" defer></script>
  <script type="application/ld+json">{structured}</script>
</head><body>'''


def header(prefix=""):
    home = prefix or "./"
    return f'''
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header"><div class="container header-inner">
  <a class="brand" href="{e(home)}" aria-label="Cyprian Wetende, home">
    <span class="brand-mark" aria-hidden="true">CW</span>
    <span><span class="brand-name">Cyprian Wetende</span><span class="brand-role">Technical Lead · Datecho</span></span>
  </a>
  <button class="nav-toggle" type="button" aria-controls="primary-nav" aria-expanded="false" hidden>Menu</button>
  <nav class="site-nav" id="primary-nav" aria-label="Main navigation">
    <a href="{e(prefix)}#expertise">Data expertise</a>
    <a href="{e(prefix)}#work">Services & work</a>
    <a href="{e(prefix)}#approach">Approach</a>
    <a class="button button-dark" href="{e(DATA['contact_url'])}">Let’s talk <span aria-hidden="true">↗</span></a>
  </nav>
</div></header>'''


def footer():
    year = datetime.now(timezone(timedelta(hours=3))).year
    return f'''
<footer class="site-footer"><div class="container footer-inner">
  <p>© {year} Cyprian Wetende · Technical Lead at <a href="{e(DATA['company_url'])}">Datecho Analytics</a></p>
  <nav class="footer-links" aria-label="Elsewhere">
    <a href="{e(DATA['linkedin'])}" rel="me">LinkedIn</a>
    <a href="{e(DATA['github'])}" rel="me">GitHub</a>
    <a href="{e(DATA['personal_portfolio'])}">Personal portfolio</a>
    <a href="https://datecho.com/privacy/">Privacy</a>
  </nav>
</div></footer>
</body></html>'''


def contact():
    return f'''
<section class="contact-band" id="contact"><div class="container contact-grid">
  <div class="contact-copy"><p class="eyebrow">A conversation is a useful first step</p>
    <h2>Have a data workflow that needs to work better?</h2>
    <p>Talk with Datecho about your data analysis, Power BI dashboards and reporting needs. I bring the analytics and technical delivery together.</p>
  </div>
  <div class="contact-links">
    <a class="button button-gold" href="{e(DATA['contact_url'])}">Discuss a project <span aria-hidden="true">↗</span></a>
    <a href="mailto:{e(DATA['email'])}">{e(DATA['email'])}</a>
    <a href="tel:+254799883309">{e(DATA['phone'])}</a>
    <small>For company enquiries · Datecho Analytics</small>
  </div>
</div></section>'''


def project_row(row, index):
    tags = "".join(f'<li class="tag">{e(tool)}</li>' for tool in row["stack"])
    href = f'work/{row["slug"]}/'
    label = "Service details" if row.get("kind") == "service" else "Project notes"
    return f'''
<article class="project-row" data-categories="{e(' '.join(row['categories']))}">
  <span class="project-index" aria-hidden="true">{index:02d}</span>
  <div class="project-main">
    <p class="project-context">{e(row['context'])}</p>
    <h3 class="project-title"><a href="{e(href)}">{e(row['title'])} <span aria-hidden="true">/</span> {e(row['subtitle'])}</a></h3>
    <p class="project-summary">{e(row['summary'])}</p>
    <ul class="project-tags" aria-label="Technologies">{tags}</ul>
  </div>
  <a class="project-link" href="{e(href)}" aria-label="Read {e(row['title'])}: {label.lower()}">{label} <span aria-hidden="true">↗</span></a>
</article>'''


def home_page():
    work = "".join(project_row(row, index) for index, row in enumerate(DATA["projects"], 1))
    capabilities = "".join(f'''<article class="capability"><h3>{e(row['title'])}</h3><p>{e(row['description'])}</p><p class="tool-list">{e(row['tools'])}</p></article>''' for row in DATA["capabilities"])
    steps = "".join(f'''<li><span class="step-number" aria-hidden="true">{index:02d}</span><div><h3>{e(row['title'])}</h3><p>{e(row['description'])}</p></div></li>''' for index, row in enumerate(DATA["steps"], 1))
    return head("Cyprian Wetende — Data Analytics & Power BI | Datecho", DATA["description"]) + header() + f'''
<main id="main">
  <section class="hero" id="top"><div class="container">
    <div class="hero-grid">
      <div class="hero-copy">
        <p class="eyebrow">Technical Lead / Datecho Analytics</p>
        <h1>Clear data.<br><em>Better decisions.</em></h1>
        <p class="hero-intro">I’m Cyprian Wetende. {e(DATA['intro'])}</p>
        <div class="actions"><a class="button button-gold" href="#expertise">Explore data expertise <span aria-hidden="true">↓</span></a><a class="button button-outline" href="{e(DATA['linkedin'])}">Connect on LinkedIn <span aria-hidden="true">↗</span></a></div>
      </div>
      <figure class="hero-portrait"><img src="assets/cyprian-wetende.webp" width="900" height="1125" alt="Cyprian Wetende working at a laptop" fetchpriority="high" decoding="async"><figcaption><strong>Cyprian Wetende</strong><span>Analytics · Power BI · automation</span></figcaption></figure>
    </div>
    <div class="hero-notes"><span>Power BI · Python & pandas · SQL · Excel · Tableau</span><a href="{e(DATA['company_url'])}">Part of Datecho Analytics <span aria-hidden="true">↗</span></a></div>
  </div></section>

  <section class="section section-mint" id="expertise"><div class="container">
    <div class="section-heading"><div><p class="eyebrow">01 / Data expertise</p><h2>Analytics, reporting<br>and the data behind them.</h2></div><p class="section-intro">From preparing a dataset to building a Power BI dashboard, I work across the data workflow. My skills bring analysis, visual reporting and automation into Datecho’s service delivery.</p></div>
    <div class="capability-grid">{capabilities}</div>
    <p><a class="text-link" href="https://datecho.com/services/">Explore Datecho’s services <span aria-hidden="true">↗</span></a></p>
  </div></section>

  <section class="section" id="work"><div class="container">
    <div class="section-heading"><div><p class="eyebrow">02 / Services & selected work</p><h2>Data services.<br>Practical delivery.</h2></div><p class="section-intro">Power BI reporting and data analysis are services I offer through Datecho. Alongside them, selected platform and integration projects show the technical work behind my delivery.</p></div>
    <div class="filter-bar" data-filter-controls hidden role="group" aria-label="Filter selected work">
      <button class="filter-button" type="button" data-filter="all" aria-pressed="true">All services & work</button>
      <button class="filter-button" type="button" data-filter="analytics-bi" aria-pressed="false">Analytics & BI</button>
      <button class="filter-button" type="button" data-filter="data-applications" aria-pressed="false">Data applications</button>
      <button class="filter-button" type="button" data-filter="integrations" aria-pressed="false">Integrations</button>
      <button class="filter-button" type="button" data-filter="automation" aria-pressed="false">Automation</button>
      <p class="filter-status" aria-live="polite">Showing {len(DATA['projects'])} items</p>
    </div>
    <div class="project-list">{work}</div>
  </div></section>

  <section class="section" id="approach"><div class="container approach-grid">
    <div class="approach-intro"><p class="eyebrow">03 / How I approach a brief</p><h2>Start with the question.<br>Make the findings clear.</h2><p class="section-intro">Understand the business question, prepare dependable data and communicate the findings in a form people can use.</p></div>
    <ol class="steps">{steps}</ol>
  </div></section>
  {contact()}
</main>''' + footer()


def case_page(row, index):
    prefix = "../../"
    path = f'work/{row["slug"]}/'
    scope = "".join(f'<li>{e(item)}</li>' for item in row["scope"])
    tools = "".join(f'<li class="tag">{e(tool)}</li>' for tool in row["stack"])
    service = row.get("kind") == "service"
    entry_label = "Service" if service else "Project notes"
    scope_label = "Service scope" if service else "Engineering scope"
    delivery_label = "How I deliver" if service else "The work in practice"
    perspective = "Data analytics & reporting" if service else "Technical engineering"
    image = ""
    if row.get("image"):
        image = f'''<figure class="case-figure"><img src="{prefix}assets/{e(row['image'])}" alt="{e(row['image_alt'])}" width="1200" height="552" loading="lazy" decoding="async"><figcaption>Public Datecho platform · homepage view</figcaption></figure>'''
    next_row = DATA["projects"][(index + 1) % len(DATA["projects"])]
    return head(f"{row['title']} — {row['subtitle']} | Cyprian Wetende", row["summary"], path, prefix) + header(prefix) + f'''
<main id="main">
  <section class="case-hero"><div class="container">
    <nav class="breadcrumbs" aria-label="Breadcrumb"><a href="{prefix}#work">Selected work</a><span aria-hidden="true">/</span><span aria-current="page">{e(row['title'])}</span></nav>
    <p class="eyebrow case-kicker">{entry_label} / {e(row['context'])}</p>
    <h1 class="case-title">{e(row['title'])}<br>{e(row['subtitle'])}</h1>
    <p class="case-summary">{e(row['summary'])}</p>
    <div class="case-meta"><div class="meta-item"><strong>Context</strong><span>{e(row['context'])}</span></div><div class="meta-item"><strong>Focus</strong><span>{e(row['focus'])}</span></div><div class="meta-item"><strong>Perspective</strong><span>Cyprian Wetende · {perspective}</span></div></div>
  </div></section>
  <div class="container case-layout">
    <div class="case-body">
      <section class="case-block"><h2>The data and workflow challenge</h2><p>{e(row['challenge'])}</p></section>
      {image}
      <section class="case-block"><h2>{scope_label}</h2><ul>{scope}</ul></section>
      <section class="case-block"><h2>{delivery_label}</h2><p>{e(row['delivery'])}</p></section>
      <section class="case-block"><h2>How this connects to Datecho</h2><p>{e(row['relevance'])}</p></section>
    </div>
    <aside class="case-sidebar" aria-label="Project details">
      <section class="sidebar-block"><h2>Technologies</h2><ul class="project-tags">{tools}</ul></section>
      <section class="sidebar-block"><h2>{'Service context' if service else 'Project context'}</h2><p>{e(row['context'])}</p><p><a class="text-link" href="{e(row['link'])}">{e(row['link_label'])} <span aria-hidden="true">↗</span></a></p></section>
      <section class="sidebar-block"><h2>Talk about a similar requirement</h2><p>Discuss your systems, sources and workflow with Datecho.</p><p><a class="text-link" href="{e(DATA['contact_url'])}">Start a conversation <span aria-hidden="true">↗</span></a></p></section>
    </aside>
  </div>
  <section class="case-next"><div class="container"><p class="eyebrow">Continue exploring</p><h2><a href="../{e(next_row['slug'])}/">{e(next_row['title'])} <span aria-hidden="true">↗</span></a></h2><p>{e(next_row['subtitle'])}</p></div></section>
</main>''' + footer()


(DIST / "index.html").write_text(home_page(), encoding="utf-8")
for index, row in enumerate(DATA["projects"]):
    target = DIST / "work" / row["slug"]
    target.mkdir(parents=True)
    (target / "index.html").write_text(case_page(row, index), encoding="utf-8")
for slug in retired_slugs:
    target = DIST / "work" / slug
    target.mkdir(parents=True)
    redirect = head("Explore Cyprian’s portfolio | Datecho", DATA["description"], prefix="../../", noindex=True)
    redirect = redirect.replace("</head>", '<meta http-equiv="refresh" content="0;url=../../#work"></head>')
    redirect += '<main id="main"><section class="section container"><h1>Explore services and selected work</h1><p><a href="../../#work">Continue to the portfolio</a></p></section></main>' + footer()
    (target / "index.html").write_text(redirect, encoding="utf-8")
not_found = head("Page not found | Cyprian Wetende", "Return to Cyprian Wetende’s selected engineering work.", "404.html", BASE, True) + header(BASE)
not_found += f'<main id="main"><section class="section"><div class="container"><p class="eyebrow">404 / Page not found</p><h1>This page is not available.</h1><p class="section-intro">Return to the portfolio to explore selected work and contact details.</p><div class="actions"><a class="button button-dark" href="{e(BASE)}">Back to the portfolio</a></div></div></section></main>' + footer()
(DIST / "404.html").write_text(not_found, encoding="utf-8")
(DIST / ".nojekyll").touch()
(DIST / "robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: " + urljoin(BASE, "sitemap.xml") + "\n")
ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
sitemap = ET.Element("{http://www.sitemaps.org/schemas/sitemap/0.9}urlset")
for path in [""] + [f'work/{row["slug"]}/' for row in DATA["projects"]]:
    node = ET.SubElement(sitemap, "{http://www.sitemaps.org/schemas/sitemap/0.9}url")
    ET.SubElement(node, "{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text = urljoin(BASE, path)
ET.ElementTree(sitemap).write(DIST / "sitemap.xml", encoding="utf-8", xml_declaration=True)
print(f"Built homepage, {len(DATA['projects'])} service/project pages, {len(retired_slugs)} redirect(s), 404 page and sitemap for {BASE}")
