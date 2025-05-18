#!/usr/bin/env python3

import csv
import argparse
import random
import math
import statistics
import os
import numpy as np
from collections import Counter       # ✅ THIS IS REQUIRED
import matplotlib.pyplot as plt       # ✅ FOR HISTOGRAM
# from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend (saves plots to file)
import matplotlib.pyplot as plt



# Thresholds for over/under analysis
GAME_THRESHOLDS = [19.5, 21.5, 22]

class PlayerStats:
    def __init__(self, DR, A_percent, DF_percent, FirstIn, FirstPercent, SecondPercent):
        self.DR = DR
        self.A_percent = A_percent
        self.DF_percent = DF_percent
        self.FirstIn = FirstIn
        self.FirstPercent = FirstPercent
        self.SecondPercent = SecondPercent


def simulate_game(win_prob):
    """Simulate a single game outcome (win/loss) for Player A."""
    return np.random.random() < win_prob


def simulate_set(win_prob):
    """Simulate a set, returning total games played and whether Player A won."""
    a_games, b_games = 0, 0
    while True:
        if simulate_game(win_prob):
            a_games += 1
        else:
            b_games += 1
        
        # Check set win conditions (6 games with 2-game margin or tiebreak)
        if (a_games >= 6 or b_games >= 6) and abs(a_games - b_games) >= 2:
            break
        
        # Handle tiebreak at 6-6
        if a_games == 6 and b_games == 6:
            a_points, b_points = 0, 0
            while True:
                if simulate_game(win_prob):
                    a_points += 1
                else:
                    b_points += 1
                if (a_points >= 7 or b_points >= 7) and abs(a_points - b_points) >= 2:
                    break
            if a_points > b_points:
                a_games += 1
            else:
                b_games += 1
            break
    
    return (a_games + b_games, a_games > b_games)

def simulate_match_scoreline(win_prob):
    a_sets, b_sets = 0, 0
    set_scores = []

    while a_sets < 2 and b_sets < 2:
        a_games, b_games = 0, 0

        while True:
            if simulate_game(win_prob):
                a_games += 1
            else:
                b_games += 1

            if (a_games >= 6 or b_games >= 6) and abs(a_games - b_games) >= 2:
                break

            if a_games == 6 and b_games == 6:
                if simulate_game(win_prob):
                    a_games += 1
                else:
                    b_games += 1
                break

        set_scores.append((a_games, b_games))
        if a_games > b_games:
            a_sets += 1
        else:
            b_sets += 1

    total_games = sum(a + b for a, b in set_scores)
    return set_scores, total_games, a_sets > b_sets


