"""Find each active organization's own web presence and contact details."""
import argparse
import json
import os
import re
import time
from datetime import date
from urllib.parse import urlparse

import pandas as pd
import requests
from dotenv import load_dotenv

from lookup_rules import (PLATFORMS, PHONE_RE, PHONE_RE_LOCAL, host,
                          is_directory, is_mention, is_profile, name_matches,
                          name_stems, pick_description, pick_email)

SRC = "data/processed/07_with_activity.csv"
DST = "data/processed/07_contacts.jsonl"

load_dotenv()
SERPER_KEY = os.environ["SERPER_API_KEY"]


def search(query):
    """One Serper query, restricted to Latvian results."""
    response = requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": SERPER_KEY, "Content-Type": "application/json"},
        json={"q": query, "gl": "lv", "hl": "lv", "num": 10},
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("organic", [])


def fetch(url):
    """Fetch a page; failure is expected and not an error."""
    try:
        r = requests.get(url, timeout=20, headers={
            "User-Agent": "Mozilla/5.0 (research contact lookup)"})
        r.raise_for_status()
        return r.text
    except requests.RequestException:
        return ""


def lookup(row):
    """Search for one organization and classify what comes back."""
    # names in the register carry their own quotes; nesting breaks exact search
    clean = str(row["Nosaukums"]).replace('"', "").replace("„", "").replace("”", "")
    results = search(f'"{clean}"')
    regcode = str(row["Reģ. nr."]).strip()

    out = {"majaslapa": "", "facebook": "", "youtube": "", "linkedin": "",
           "apraksts": "", "e_pasts": "", "telefons": "",
           "regnr_apstiprinats": False, "nosaukums_lapa": False,
           "atrasts_katalogos": False, "avoti": []}

    for r in results:
        url, snippet = r.get("link", ""), r.get("snippet", "")
        title = r.get("title", "")
        h = host(url)

        if is_directory(url, h, clean):
            # A registration number in a page's HTML proves ownership only if
            # the page is a candidate at all; for a catalogue it merely proves
            # the catalogue is correct. Hence the identity gate comes first.
            out["atrasts_katalogos"] = True
            continue

        kind = PLATFORMS.get(h)
        if kind:
            # For a profile the URL itself is the identity: a snippet may
            # discuss our topic on someone else's page, the handle cannot.
            handle = " ".join(urlparse(url).path.split("/"))
            if (not out[kind] and is_profile(url, kind)
                    and name_matches(clean, f"{title} {handle}")):
                # Google may return a sub-page (/photos/, /videos/); keep the
                # profile itself rather than whichever section it returned.
                parts = [p for p in urlparse(url).path.split("/") if p]
                depth = 2 if parts[0] in ("p", "channel", "c", "user",
                                          "company", "school") else 1
                out[kind] = f"https://{h}/" + "/".join(parts[:depth]) + "/"
            continue

        if is_mention(url, h):
            continue

        # An organization's own site lives at the root or one level down.
        # Downloads, encyclopaedia entries, forum threads and portal records
        # all sit deep inside someone else's domain — one rule, five forms.
        depth = len([p for p in urlparse(url).path.split("/") if p])
        own_domain = bool(name_stems(clean) & {w[:6] for w in re.findall(r"\w+", h)})
        if depth > 2 and not own_domain:
            continue

        # The name gate: a page that does not carry the organization's
        # distinctive words is not its page, whatever else it looks like.
        if not out["majaslapa"] and name_matches(clean, f"{title} {snippet} {url}"):
            out["majaslapa"] = url
            if regcode in snippet:
                out["regnr_apstiprinats"] = True
            out["avoti"].append(url)

    # Contacts come only from the organization's own site. Directory phone
    # numbers sit next to addresses the register has already superseded.
    if out["majaslapa"]:
        html = fetch(out["majaslapa"])
        # The page is the primary source, but a rule that deletes repeats the
        # mistake one level down: a site whose name sits in an image or is
        # rendered by JavaScript would fail too. So this demotes, never drops.
        out["nosaukums_lapa"] = bool(html) and name_matches(clean, html)
        if html:
            if regcode in html:
                out["regnr_apstiprinats"] = True
            out["apraksts"] = pick_description(html)
            out["e_pasts"] = pick_email(html, host(out["majaslapa"]))
            phone = PHONE_RE.search(html) or PHONE_RE_LOCAL.search(html)
            out["telefons"] = phone.group(0) if phone else ""

    # Five rungs in order of evidential strength; nothing is discarded, only
    # sorted. The middle rungs are the grey zone a person resolves.
    if out["majaslapa"]:
        if out["regnr_apstiprinats"]:
            out["statuss"] = "apstiprināta"
        elif out.get("nosaukums_lapa"):
            out["statuss"] = "nosaukums lapā"
        else:
            out["statuss"] = "nosaukums tikai meklētājā"
    elif out["facebook"] or out["youtube"] or out["linkedin"]:
        out["statuss"] = "tikai sociālie tīkli"
    else:
        out["statuss"] = "nav atrasts"

    out["avoti"] = " | ".join(out["avoti"][:3])
    return out


def load_done(path):
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as f:
        return {json.loads(line)["regcode"] for line in f if line.strip()}


parser = argparse.ArgumentParser()
parser.add_argument("--klase", help="restrict to one class")
parser.add_argument("--limit", type=int, help="process only the first N")
args = parser.parse_args()

df = pd.read_csv(SRC, encoding="utf-8", dtype={"Reģ. nr.": str})
df = df[df["aktivitate"] == "Aktīva"]
if args.klase:
    df = df[df["Klase"] == args.klase]

done = load_done(DST)
todo = [r for _, r in df.iterrows() if str(r["Reģ. nr."]).strip() not in done]
if args.limit:
    todo = todo[:args.limit]

print(f"{len(df)} active in scope, {len(done)} already done, {len(todo)} to look up")

today = date.today().isoformat()
with open(DST, "a", encoding="utf-8") as out:
    for i, row in enumerate(todo, 1):
        name = str(row["Nosaukums"])
        try:
            result = lookup(row)
        except requests.RequestException as e:
            print(f"  {i}/{len(todo)} FAILED {type(e).__name__}: {name[:40]}")
            time.sleep(5)
            continue

        result.update({"regcode": str(row["Reģ. nr."]).strip(), "name": name,
                       "klase": row["Klase"], "parbaudits": today})
        out.write(json.dumps(result, ensure_ascii=False) + "\n")
        out.flush()

        print(f"  {i}/{len(todo)} {result['statuss']:<22} {name[:45]}")
        time.sleep(1)  # courtesy delay between queries

if os.path.exists(DST):
    res = pd.read_json(DST, lines=True)
    print(f"\nlooked up: {len(res)}")
    print(res["statuss"].value_counts().to_string())
    print(f"\nwith email: {(res['e_pasts'].fillna('') != '').sum()}")
    print(f"registration number confirmed: {res['regnr_apstiprinats'].sum()}")