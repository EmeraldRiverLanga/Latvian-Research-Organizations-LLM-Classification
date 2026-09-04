# Latvian Research Organizations Database

## Overview

Latvia's Register of Enterprises holds 27,499 active associations and
foundations. Somewhere in that list are the bodies that unite researchers —
scientific societies, medical specialty associations, research institutes —
but the register has no field that marks them, and no authoritative list
exists.

This project builds one. A selection pipeline reads every registered name,
classifies it against written criteria, verifies which organizations are
still operating, and collects the contact details that exist publicly. The
result is a spreadsheet of 681 organizations in fourteen classes, usable by
anyone who needs to reach Latvia's research community: funding bodies
announcing calls, conference organizers, science policy researchers, or
journalists looking for subject expertise.

The harder part of the work is not the pipeline but the question it answers.
"An organization that unites researchers" is a conceptual category with no
ground truth. Most of this project is about making such a category
decidable, measurable and honest about its own limits.

## The Database

`output/petniecibas_organizacijas_latvija.xlsx` has two sheets. **Datubāze**
holds one row per organization; **Kopsavilkums** gives per-class totals with
website and email coverage.

Column headings and values are in Latvian, since the source register is and
the intended users are. The table below translates them.

| Column | Contents |
|---|---|
| `Reģ. nr.` | Registration number — the key to every source used here |
| `Nosaukums` | Registered name |
| `Klase` | One of the fourteen classes (see *Classes* below) |
| `Aktivitāte` | `Aktīva` (filed for 2023+), `Pasīva` (2016–2022), `Nav pārskatu datos`, `Nesen reģistrēta` |
| `Pēdējais pārskats` | Year of the most recent annual report |
| `Mājaslapa` | The organization's own site, where one was found |
| `E-pasts`, `Telefons` | Taken from that site only, never from directories |
| `Facebook`, `YouTube` | The organization's own profile, not a mention |
| `Juridiskā forma` | `Biedrība` or `Nodibinājums` |
| `Adrese` | Registered legal address |
| `Deklarētās jomas` | Self-declared activity areas, kept as context, not used for selection |
| `Pārbaudīts` | Date the contacts were verified |
| `Labots` | What was corrected during manual review, and why |

![The final database with its summary sheet](screenshots/database.png)

Classes are ordered by the level they came from, so the three levels stay
contiguous: research societies first, then the professional associations,
then the wider set of related organizations.

## Technologies Used

- **Python 3.11** — core language
- **Pandas** — register processing, joins, exports
- **OpenPyXL** — formatted Excel output with data validation
- **openai/gpt-oss-120b** (via OpenRouter) — name classification at scale
- **Serper (Google Search API)** — locating each organization's web presence
- **Requests** — page fetching, with regex extraction for contacts
- **pytest** — unit tests for the search-result rules
- **python-dotenv** — API key management
- **VS Code** — development environment

## Data Sources

