import argparse
import pandas as pd

def main():

    # init parser 
    parser = argparse.ArgumentParser(
        description="Analyze QUIC datacenter SCT logs."
    )
    parser.add_argument(
        "--file",
        default="../logs/server/scts_drr.csv",
        help="Path to CSV log file (default: ../logs/server/scts_drr.csv)",
    )
    args = parser.parse_args()

if __name__ == "__main__":
    main()
