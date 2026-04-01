import os
from pathlib import Path
import pandas as pd
import kagglehub
from kagglehub import KaggleDatasetAdapter

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# First, inspect the dataset manually on Kaggle to find the actual file name inside it.
# Put that file name here after checking. Example: "healthy_indian_recipes.csv"
FILE_PATH = "healthy_indian_recipes.csv"

df = kagglehub.load_dataset(
    KaggleDatasetAdapter.PANDAS,
    "bhavyadhingra00020/healthy-indian-recipes",
    FILE_PATH,
)

print("Columns:")
print(df.columns.tolist())
print("\nFirst 5 rows:")
print(df.head())

output_path = RAW_DIR / "healthy_indian_recipes_raw.csv"
df.to_csv(output_path, index=False, encoding="utf-8")
print(f"\nSaved raw file to: {output_path}")