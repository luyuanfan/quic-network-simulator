import os
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

LOG_DIR = "../logs/server"
OUT_SUMMARY = "./results/summary_by_class.csv"

def parse_filename(path):
    '''
    example filename: sc-simple-p2p_d20_bw10_ql20_sch-drr_q7200-3600-1200.csv
    '''
    name = os.path.basename(path)
    if name.endswith(".csv"):
        name = name[:-4]

    # make meta data struct
    parts = name.split("_")
    meta = {
        "scenario": None,
        "delay_ms": None,
        "bandwidth_mbps": None,
        "queue_pkts": None,
        "scheduler": None,
        "quantum0": None,
        "quantum1": None,
        "quantum2": None,
        "file": name,
    }

    for p in parts:
        if p.startswith("sc-"):
            meta["scenario"] = p[3:]                 # after "sc-"
        elif p.startswith("d") and p[1:].isdigit():
            meta["delay_ms"] = int(p[1:])            # "d20" -> 20
        elif p.startswith("bw"):
            meta["bandwidth_mbps"] = int(p[2:])      # "bw10" -> 10
        elif p.startswith("ql"):
            meta["queue_pkts"] = int(p[2:])          # "ql20" -> 20
        elif p.startswith("sch-"):
            meta["scheduler"] = p[4:]                # "sch-drr" -> "drr"
        elif p.startswith("q"):                      # quantums: q7200-3600-1200
            nums = p[1:].split("-")
            if len(nums) == 3:
                meta["quantum0"] = int(nums[0])
                meta["quantum1"] = int(nums[1])
                meta["quantum2"] = int(nums[2])

    return meta

def print_info():
    pass

def main():

    # get csv files
    files = []
    for fname in os.listdir(LOG_DIR):
        if fname.endswith(".csv"):
            files.append(os.path.join(LOG_DIR, fname))
    files.sort()

    if not files:
        print(f"warning: no CSV files found in {LOG_DIR}")
        return
    
    # read csv files
    for f in files:
        print(f"reading file {path}")
        meta = parse_filename(path)


if __name__ == "__main__":
    main()
