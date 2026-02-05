"""Check data quality for debugging model performance."""
import pandas as pd

# Load interaction logs
df = pd.read_csv('data/processed/interaction_logs.csv')

print("=" * 60)
print("DATA QUALITY REPORT")
print("=" * 60)

print(f"\nTotal interactions: {len(df):,}")

print("\n📊 LABEL DISTRIBUTION:")
print(df['label'].value_counts())
positive_rate = df['label'].mean()
print(f"\nPositive rate: {positive_rate:.2%}")

if positive_rate < 0.1 or positive_rate > 0.9:
    print("⚠️  WARNING: Severely imbalanced labels!")
elif positive_rate < 0.2 or positive_rate > 0.8:
    print("⚠️  Moderate label imbalance")
else:
    print("✅ Reasonable label balance")

print("\n📈 FEATURE STATISTICS:")
feature_cols = ['user_avg_rating', 'user_rating_count', 'item_avg_rating', 
                'item_rating_count', 'release_year']
for col in feature_cols:
    if col in df.columns:
        print(f"{col}: mean={df[col].mean():.3f}, std={df[col].std():.3f}")

print("\n🔍 SAMPLE ROWS:")
print(df.head(10))
