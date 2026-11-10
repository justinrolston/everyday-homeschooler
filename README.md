# Everyday Homeschooler

Static copy of everydayhomeschooler.com, moved off Squarespace. It's built with Jekyll and hosted on GitHub Pages.

## How it's put together

- `_pages/**.html`: one file per old Squarespace URL. `permalink` keeps the original path, so old links (Pinterest and so on) still work. The page bodies are Squarespace's rendered HTML, wrapped in `{% raw %}`.
- `index.html`: the homepage.
- `_includes/header.html`, `footer.html`, `head-styles.html`, `svg-sprite.html`: site chrome taken from the live site.
- `assets/css`: Squarespace's site, theme and component CSS, saved locally. `assets/site-fixes.css` overrides the parts that relied on Squarespace's JavaScript.
- `assets/js/site.js`: a small replacement for the Squarespace runtime (mobile menu, nav chevrons, accordions, YouTube embeds).
- `assets/img`, `assets/fonts`: every image and font the site used.
- `s/`: downloadable recipe-card PDFs, at their original `/s/...` URLs.
- `scripts/mirror.py`: the one-time scraper that produced all of this. Running it again overwrites hand edits.

## Not migrated (on purpose)

- **Shop**: moving to another platform. Nav links removed; homepage shop sections hidden.
- **Contact / Request a Consultation forms**: the pages show a placeholder. Decide later between Formspree, a Google Form or a mailto link (search for `eh-form-placeholder`).
- **Sarah's blog, sidebar, example pages**: dropped.
- **Justin's blog** (`/justins-blog`): kept as an archive. It isn't linked anywhere, it's left out of the sitemap, and it's marked `noindex`.

## Local preview

```bash
bundle install
LANG=en_US.UTF-8 bundle exec jekyll serve
```

## Going live

1. Push to GitHub and enable Pages (Settings → Pages → Deploy from branch `main`, root).
2. In DNS, point `www` at `<user>.github.io` (CNAME) and the apex at GitHub's A records.
3. Cancel Squarespace once the new site is verified.
