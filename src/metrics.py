#!/usr/bin/env python3
import argparse
from runcsv import process_matchups

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Batch compute DT & Monte Carlo metrics for a player1,player2 CSV"
    )
    parser.add_argument("input_csv", help="input CSV with headers Player1,Player2")
    parser.add_argument("output_csv", nargs="?",
                        help="optional output CSV (default: overwrite input)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    process_matchups(
        input_csv=args.input_csv,
        output_csv=args.output_csv,
        verbose=args.verbose
    )
