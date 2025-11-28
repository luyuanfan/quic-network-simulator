import argparse
import pandas as pd

def main():

    # init parser (read server log by default)
    parser = argparse.ArgumentParser(
        description="Analyze QUIC datacenter SCT logs."
    )
    parser.add_argument(
        "--file",
        default="../logs/server/scts_drr.csv",
        help="Path to CSV log file (default: ../logs/server/scts_drr.csv)",
    )
    args = parser.parse_args()

    # read csv file into dataframe
    print(f"reading {args.file} ...")
    df = pd.read_csv(args.file)

    print("\n=== columns ===")
    print(df.columns.tolist())

    print("\n=== peek first 10 rows ===")
    print(df.head(10))

    print("\n=== overall SCT stats (in ms) ===")
    print("(stream completion time)")
    if "sct_ms" in df.columns:
        print(df["sct_ms"].describe())
    else:
        print("warning: no 'sct_ms' column found.")

    print("\n=== SCT stats by class (short/medium/long) ===")
    if {"class", "sct_ms"}.issubset(df.columns):
        grouped = df.groupby("class")["sct_ms"].describe()
        print(grouped)
    else:
        print("warning: missing 'class' or 'sct_ms' columns.")

if __name__ == "__main__":
    main()
