# Inclusion Criteria

## What counts as an organization

We are looking for **organizations whose members are researchers or
scientists as individuals**, or which represent them.

This is not the same as an organization that does research or funds it. A
university endowment fund finances research but unites no researchers — it
does not qualify. A mycological society whose members are mycologists does.

Levels 1 and 2 apply this definition strictly. **Level 3 deliberately widens
beyond it** — to institutional members, research bodies without members, and
adjacent communities. This widening is intentional, not a contradiction.

The register covers two Latvian legal forms: `Biedrība` (membership
association) and `Nodibinājums` (foundation, which has no members).

Because a `Nodibinājums` has no members, it can only qualify at level 3, and
only as a research body. This is decided from the name:

- The name contains a research-body marker — such as `institūts`,
  `pētniecības centrs`, `zinātniskais centrs`, `domnīca` — it can qualify
  (level 3). This list is exemplary, not closed: a name that unambiguously
  denotes a research body by other wording also qualifies, at `medium`
  confidence.
- `centrs` on its own is not a research-body marker; it must be qualified
  (`pētniecības centrs`, `zinātniskais centrs`). A bare `centrs` names any
  kind of organization.
- `akadēmija` counts as a research-body marker only next to a science word
  (`zinātņu akadēmija`). On its own it names a school or a course provider
  and falls under the education-provider exclusion (level 0, `high`).
- The name contains a support marker — `fonds`, `atbalsta`, `stipendiju`,
  `piemiņas`, `balvas` — it does not qualify (level 0, `high`). This
  negative list is firm, not exemplary. When a name contains both a
  research-body and a support marker ("X institūta atbalsta fonds"), the
  support marker wins: the entity funds a research body, it is not one.
- No signal either way — level 0, `low` (the review queue). An unmarked
  `Nodibinājums` is never level 0 `high` on the name alone.

## How to decide

The classifier receives three fields per organization: the **name**, the
**legal form** (`type_text`: `Biedrība` or `Nodibinājums`), and the
**declared activity areas**. Every rule in this document is decidable from
these three fields and nothing else.

Apply the rules in this order. The first rule that fires decides.

0. **The legal-form rule** — if the entity is a `Nodibinājums`, its ceiling
   is level 3, and the marker test above **replaces the level signals of
   step 2**. Exclusion signals (step 1) still apply to a `Nodibinājums`:
   an olympiad, sports-structure or support name is level 0 `high` for
   either legal form.
1. **Exclusion signals** (see *Exclusions*), subject to the industry-discipline rule.
2. **Level signals** (see the level definitions).
3. **The default rule** — when neither fires.

### The default rule

If the name carries no level signal and no exclusion signal (only a place
name, a slogan, an abbreviation, a personal name), assign **level 0 with
`low` confidence** and state "no signal in the name" as the reason.

Level 0 therefore has two meanings, distinguished by confidence:

- `level 0, high` — positive evidence that the organization does not qualify.
- `level 0, low` — no evidence either way; a candidate for human review.

Never guess a positive level from an uninformative name. The review queue is
the set of all `low` results, whatever their level.

## Levels

The level records which category an organization belongs to, from narrowest
to widest. The contact circle at width N is the set of organizations with
`1 <= level <= N`. Level 0 means the organization is not in the circle at
any width.

### Level 1 — research societies

Organizations that unite researchers of a scientific discipline. The
observable signal: **the name denotes a scientific discipline or its
researchers** — typically the discipline or the researcher noun in the
genitive — and the organization is a society or association.

- "Latvijas Mikologu biedrība", "Latvijas Ornitoloģijas biedrība",
  "Latvijas Botāniķu biedrība", "Latvijas Ģeogrāfijas biedrība",
  "Latvijas Zinātnieku savienība", "Latvijas anatomu, histologu un
  embriologu biedrība".
- Both forms count: the discipline ("Ornitoloģijas") and its researchers
  ("ornitologu"). Selection is by concept, not by a single word form.
- Humanities and social sciences are disciplines: linguistics, folklore
  studies, sociology, history *as an academic field* all qualify. General
  cultural or creative unions (writers, artists, composers) do not — they
  unite practitioners of an art, not researchers. This exclusion applies
  **only when no research signal is present in the name**: a research word
  (`zinātnieku`, `pētnieku`) or an academic discipline (`mākslas zinātnes`)
  fires the discipline rule first, and the discipline rule wins — "Latvijas
  Mākslas zinātnieku un kuratoru biedrība" is level 1, not 0.
- **Hobby override:** if the name also contains an amateur marker —
  `amatieru`, `draugu`, `klubs`, `entuziastu`, `kolekcionāru` — assign
  level 3, not 1. A discipline word alone, without such a marker, stays at
  level 1 even if the society is known to include amateurs; the marker, not
  outside knowledge, decides. This override deliberately errs downward: a
  genuine researcher group that calls itself a `klubs` lands at level 3, not
  1 — an accepted cost, since it stays in the widest circle.
- `Novadpētniecības` (local-history) societies are amateur research by
  default: level 3.
