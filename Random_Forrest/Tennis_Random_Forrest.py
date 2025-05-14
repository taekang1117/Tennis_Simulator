import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib

# --- Load dataset ---
df = pd.read_csv("cleaned_output.csv")

# Define stat and target columns
percent_cols = ['A%', 'DF%', '1stIn', '1st%', '2nd%',
                'Ret_TPW', 'Ret_RPW', 'Ret_vA%', 'Ret_v1st%', 'Ret_v2nd%', 'Ret_BPCnv']
stat_cols = ['DR'] + percent_cols
target_col = 'Total_Games'

# Convert relevant columns to float
for col in stat_cols + [target_col]:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Drop rows with missing target
df.dropna(subset=[target_col], inplace=True)

# Context features already encoded
context_cols = [col for col in df.columns if col.startswith("Surface_") or col.startswith("Rd_")]

# --- Cache player stats ---
player_cache = df.groupby("Player")
opponent_cache = df.groupby("Opponent")

# --- Feature extractor: p1 + p2 + diff + context ---
def extract_features(row, recent_n=5):
    p1 = row['Player']
    p2 = row['Opponent']

    p1_data = player_cache.get_group(p1).tail(recent_n) if p1 in player_cache.groups else None
    if p2 in opponent_cache.groups:
        p2_data = opponent_cache.get_group(p2).tail(recent_n)
    elif p2 in player_cache.groups:
        p2_data = player_cache.get_group(p2).tail(recent_n)
    else:
        p2_data = None

    if p1_data is None or p2_data is None:
        return None

    p1_stats = p1_data[stat_cols].mean(numeric_only=True)
    p2_stats = p2_data[stat_cols].mean(numeric_only=True)

    common = p1_stats.index.intersection(p2_stats.index)
    if len(common) < 5:
        return None

    diff = p1_stats[common] - p2_stats[common]
    diff.index = [f"{col}_diff" for col in common]

    # Add original stats
    p1_stats.index = [f"{col}_p1" for col in p1_stats.index]
    p2_stats.index = [f"{col}_p2" for col in p2_stats.index]

    # Add match context
    context = row[context_cols]

    return pd.concat([p1_stats, p2_stats, diff, context])

# --- Build feature matrix ---
X_list, y_list = [], []
skipped = 0

for idx, row in df.iterrows():
    features = extract_features(row)
    if features is None or features.isnull().sum() > 5:
        skipped += 1
        continue
    X_list.append(features)
    y_list.append(row[target_col])

print(f"\n Dataset built: {len(X_list)} used, {skipped} skipped")

# Convert to DataFrame and fill missing values with mean
X = pd.DataFrame(X_list)
X = X.fillna(X.mean())  # More realistic than zero-filling
y = pd.Series(y_list)

# --- Train/test split ---
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# --- Train model ---
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# --- Evaluate ---
y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print("\n Model Evaluation:")
print(f"  - Mean Squared Error: {mse:.2f}")
print(f"  - R² Score: {r2:.3f}")

# --- Save model ---
joblib.dump(model, "total_games_rf_model.pkl")
print("\n Model saved as: total_games_rf_model.pkl")