def monte_carlo_simulation(p1: PlayerStats, p2: PlayerStats, iterations=5000, visualize=True, save_plots=False):
    import matplotlib.pyplot as plt
    from collections import Counter

    # Change to match web iterations
    scoreline_list = []
    set_counts = []
    total_games_list = []
    margin_list = []
    p1_wins = 0

    WspA = calculate_Wsp(p1)
    WspB = calculate_Wsp(p2)
    CSA = WspA - WspB
    win_prob = 1.0 / (1.0 + math.exp(-CSA))
            
    for _ in range(iterations):
        scoreline, total_games, p1_won = simulate_match_scoreline(win_prob)

        scoreline_list.append(" ".join(f"{a}-{b}" for a, b in scoreline))
        set_counts.append(len(scoreline))
        total_games_list.append(total_games)

        a_total = sum([a for a, _ in scoreline])
        b_total = sum([b for _, b in scoreline])
        margin_list.append(abs(a_total - b_total))

        if p1_won:
            p1_wins += 1

    # avg games
    avg_games = sum(total_games_list) / iterations
    # mode
    from collections import Counter
    mode_games = Counter(total_games_list).most_common(1)[0][0]
    
    from scipy.stats import gaussian_kde
    x_vals = np.linspace(min(total_games_list), max(total_games_list), 10000)
    kde = gaussian_kde(total_games_list)
    kde_peak = x_vals[np.argmax(kde(x_vals))]
    
    win_pct = p1_wins / iterations * 100
    avg_sets = sum(set_counts) / iterations
    std_dev_games = np.std(total_games_list)
    variance_games = std_dev_games ** 2

    confidence = "HIGH" if std_dev_games < 2.5 else "MEDIUM" if std_dev_games < 4.5 else "LOW"

    avg_margin = sum(margin_list) / iterations
    std_dev_margin = np.std(margin_list)
    margin_conf = "HIGH (consistent matchups)" if std_dev_margin < 2.0 else "MEDIUM" if std_dev_margin < 4.0 else "LOW (volatile matchups)"

    print(f"Avg Total Games (Monte Carlo): {avg_games:.1f}")
    print(f"Std Dev of Total Games: {std_dev_games:.2f}")
    print(f"Confidence Level: {confidence}")
    print(f"Avg Margin of Victory (in games): {avg_margin:.2f}")
    print(f"Std Dev of Margin: {std_dev_margin:.2f}")
    print(f"Margin Confidence: {margin_conf}")
    print(f"Variance of Total Games: {variance_games:.2f}")
    print(f"Expected Games (Mean): {avg_games:.1f}")
    print(f"Expected Games (Mode): {mode_games}")
    print(f"Expected Games (KDE Peak): {kde_peak:.1f}")

    
    over_under_probs = []
    for line in GAME_THRESHOLDS:
        over_pct = sum(g > line for g in total_games_list) / iterations * 100
        under_pct = 100 - over_pct
        print(f"Chance of OVER  {line:>4} games: {over_pct:.2f}%")
        print(f"Chance of UNDER {line:>4} games: {under_pct:.2f}%\n")
        over_under_probs.append((line, over_pct, under_pct))


    if visualize or save_plots:
        # --- Plot 1: Total Games Distribution ---
        plt.figure()
        counter = Counter(total_games_list)
        keys = sorted(counter.keys())
        values = [counter[k] for k in keys]
        plt.bar(keys, values)
        plt.xlabel("Total Games in Match")
        plt.ylabel("Frequency")
        plt.title("Monte Carlo Distribution of Total Games")
        plt.grid(True)
        if save_plots:
            plt.savefig("static/plot1.png")


        # --- Plot 2: Scoreline Distribution ---
        plt.figure(figsize=(10, 4))
        score_counter = Counter(scoreline_list)
        common_scores = score_counter.most_common(10)
        labels = [x[0] for x in common_scores]
        counts = [x[1] for x in common_scores]
        plt.barh(labels, counts)
        plt.xlabel("Frequency")
        plt.ylabel("Scoreline")
        plt.title("Most Common Scorelines (Monte Carlo)")
        plt.tight_layout()
        if save_plots:
            plt.savefig("static/plot2.png")

        # --- Plot 3: Margin of Victory ---
        plt.figure()
        margin_counter = Counter(margin_list)
        keys = sorted(margin_counter.keys())
        values = [margin_counter[k] for k in keys]
        plt.bar(keys, values)
        plt.xlabel("Game Margin")
        plt.ylabel("Frequency")
        plt.title("Distribution of Match Margins (Monte Carlo)")
        plt.grid(True)
        plt.tight_layout()
        if save_plots:
            plt.savefig("static/plot3.png")

    if visualize:
        input("Press Enter to close all graphs and continue...")
        plt.close('all')

    if save_plots:
        return (
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
            "static/plot1.png",
            "static/plot2.png",
            "static/plot3.png",
    )

# even if save_plots is False
    return (
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
        "static/plot1.png" if save_plots else None,
        "static/plot2.png" if save_plots else None,
        "static/plot3.png" if save_plots else None,
)


def simulate_match(win_prob):
    """Simulate a best-of-3 match, returning total games played."""
    a_sets, b_sets = 0, 0
    total_games = 0
    while a_sets < 2 and b_sets < 2:
        set_games, a_won = simulate_set(win_prob)
        total_games += set_games
        if a_won:
            a_sets += 1
        else:
            b_sets += 1
    return total_games