- **Practice, not study.** A discipline-shaped word is a level 1 signal only
  when the name denotes the study of the field. A name denoting its
  practice, delivery or application is a practitioners' or hobby body, not a
  research society. `Mikoloģijas biedrība` studies fungi; `Dārzkopības
  biedrība` grows plants.
  Applied fields whose name denotes a practice — `medicīnas`, `ķirurģijas`,
  `terapijas`, `radioloģijas`, `farmācijas`, and likewise gardening,
  breeding, consultancy — are practitioner domains, not objects of study.
  A practice field reaches level 1 only when the name also carries a
  research word (`zinātnes`, `pētniecības`) or a researcher noun
  (`mikrobiologu`, `fiziologu`); otherwise level 3, `medium`, or level 0
  with a commercial or service marker.

### Level 2 — professional associations with a research component

Everything in level 1, plus associations of practising specialists in an
academic profession. The observable signal: **the name denotes persons of a
profession** — a person-noun in the plural genitive: `ārstu`, `ķirurgu`,
`psihologu`, `inženieru`, `arhitektu`, `agronomu`, `juristu`, `farmaceitu`
and similar.

The delimitation, since "and similar" must not float: the profession must
**require higher education and rest on a research literature** in its
practice. Medicine, engineering, law, architecture, psychology, agronomy,
pharmacy, veterinary medicine qualify. Accountancy, audit, tax consultancy,
real-estate brokerage, professional drivers and similar occupational groups
do not — they are level 0, `high`, unless a separate research signal is
present.
The person-noun requirement is strict: `medicīnas`, `ķirurģijas`,
`psiholoģijas` are field names, not person-nouns, and do not trigger level 2.
Only `ārstu`, `ķirurgu`, `psihologu` and the like do. A field name without a
person-noun falls through to the level 1 rules, where the practice-not-study
test decides.

Two boundary rules:

- **Medicine:** a profession word in the name (`ārstu`, `endokrinologu`,
  `onkologu`) → level 2. A disease or condition word **without** a
  profession word → a patient organization → level 0. If both appear, the
  profession word wins (level 2, `medium`).
- **Subject-teacher associations** (`ķīmijas skolotāju asociācija`):
  level 3. Teaching is an academic profession, but its work is adjacent to
  the discipline rather than research within it.

### Level 3 — the widest circle

Everything in level 2, plus:

- associations whose members are **institutions rather than individuals** —
  the name denotes institutions or a sector: `slimnīcu`, `universitāšu`,
  `muzeju`, `bibliotēku`, `arhīvu` asociācija;
- **think tanks and research institutes** registered as associations or
  foundations (name markers as in the `Nodibinājums` rule);
- **student and early-career researcher societies** — `jauno zinātnieku`,
  `studentu zinātniskā biedrība`. Studentu korporācijas do **not** qualify
  (see *Exclusions*);
- **associations named after an industry-technology discipline** 
(see the industry-discipline rule);
- mixed amateur–researcher societies (the hobby override above) and
  novadpētniecības societies.

When a name carries both a discipline signal and a research-body marker
("Sociālo zinātņu institūts"), the research-body marker wins: the entity is
an institute, whichever discipline it works in. This applies to a `Biedrība`
as well as a `Nodibinājums`.

The person/institution distinction is the level 2 / level 3 boundary:
person-nouns in the name → level 2; institution- or sector-nouns → level 3.

## Exclusions

These apply at every level, subject to the industry-discipline rule below.

| Excluded | Reason |
|---|---|
| Event organizers | Markers `olimpiāde`, `konkurss`, `festivāls`, `konference`, `forums` — run events but unite no researchers, e.g. "Ģeogrāfijas Olimpiāde" |
| Sports federations and clubs | A sports structure regardless of the subject in its name |
| Trade unions (`arodbiedrība`) | Represent members in employment matters, not in science |
| Grant and support funds | Finance research but unite no researchers. The support markers `fonds`, `atbalsta`, `stipendiju`, `piemiņas`, `balvas` apply to any legal form, not only `Nodibinājums` |
| Patient organizations | A disease word without a profession word — unite patients, not medical researchers |
| Hobby and interest groups without a research signal | Collector or amateur clubs with no discipline word |
| Creative and artists' unions | `rakstnieku`, `mākslinieku`, `komponistu`, `dizaineru` savienība or apvienība with no research word — unite practitioners of an art, not researchers |
| School support bodies | `vecāku` or `absolventu` next to a school or institution name — parent or alumni associations |
| School support bodies | `vecāku` or `absolventu` next to a school or institution name — parent or alumni associations |
| Educational institutions and training providers | `skola`, `tautskola`, `kursi`, `mācību centrs`, standalone `akadēmija` — the entity is a school or course provider, not a researcher community |
| Studentu korporācijas | A social structure, not a researcher community |
| Commercial sector bodies | Represent business interests — chambers, employer and trade associations |

**Industry-technology disciplines.** Some field names denote a branch of
industry as much as a science: `biotehnoloģija`, `farmācija`, `enerģētika`,
`informācijas tehnoloģijas`, `telekomunikācijas`, `pārtikas tehnoloģija`
and similar. An association named after such a field is, in Latvia,
typically an association of companies, not of researchers → level 3,
`medium` — present in the widest circle, but never confidently in the
narrowest.

