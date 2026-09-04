"""Sanity checks on the classification output file."""
import json
import pandas as pd

PATH = "data/processed/03_classified.jsonl"
SRC = "data/processed/01_active_orgs.csv"

rows = []
with open(PATH, encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"line {i}: not valid JSON")

df = pd.DataFrame(rows)
df["regcode"] = df["regcode"].astype(str)

print(f"rows: {len(df)}")
print(f"unique regcodes: {df['regcode'].nunique()}")
print(f"duplicates: {len(df) - df['regcode'].nunique()}")

expected = {"regcode", "level", "confidence", "reason", "name"}
print(f"missing fields: {expected - set(df.columns) or 'none'}")
print(f"empty reasons: {(df['reason'].fillna('').str.strip().str.len() == 0).sum()}")
extra = set(df.columns) - expected
print(f"unexpected fields: {extra or 'none'}")

bad_levels = (~df["level"].isin([0, 1, 2, 3])).sum()
print(f"invalid level values: {bad_levels}")

orgs = pd.read_csv(SRC, encoding="utf-8", dtype={"regcode": str})
unknown = set(df["regcode"]) - set(orgs["regcode"])
print(f"regcodes not in the register: {len(unknown)}")
if unknown:
    print(list(unknown)[:5])

missing = set(orgs["regcode"]) - set(df["regcode"])
print(f"not yet classified: {len(missing)}")