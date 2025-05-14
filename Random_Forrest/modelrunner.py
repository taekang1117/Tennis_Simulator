import pandas as pd
import joblib
import numpy as np
import os

# --- Load match history once ---
df = pd.read_csv("cleaned_output.csv")

# --- Stats used during training ---
percent_cols = ['A%', 'DF%', '1stIn', '1st%', '2nd%',
                'Ret_TPW', 'Ret_RPW', 'Ret_vA%', 'Ret_v1st%', 'Ret_v2nd%', 'Ret_BPCnv']
stat_cols = ['DR'] + percent_cols
context_cols = [col for col in df.columns if col.startswith("Surface_") or col.startswith("Rd_")]

# --- Create player caches ---
player_cache = df.groupby("Player")
opponent_cache = df.groupby("Opponent")

# --- Predict from any saved model ---
def predict_from_model(player1, player2, surface, round_, line):
    model_file = f"over_under_{str(line).replace('.', '_')}_model.pkl"
    if not os.path.exists(model_file):
        print(f" Model file not found: {model_file}")
        return

    model = joblib.load(model_file)

    # One-hot surface and round
    context = {col: 0 for col in context_cols}
    if f"Surface_{surface}" in context:
        context[f"Surface_{surface}"] = 1
    if f"Rd_{round_}" in context:
        context[f"Rd_{round_}"] = 1

    # Fetch player data
    def recent_matches(name):
        if name in player_cache.groups:
            return player_cache.get_group(name).tail(5)
        elif name in opponent_cache.groups:
            return opponent_cache.get_group(name).tail(5)
        return None

    p1_data = recent_matches(player1)
    p2_data = recent_matches(player2)
    if p1_data is None or p2_data is None:
        print(" Missing recent match data for one or both players.")
        return

    p1_stats = p1_data[stat_cols].mean(numeric_only=True)
    p2_stats = p2_data[stat_cols].mean(numeric_only=True)

    common = p1_stats.index.intersection(p2_stats.index)
    if len(common) < 5:
        print(" Not enough overlapping stats.")
        return

    diff = p1_stats[common] - p2_stats[common]
    diff.index = [f"{col}_diff" for col in common]
    p1_stats.index = [f"{col}_p1" for col in p1_stats.index]
    p2_stats.index = [f"{col}_p2" for col in p2_stats.index]

    full_vector = pd.concat([p1_stats, p2_stats, diff, pd.Series(context)])

    # Align features
    for col in model.feature_names_in_:
        if col not in full_vector.index:
            full_vector[col] = 0
    full_vector = full_vector[model.feature_names_in_].fillna(0)

    # Predict
    pred = model.predict([full_vector])[0]
    prob = model.predict_proba([full_vector])[0][1]

    print(f"\n {player1} vs {player2}")
    print(f"  Surface: {surface} | Round: {round_} | Line: {line}")
    print(f" Prediction: {'Over' if pred else 'Under'} {line}")
    print(f" Probability of Over: {prob:.2%}")

# === Example usage ===
predict_from_model(
    player1="Hubert Hurkacz",
    player2="Tommy Paul",
    surface="Clay",     # Options: Hard, Clay, Grass, Carpet
    round_="SF",        # Options: F, SF, QF, R16, BR, etc.
    line=23           #  Use any threshold you've trained a model for
)