The test: the field names a technology or a production sector — something
companies sell — rather than an object of study. `Biotehnoloģija` names an
industry; `mikoloģija` names a subject.

Three boundaries keep this rule contained:

- A **person-noun** escapes it: "Biotehnologu asociācija" names people, so
  the ordinary level 1/2 rules apply — the person/institution distinction
  already in force decides.
- A **pure-science field** (`ornitoloģija`, `entomoloģija`, `valodniecība`)
  is not an industry: level 1 as before.
- A name with **only a commercial sector and no discipline**
  (`tirdzniecības`, `būvniecības uzņēmēju`) stays excluded: level 0.

**Federācija:** the word itself is a sports-structure signal. If the
subject in the name is a sport or game → level 0, `high`. If the subject is
a scientific discipline, the two signals **conflict** — a "federācija" of a
discipline is as likely a sporting, breeders' or hunters' body as a
research one — so assign level 0, `low` (review queue), never a confident
answer in either direction. If the subject is undecidable → the default
rule.

Names in a foreign language or historical orthography are classified by the
same signals once translated; if the signal is unclear, use the default
rule rather than level 0 `high`.

## Confidence

Alongside the level, each organization receives a confidence value:

- `high` — a single clear lexical signal decided the level.
- `medium` — a signal was present but a boundary rule had to arbitrate
  (e.g. profession word plus disease word, hobby override,
  industry-discipline rule).
  or the name mixes a genuine signal with jocular or informal wording
  ("Fiziķu banda" keeps its discipline level, but not `high`).
- `low` — no signal, or conflicting signals the rules do not resolve.

Lowering rules do not stack. Whatever combination of boundary rules and
contradicting declarations applies, confidence drops at most one step below
what the level signal alone would give.

All `low` results, at every level including 0, form the human review queue.
Low confidence is not an error — it is a flag for review.

## Declared activity area

The activity area recorded in the register is a **supporting signal, not a
criterion**.

Measurement showed that most scientific societies have not declared a
science area at all. Latvijas Mikologu biedrība declared "Izglītība" and
"Vides un dabas aizsardzība"; Latvijas Botāniķu biedrība declared
"Profesionālā biedrība vai nodibinājums"; Latvijas Jauno zinātnieku
apvienība declared "Citur neklasificēta darbības joma". Several scientific
organizations declared nothing.

Use the declared area only to adjust confidence, never the level:

- A declared science area may raise confidence one step, and only from
  `low` to `medium` — never to `high`, since `high` requires a clear signal
  in the name itself, and never establishes a level: "Ģeogrāfijas
  Olimpiāde" declared "Zinātne" and is still an event organizer. **This
  raise applies to levels 1–3 only.** On a level 0 default result (no
  signal in the name) a declared science area changes nothing except the
  reason, which should mention the declaration — such names stay `low` and
  are the first candidates for human review, not the last.
- A declaration that **contradicts** the name signal lowers confidence one
  step. Only three declared areas count as contradictions of a discipline
  name: sports, hobby/leisure activity, and commercial activity
  ("Ornitoloģijas biedrība" declaring "Sports" drops from `high` to
  `medium` — the contradiction hints that the name may not mean the
  academic discipline). Adjacent areas — education, culture, environment,
  professional activity — are **neutral**, not contradictions: measurement
  shows genuine research societies routinely declare exactly these.
- More than five declared areas indicate indiscriminate self-reporting;
  give the declaration no weight.
- An absent declaration is no signal at all.

## Worked examples

Invented names, one per rule, each with its full decision path. These are
illustrations of the procedure, not entries from the register.

| Name (form) | Path | Result |
|---|---|---|
| Nodibinājums "Vidzemes ilgtspējas pētniecības centrs" | Step 0: research-body marker `pētniecības centrs` | 3, `high` |
| Nodibinājums "Profesora A. Kalniņa piemiņas fonds" | Step 0 + step 1: support markers `piemiņas`, `fonds` | 0, `high` |
| Biedrība "Latvijas Entomoloģijas biedrība" | Step 2: discipline word, no override | 1, `high` |
| Biedrība "Latvijas Endokrinologu un cukura diabēta asociācija" | Step 2: profession word beats disease word | 2, `medium` |
| Biedrība "Astronomijas entuziastu klubs" | Step 2: discipline word, hobby markers `entuziastu`, `klubs` → override | 3, `medium` |
| Biedrība "Latvijas Makšķernieku federācija" | Step 1: `federācija` + a sport/hobby subject | 0, `high` |
| Biedrība "Zemgales attīstībai" | No signal at any step → default rule | 0, `low` |
| Biedrība "Latvijas Enerģētikas asociācija" | Step 1: industry-technology field, no person-noun | 3, `medium` |

## Output format

For each organization the classifier returns:

| Field | Values |
|---|---|
| `regcode` | Registration number, echoed back for verification |
| `level` | 0–3 |
| `confidence` | `high`, `medium`, `low` |
| `reason` | One sentence, in English, naming the signal or rule that decided |