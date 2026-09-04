"""Pure rules for judging what a search result is.

Cut out of the lookup pipeline so they can be tested without a network:
every function here decides something about a URL or a piece of text, with
no side effects and no I/O.
"""
import re
from urllib.parse import urlparse

# Directories that do not put a registration number in the URL. The rule in
# is_directory() catches the rest; this list is a supplement, not the test.
DIRECTORIES = {
    "lursoft.lv", "company.lursoft.lv", "firmas.lv", "zl.lv", "1188.lv",
    "kompass.com", "pilseta24.lv", "visaigimenei.lv", "company.lv",
    "ur.gov.lv", "dati.ur.gov.lv", "data.gov.lv", "opencorporates.com",
    "companywall.lv", "nace.lv", "bizness.lv", "okredo.com", "kombo.lv",
    "infolapas.lv", "enciklopedija.lv", "literatura.lv", "barikadopedija.lv",
    "digitalabiblioteka.lv", "lvportals.lv",
}

# Platforms where an organization may keep its own profile.
PLATFORMS = {
    "facebook.com": "facebook",
    "youtube.com": "youtube",
    "linkedin.com": "linkedin",
}

# Encyclopaedic and news coverage: evidence the body is real, not its own site.
MENTIONS = {"wikipedia.org", "lsm.lv", "delfi.lv", "tvnet.lv", "nra.lv",
            "la.lv", "diena.lv", "db.lv", "ir.lv", "ventasbalss.lv",
            "plz.lv", "jauns.lv", "apollo.lv", "bnn.lv", "ntz.lv"}
MENTION_PATHS = ("/jaunums/", "/zinas/", "/raksts/", "/aktualitates/",
                 "/news/", "/blog")
# Catalogue paths: a page that lists organizations, not one that belongs to
# one. Matched with both boundaries — a bare "/company" would also hit
# "/our-company-history", the same trap the phone regex fell into.
DIRECTORY_PATHS = ("/infolapa", "/company", "/uznemums", "/profile",
                   "/katalogs", "/biedribas-un-nodibinajumi", "/kandidati",
                   "/firma", "/reviews", "/dalibnieki",
                   # reference works are catalogues too: an entry about the
                   # organization in someone else's collection
                   "/skirklis", "/raksti", "/organizacijas", "/iestade",
                   "/wiki")

# A registration number in a URL marks a catalogue entry; the same number in
# a page's HTML proves the page belongs to that organization. One signal,
# opposite meanings depending on which layer it appears in.
REGNR_IN_URL = re.compile(r"\b[45]\d{10}\b")

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
EMAIL_BLACKLIST = ("wixpress", "sentry", "example.", "domain.com", "@2x",
                   "cloudfront", "googleapis", "schema.org", "yourdomain")
GENERIC = ("info@", "biedriba@", "birojs@", "office@", "kontakti@", "pasts@")

# Two passes: with the country code, then a bare Latvian mobile or landline.
# The second is looser and may catch a stray number; the first is trusted.
PHONE_RE = re.compile(r"\+371[\s\-]?\d{2}[\s\-]?\d{3}[\s\-]?\d{3}")
PHONE_RE_LOCAL = re.compile(r"\b[26]\d{7}\b")

# Words shared by hundreds of names carry no identifying power.
STOP = {"latvijas", "biedrība", "asociācija", "apvienība", "savienība",
        "komiteja", "nodibinājums", "fonds", "centrs", "klubs",
        "starptautiskā", "nacionālā", "republikas"}

META_RE = re.compile(
    r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']{20,400})',
    re.I)
TITLE_RE = re.compile(r"<title[^>]*>([^<]{5,200})</title>", re.I)


def host(url):
    """Bare hostname, without the www prefix."""
    return urlparse(url).netloc.lower().removeprefix("www.")


def name_stems(text):
    """Distinctive words, truncated to absorb Latvian case endings."""
    return {w[:6] for w in re.findall(r"\w+", text.lower())
            if w not in STOP and len(w) > 3}


