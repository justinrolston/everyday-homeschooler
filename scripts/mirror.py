"""One-time mirror of everydayhomeschooler.com (Squarespace) into this Jekyll repo.

Usage: python scripts/mirror.py <repo-root> <cache-dir>
Fetches every page reachable from the sitemap + nav (minus the shop), downloads
CSS/fonts/images/PDFs into assets/, and writes one Jekyll page per URL that keeps
the original path as its permalink.
"""
import hashlib, json, os, re, sys, time
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup, Comment

SITE = "https://www.everydayhomeschooler.com"
ROOT, CACHE = sys.argv[1], sys.argv[2]
os.makedirs(CACHE, exist_ok=True)
S = requests.Session()
S.headers["User-Agent"] = "Mozilla/5.0 (site-migration)"

SKIP = re.compile(r"^/(shop|cart|sidebar|example|sarahsblog|account|commerce|s/|search|config|static|api|checkout)")
HIDDEN = re.compile(r"^/justins-blog")  # kept as an archive, not linked or indexed
ASSET_HOSTS = ("images.squarespace-cdn.com", "static1.squarespace.com", "assets.squarespace.com",
               "definitions.sqspcdn.com")
asset_map = {}


def get(url, binary=False):
    key = hashlib.sha1(url.encode()).hexdigest()
    path = os.path.join(CACHE, key)
    if os.path.exists(path):
        data = open(path, "rb").read()
    else:
        for i in range(4):
            r = S.get(url, timeout=60)
            if r.status_code == 429:
                time.sleep(5 * (i + 1)); continue
            break
        if r.status_code != 200:
            print("  !", r.status_code, url); return None
        data = r.content
        open(path, "wb").write(data)
        time.sleep(0.2)
    return data if binary else data.decode("utf-8", "replace")


def local_asset(url, kind=None):
    """Download a remote asset and return its site-relative path."""
    if url.startswith("//"):
        url = "https:" + url
    url = url.replace("&amp;", "&")
    p = urlparse(url)
    if p.netloc not in ASSET_HOSTS:
        return None
    base = p.scheme + "://" + p.netloc + p.path
    fetch = base
    is_img = p.netloc == "images.squarespace-cdn.com"
    if is_img:
        fetch = base + "?format=1500w"
    if base in asset_map:
        return asset_map[base]
    name = unquote(os.path.basename(p.path)).replace(" ", "-").replace("+", "-") or "file"
    name = re.sub(r"[^A-Za-z0-9._-]", "", name)[-80:]
    h = hashlib.sha1(base.encode()).hexdigest()[:8]
    ext = os.path.splitext(name)[1].lower()
    if kind is None:
        kind = ("img" if is_img or ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")
                else "files" if ext in (".pdf", ".doc", ".docx", ".zip") else
                "css" if ext == ".css" else "fonts" if ext in (".woff", ".woff2", ".ttf", ".otf", ".eot") else "misc")
    rel = f"/assets/{kind}/{h}-{name}"
    data = get(fetch, binary=True)
    if data is None and fetch != base:
        data = get(base, binary=True)
    if data is None:
        asset_map[base] = None
        return None
    dest = ROOT + rel
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if kind == "css":
        css = data.decode("utf-8", "replace")
        css = rewrite_css(css, fetch)
        data = css.encode()
    open(dest, "wb").write(data)
    asset_map[base] = rel
    return rel


def rewrite_css(css, base_url):
    def repl(m):
        u = m.group(2).strip()
        if u.startswith("data:"):
            return m.group(0)
        full = urljoin(base_url, u)
        loc = local_asset(full)
        return f"url({m.group(1)}{loc or full}{m.group(1)})"
    css = re.sub(r"url\((['\"]?)([^)'\"]+)\1\)", repl, css)
    # @import of remote css
    return css


ASSET_RE = re.compile(r"(?:https?:)?//(?:images\.squarespace-cdn\.com|static1\.squarespace\.com)/[^\s\"'<>)]+")


def rewrite_urls(html):
    return ASSET_RE.sub(lambda m: local_asset(m.group(0)) or m.group(0), html)


def norm(path):
    path = path.split("#")[0].split("?")[0]
    if not path.startswith("/"):
        return None
    if len(path) > 1:
        path = path.rstrip("/")
    return path


# ---------------------------------------------------------------- crawl
sitemap = get(SITE + "/sitemap.xml")
queue = [norm(urlparse(u).path) or "/" for u in re.findall(r"<loc>([^<]+)</loc>", sitemap)]
queue = ["/"] + [q for q in queue if q not in ("/", "/home")]
seen, pages = set(), {}
while queue:
    path = queue.pop(0)
    if path in seen or SKIP.match(path):
        continue
    seen.add(path)
    html = get(SITE + path)
    if html is None:
        continue
    pages[path] = html
    print("page", path)
    for href in re.findall(r'href="([^"]+)"', html):
        if href.startswith(SITE):
            href = href[len(SITE):]
        n = norm(href)
        if n and n not in seen and not SKIP.match(n) and "." not in n.rsplit("/", 1)[-1]:
            queue.append(n)

