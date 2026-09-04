"""Load the full register, keep active associations and foundations."""
import pandas as pd

SRC = "data/raw/register.csv"
DST = "data/processed/01_active_orgs.csv"

TYPES = ["Biedrība", "Nodibinājums", "Sabiedriskā organizācija"]

df = pd.read_csv(SRC, sep=";", encoding="utf-8",
                 usecols=["regcode", "name", "type_text",
                          "registered", "terminated", "closed", "address"],
                 dtype={"regcode": str})

df["closed"] = df["closed"].str.strip().replace("", pd.NA)

print("total rows:", len(df))

df = df[df["type_text"].isin(TYPES)]
print("after type filter:", len(df))
print(df["type_text"].value_counts())

active = df[df["terminated"].isna()]
print("active:", len(active))
print(active["type_text"].value_counts())

active.to_csv(DST, index=False, encoding="utf-8")