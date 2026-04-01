from pathlib import Path
from datasets import load_dataset

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

def main():
    ds = load_dataset("AkashPS11/recipes_data_food.com", split="train")
    out_path = RAW_DIR / "recipes_foodcom_raw.parquet"
    ds.to_parquet(str(out_path))
    print(f"Saved to {out_path}")

if __name__ == "__main__":
    main()