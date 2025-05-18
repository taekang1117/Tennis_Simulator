#!/usr/bin/env python3
import csv
import sys
from predictor import load_all_stats_from_csv, predict_match

def normalize_player_name(name: str) -> str:
    """Normalize player name to match your CSV‐loaded keys."""
    return name.strip().replace(" ", "").lower()

def process_matchups(input_csv: str, output_csv: str = None, verbose: bool = False):
    import csv
    from predictor import load_all_stats_from_csv, predict_match

    def normalize_player_name(name: str) -> str:
        return name.strip().replace(" ", "").lower()

    # load stats once
    stat_dict = load_all_stats_from_csv()
    if verbose:
        print(f"[+] Loaded stats for {len(stat_dict)} players")

    # open & sniff headers
    with open(input_csv, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        headers = reader.fieldnames or []
        if verbose:
            print(f"[+] Detected columns: {headers}")

    # decide which two columns are your player names
    if "Player1" in headers and "Player2" in headers:
        col1, col2 = "Player1", "Player2"
    elif len(headers) >= 2:
        col1, col2 = headers[0], headers[1]
        if verbose:
            print(f"[!] Falling back to first two columns: '{col1}', '{col2}'")
    else:
        raise ValueError("Input CSV must have at least two columns")

    # augment each row
    out_fields = headers + ["DecisionTree", "MC_Mean", "MC_Mode", "MC_KDE", "Average"]
    for r in rows:
        p1, p2 = r[col1], r[col2]
        res = predict_match(normalize_player_name(p1),
                            normalize_player_name(p2),
                            stat_dict)
        if "error" in res:
            dt = mean = mode = kde = avg = ""
        else:
            dt   = float(res["predicted_games"])
            mean = float(res["mc_games"])
            mode = float(res["expected_mode"])
            kde  = float(res["expected_kde_peak"])
            avg  = (dt + mean + mode + kde) / 4.0
        r.update({
            "DecisionTree": f"{dt:.1f}",
            "MC_Mean":      f"{mean:.1f}",
            "MC_Mode":      f"{mode:.0f}",
            "MC_KDE":       f"{kde:.1f}",
            "Average":      f"{avg:.1f}"
        })
        if verbose:
            print(f"{p1} vs {p2} → DT={dt:.1f}, Mean={mean:.1f}, "
                  f"Mode={mode:.0f}, KDE={kde:.1f}, Avg={avg:.1f}")

    # write back out
    out_path = output_csv or input_csv
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(rows)

    if verbose:
        print(f"[+] Written results to {out_path}")

    # Write results out
    out_path = output_csv or input_csv
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(rows)

    if verbose:
        print(f"[+] Written results to {out_path}")


import argparse

from predictor import load_all_stats_from_csv, predict_match  # :contentReference[oaicite:0]{index=0}:contentReference[oaicite:1]{index=1}

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Read a CSV with columns Player1,Player2, "
            "append Decision Tree, Mean, Mode, KDE and Average metrics."
        )
    )
    parser.add_argument(
        "input_csv",
        help="Path to input CSV (must have headers Player1 and Player2)"
    )
    parser.add_argument(
        "output_csv",
        nargs="?",
        help=(
            "Optional path to write results to. "
            "If omitted, the input file will be overwritten."
        )
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print progress as you go"
    )
    args = parser.parse_args()

    process_matchups(
        input_csv=args.input_csv,
        output_csv=args.output_csv,
        verbose=args.verbose
    )


def get_match_metrics(p1_name: str, p2_name: str):
    # Load all player stats (median values)
    stat_dict = load_all_stats_from_csv()
    
    # Normalize lookup keys
    key1 = p1_name.strip().replace(" ", "").lower()
    key2 = p2_name.strip().replace(" ", "").lower()
    
    # Run the full ML pipeline
    result = predict_match(key1, key2, stat_dict)
    if "error" in result:
        raise ValueError(result["error"])
    
    # Extract metrics
    dt     = float(result["predicted_games"])       # Decision Tree  
    mean   = float(result["mc_games"])             # Monte Carlo mean  
    mode   = float(result["expected_mode"])        # Monte Carlo mode  
    kde    = float(result["expected_kde_peak"])    # Monte Carlo KDE peak  
    
    # Compute simple average
    avg = (dt + mean + mode + kde) / 4.0
    
    return dt, mean, mode, kde, avg

def main():
    parser = argparse.ArgumentParser(
        description="Compute Decision Tree & Monte Carlo metrics for two tennis players"
    )
    parser.add_argument("player1", help="First player name (e.g. janniksinner)")
    parser.add_argument("player2", help="Second player name (e.g. casperruud)")
    args = parser.parse_args()

    try:
        dt, mean, mode, kde, avg = get_match_metrics(args.player1, args.player2)
    except ValueError as e:
        print(f"Error: {e}")
        return

    # Display results
    print(f"Decision Tree Prediction : {dt:.1f}")
    print(f"Monte Carlo Mean         : {mean:.1f}")
    print(f"Monte Carlo Mode         : {mode:.0f}")
    print(f"Monte Carlo KDE Peak     : {kde:.1f}")
    print(f"Average of all four      : {avg:.1f}")

if __name__ == "__main__":
    main()
