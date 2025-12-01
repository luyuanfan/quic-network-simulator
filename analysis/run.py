import os
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import skew as sp_skew, kurtosis as sp_kurtosis

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
        elif p.startswith("q"):                      # "q7200-3600-1200" -> 7200,3600,1200
            nums = p[1:].split("-")
            if len(nums) == 3:
                meta["quantum0"] = int(nums[0])
                meta["quantum1"] = int(nums[1])
                meta["quantum2"] = int(nums[2])

    return meta

''' compute moments for a flow length group
    e.g., compute the mean, std, skew, kurt of short flows in xyz scenario
'''
def compute_moments(class_name, group):

    x = group["sct_ms"].values.astype(float)
    n = len(x)

    if n == 0:
        print(f"no data for class {class_name}")
        return pd.Series({
            "count": None,
            "mean": None,
            "std": None,
            "skew": None,
            "kurtosis": None,
        })

    mean = np.mean(x)
    std = np.std(x, ddof=1)
    sk = sp_skew(x, bias=False)
    kt = sp_kurtosis(x, bias=False)

    return pd.Series({
        "count": n,
        "mean": mean,
        "std": std,
        "skew": sk,
        "kurtosis": kt,
    })

'''
get stream completion time by class (stream length) for one scenario
'''
def print_sct_stats(df):

    rows = []
    # get sct across all classes
    s = compute_moments("full", df)
    s["class"] = "full"
    rows.append(s)
    # get sct by class
    for class_name, group in df.groupby("class"):
        s = compute_moments(class_name, group)
        s["class"] = class_name
        rows.append(s)
    results = pd.DataFrame(rows)
    print(results)

'''
get best quantum among scenarios
'''
def get_best_params(path):
    pass

def print_info():
    pass

def main():

    # get csv files
    files = []
    for fname in os.listdir(LOG_DIR):
        if fname.endswith(".csv"):
            files.append(os.path.join(LOG_DIR, fname))

    if not files:
        print(f"warning: no CSV files found in {LOG_DIR}")
        return

    files.sort()
    
    # process each csv file
    for f in files:
        print(f"reading file {f}")
        meta = parse_filename(f)
        df = pd.read_csv(f, sep=',')
        print_sct_stats(df)
    


if __name__ == "__main__":
    main()