def calculate_Wsp(p: PlayerStats):
    A = p.A_percent / 100.0
    DF = p.DF_percent / 100.0
    FirstIn = p.FirstIn / 100.0
    FirstPercent = p.FirstPercent / 100.0
    SecondPercent = p.SecondPercent / 100.0
    DR_1 = p.DR  # equivalent to p.DR / 1

    # Classic Wsp components
    W1st = FirstIn * (1 + FirstPercent)
    W2nd = (1 - FirstIn - A - DF) * (1 + SecondPercent)
    Wsp = DR_1 * (W1st + W2nd)
    return Wsp

    """
def generate_features(pA: PlayerStats, pB: PlayerStats):
    return [
        pA.DR - pB.DR,
        pA.A_percent - pB.A_percent,
        pA.DF_percent - pB.DF_percent,
        pA.FirstIn - pB.FirstIn,
        pA.FirstPercent - pB.FirstPercent,
        pA.SecondPercent - pB.SecondPercent
    ]   
    """

def generate_features(p1: PlayerStats, p2: PlayerStats):
    features = []

    # --- Basic Differences ---
    features.append(p1.DR - p2.DR)
    features.append(p1.A_percent - p2.A_percent)
    features.append(p1.DF_percent - p2.DF_percent)
    features.append(p1.FirstIn - p2.FirstIn)
    features.append(p1.FirstPercent - p2.FirstPercent)
    features.append(p1.SecondPercent - p2.SecondPercent)

    # --- Absolute Differences ---
    features.append(abs(p1.DR - p2.DR))
    features.append(abs(p1.A_percent - p2.A_percent))
    features.append(abs(p1.DF_percent - p2.DF_percent))
    features.append(abs(p1.FirstIn - p2.FirstIn))
    features.append(abs(p1.FirstPercent - p2.FirstPercent))
    features.append(abs(p1.SecondPercent - p2.SecondPercent))

    # --- Ratios (stabilized) ---
    epsilon = 1e-3  # avoid division by zero
    features.append(p1.DR / (p2.DR + epsilon))
    features.append(p1.FirstPercent / (p2.FirstPercent + epsilon))
    features.append(p1.SecondPercent / (p2.SecondPercent + epsilon))

    return features

def get_feature_importance(self):
    names = [
        "1st Serve In % diff",
        "1st Serve Win % diff",
        "2nd Serve In % diff",
        "2nd Serve Win % diff"
    ]
    return sorted(zip(names, [abs(w) for w in self.weights]), key=lambda x: x[1], reverse=True)


def generate_win_training_data(num_samples=10000):
    """Generate training data for win probability model"""
    training_data = []
    # Seed for reproducibility can be added if desired
    for _ in range(num_samples):
        # Random DR (1.5±0.5), clamped ≥0.5
        DR_A = max(0.5, random.gauss(1.5, 0.5))
        DR_B = max(0.5, random.gauss(1.5, 0.5))
        # Random Ace % (10±4), clamped [0,25]
        A_A = min(25.0, max(0.0, random.gauss(10.0, 4.0)))
        A_B = min(25.0, max(0.0, random.gauss(10.0, 4.0)))
        # Random DF % (4±2), clamped [0,15]
        DF_A = min(15.0, max(0.0, random.gauss(4.0, 2.0)))
        DF_B = min(15.0, max(0.0, random.gauss(4.0, 2.0)))
        # First Serve In % (65±7), clamped [45,85]
        FI_A = min(85.0, max(45.0, random.gauss(65.0, 7.0)))
        FI_B = min(85.0, max(45.0, random.gauss(65.0, 7.0)))
        # First Serve Win % (75±7), clamped [55,95]
        FP_A = min(95.0, max(55.0, random.gauss(75.0, 7.0)))
        FP_B = min(95.0, max(55.0, random.gauss(75.0, 7.0)))
        # Second Serve Win % (55±7), clamped [35,75]
        SP_A = min(75.0, max(35.0, random.gauss(55.0, 7.0)))
        SP_B = min(75.0, max(35.0, random.gauss(55.0, 7.0)))

        pA = PlayerStats(DR_A, A_A, DF_A, FI_A, FP_A, SP_A)
        pB = PlayerStats(DR_B, A_B, DF_B, FI_B, FP_B, SP_B)

        WspA = calculate_Wsp(pA)
        WspB = calculate_Wsp(pB)
        CSA = WspA - WspB
        win_prob = 1.0 / (1.0 + math.exp(-CSA))
        result = 1.0 if random.random() < win_prob else 0.0
        features = generate_features(pA, pB)
        training_data.append((features, result))
    return training_data


