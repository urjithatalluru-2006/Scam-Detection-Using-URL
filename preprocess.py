
import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
DATASET_CANDIDATES = [
    PROJECT_DIR / "PhiUSIIL_Phishing_URL_Dataset.csv",
    Path.home() / "Downloads" / "phiusiil+phishing+url+dataset" / "PhiUSIIL_Phishing_URL_Dataset.csv",
]
DATASET_PATH = next((path for path in DATASET_CANDIDATES if path.is_file()), None)
if DATASET_PATH is None:
    locations = "\n".join(str(path) for path in DATASET_CANDIDATES)
    raise FileNotFoundError(f"PhiUSIIL dataset not found. Checked:\n{locations}")

# 1. Load dataset
df = pd.read_csv(DATASET_PATH)

print("Original shape:", df.shape)
print("\nColumns:")
print(df.columns.tolist())

# 2. Clean column names
df.columns = df.columns.str.strip()

# 3. Remove completely empty rows and columns
df = df.dropna(how="all")
df = df.dropna(axis=1, how="all")

# 4. Remove duplicate rows
df = df.drop_duplicates()

# 5. Remove duplicate URLs
if "URL" in df.columns:
    df["URL"] = df["URL"].astype("string").str.strip()

    df = df[
        df["URL"].notna()
        & (df["URL"] != "")
    ]

    df = df.drop_duplicates(subset=["URL"])

# 6. Remove filename column
if "FILENAME" in df.columns:
    df = df.drop(columns=["FILENAME"])

# 7. Check target column
if "label" not in df.columns:
    raise ValueError(
        "Label column not found. Check the dataset columns."
    )

# PhiUSIIL labels:
# 0 = Phishing
# 1 = Legitimate

df["label"] = pd.to_numeric(df["label"], errors="coerce")

# Remove rows with missing or invalid labels
df = df[df["label"].isin([0, 1])].copy()
df["label"] = df["label"].astype(int)

# 8. Convert numeric-looking columns to numeric
for col in df.columns:
    if col not in ["URL", "Domain", "TLD", "label"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# 9. Replace infinite values with missing values
numeric_cols = df.select_dtypes(include=np.number).columns

df[numeric_cols] = df[numeric_cols].replace(
    [np.inf, -np.inf], np.nan
)

# 10. Remove completely empty feature columns
empty_cols = [
    col for col in df.columns
    if col != "label" and df[col].isna().all()
]

df = df.drop(columns=empty_cols)

# 11. Report missing values
print("\nMissing values:")
print(df.isnull().sum()[df.isnull().sum() > 0])

# Keep remaining missing feature values for imputation
# inside the training pipeline, after train/test splitting.

# 12. Save preprocessed dataset
OUTPUT_PATH = PROJECT_DIR / "cleaned_dataset.csv"
df.to_csv(OUTPUT_PATH, index=False)

print("\nPreprocessing completed!")
print("Final shape:", df.shape)
print("Removed empty columns:", empty_cols)

print("\nClass distribution:")
print(df["label"].value_counts())

print("\nLabel meaning:")
print("0 = Phishing")
print("1 = Legitimate")

print(f"\nSaved as {OUTPUT_PATH}")