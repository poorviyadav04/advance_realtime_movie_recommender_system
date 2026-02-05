import pandas as pd

# Check the data file
df = pd.read_csv('data/processed/interaction_logs.csv')

print("=" * 70)
print("DATA FILE CHECK")
print("=" * 70)
print(f"\nTotal interactions: {len(df):,}")
print(f"Positive rate: {df['label'].mean():.2%}")
print(f"\nColumns: {df.columns.tolist()}")
print(f"\nFirst 3 rows:")
print(df.head(3))
