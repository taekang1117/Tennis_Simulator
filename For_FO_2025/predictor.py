import os
import glob
from main import (
    load_player_stats,
    calculate_Wsp,
    monte_carlo_simulation,
    generate_features,
    generate_games_training_data,
    DecisionTreeModel,
    PlayerStats
)

def load_all_stats_from_csv():
    """Load player stats from CSV files using median values"""
    stat_dict = {}
    # point at the new folder
    folder_path = os.path.join("data", "checkpoints")
    # match all CSVs there
    pattern     = os.path.join(folder_path, "*.csv")

    for path in glob.glob(pattern):
        filename = os.path.basename(path)
        # strip the .csv extension to get your key
        name = os.path.splitext(filename)[0]
        stat_dict[name.lower()] = load_player_stats(path, use_median=True)

    return stat_dict

def predict_match(player1_name, player2_name, stat_dict):
    """Run full ML prediction pipeline"""
    p1_key = player1_name.strip().lower()
    p2_key = player2_name.strip().lower()

    if p1_key not in stat_dict or p2_key not in stat_dict:
        return {"error": f"Player not found: {player1_name} or {player2_name}"}

    p1 = stat_dict[p1_key]
    p2 = stat_dict[p2_key]

    # Decision Tree games prediction
    model = DecisionTreeModel(max_depth=5)
    data = generate_games_training_data(10000)
    model.train(data)
    features = generate_features(p1, p2)
    pred_games = model.predict(features)

    # Monte Carlo simulation
    (
        avg_games,
        win_pct,
        confidence,
        margin_conf,
        std_dev_games,
        variance_games,
        avg_margin,
        std_dev_margin,
        mode_games,
        kde_peak,
        over_under_probs,
        path1,
        path2,
        path3,
    ) = monte_carlo_simulation(
        p1, p2, iterations=10000, visualize=False, save_plots=True
    )

    return {
        'player1': player1_name,
        'player2': player2_name,
        'p1_stats': p1,
        'p2_stats': p2,
        'predicted_games': round(pred_games, 1),
        'predicted_win_pct': round(win_pct, 2),
        'mc_games': round(avg_games, 1),
        'variance_games': round(variance_games, 2),
        'expected_mode': int(mode_games),
        'expected_kde_peak': round(kde_peak, 1),
        'confidence_level': confidence,
        'avg_margin': round(avg_margin, 2),
        'std_dev': round(std_dev_games, 2),
        'margin_conf': margin_conf,
        'std_dev_margin': round(std_dev_margin, 2),
        'over_under_probs': over_under_probs,
    }

def run_ml_pipeline(p1, p2, name1, name2):
    """ML pipeline for terminal output"""
    # Decision Tree prediction
    model = DecisionTreeModel(max_depth=5)
    data = generate_games_training_data(10000)
    model.train(data)
    features = generate_features(p1, p2)
    pred_games = model.predict(features)

    # Monte Carlo simulation (updated unpacking!)
    (
        avg_games,
        win_pct,
        confidence,
        margin_conf,
        std_dev_games,
        variance_games,
        avg_margin,
        std_dev_margin,
        mode_games,
        kde_peak,
        over_under_probs,
        path1,
        path2,
        path3,
    ) = monte_carlo_simulation(
        p1, p2, iterations=10000, visualize=False, save_plots=True
    )

    # Print terminal output
    print("\n--- Machine Learning Predictions ---")
    print(f"Predicted Total Games (Decision Tree): {pred_games:.1f}")
    print(f"Expected Games (Mean): {avg_games:.1f}")
    print(f"Expected Games (Mode): {mode_games}")
    print(f"Expected Games (KDE Peak): {kde_peak:.1f}")
    print(f"Variance: {variance_games:.2f}")
    print(f"\nWin Probabilities (Monte Carlo):")
    print(f"{name1}: {win_pct:.2f}%")
    print(f"{name2}: {100 - win_pct:.2f}%")
    print("\nMatch Confidence:")
    print(f"- Games Std Dev: {std_dev_games:.2f} ({confidence})")
    print(f"- Avg Margin: {avg_margin:.2f} games")
    print(f"- Margin Std Dev: {std_dev_margin:.2f} ({margin_conf})")

    return {
        'predicted_games': pred_games,
        'mc_games': avg_games,
        'win_pct': win_pct,
        'variance_games': variance_games,
        'expected_mode': mode_games,
        'expected_kde_peak': kde_peak,
        'std_dev_games': std_dev_games,
        'avg_margin': avg_margin,
        'std_dev_margin': std_dev_margin,
    }