| Source | What it provides | Size |
|---|---|---|
| [Register of Enterprises open data](https://dati.ur.gov.lv/register/) | All registered legal entities, legal form, termination status, address | ~120 MB |
| Activity areas of associations and foundations (same portal) | Self-declared field of activity | ~2 MB |
| [Annual report financial data](https://data.gov.lv/dati/lv/dataset/gada-parskatu-finansu-dati) | Filing year and employee count — the activity signal | ~196 MB |
| Google Search via Serper | Web presence and contacts | 551 queries |

**Snapshot: August 2026.** Register contents, filing records and contact
details all change; the `Pārbaudīts` column carries the date each contact was
verified.

Commercial company-information services were deliberately not used: their
base data comes from the Register of Enterprises, where it is free.

A note on legal forms: Latvian law recognises only two — `Biedrība`
(membership association) and `Nodibinājums` (foundation). Bodies calling
themselves an association, a union or an institute are all registered as the
former.

## Project Structure

```
latvian-research-organizations/
├── criteria.md                 # the classification specification
├── scripts/
│   ├── 01_filter_register.py   # active associations and foundations
│   ├── 02_select_by_area.py    # selection by declared area — the rejected route
│   ├── 03_classify.py          # classification against criteria.md
│   ├── 04_select.py            # candidates + review queue
│   ├── 05_export.py            # workbook for manual review
│   ├── 06_activity.py          # activity status from annual reports
│   ├── 07_contacts.py          # web presence and contact lookup
│   ├── 08_export_contacts.py   # final workbook
│   ├── lookup_rules.py         # pure rules for judging search results
│   ├── run_anchors.py          # criteria test harness
│   └── check_output.py         # audits the classification output file
├── tests/
│   ├── anchors.csv             # anchor cases with expected outcomes
│   ├── test_plan.md            # what each series tests, and what a failure means
│   └── test_lookup_rules.py    # unit tests for lookup_rules.py
├── screenshots/
├── data/
│   ├── raw/                    # downloaded open data (not in the repository)
│   └── processed/              # intermediate outputs (not in the repository)
├── output/                     # the workbook is produced here, not committed
├── .env.example
├── .gitignore
├── LICENSE
└── requirements.txt
```

The pipeline produces `petniecibas_organizacijas_latvija.xlsx` with two
sheets. **Datubāze** holds one row per organization; **Kopsavilkums** gives
per-class totals with website and email coverage. The workbook itself is not
published here — the field table below describes what it contains, and the
figures throughout this README come from it.

## Setup

### Requirements

- Python 3.11
- An OpenRouter API key and a Serper API key
- The three open datasets above, downloaded into `data/raw/`

```bash
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add both keys. The `.env` file is in
`.gitignore` from the first commit.

### Running the pipeline

```bash
python scripts/01_filter_register.py     # seconds
python scripts/run_anchors.py            # ~2 minutes, a few cents
python scripts/03_classify.py            # ~17 hours, under €3 — run it overnight
python scripts/04_select.py              # seconds
python scripts/05_export.py              # seconds
python scripts/06_activity.py            # ~1 minute
python scripts/07_contacts.py            # ~2 hours, within Serper's free tier
python scripts/08_export_contacts.py     # seconds
python -m pytest tests/                  # unit tests, no network needed
```

Run the anchor harness before the classification: it costs two minutes and
protects seventeen hours. Both long stages checkpoint after each batch and
resume where they left off, so an interruption costs one batch.

## How the Selection Works

### 1. Why keyword and category filters were rejected

Both alternatives were tested against known science societies before being
discarded, and both failed in ways worth recording.

**Filtering by declared activity area** returns 314 organizations and misses
the core of what the project looks for. The Latvian Mycological Society
declared its areas as *Education* and *Environmental protection*; the Latvian
Botanical Society declared *Professional association*; the Latvian Young
Scientists Association declared *Field of activity not otherwise classified*.
Several clearly scientific bodies declared nothing at all. Declarations can
also be indiscriminate: one foundation declared 22 areas, three of them
scientific.

**Filtering by keyword** fails on principle and in practice. "Organization
uniting researchers" is a conceptual, not a lexical category — no shared word
links the Latvian Ornithological Society and the Young Scientists
Association. A hand-written probe list of eight Latvian word stems, written
by someone who knew exactly what he was looking for, missed the
ornithological society outright: the register name uses the discipline
(*ornithology*) where the probe expected its practitioners
(*ornithologists*), and Latvian case endings widen the gap further.

### 2. Written criteria, tested before use

The classification rules live in [`criteria.md`](criteria.md) as a
specification: what counts as the unit, three cumulative levels, exclusions,
borderline cases with their decisions, and a confidence scale. The same text
is sent verbatim to the classifier and published as documentation.

Every rule is decidable from the three fields the classifier actually
receives — name, legal form, declared areas — and nothing else. Rules that
required knowledge outside those fields were rewritten until they were
observable, or removed.

Before the criteria were applied to 27,499 records, they were run against a
suite of anchor cases with known expected outcomes, three times over, to
separate defects from noise. [`tests/test_plan.md`](tests/test_plan.md)
records what each series tests and what a given failure points at.

The suite earned its cost immediately. It caught an internal contradiction
where a standalone *academy* was described as "no signal" in one section and
as an education provider in another — the model obeyed a different sentence
on each run, which no single execution would have revealed. It also caught a
branching rule whose two paths had only one test between them.

![Anchor failures naming the rule, the problem and the model's own reason](screenshots/anchor_failures.png)

Running the same suite twice produced a different set of failures — same
code, same criteria, different rows.

![The same suite on a rerun: the failures move](screenshots/anchor_failures_rerun.png)

Hence a finding worth stating plainly: **zero temperature is not
determinism.** It selects the most likely token, and where two candidates are
near-equal, the answer moves. Across repeated runs the classification *level*
was reproducible; the confidence value at a boundary was not.

### 3. Classification at scale

All 27,499 names were classified in batches of 35, with the criteria document
attached to every call. Each record returns a level, a confidence value and a
one-sentence reason naming the rule that decided — the reason is what makes
the run auditable after the fact.

Failures during a seventeen-hour run are certain rather than possible, so
every batch is checkpointed and already-processed records are skipped.

![A crash at batch 261 and the resumed run continuing from 11,099 records already done](screenshots/resume_after_failure.png)

Two mechanisms proved worth their code. Truncated responses are saved to disk
rather than discarded — from the error alone, "broken JSON" and "the answer
was cut off" are indistinguishable, and the fixes for them are different. And
the output is audited from the other side by a separate script, which is how
a single record among 27,499 was found where the model had written its reason
under a different key.

![The completed run with the level and confidence breakdown, followed by the output audit](screenshots/classification_run.png)

The run produced 1,201 candidates.

### 4. Review

The 1,201 candidates were read and grouped into error classes —
pseudoscience, animal breeding clubs, service providers, hobby collectors,
records where the name had been misread. Grouping a thousand rows is
mechanical work and was done with model assistance; deciding what each class
means, and which groupings were wrong, was not. Every class-level decision is
the author's, and several of the proposed groupings were overruled.

681 organizations remained, in fourteen classes. The classes are a product of
that review rather than an input to it: "History and local heritage" exists
because thirty-one records failed in the same way, not because the category
was planned.

The fourteen classes are a product of that review rather than an input to
it. The classifier returns a level from 0 to 3; the classes emerged from
grouping what the review actually found — "History and local heritage"
exists because thirty-one records failed in the same way, not because the
category was planned. Each class maps back onto one of the three levels, so
the ordering of the classes still carries the original breadth.

This 41% removal rate is the honest measure of what a name-only classifier
achieves on this material. It is also the reason the classifier was worth
running: reducing 27,499 to 1,201 is not work a person can do, while reducing
1,201 to 681 is an afternoon.

### 5. Activity from annual reports

Associations and foundations are required by law to file an annual report,
even with zero turnover. Filing is therefore a verifiable fact with a date,
not an inference from how fresh a website looks.

551 of the 681 organizations filed a report for 2023 or later. The rest stay
in the list with their status recorded; contacts were only sought for the
active ones.

The filing data carries two traps, both visible in a single cross-tabulation
of year against report type.

![Report type by year: the marker disappears after 2022 and 2015 is nearly empty](screenshots/annual_report_years.png)

The type marker `BNAGP` identifies association reports up to 2022 and is
empty afterwards. Filtering on the marker silently drops the three most
recent years and makes active organizations look abandoned — the error
surfaced as the Latvian Union of Scientists appearing to have filed nothing.
And the data before 2016 is not comparable: 2015 is nearly empty and
2012–2014 hold roughly half the later volume, so the activity scale stops at
"dormant" rather than grading the older years.

### 6. Contact lookup

Each active organization was searched by its exact name. What comes back is
overwhelmingly catalogue reflections of the register itself — in one sample
query, nine of ten results were company directories.

Directories are therefore identified by rule rather than by list, since
catalogue domains are endless while catalogue *forms* are countable:

- a registration-number-shaped digit string in the URL
- a known catalogue path segment (`/company/`, `/profile/`, `/uznemums/`)
- a query-driven database view (`?view=…&id=…`)
- the organization's own name in the URL slug — catalogues put it there, an
  organization's own site practically never does

A registration number in a URL marks a catalogue entry; the same number in a
page's HTML proves the page belongs to that organization. One signal,
opposite meanings depending on which layer it appears in.

These rules are the tested part of the codebase. Each case in
[`tests/test_lookup_rules.py`](tests/test_lookup_rules.py) comes from a
mistake the pipeline made on live data — a Facebook photo sub-page rejected
as a profile, a news headline slug hidden in a query parameter, a museum page
accepted for a society because both mention the same research topic.

## Data Collection Practice

Only organizational contacts were collected: general addresses of the form
`info@`, `biedriba@`, `office@` are preferred, and contacts are taken solely
from an organization's own pages. No named individuals were compiled, and
personal addresses that appeared incidentally were removed during review.

Searches ran at one query per second and page fetches at the same rate, with
each page requested once. Directory phone numbers were deliberately not
harvested: they sit next to addresses the register has already superseded.

The database contains organizations, not people. Anyone extending it should
keep that boundary — the same reasoning that makes an association's public
contact address fair to collect makes a board member's private one not.

The workbook is therefore not published in this repository. Every address in
it is already public on the organization's own website, but a compiled list
is a different object from the same addresses scattered across two hundred
sites: it is directly usable for bulk mail, and none of these organizations
agreed to appear in such a list. The pipeline is here so the result can be
reproduced by anyone with a reason to; the result is not here for anyone to
take.

## Key Design Decisions

### 1. Uncertainty is a status, not a reject

An early version of the contact lookup deleted any page whose name it could
not confirm. It threw away a real society's home page, because the site's
title read only "Home" and the name lived in an image. A gate that deletes
repeats its own mistake one level down; a gate that demotes loses nothing.

Both halves of the project converged on the same shape. Classification
returns `high` / `medium` / `low`, where `low` is a review flag rather than an
error. Contact lookup returns *confirmed* → *name on the page* → *name only in
search results* → *social media only* → *not found*. The automation sorts
evidence by strength; a person resolves the middle.

### 2. The error direction is fixed

Where a judgment is genuinely arguable, the pipeline errs toward the wider
level, never toward confident placement in a narrower one.

This has a cost that is documented rather than solved. An association named
after its *practitioners* reaches the professional tier on the person-noun,
while the same body named after its *field* does not — two organizations that
may be identical in substance sit at different levels, because nothing in the
second name proves it unites practitioners.

### 3. Every filter is checked against the data, never the description

The register's documentation lists a `uri` column that does not exist in the
export. The `closed` column marks empty values with a whitespace string
rather than `NaN`, so the first activity filter returned zero rows. The
annual report file changes its type marker mid-series. One legal form appears
2,238 times and all 2,238 are terminated.

Each of these was found by inspecting values before filtering on them, and
each would have been invisible in the output.

## Results

| Stage | Count |
|---|---|
| Registered associations and foundations (active in the register) | 27,499 |
| Classified as candidates | 1,201 |
| After review | 681 |
| Filing annual reports for 2023 or later | 551 |

Contacts were sought for the 551 active organizations only. Their web
presence, as mutually exclusive categories:

| Presence | Count |
|---|---|
| Website and social media page | 95 |
| Website only | 114 |
| Social media page only | 36 |
| Neither | 306 |

Extracted from those pages: **89 email addresses** and **107 phone numbers**.

### Classes

| Class | Total | Active | With a website | With an email |
|---|---|---|---|---|
| Research societies | 83 | 68 | 24 | 10 |
| Medical specialty associations | 119 | 110 | 54 | 19 |
| Applied psychology and therapy | 68 | 58 | 27 | 15 |
| Care and health professions | 31 | 19 | 12 | 7 |
| Other academic professions | 30 | 26 | 15 | 6 |
| Legal profession | 16 | 14 | 6 | 2 |
| Engineering profession | 15 | 14 | 10 | 5 |
| Research institutes and centres | 95 | 74 | 16 | 7 |
| Institutional associations | 22 | 21 | 9 | 3 |
| Student and early-career societies | 19 | 13 | 5 | 3 |
| Subject-teacher associations | 38 | 31 | 14 | 4 |
| History and local heritage | 51 | 43 | 6 | 2 |
| Outreach and education | 37 | 26 | 9 | 5 |
| Unclear | 57 | 34 | 2 | 1 |
| **Total** | **681** | **551** | **209** | **89** |

## Scope and Limitations

**Contact coverage is bounded by the data, not by the method.** 89 email
addresses across the 551 active organizations is thin, and the reason was
measured rather than assumed: 306 of them have no web presence at all, and
another 36 have only a social media page with no published address. Small
Latvian associations do not publish contact details online — they operate
through personal networks and host institutions. Those contacts are not
missing from this list; they are missing from the internet, and anyone
building the same list by hand would meet the same ceiling.

That measurement is itself a result. It tells whoever extends this list where
searching is not worth the time, and points to the sources that would work
instead: the Academy of Sciences' associated societies list, university
institute pages, and NGO directories.

**The narrowest class will never be fully clean from a name alone.**
Individual misplacements survived every rule revision, which is why level 1
was reviewed by eye in full rather than trusted.

**The heuristic converges on honest uncertainty, not on correctness.** After
roughly six revision cycles, contact-lookup fixes stopped being pure gains
and became trades — each corrected a class of errors and broke something
else. That is the objective sign that the automation's balance has closed and
the remainder belongs to the reviewer..

**Classification did not revisit its own conclusions.** Names were classified
before the pages were fetched, and the pages were never fed back. The 57
unclear records are unclear only because the classifier never saw what the
lookup later found.

## Possible Improvements

- Re-classify the unclear records from page content the pipeline already
  collected — the cheapest remaining gain
- Fill contacts from structured sources, which cover exactly the organizations
  this pipeline found hardest
- Generate descriptions from page content rather than meta tags, which are
  present on only a minority of sites
- Track changes between register snapshots so the list stays current

## Licence

The code is released under the MIT licence. The database in `output/` is
derived from Latvian open government data and is published under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — free to use and
redistribute with attribution. Both are set out in [`LICENSE`](LICENSE).

Attribution for the database should name this project together with its
underlying sources: the Register of Enterprises and the State Revenue Service
annual report data.
