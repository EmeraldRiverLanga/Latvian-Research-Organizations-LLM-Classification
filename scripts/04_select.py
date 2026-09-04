"""Build the candidate list and the review queue from classified records."""
import pandas as pd

CLASSIFIED = "data/processed/03_classified.jsonl"
ORGS = "data/processed/01_active_orgs.csv"
AREAS = "data/raw/areas_of_activity_of_associations_foundations.csv"

CANDIDATES = "data/processed/04_candidates.csv"
REVIEW = "data/processed/04_review_queue.csv"

# Narrow science areas only. "Izglītība" and similar are too broad to act
# as a signal: most of the register declares them.
SCIENCE_AREAS = [
    "Zinātne",
    "Zinātne un tehnoloģijas",
    "Medicīniskā pētniecība",
    "Sociālās zinātnes, socioloģiskā un politikas pētniecība",
    "Vēsture un humanitārās zinātnes",
]

df = pd.read_json(CLASSIFIED, lines=True, dtype={"regcode": str})
df = df[["regcode", "name", "level", "confidence", "reason"]]

orgs = pd.read_csv(ORGS, encoding="utf-8", dtype={"regcode": str})
orgs = orgs[["regcode", "type_text", "registered", "address"]]

areas = pd.read_csv(AREAS, sep=";", encoding="utf-8", dtype=str)
areas = areas[areas["area_of_activity"].notna()]

# The area names must match the register verbatim; a typo would silently
# empty the science group instead of failing.
missing = [a for a in SCIENCE_AREAS if a not in set(areas["area_of_activity"])]
if missing:
    raise SystemExit(f"SCIENCE_AREAS not found verbatim in the register: {missing}")

declared = (areas.groupby("regcode")["area_of_activity"]
            .apply(lambda s: " | ".join(sorted(set(s))))
            .reset_index()
            .rename(columns={"area_of_activity": "declared_areas"}))

science_codes = set(areas[areas["area_of_activity"].isin(SCIENCE_AREAS)]["regcode"])

df = df.merge(orgs, on="regcode", how="left").merge(declared, on="regcode", how="left")
df["declared_areas"] = df["declared_areas"].fillna("")

# --- Candidate list: everything the classifier placed in a circle ---------

candidates = df[df["level"].between(1, 3)].copy()
assert not candidates["type_text"].isna().any(), "candidate missing from the register"
candidates = candidates.sort_values(["level", "name"])
candidates.to_csv(CANDIDATES, index=False, encoding="utf-8")

print(f"candidates (level 1-3): {len(candidates)}")
print(candidates["level"].value_counts().sort_index().to_string())

# --- Review queue: four groups, each for a different reason ---------------
#
# The queue catches known kinds of contradiction, not all of them. A `0 low`
# record whose name does carry a discipline word the model failed to see
# stays in the background: detecting it would need a list of disciplines,
# which the project deliberately does not have. Same boundary as the manual
# review of level 1.
#
# The first group overlaps the candidate list by design: a candidate with an
# unresolved signal belongs in both files.

groups = []

# Positive level with an unresolved signal.
g = df[(df["level"].between(1, 3)) & (df["confidence"] == "low")].copy()
g["review_group"] = "uncertain placement"
groups.append(g)

# Outside the specification: level 0 admits only high or low.
g = df[(df["level"] == 0) & (df["confidence"] == "medium")].copy()
g["review_group"] = "off-spec combination"
groups.append(g)

# The federation rule sends conflicts to 0/low by design. Detected on the
# name, not on the reason text, which the model words differently each time.
g = df[(df["level"] == 0) & (df["confidence"] == "low")
       & (df["name"].str.contains("federācij", case=False, na=False))].copy()
g["review_group"] = "federation conflict"
groups.append(g)

# The name says nothing, but the organization declared science itself.
g = df[(df["level"] == 0) & (df["confidence"] == "low")
       & (df["regcode"].isin(science_codes))].copy()
g["review_group"] = "no name signal, science declared"
groups.append(g)

review = pd.concat(groups).drop_duplicates(subset="regcode", keep="first")
review = review.sort_values(["review_group", "name"])
review.to_csv(REVIEW, index=False, encoding="utf-8")

print(f"\nreview queue: {len(review)}")
print(review["review_group"].value_counts().to_string())

print(f"\nWritten to {CANDIDATES} and {REVIEW}")