# ---------------------------------------------------------------- shared head CSS
home = BeautifulSoup(pages["/"], "html.parser")
css_links = []
for l in home.head.find_all("link", rel="stylesheet"):
    href = l["href"]
    if "commerce" in href:
        continue
    loc = local_asset(href if not href.startswith("//") else "https:" + href, "css")
    css_links.append(loc or href)
inline_styles = [str(s) for s in home.head.find_all("style")]
# fonts: Typekit / Google fonts links are kept remote
font_links = [str(l) for l in home.head.find_all("link") if "fonts" in l.get("href", "") or "typekit" in l.get("href", "")]

# ---------------------------------------------------------------- header / footer
def clean(node):
    for t in node.find_all(["script", "noscript"]):
        t.decompose()
    for c in node.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()
    for img in node.find_all("img"):
        if img.get("data-src") and not img.get("src"):
            img["src"] = img["data-src"]
        img.attrs.pop("srcset", None)
        img.attrs.pop("data-load", None)
    return node


def drop_nav(node):
    """Remove Shop + cart from navigation."""
    for a in node.find_all("a", href=True):
        h = a["href"]
        if h in ("/shop", "/cart") or h.startswith("/shop/"):
            item = a.find_parent(class_=re.compile(r"(header-nav-item|header-menu-nav-item|header-actions-action--cart)"))
            (item or a).decompose()
    for c in node.select(".header-actions-action--cart, .showOnMobile .header-actions-action--cart, .user-accounts-link"):
        c.decompose()


header = clean(home.find("header"))
drop_nav(header)
footer = clean(home.find("footer", id="footer-sections"))
inc = os.path.join(ROOT, "_includes"); os.makedirs(inc, exist_ok=True)
open(os.path.join(inc, "header.html"), "w").write(rewrite_urls(str(header)))
open(os.path.join(inc, "footer.html"), "w").write(rewrite_urls(str(footer)) if footer else "")
open(os.path.join(inc, "head-styles.html"), "w").write(
    "\n".join(font_links) + "\n" +
    "\n".join(f'<link rel="stylesheet" type="text/css" href="{h}">' for h in css_links) + "\n" +
    rewrite_urls("\n".join(inline_styles)) + "\n")

# ---------------------------------------------------------------- pages
def fm_str(s):
    return json.dumps(s or "", ensure_ascii=False)


for path, html in pages.items():
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main", id="page")
    if not main:
        print("  ! no main", path); continue
    clean(main)
    # rewrite links to dropped areas
    for a in main.find_all("a", href=True):
        h = a["href"].replace(SITE, "")
        a["href"] = h
    for t in main.select("[data-block-css], [data-block-scripts]"):
        t.attrs.pop("data-block-scripts", None)
    # pull any per-block component CSS
    extra_css = set()
    for m in re.finditer(r'https://definitions\.sqspcdn\.com/[^&"]+?\.css', html):
        extra_css.add(m.group(0))
    extra = [local_asset(u, "css") for u in sorted(extra_css)]
    title = soup.title.get_text(strip=True) if soup.title else ""
    desc = soup.find("meta", attrs={"name": "description"})
    body_class = " ".join(soup.body.get("class", []))
    body_id = soup.body.get("id", "")
    hidden = bool(HIDDEN.match(path))
    out = path.strip("/") or "index"
    dest = os.path.join(ROOT, "_pages", out + ".html") if path != "/" else os.path.join(ROOT, "index.html")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    fm = ["---", "layout: default", f"title: {fm_str(title)}",
          f"description: {fm_str(desc['content'] if desc else '')}",
          f"permalink: {path if path == '/' else path + '/'}",
          f"body_class: {fm_str(body_class)}", f"body_id: {fm_str(body_id)}"]
    if extra:
        fm.append("extra_css:")
        fm += [f"  - {e}" for e in extra if e]
    if hidden:
        fm += ["sitemap: false", "noindex: true"]
    fm.append("---")
    inner = rewrite_urls(main.decode_contents())
    open(dest, "w").write("\n".join(fm) + "\n{% raw %}" + inner + "{% endraw %}\n")

json.dump({k: v for k, v in asset_map.items()}, open(os.path.join(CACHE, "asset_map.json"), "w"), indent=1)
print(len(pages), "pages,", len(asset_map), "assets")