def generate_games_training_data(num_samples=10000):
    """Generate training data for games prediction model"""
    training_data = []
    for _ in range(num_samples):
        # Random DR (1.5±0.5), clamped ≥0.5
        DR_A = max(0.5, np.random.normal(1.5, 0.5))
        DR_B = max(0.5, np.random.normal(1.5, 0.5))
        # Random Ace % (10±4), clamped [0,25]
        A_A = min(25.0, max(0.0, np.random.normal(10.0, 4.0)))
        A_B = min(25.0, max(0.0, np.random.normal(10.0, 4.0)))
        # Random DF % (4±2), clamped [0,15]
        DF_A = min(15.0, max(0.0, np.random.normal(4.0, 2.0)))
        DF_B = min(15.0, max(0.0, np.random.normal(4.0, 2.0)))
        # First Serve In % (65±7), clamped [45,85]
        FI_A = min(85.0, max(45.0, np.random.normal(65.0, 7.0)))
        FI_B = min(85.0, max(45.0, np.random.normal(65.0, 7.0)))
        # First Serve Win % (75±7), clamped [55,95]
        FP_A = min(95.0, max(55.0, np.random.normal(75.0, 7.0)))
        FP_B = min(95.0, max(55.0, np.random.normal(75.0, 7.0)))
        # Second Serve Win % (55±7), clamped [35,75]
        SP_A = min(75.0, max(35.0, np.random.normal(55.0, 7.0)))
        SP_B = min(75.0, max(35.0, np.random.normal(55.0, 7.0)))

        pA = PlayerStats(DR_A, A_A, DF_A, FI_A, FP_A, SP_A)
        pB = PlayerStats(DR_B, A_B, DF_B, FI_B, FP_B, SP_B)

        # Calculate win probability using existing Wsp formula
        WspA = calculate_Wsp(pA)
        WspB = calculate_Wsp(pB)
        CSA = WspA - WspB
        win_prob = 1 / (1 + np.exp(-CSA))
        
        # Simulate total games for this match
        total_games = simulate_match(win_prob)
        features = generate_features(pA, pB)
        training_data.append((features, total_games))
    
    return training_data


def load_all_player_stats(filename):
    stats = []
    with open(filename, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)  # skip header
        for row in reader:
            if len(row) < 6:
                continue
            DR = float(row[0])
            # Remove % symbol before converting to float
            A_percent = float(row[1].replace('%', ''))
            DF_percent = float(row[2].replace('%', ''))
            FirstIn = float(row[3].replace('%', ''))
            FirstPercent = float(row[4].replace('%', ''))
            SecondPercent = float(row[5].replace('%', ''))
            stats.append(PlayerStats(DR, A_percent, DF_percent, FirstIn, FirstPercent, SecondPercent))
    return stats


