# Anchor Test Plan

## Purpose

Verify that the classifier applies `criteria.md` as
written, before the full run of 27,499 names. The anchors measure rule
application, not general ability: every row in `tests/anchors.csv` maps
to a named rule, and a failure points at either the spec or the prompt,
never vaguely at "the model".

## Ground rules

- **The anchors never enter the classifier prompt.** The spec's worked
  examples use different, invented names for exactly this reason. If an
  anchor leaks into the prompt, replace it — a memorized anchor measures
  copying, not generalization.
- The classifier receives only the input columns: `name`, `type_text`,
  `declared_areas` (pipe-separated). The expected columns are the answer
  key and stay in the harness.
- Real organization names are used where a real one exists for the rule;
  invented names fill the rest. An invented name failing is as meaningful
  as a real one — the classifier cannot tell them apart.

## Structure

| Series | Count | What it measures |
|---|---|---|
| A01–A07 | 7 | Canonical cases — must be boringly correct; any failure is a prompt/setup defect |
| R01–R05 | 5 | Regressions from test round 1, with expectations updated to the current criteria |
| N01–N07 | 7 | The `Nodibinājums` rules — step 0, marker priority, decision order |
| P01–P20 | 20 | Provocations — boundaries, order dependencies, and the later fixes |

## Pass criteria

- **Level: exact match required** for every row except P05, which accepts
  1 or 2 (the discipline/profession boundary is genuinely arguable there;
  0 is a failure).
- **Confidence: one-step tolerance** by default, **strict match** where
  `strict_confidence = yes` — those are the rows where the confidence value
  *is* the thing under test (conflict cases, the review-queue rules, the
  contradiction rule).
- **Reason: must name the rule or signal.** A correct level with a reason
  citing the wrong rule counts as a failure — at 27k names the reasons are
  the only way to audit the run.

## Consistency protocol

Order-dependent rules are where models fail *inconsistently*, so a single
pass is not enough for them. Run these five rows **three times each**:
N03, N05, P10, P19, R02.

- Level must agree 3/3. A 2/3 level split on an order test means the
  decision order is not binding in the prompt — fix the prompt, not the
  spec.
- Confidence must agree at least 2/3.

## Cases worth reading before judging the output

- **N04 (Providus).** A real think tank that the spec *knowingly* sends to
  the review queue because its name carries no marker. `0, low` is the
  correct answer and the accepted cost of a name-only classifier. If this
  outcome is unacceptable, the fix is a whitelist outside the classifier,
  not a looser rule.
- **P13 vs P12.** The korporācija exclusion fires only when the word is in
  the name; a bare fraternity name ("Selonija") is indistinguishable from
  any other proper name and lands in the review queue. Both paths keep it
  out of the contact list, which is what matters.
- **P15.** The name carries both a discipline signal (`Social Sciences`)
  and a research-body marker (`Institute`). The criteria now state that the
  marker wins, so the expected answer is level 3. Before that rule existed
  this row was undecidable — it is the row that exposed the gap.
- **P17.** A science declaration on a no-signal name must not
  raise confidence, or the most review-worthy names would silently leave
  the review queue. If this row fails, the model is applying the old raise
  rule too broadly.
- **P19 (Astronomijas tautskola).** The education-provider exclusion beats
  the discipline word by decision order, giving `0, high`. This is a
  deliberate call — a folk school *about* astronomy is a course provider,
  not a researcher society. If the project owner disagrees, the time to
  say so is now.
- **P18 / P20 pair.** The contradiction rule must fire on a sports
  declaration and must not fire on a cultural one. If both land at
  `medium`, the model reads "contradiction" broader than the enumerated
  list — tighten the prompt.

## Stopping rule

The purpose of this run is to decide whether to classify all 27,499 names,
not to produce a further revision of the criteria.

- **Canonical (A) failures block the run.** They mean the prompt does not
  transmit the criteria, and no result from the full run would be trusted.
- **A failure pattern that spans a class of names blocks the run** — the
  kind found in round 1, where informal names were all confidently
  misclassified. Systematic errors are invisible at scale.
- **Isolated borderline failures do not block the run.** Two or three rows
  disagreeing on a genuinely arguable case is the expected noise level of a
  name-only classifier. Record them and proceed.

A longer specification is not automatically a better one: each added rule is
another place to misapply. If a revision does not remove a failure class, it
is not worth making.

## Known untested rule

The confidence raise (a declared science area lifting `low` to `medium` at
levels 1–3) has no anchor, because a positive level almost always arrives
either from a clear lexical signal (`high`) or from an arbitrated boundary
(`medium`). If the full run produces no case where the raise fires, the rule
should be deleted rather than tested — an unreachable rule is only a place
for the classifier to go wrong.

## What a failure means

| Failure pattern | Likely cause | Fix target |
|---|---|---|
| A-series row fails | Prompt does not transmit the spec faithfully | Prompt |
| R-series row fails | A v3.1 fix did not take effect | Prompt or spec wording |
| Level split across repeat runs | Decision order not binding | Prompt (state the order imperatively) |
| Many `strict_confidence` rows off by one | Confidence definitions too abstract | Spec: add one example per confidence value |
| Reasons cite the right level, wrong rule | Model pattern-matches outcomes, skips the procedure | Prompt: require the decision path in the reason |