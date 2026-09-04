"""Classify active organizations against the inclusion criteria."""
import argparse
import json
import os
import time

import pandas as pd
import requests
from dotenv import load_dotenv

CRITERIA = "criteria.md"
SRC = "data/processed/01_active_orgs.csv"
AREAS = "data/raw/areas_of_activity_of_associations_foundations.csv"
DST = "data/processed/03_classified.jsonl"
UNRESOLVED = "data/processed/unresolved.txt"

MODEL = "openai/gpt-oss-120b"
MAX_ATTEMPTS = 3

VALID_LEVELS = {0, 1, 2, 3}
VALID_CONFIDENCE = {"high", "medium", "low"}

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


def load_done(path):
    """Return regcodes already classified in a previous run."""
    if not os.path.exists(path):
        return set()
    done = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                # str() so a code once written as a number still matches on resume
                done.add(str(json.loads(line)["regcode"]))
    return done


def build_input(limit):
    """Load active organizations joined with their declared activity areas."""
    orgs = pd.read_csv(SRC, encoding="utf-8", dtype={"regcode": str})
    areas = pd.read_csv(AREAS, sep=";", encoding="utf-8", dtype=str)

    grouped = (areas[areas["area_of_activity"].notna()]
               .groupby("regcode")["area_of_activity"]
               .apply(lambda s: " | ".join(sorted(set(s))))
               .reset_index()
               .rename(columns={"area_of_activity": "declared_areas"}))

    df = orgs.merge(grouped, on="regcode", how="left").fillna({"declared_areas": ""})
    df = df[["regcode", "name", "type_text", "declared_areas"]]
    return df.head(limit).to_dict("records") if limit else df.to_dict("records")


def call_model(batch, criteria):
    """Send one batch and return the parsed results keyed by regcode (as str)."""
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {KEY}"},
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": INSTRUCTION + criteria},
                {"role": "user", "content": json.dumps(batch, ensure_ascii=False)},
            ],
            "temperature": 0,
        },
        timeout=300,
    )
    response.raise_for_status()
    payload = response.json()
    content = payload.get("choices", [{}])[0].get("message", {}).get("content")
    if not content:
        raise ValueError(f"empty content from API: {json.dumps(payload)[:400]}")
    raw = content.strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    # str() because the model may return a numeric regcode without quotes;
    # json.loads then yields an int, which would never match the sent codes
    try:
        return {str(r["regcode"]): r for r in json.loads(raw)}
    except json.JSONDecodeError:
        path = f"data/processed/debug_raw_{batch[0]['regcode']}.txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write(raw)
        print(f"    broken JSON, raw saved to {path}")
        raise


def valid_result(result):
    """A result counts only if all four fields are present and legal."""
    if not {"regcode", "level", "confidence", "reason"} <= set(result):
        return False
    try:
        level = int(result.get("level"))
    except (TypeError, ValueError):
        return False
    return (level in VALID_LEVELS
            and result.get("confidence") in VALID_CONFIDENCE
            and bool(str(result.get("reason", "")).strip()))


def classify_batch(batch, criteria):
    """Call the model, retrying failures and missing codes.

    Accumulates results across attempts: codes answered on attempt 1 are
    kept even when attempt 2 only returns the stragglers.
    Returns (results_by_regcode, unresolved_codes).
    """
    sent = {r["regcode"] for r in batch}
    collected = {}
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            got = call_model(batch, criteria)
        except (requests.RequestException, ValueError, KeyError,
                IndexError, TypeError, AttributeError) as e:
            print(f"    attempt {attempt} failed: {type(e).__name__}: {e}")
            time.sleep(5 * attempt)
            continue
        # Keep only codes we actually sent; a hallucinated code is not a result.
        # Drop malformed results too, so they get retried like missing ones.
        for code, result in got.items():
            if code in sent and valid_result(result):
                collected[code] = result
        missing = sent - set(collected)
        if not missing:
            return collected, set()
        print(f"    attempt {attempt}: {len(missing)} missing or invalid, retrying those")
        batch = [r for r in batch if r["regcode"] in missing]
    return collected, sent - set(collected)


parser = argparse.ArgumentParser()
parser.add_argument("--limit", type=int, help="classify only the first N organizations")
parser.add_argument("--batch-size", type=int, default=35,
                    help="rows per API call; rerun stuck remainders with "
                         "--batch-size 1 to isolate a poisoned name")
args = parser.parse_args()
BATCH_SIZE = args.batch_size

with open(CRITERIA, encoding="utf-8") as f:
    criteria = f.read()

rows = build_input(args.limit)
done = load_done(DST)
todo = [r for r in rows if r["regcode"] not in done]

print(f"{len(rows)} in scope, {len(done)} already done, {len(todo)} to classify")

unresolved = []
consecutive_failures = 0
names_by_code = {r["regcode"]: r["name"] for r in rows}
with open(DST, "a", encoding="utf-8") as out:
    for i in range(0, len(todo), BATCH_SIZE):
        batch = todo[i:i + BATCH_SIZE]
        n = i // BATCH_SIZE + 1
        total = (len(todo) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"  batch {n}/{total} ({len(batch)} rows)")

        results, missing = classify_batch(batch, criteria)
        for code, result in results.items():
            result["regcode"] = code            # normalized string form
            result["level"] = int(result["level"])
            result["name"] = names_by_code[code]
            out.write(json.dumps(result, ensure_ascii=False) + "\n")
        out.flush()  # checkpoint: an interrupted run keeps everything so far

        if missing:
            unresolved.extend(missing)
            print(f"    unresolved: {len(missing)}")

        # A whole batch failing repeatedly is a persistent fault, not bad luck.
        if not results:
            consecutive_failures += 1
            if consecutive_failures >= 3:
                print("3 batches failed in a row - persistent API failure "
                      "(credits? outage?). Stopping; rerun to resume.")
                break
        else:
            consecutive_failures = 0

# Persist the current stuck set (overwritten each run, so a set that does
# not shrink between runs is visible even after the terminal is gone).
with open(UNRESOLVED, "w", encoding="utf-8") as f:
    for code in unresolved:
        f.write(f"{code}\t{names_by_code.get(code, '?')}\n")

print(f"\nWritten to {DST}")
if unresolved:
    print(f"{len(unresolved)} organizations unresolved (see {UNRESOLVED}); "
          f"rerun to retry them, with --batch-size 1 if the set stops shrinking")

df = pd.read_json(DST, lines=True)
print(f"\nclassified: {len(df)}")
print("\nby level:")
print(df["level"].value_counts().sort_index().to_string())
print("\nby level and confidence:")
print(pd.crosstab(df["level"], df["confidence"]).to_string())
print(f"\nreview queue (confidence=low): {(df['confidence'] == 'low').sum()}")