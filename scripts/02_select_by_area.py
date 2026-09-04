"""Pick organizations by declared activity area in the register."""
import pandas as pd

ORGS = "data/processed/01_active_orgs.csv"
AREAS = "data/raw/areas_of_activity_of_associations_foundations.csv"
DST = "data/processed/02_selection_a.csv"

SCIENCE_AREAS = [
    "Zinātne",
    "Zinātne un tehnoloģijas",
    "Medicīniskā pētniecība",
    "Sociālās zinātnes, socioloģiskā un politikas pētniecība",
    "Vēsture un humanitārās zinātnes",
]

orgs = pd.read_csv(ORGS, encoding="utf-8", dtype={"regcode": str})
areas = pd.read_csv(AREAS, sep=";", encoding="utf-8", dtype=str)

# coverage check: how many active orgs have any declared area
with_area = areas[areas["area_of_activity"].notna()]["regcode"].nunique()
print("active orgs:", len(orgs))
print("orgs with at least one declared area:", with_area)
print()

# collapse multiple areas per org into one row
grouped = (areas[areas["area_of_activity"].notna()]
           .groupby("regcode")["area_of_activity"]
           .apply(lambda s: " | ".join(sorted(set(s))))
           .reset_index()
           .rename(columns={"area_of_activity": "areas"}))

selected = areas[areas["area_of_activity"].isin(SCIENCE_AREAS)]["regcode"].unique()
print("unique regcodes in science areas:", len(selected))

result = orgs[orgs["regcode"].isin(selected)].merge(grouped, on="regcode", how="left")
print("after keeping only active orgs:", len(result))

result.to_csv(DST, index=False, encoding="utf-8")
print(result[["name", "areas"]].head(20).to_string())