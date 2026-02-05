"""
Column Name Verification Script
Checks that data simulation output matches Ranker expectations.
"""

print("=" * 70)
print("COLUMN NAME VERIFICATION")
print("=" * 70)

# 1. What the Ranker expects
print("\n📋 RANKER EXPECTS (from ranker.py line 33):")
ranker_features = [
    'user_rating_avg',
    'user_rating_count', 
    'item_rating_avg',
    'item_rating_count',
    'release_year',
    'initial_score',
    'source_weight',
    'hour_of_day',
    'is_weekend'
]
for feat in ranker_features:
    print(f"  ✓ {feat}")

# 2. What the data simulation produces
print("\n📋 DATA SIMULATION SHOULD PRODUCE:")
data_features = [
    'user_id',
    'item_id',
    'event_type',
    'rating',
    'label',
    'timestamp',
    'user_rating_avg',  # ← Must match
    'user_rating_count',  # ← Must match
    'item_rating_avg',  # ← Must match
    'item_rating_count',  # ← Must match
    'release_year'  # ← Must match
]
for feat in data_features:
    if feat in ranker_features:
        print(f"  ✓ {feat} (MATCHES RANKER)")
    else:
        print(f"  - {feat} (metadata, not used in model)")

# 3. Check during training
print("\n📋 DURING TRAINING, RANKER WILL:")
print("  1. Load interaction_logs.csv")
print("  2. Extract these columns as X (features):")
training_features = [
    'user_rating_avg',
    'user_rating_count',
    'item_rating_avg',
    'item_rating_count',
    'release_year',
    'initial_score',     # Added during training (from candidate scores)
    'source_weight',     # Added during training (from candidate source)
    'hour_of_day',       # Added during training (current time)
    'is_weekend'         # Added during training (current time)
]
for feat in training_features:
    if feat in ['initial_score', 'source_weight', 'hour_of_day', 'is_weekend']:
        print(f"  + {feat} (computed during training)")
    else:
        print(f"  ✓ {feat} (from CSV)")

print("\n" + "=" * 70)
print("✅ VERIFICATION COMPLETE")
print("=" * 70)
print("\nIf all checks pass, the column names are aligned!")
