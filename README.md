# Cyprian Wetende — Datecho portfolio

A separate portfolio for Cyprian's technical role at Datecho Analytics: data
analytics, Power BI reporting, data preparation, integrations and automation. The original personal site
at https://wetende.github.io/portfolio/ is maintained separately and is not
redirected or modified by this repository.

The site is pre-rendered HTML/CSS with small progressive enhancements for the
mobile navigation and work filters. It has no runtime framework, analytics or
contact-form service. Enquiries link to Datecho's existing contact workflow.

## Build and check

Python 3.11 or newer, with no third-party build packages:

```bash
python3 scripts/build.py
python3 scripts/check_site.py
python3 -m http.server 8007 --directory dist
```

Edit `content/portfolio.json` for the public copy. Power BI reporting and data
analysis are presented as Datecho service offerings, with scope and delivery
methods rather than invented completed client engagements. Cyprian confirmed
Power BI, Tableau, Excel and pandas alongside Python and SQL as personal skills.
Prior project names were
approved for reuse; those projects remain labelled as prior/independent work,
with Datecho's own platform identified separately. Descriptions are grounded
in the existing portfolio and the deployed Datecho application. No quantified
business outcomes or client endorsements are inferred. The retired CrossView
project URL redirects to the portfolio rather than remaining in the work list.

## Hosting

GitHub Actions builds and deploys `dist/` to this repository's GitHub Pages site.
`site-config.json` controls canonical URLs. The planned custom domain is
`cyprian.datecho.com`; the initial preview is
`https://wetende.github.io/cyprian-portfolio/`.

When connecting the domain, configure it in this repository's Pages settings,
set the DNS CNAME `cyprian` to `wetende.github.io`, and update `base_url` plus
`custom_domain` in `site-config.json`. The GitHub Pages custom-domain setting is
separate from this source configuration; custom Actions workflows do not use a
CNAME file to register the domain. Enable HTTPS after the certificate is ready.

Reference: https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site

The portrait is the user-supplied Datecho image. Font licence notices are
included in `assets/fonts/`. Source and content notes under `.cache/` are local
working material and are excluded from Git and published build output.