def load_player_stats(filename, use_median=True):
    all_stats = load_all_player_stats(filename)
    DR_vals = [p.DR for p in all_stats]
    A_vals = [p.A_percent for p in all_stats]
    DF_vals = [p.DF_percent for p in all_stats]
    FI_vals = [p.FirstIn for p in all_stats]
    FP_vals = [p.FirstPercent for p in all_stats]
    SP_vals = [p.SecondPercent for p in all_stats]

    if use_median:
        stats = PlayerStats(
            DR=statistics.median(DR_vals) if DR_vals else 0.0,
            A_percent=statistics.median(A_vals) if A_vals else 0.0,
            DF_percent=statistics.median(DF_vals) if DF_vals else 0.0,
            FirstIn=statistics.median(FI_vals) if FI_vals else 0.0,
            FirstPercent=statistics.median(FP_vals) if FP_vals else 0.0,
            SecondPercent=statistics.median(SP_vals) if SP_vals else 0.0
        )
    else:
        stats = PlayerStats(
            DR=statistics.mean(DR_vals) if DR_vals else 0.0,
            A_percent=statistics.mean(A_vals) if A_vals else 0.0,
            DF_percent=statistics.mean(DF_vals) if DF_vals else 0.0,
            FirstIn=statistics.mean(FI_vals) if FI_vals else 0.0,
            FirstPercent=statistics.mean(FP_vals) if FP_vals else 0.0,
            SecondPercent=statistics.mean(SP_vals) if SP_vals else 0.0
        )
    return stats


class LinearModel:
    def __init__(self, feature_count, lr=0.1, iterations=10000):
        self.lr = lr
        self.iterations = iterations
        # Initialize weights and bias
        self.weights = [random.gauss(0, 0.1) for _ in range(feature_count)]
        self.bias = random.gauss(0, 0.1)

    def predict(self, features):
        z = self.bias + sum(w * f for w, f in zip(self.weights, features))
        return 1.0 / (1.0 + math.exp(-z))

    def train(self, training_data):
        print(f"Training ML model on {len(training_data)} samples...")
        for i in range(self.iterations):
            weight_grads = [0.0] * len(self.weights)
            bias_grad = 0.0
            for features, result in training_data:
                pred = self.predict(features)
                error = pred - result
                for j in range(len(self.weights)):
                    weight_grads[j] += error * features[j]
                bias_grad += error
            # Update parameters
            n = len(training_data)
            self.weights = [w - self.lr * gw / n for w, gw in zip(self.weights, weight_grads)]
            self.bias -= self.lr * bias_grad / n
            # Optional: print loss periodically
            if (i + 1) % 100 == 0 or i == 0:
                loss = sum((self.predict(f) - y)**2 for f, y in training_data) / n
                print(f"Iter {i+1}/{self.iterations}, Loss: {loss:.4f}")

    def get_feature_importance(self):
        names = [
            "DR diff", "Ace % diff", "DF % diff",
            "FirstIn % diff", "FirstServeWin % diff", "SecondServeWin % diff"
        ]
        return sorted(zip(names, [abs(w) for w in self.weights]), key=lambda x: x[1], reverse=True)


class DecisionTreeModel:
    def __init__(self, max_depth=None, n_estimators=100):  # new param
        self.model = RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth)

    def train(self, data):
        X = [f for f, _ in data]
        y = [label for _, label in data]
        self.model.fit(X, y)

    def predict(self, features):
        return self.model.predict([features])[0]

model = DecisionTreeModel(max_depth=5)


def print_player_stats(stats, name):
    print(f"--- {name} Stats Summary ---")
    print(f"DR: {stats.DR}")
    print(f"Ace %: {stats.A_percent}%")
    print(f"Double Fault %: {stats.DF_percent}%")
    print(f"First Serve In %: {stats.FirstIn}%")
    print(f"First Serve Win %: {stats.FirstPercent}%")
    print(f"Second Serve Win %: {stats.SecondPercent}%\n")