def name_matches(org_name, text):
    """The page must carry the organization's distinctive words."""
    need = name_stems(org_name)
    if not need:
        return False          # nothing distinctive to match on: cannot verify
    have = {w[:6] for w in re.findall(r"\w+", text.lower())}
    # short names have few distinctive stems; requiring "all but one" then
    # accepts a half-match, so demand all of them when there are two or fewer
    hits = sum(1 for t in need if t in have)
    return hits >= (len(need) if len(need) <= 2 else len(need) - 1)


def is_directory(url, h, org_name=""):
    """A directory by rule, not by list.

    Three forms give a catalogue away: a registration number in the URL, a
    known catalogue path, and a query-driven database view. The fourth is
    the strongest — catalogues put the organization's name in the URL slug,
    an organization's own site practically never does.
    """
    parsed = urlparse(url)
    path = parsed.path.lower().rstrip("/")
    if (h in DIRECTORIES
            or bool(REGNR_IN_URL.search(url))
            or any(p + "/" in path + "/" for p in DIRECTORY_PATHS)
            or ("view=" in parsed.query and "id=" in parsed.query)):
        return True
    # the name may sit in the path slug or in a subdomain
    slug = path.split("/")[-1] + "-" + h.split(".")[0]
    if org_name and slug.count("-") >= 2:
        need = name_stems(org_name)
        have = {w[:6] for w in re.findall(r"\w+", slug.replace("-", " "))}
        # short names yield a single distinctive stem, so a fixed threshold
        # of two makes the rule unreachable for them
        return sum(1 for t in need if t in have) >= min(2, len(need))
    return False


def is_mention(url, h):
    """Coverage of the organization rather than its own presence."""
    path = urlparse(url).path.lower()
    # A last segment with five or more hyphens is an article headline, not a
    # home page — form rather than a list of news domains. Such slugs appear
    # in the path or in a query parameter.
    slug = path.rstrip("/").split("/")[-1] + urlparse(url).query.lower()
    return (any(h.endswith(m) for m in MENTIONS)
            or h.endswith(".gov.lv")
            or any(p in path for p in MENTION_PATHS)
            or slug.count("-") >= 5)


def is_profile(url, platform):
    """Distinguish an organization's own profile from a group or a post."""
    parts = [p for p in urlparse(url).path.split("/") if p]
    if platform == "facebook":
        # Google may return a sub-page; the profile is the first segment
        if not parts or parts[0] in ("groups", "events", "watch", "share"):
            return False
        # a numeric handle carries no words, so it can never pass the name
        # gate: unverifiable rather than unverified
        return not parts[-1].isdigit()
    if platform == "youtube":
        return bool(parts) and parts[0].startswith(("@", "c", "channel", "user"))
    if platform == "linkedin":
        return bool(parts) and parts[0] in ("company", "school")
    return False


def pick_description(html):
    """What the organization writes about itself, not a search fragment.

    A snippet comes from wherever the search term appeared on the page —
    a footer, a cookie notice — while the meta description is written for
    the purpose. When neither exists the field stays empty, which is
    honester than a fragment.
    """
    meta = META_RE.search(html)
    if meta:
        return meta.group(1).strip()
    # A <title> is a page name, not a description — better empty than "Sākums"
    return ""


def pick_email(html, domain):
    """Prefer a general address on the organization's own domain.

    No strict domain match: small associations routinely host on Wix and
    keep contact on gmail. The preference order gives the right asymmetry.
    """
    found = [e.lower() for e in EMAIL_RE.findall(html)]
    found = [e for e in found
             if not e.endswith((".png", ".jpg", ".gif", ".svg", ".webp"))
             and not any(b in e for b in EMAIL_BLACKLIST)]
    same = [e for e in found if domain and e.endswith("@" + domain)]
    for pool in (same, found):
        for e in pool:
            if e.startswith(GENERIC):
                return e
        if pool:
            return pool[0]
    return ""