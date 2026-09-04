"""Run the anchor test set against the classification criteria."""
import json
import os
import time
from collections import Counter

import pandas as pd
import requests
from dotenv import load_dotenv

CRITERIA = "criteria.md"
ANCHORS = "tests/anchors.csv"
MODEL = "openai/gpt-oss-120b"
BATCH_SIZE = 20

# Order-dependent rows are run three times; models fail these inconsistently.
REPEAT_IDS = ["N03", "N05", "P10", "P19", "R02"]
REPEATS = 3

RANK = {"low": 0, "medium": 1, "high": 2}

INSTRUCTION = """You classify Latvian registered organizations against the criteria below.

Classify every organization in the input. Return a JSON array only - no
prose, no markdown fences. One object per input organization, in the same
order, each with exactly these keys: regcode, level, confidence, reason.

Apply the decision order stated in the criteria. The first rule that fires
decides. State in the reason which rule or signal decided.

Echo regcode back exactly as given. Never omit an organization.

--- CRITERIA ---
"""

load_dotenv()
KEY = os.environ["OPENROUTER_API_KEY"]


def classify(batch, criteria, attempts=3):
    """Send one batch to the model; on a broken response, save it and retry."""
    payload = [
        {"regcode": r["id"], "name": r["name"],
         "type_text": r["type_text"], "declared_areas": r["declared_areas"]}
        for r in batch
    ]
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {KEY}"},
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": INSTRUCTION + criteria},
                        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                    ],
                    "temperature": 0,
                },
                timeout=300,
            )
            response.raise_for_status()
            raw = response.json()["choices"][0]["message"]["content"].strip()
            raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            return {str(r["regcode"]): r for r in json.loads(raw)}
        except requests.RequestException as e:
            last_error = e
            print(f"    attempt {attempt}: {type(e).__name__}")
        except json.JSONDecodeError as e:
            last_error = e
            path = f"data/processed/debug_raw_{batch[0]['id']}_{attempt}.txt"
            with open(path, "w", encoding="utf-8") as f:
                f.write(raw)
            print(f"    attempt {attempt}: broken JSON at char {e.pos}, raw saved to {path}")
        time.sleep(3 * attempt)
    raise last_error


def run_all(rows, criteria):
    """Classify every row, in batches."""
    out = {}
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        print(f"  batch {i // BATCH_SIZE + 1}: {len(batch)} rows")
        out.update(classify(batch, criteria))
    return out


def level_ok(row, got):
    """Level must match exactly, or be one of the accepted alternatives."""
    accepted = str(row["accept_levels"]).split("|")
    return str(got) in accepted


def confidence_ok(row, got):
    """Strict match where the confidence is what is under test, else one step."""
    expected = row["expected_confidence"]
    if str(row["strict_confidence"]).lower() == "yes":
        return got == expected
    return abs(RANK.get(got, -9) - RANK.get(expected, 9)) <= 1


with open(CRITERIA, encoding="utf-8") as f:
    criteria = f.read()

anchors = pd.read_csv(ANCHORS, dtype=str).fillna("")
rows = anchors.to_dict("records")

print(f"Running {len(rows)} anchors")
results = run_all(rows, criteria)

failures = []
for row in rows:
    got = results.get(row["id"])
    if got is None:
        failures.append((row, None, "missing from response"))
        continue
    problems = []
    if not level_ok(row, got["level"]):
        problems.append(f"level {got['level']} != {row['expected_level']}")
    if not confidence_ok(row, got["confidence"]):
        strict = "strict" if row["strict_confidence"].lower() == "yes" else "tolerant"
        problems.append(f"confidence {got['confidence']} != {row['expected_confidence']} ({strict})")
    status = "FAIL" if problems else "PASS"
    print(f"{status}  {row['id']:<4} level={got['level']} {got['confidence']:<7} {row['name'][:45]}")
    if problems:
        failures.append((row, got, "; ".join(problems)))

# Order-dependent rows: level must agree 3/3, confidence at least 2/3.
print(f"\nConsistency check: {len(REPEAT_IDS)} rows x {REPEATS} runs")
repeat_rows = [r for r in rows if r["id"] in REPEAT_IDS]
runs = [results] + [run_all(repeat_rows, criteria) for _ in range(REPEATS - 1)]

unstable = []
for row in repeat_rows:
    levels = [str(run[row["id"]]["level"]) for run in runs if row["id"] in run]
    confs = [run[row["id"]]["confidence"] for run in runs if row["id"] in run]
    level_agree = len(set(levels)) == 1
    conf_agree = Counter(confs).most_common(1)[0][1] >= 2
    status = "PASS" if level_agree and conf_agree else "UNSTABLE"
    print(f"{status:<9} {row['id']:<4} levels={levels} confidence={confs}")
    if not (level_agree and conf_agree):
        unstable.append(row["id"])

print(f"\n{len(rows) - len(failures)}/{len(rows)} passed")

if failures:
    print("\nFailures:")
    for row, got, problem in failures:
        print(f"\n{row['id']}  {row['name']}")
        print(f"  rule:    {row['rule_under_test']}")
        print(f"  problem: {problem}")
        if got:
            print(f"  reason:  {got['reason']}")

if unstable:
    print(f"\nUnstable across runs: {', '.join(unstable)}")
    print("A level split means the decision order is not binding in the prompt.")

print("\nRead the reasons of passing rows too: a correct level with the wrong "
      "rule cited is a failure the harness cannot detect.")