def main():
    parser = argparse.ArgumentParser(description="Tennis Predictor")
    parser.add_argument("player1_file")
    parser.add_argument("player2_file")
    parser.add_argument("--avg", action="store_true", help="Use average (mean) instead of median")
    parser.add_argument("--classic", action="store_true", help="Classic formula only")
    parser.add_argument("--ml", action="store_true", help="Machine learning only")
    parser.add_argument("--both", action="store_true", help="Use both methods")
    args = parser.parse_args()

    use_median = not args.avg
    use_classic = False
    use_ml = True  # Default is ML

    if args.classic:
        use_classic = True
        use_ml = False
    elif args.both:
        use_classic = True
        use_ml = True
    elif args.ml:
        use_classic = False
        use_ml = True



    method = "median" if use_median else "average"
    print(f"Using {method} stats for both players.\n")
    print(f"Prediction Method: {'ML' if use_ml else 'Classic'}\n")

    p1 = load_player_stats(args.player1_file, use_median)
    p2 = load_player_stats(args.player2_file, use_median)
    name1 = os.path.splitext(os.path.basename(args.player1_file))[0]
    name2 = os.path.splitext(os.path.basename(args.player2_file))[0]

    print_player_stats(p1, name1)
    print_player_stats(p2, name2)

    if use_classic:
        WspA = calculate_Wsp(p1)
        WspB = calculate_Wsp(p2)
        CSA = WspA - WspB
        winA = 1.0 / (1.0 + math.exp(-CSA))
        winB = 1.0 - winA
        print("--- Classic Prediction ---")
        print(f"{name1} Wsp: {WspA:.2f}")
        print(f"{name2} Wsp: {WspB:.2f}")
        print(f"CSA: {CSA:.2f}")
        print(f"{name1} Win %: {winA*100:.2f}%")
        print(f"{name2} Win %: {winB*100:.2f}%\n")

    if use_ml:
        print("--- Decision Tree Prediction ---")
        data = generate_games_training_data(5000)
        model = DecisionTreeModel(max_depth=5)
        model.train(data)

        feats = generate_features(p1, p2)
        pred_games = model.predict(feats)
        print(f"Predicted Total Games: {pred_games:.1f}")

        # Add Win Probability Estimate using Wsp
        WspA = calculate_Wsp(p1)
        WspB = calculate_Wsp(p2)
        CSA = WspA - WspB
        winA = 1.0 / (1.0 + math.exp(-CSA))
        winB = 1.0 - winA
        print(f"\nEstimated Win Probability:")
        print(f"{name1}: {winA * 100:.2f}%")
        print(f"{name2}: {winB * 100:.2f}%")
        print("\n--- Monte Carlo Simulation ---")
        (
            avg_games_mc,
            win_pct_mc,
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
        ) = monte_carlo_simulation(p1, p2, iterations=10000, visualize=True)
        print(f"Avg Total Games (Monte Carlo): {avg_games_mc:.1f}")
        print(f"Expected Games (Mode): {mode_games}")
        print(f"Expected Games (KDE Peak): {kde_peak:.1f}")
        print(f"Variance: {variance_games:.2f}")
        print(f"{name1} Win % (Monte Carlo): {win_pct_mc:.2f}%")
        print(f"{name2} Win % (Monte Carlo): {100 - win_pct_mc:.2f}%")


def run_ml_pipeline(p1, p2, name1, name2):
    print("--- Decision Tree Prediction ---")
    data = generate_games_training_data(10000)
    model = DecisionTreeModel(max_depth=1000)
    model.train(data)

    features = generate_features(p1, p2)
    pred_games = model.predict(features)

    WspA = calculate_Wsp(p1)
    WspB = calculate_Wsp(p2)
    CSA = WspA - WspB
    winA = 1.0 / (1.0 + math.exp(-CSA))
    winB = 1.0 - winA

    avg_games_mc, win_pct_mc, confidence, margin_conf, std_dev_games, avg_margin, std_dev_margin, over_under_probs, path1, path2, path3 = monte_carlo_simulation(
        p1, p2, iterations=1000, visualize=False, save_plots=True
    )

    return {
        "predicted_games": round(pred_games, 1),
        "predicted_win_pct": round(winA * 100, 2),
        "mc_games": round(avg_games_mc, 1),
        "mc_win_pct": round(win_pct_mc, 2),
        "confidence_level": confidence,
        "margin_conf": margin_conf,
        "std_dev": round(std_dev_games, 2),
        "avg_margin": round(avg_margin, 2),
        "std_dev_margin": round(std_dev_margin, 2),
        "over_under_probs": over_under_probs,
        "graph1": path1,
        "graph2": path2,
        "graph3": path3,
    }
  


if __name__ == "__main__":
    main()
