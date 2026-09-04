"""Add activity status from annual report filings to the candidate list."""
import pandas as pd

REPORTS = "data/raw/financial_statements.csv"
ORGS = "data/processed/01_active_orgs.csv"
REVIEWED = "output/output_reviewed.xlsx"
DST = "data/processed/07_with_activity.csv"

ACTIVE_FROM = 2023      # a report for 2023 or later counts as active
DORMANT_FROM = 2016     # older than this is long dormant
NEW_FROM = 2024         # registered this recently: no filing deadline yet

reports = pd.read_csv(REPORTS, sep=";", encoding="utf-8",
                      usecols=["legal_entity_registration_number", "source_type",
                               "year", "employees"],
                      dtype={"legal_entity_registration_number": str})
reports = reports.rename(columns={"legal_entity_registration_number": "regcode"})
reports["regcode"] = reports["regcode"].str.strip()

# BNAGP marks association reports up to 2022; after that source_type is empty.
# Filtering on the marker alone silently drops the three most recent years.
bn = reports[reports["source_type"].isin(["BNAGP"]) | reports["source_type"].isna()]

bn = bn.copy()
bn["employees"] = pd.to_numeric(bn["employees"], errors="coerce")

# employees from the most recent filing, not the historical maximum
# whole rows, not per-column last: groupby().last() would take employees
# from an older year when the newest filing leaves the field empty
latest_row = (bn.sort_values("year")
              .drop_duplicates("regcode", keep="last")
              .set_index("regcode"))
per_org = pd.DataFrame({
    "pedejais_parskats": latest_row["year"],
    "parskatu_skaits": bn.groupby("regcode")["year"].nunique(),
    "darbinieki": latest_row["employees"],
})

reviewed = pd.read_excel(REVIEWED, sheet_name="Ieraksti", dtype={"Reģ. nr.": str})
# rows emptied during manual review keep their place in the sheet
reviewed = reviewed[reviewed["Reģ. nr."].notna()].copy()
print("rows in sheet:", len(reviewed))
reviewed["regcode"] = reviewed["Reģ. nr."].str.strip()

orgs = pd.read_csv(ORGS, encoding="utf-8", dtype={"regcode": str})
orgs["regcode"] = orgs["regcode"].str.strip()
registered = orgs.set_index("regcode")["registered"]

df = reviewed.join(per_org, on="regcode")
df["registrets"] = df["regcode"].map(registered).str[:4].astype(float)

assert df["registrets"].notna().all(), "candidate missing from the register"


def status(row):
    """Activity from the last filing; absence of data is its own category."""
    year = row["pedejais_parskats"]
    if pd.isna(year):
        if row["registrets"] >= NEW_FROM:
            return "Nesen reģistrēta"
        return "Nav pārskatu datos"
    if year >= ACTIVE_FROM:
        return "Aktīva"
    if year >= DORMANT_FROM:
        return "Pasīva"
    return "Sen neaktīva"


df["aktivitate"] = df.apply(status, axis=1)
df = df.drop(columns="regcode")
df.to_csv(DST, index=False, encoding="utf-8")

print("candidates:", len(df))
print("\nby activity:")
print(df["aktivitate"].value_counts().to_string())
print("\nactivity by class:")
print(pd.crosstab(df["Klase"], df["aktivitate"]).to_string())
print("\nlast report year:")
print(df["pedejais_parskats"].value_counts(dropna=False).sort_index().to_string())
print(f"\nWritten to {DST}")