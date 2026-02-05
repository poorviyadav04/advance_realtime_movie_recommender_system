"""
Deep diagnostic for model performance issues.
"""
import pandas as pd
import numpy as np

print("=" * 70)
print("COMPREHENSIVE MODEL DIAGNOSTIC")
print("=" * 70)

# 1. Check the interaction logs
print("\n📂 CHECKING INTERACTION LOGS...")
df = pd.read_csv('data/processed/interaction_logs.csv')
print(f"Total records: {len(df):,}")
print(f"\nColumns: {df.columns.tolist()}")

# 2. Feature presence
print("\n🔍 FEATURE VERIFICATION:")
required_features = ['user_avg_rating', 'user_rating_count', 'item_avg_rating', 
                     'item_rating_count', 'release_year']
for feat in required_features:
    if feat in df.columns:
        print(f"  ✓ {feat}: present")
        print(f"    - Mean: {df[feat].mean():.3f}, Std: {df[feat].std():.3f}")
        print(f"    - Range: [{df[feat].min():.1f}, {df[feat].max():.1f}]")
    else:
        print(f"  ✗ {feat}: MISSING!")

# 3. Label distribution
print("\n📊 LABEL DISTRIBUTION:")
print(df['label'].value_counts())
positive_rate = df['label'].mean()
print(f"Positive rate: {positive_rate:.2%}")

# 4. Feature correlation with label
print("\n🔗 FEATURE-LABEL CORRELATIONS:")
for feat in required_features:
    if feat in df.columns:
        corr = df[feat].corr(df['label'])
        print(f"  {feat:20s}: {corr:+.4f}")

# 5. Check for constant features
print("\n⚠️  CONSTANT FEATURES CHECK:")
for feat in required_features:
    if feat in df.columns:
        unique_vals = df[feat].nunique()
        if unique_vals < 5:
            print(f"  WARNING: {feat} has only {unique_vals} unique values!")

# 6. Sample data
print("\n📝 SAMPLE DATA (first 5 rows):")
cols_to_show = ['user_id', 'item_id', 'label'] + [f for f in required_features if f in df.columns]
print(df[cols_to_show].head())

# 7. Check what features the Ranker is configured to use
print("\n🤖 RANKER CONFIGURATION:")
try:
    import sys
    sys.path.insert(0, '.')
    from models.ranker import Ranker
    ranker = Ranker()
    print(f"Ranker expects these features: {ranker.features}")
    
    # Check if all expected features exist in data
    missing = set(ranker.features) - set(df.columns)
    if missing:
        print(f"\n❌ PROBLEM FOUND: Ranker expects features that don't exist in data:")
        print(f"   Missing: {missing}")
    else:
        print("\n✅ All ranker features present in data")
except Exception as e:
    print(f"Error loading Ranker: {e}")

print("\n" + "=" * 70)
