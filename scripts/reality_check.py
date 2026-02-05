"""
Reality Check: What's actually happening with the model?
"""
import pandas as pd
import joblib
import os

print("=" * 70)
print("MODEL PERFORMANCE REALITY CHECK")
print("=" * 70)

# 1. Check data
df = pd.read_csv('data/processed/interaction_logs.csv')
print(f"\n📂 DATA:")
print(f"  Total interactions: {len(df):,}")
print(f"  Positive rate: {df['label'].mean():.2%}")

# 2. Check if model has metrics
model_path = "data/models/ranker_model.joblib"
if os.path.exists(model_path):
    ranker = joblib.load(model_path)
    print(f"\n🤖 LOADED MODEL:")
    if hasattr(ranker, 'metrics'):
        print(f"  Test AUC: {ranker.metrics.get('test_auc', 'N/A'):.4f}")
        print(f"  Test LogLoss: {ranker.metrics.get('test_logloss', 'N/A'):.4f}")
        print(f"  Train AUC: {ranker.metrics.get('train_auc', 'N/A'):.4f}")
    else:
        print("  ⚠️  Model has NO metrics attribute!")
        
# 3. Check feature correlations with label
print(f"\n🔗 FEATURE-LABEL CORRELATIONS:")
features = ['user_rating_avg', 'user_rating_count', 'item_rating_avg', 
            'item_rating_count', 'release_year']
for feat in features:
    if feat in df.columns:
        corr = df[feat].corr(df['label'])
        status = "✓" if abs(corr) > 0.1 else "⚠️"
        print(f"  {status} {feat:20s}: {corr:+.4f}")

# 4. Key insight
print(f"\n💡 DIAGNOSIS:")
max_corr = max([abs(df[f].corr(df['label'])) for f in features if f in df.columns])
if max_corr < 0.15:
    print("  ❌ PROBLEM: Features have WEAK correlation with labels!")
    print("     Even with perfect hyperparameters, AUC will be low.")
    print("     Root cause: Data simulation creates random-looking patterns.")
else:
    print("  ✓ Features show reasonable correlation")

print("\n" + "=" * 70)
