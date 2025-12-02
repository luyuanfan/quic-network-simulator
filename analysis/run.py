import os
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import skew as sp_skew, kurtosis as sp_kurtosis, gaussian_kde

LOG_DIR = "../csv"
OUT_SUMMARY = "./results/summary_by_class.csv"

# TODO: maybe compute what quantum gives the lowest sct for short
# streams across all possible scenarios?

# TODO: not sure if we care about sct for long streams? 

# TODO: maybe we can plot the sct as a distribution and see if they
# shapes funny (long tail types of situations)

# TODO: CDF of stream completion time (per class, per scenario)

# TODO: Boxplot / violin plot by class and scheduler

# TODO: for each quantum combo, get sct across different scenarios

# TODO: maybe we care about 99 percentile of short flow sct or something like that
#   since if we have a long tail maybe some are dragging the mean down

# maybe an overall score: score= w1â€‹â‹…mean_short â€‹+ w2â€‹â‹…p99_short â€‹+ w3â€‹â‹…skew_short

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
    bytes_vals = group["bytes"].values.astype(float)
    sct_vals = group["sct_ms"].values.astype(float)
    valid_mask = sct_vals > 0
    bytes_vals = bytes_vals[valid_mask]
    sct_vals = sct_vals[valid_mask]
    throughput = bytes_vals / sct_vals
    n = len(throughput)

    if n == 0:
        print(f"no data for class {class_name}")
        return pd.Series({
            "count": None,
            "mean": None,
            "std": None,
            "skew": None,
            "kurtosis": None,
        })

    mean = np.mean(throughput)
    std = np.std(throughput, ddof=1)
    sk = sp_skew(throughput, bias=False)
    kt = sp_kurtosis(throughput, bias=False)

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
get best quantum for eahc scenario
'''
def get_best_quantum(path):
    pass

'''
for plotting time series of throughput for short flows
'''
def plot_throughput_timeseries(df, meta):
    """
    Create time series plot of throughput for short flows only
    """
    # Filter for short flows only
    df_short = df[df["class"] == "short"].copy()
    
    if len(df_short) == 0:
        print(f"  No short flows found for time series plot")
        return
    
    # Calculate throughput
    df_short["throughput"] = df_short["bytes"].astype(float) / df_short["sct_ms"].astype(float)
    
    # Filter valid data
    valid_mask = df_short["sct_ms"] > 0
    df_short = df_short[valid_mask]
    
    # Sort by time
    df_short = df_short.sort_values("time_ms")
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot throughput over time
    ax.scatter(df_short["time_ms"], df_short["throughput"], alpha=0.5, s=20, color='steelblue')
    
    # Add moving average for trend line
    window_size = max(10, len(df_short) // 50)  # Adaptive window size
    if len(df_short) >= window_size:
        df_short['throughput_ma'] = df_short['throughput'].rolling(window=window_size, center=True).mean()
        ax.plot(df_short["time_ms"], df_short["throughput_ma"], color='red', linewidth=2, label=f'Moving Avg (n={window_size})')
        ax.legend()
    
    # Labels and title
    title_parts = []
    if meta["scenario"]:
        title_parts.append(f"Scenario: {meta['scenario']}")
    if meta["scheduler"]:
        title_parts.append(f"Scheduler: {meta['scheduler']}")
    if meta["quantum0"] is not None:
        title_parts.append(f"Quantum: {meta['quantum0']}-{meta['quantum1']}-{meta['quantum2']}")
    title_parts.append("(Short Flows Only)")
    
    ax.set_title("\n".join(title_parts), fontsize=12)
    ax.set_xlabel("Time (ms)", fontsize=11)
    ax.set_ylabel("Throughput (bytes/ms)", fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save figure
    os.makedirs("./results/plots", exist_ok=True)
    output_path = f"./results/plots/{meta['file']}_timeseries.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"  Saved time series plot to {output_path}")
    plt.close()

'''
for plotting
'''
def plot_throughput_boxplot(df, meta):
    """
    Create box plot of throughput by class for a given scenario
    WITHOUT showing outlier points
    """
    # Calculate throughput for each flow
    bytes_vals = df["bytes"].values.astype(float)
    sct_vals = df["sct_ms"].values.astype(float)
    valid_mask = sct_vals > 0
    
    df_plot = df[valid_mask].copy()
    df_plot["throughput"] = df_plot["bytes"].astype(float) / df_plot["sct_ms"].astype(float)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Get unique classes and create box plot WITHOUT outliers
    classes = sorted(df_plot["class"].unique())
    data_by_class = [df_plot[df_plot["class"] == c]["throughput"].values for c in classes]
    
    # showfliers=False removes the outlier points
    bp = ax.boxplot(data_by_class, labels=classes, patch_artist=True, showfliers=False)
    
    # Customize colors
    for patch in bp['boxes']:
        patch.set_facecolor('lightblue')
        patch.set_alpha(0.7)
    
    # Labels and title
    title_parts = []
    if meta["scenario"]:
        title_parts.append(f"Scenario: {meta['scenario']}")
    if meta["scheduler"]:
        title_parts.append(f"Scheduler: {meta['scheduler']}")
    if meta["quantum0"] is not None:
        title_parts.append(f"Quantum: {meta['quantum0']}-{meta['quantum1']}-{meta['quantum2']}")
    
    ax.set_title("\n".join(title_parts), fontsize=12)
    ax.set_xlabel("Flow Class", fontsize=11)
    ax.set_ylabel("Throughput (bytes/ms)", fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    # Save figure
    os.makedirs("./results/plots", exist_ok=True)
    output_path = f"./results/plots/{meta['file']}_boxplot.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"  Saved plot to {output_path}")
    plt.close()

def plot_throughput_ridgeline(df, meta):
    """
    Create ridgeline plot of throughput distributions by class
    Removes outliers using IQR method
    """
    # Calculate throughput for each flow
    bytes_vals = df["bytes"].values.astype(float)
    sct_vals = df["sct_ms"].values.astype(float)
    valid_mask = sct_vals > 0
    
    df_plot = df[valid_mask].copy()
    df_plot["throughput"] = df_plot["bytes"].astype(float) / df_plot["sct_ms"].astype(float)
    
    # Get unique classes
    classes = sorted(df_plot["class"].unique())
    
    # Collect filtered data for each class
    data_by_class = {}
    for class_name in classes:
        class_data = df_plot[df_plot["class"] == class_name]["throughput"]
        
        # Remove outliers using IQR method
        Q1 = class_data.quantile(0.25)
        Q3 = class_data.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Filter out outliers
        filtered_data = class_data[(class_data >= lower_bound) & (class_data <= upper_bound)]
        data_by_class[class_name] = filtered_data.values
    
    # Create figure
    fig, axes = plt.subplots(len(classes), 1, figsize=(12, 2.5 * len(classes)), sharex=True)
    if len(classes) == 1:
        axes = [axes]
    
    # Color map for classes
    colors = {'short': '#FF6B6B', 'medium': '#4ECDC4', 'long': '#45B7D1'}
    
    # Plot each class as a density plot
    for idx, class_name in enumerate(classes):
        ax = axes[idx]
        data = data_by_class[class_name]
        
        if len(data) > 0:
            # Create histogram/density
            color = colors.get(class_name, '#95A5A6')
            ax.hist(data, bins=50, density=True, alpha=0.7, color=color, edgecolor='black', linewidth=0.5)
            
            # Add KDE (kernel density estimation) overlay
            from scipy import stats
            kde = stats.gaussian_kde(data)
            x_range = np.linspace(data.min(), data.max(), 200)
            ax.plot(x_range, kde(x_range), color='darkred', linewidth=2, alpha=0.8)
            
            # Fill under the curve
            ax.fill_between(x_range, kde(x_range), alpha=0.3, color=color)
        
        # Styling
        ax.set_ylabel(class_name, fontsize=11, rotation=0, ha='right', va='center')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.set_yticks([])
        ax.grid(True, alpha=0.3, axis='x')
        
        # Only show x-axis label on bottom plot
        if idx < len(classes) - 1:
            ax.spines['bottom'].set_visible(False)
            ax.tick_params(bottom=False)
    
    # Labels and title
    title_parts = []
    if meta["scenario"]:
        title_parts.append(f"Scenario: {meta['scenario']}")
    if meta["scheduler"]:
        title_parts.append(f"Scheduler: {meta['scheduler']}")
    if meta["quantum0"] is not None:
        title_parts.append(f"Quantum: {meta['quantum0']}-{meta['quantum1']}-{meta['quantum2']}")
    title_parts.append("(Throughput Distribution by Class)")
    
    fig.suptitle("\n".join(title_parts), fontsize=12, y=0.98)
    axes[-1].set_xlabel("Throughput (bytes/ms)", fontsize=11)
    
    plt.tight_layout()
    
    # Save figure
    os.makedirs("./results/plots", exist_ok=True)
    output_path = f"./results/plots/{meta['file']}_ridgeline.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"  Saved ridgeline plot to {output_path}")
    plt.close()

def plot_throughput_timeseries(df, meta):
    """
    Create time series plot of throughput over time for each class
    Removes outliers from visualization using IQR method
    """
    # Calculate throughput for each flow
    bytes_vals = df["bytes"].values.astype(float)
    sct_vals = df["sct_ms"].values.astype(float)
    time_vals = df["time_ms"].values.astype(float)
    valid_mask = sct_vals > 0
    
    df_plot = df[valid_mask].copy()
    df_plot["throughput"] = df_plot["bytes"].astype(float) / df_plot["sct_ms"].astype(float)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot each class with different colors
    classes = sorted(df_plot["class"].unique())
    colors = {'short': '#FF6B6B', 'medium': '#4ECDC4', 'long': '#45B7D1'}
    
    for class_name in classes:
        class_data = df_plot[df_plot["class"] == class_name].sort_values("time_ms").copy()
        
        # Remove outliers using IQR method for plotting only
        Q1 = class_data["throughput"].quantile(0.25)
        Q3 = class_data["throughput"].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Filter out outliers for plotting only
        class_data_filtered = class_data[
            (class_data["throughput"] >= lower_bound) & 
            (class_data["throughput"] <= upper_bound)
        ]
        
        color = colors.get(class_name, '#95A5A6')
        ax.scatter(class_data_filtered["time_ms"], class_data_filtered["throughput"], 
                  label=class_name, alpha=0.6, s=20, color=color)
    
    # Labels and title
    title_parts = []
    if meta["scenario"]:
        title_parts.append(f"Scenario: {meta['scenario']}")
    if meta["scheduler"]:
        title_parts.append(f"Scheduler: {meta['scheduler']}")
    if meta["quantum0"] is not None:
        title_parts.append(f"Quantum: {meta['quantum0']}-{meta['quantum1']}-{meta['quantum2']}")
    
    ax.set_title("\n".join(title_parts), fontsize=12)
    ax.set_xlabel("Time (ms)", fontsize=11)
    ax.set_ylabel("Throughput (bytes/ms)", fontsize=11)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save figure
    os.makedirs("./results/plots", exist_ok=True)
    output_path = f"./results/plots/{meta['file']}_timeseries.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"  Saved time series plot to {output_path}")
    plt.close()

def plot_throughput_ridgeline(df, meta):
    """
    Create ridgeline plot showing throughput distributions for each class
    Removes outliers using IQR method
    """
    # Calculate throughput for each flow
    bytes_vals = df["bytes"].values.astype(float)
    sct_vals = df["sct_ms"].values.astype(float)
    valid_mask = sct_vals > 0
    
    df_plot = df[valid_mask].copy()
    df_plot["throughput"] = df_plot["bytes"].astype(float) / df_plot["sct_ms"].astype(float)
    
    # Get unique classes
    classes = sorted(df_plot["class"].unique())
    colors = {'short': '#FF6B6B', 'medium': '#4ECDC4', 'long': '#45B7D1'}
    
    # Prepare data for each class (with outliers removed)
    class_data_dict = {}
    for class_name in classes:
        class_data = df_plot[df_plot["class"] == class_name]["throughput"].values
        
        # Remove outliers using IQR method
        Q1 = np.percentile(class_data, 25)
        Q3 = np.percentile(class_data, 75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Filter out outliers
        class_data_filtered = class_data[
            (class_data >= lower_bound) & 
            (class_data <= upper_bound)
        ]
        
        if len(class_data_filtered) > 1:  # Need at least 2 points for KDE
            class_data_dict[class_name] = class_data_filtered
    
    if not class_data_dict:
        print(f"  Not enough data for ridgeline plot")
        return
    
    # Create figure
    fig, axes = plt.subplots(len(class_data_dict), 1, figsize=(12, 2 * len(class_data_dict)), 
                             sharex=True)
    
    # Handle single class case
    if len(class_data_dict) == 1:
        axes = [axes]
    
    # Find global x range for consistent scaling
    all_data = np.concatenate(list(class_data_dict.values()))
    x_min, x_max = all_data.min(), all_data.max()
    x_range = np.linspace(x_min, x_max, 1000)
    
    # Plot each class
    for idx, (class_name, class_data) in enumerate(class_data_dict.items()):
        ax = axes[idx]
        
        # Create KDE
        kde = gaussian_kde(class_data)
        density = kde(x_range)
        
        # Fill the density curve
        color = colors.get(class_name, '#95A5A6')
        ax.fill_between(x_range, density, alpha=0.7, color=color)
        ax.plot(x_range, density, color=color, linewidth=2)
        
        # Styling
        ax.set_ylabel(class_name, fontsize=11, rotation=0, ha='right', va='center')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.set_yticks([])
        ax.grid(True, alpha=0.3, axis='x')
        
        # Only show x-axis label on bottom plot
        if idx < len(class_data_dict) - 1:
            ax.spines['bottom'].set_visible(False)
            ax.set_xticks([])
    
    # Set xlabel only on bottom plot
    axes[-1].set_xlabel("Throughput (bytes/ms)", fontsize=11)
    
    # Add title
    title_parts = []
    if meta["scenario"]:
        title_parts.append(f"Scenario: {meta['scenario']}")
    if meta["scheduler"]:
        title_parts.append(f"Scheduler: {meta['scheduler']}")
    if meta["quantum0"] is not None:
        title_parts.append(f"Quantum: {meta['quantum0']}-{meta['quantum1']}-{meta['quantum2']}")
    title_parts.append("Throughput Distribution by Class")
    
    fig.suptitle("\n".join(title_parts), fontsize=12, y=0.98)
    
    plt.tight_layout()
    
    # Save figure
    os.makedirs("./results/plots", exist_ok=True)
    output_path = f"./results/plots/{meta['file']}_ridgeline.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"  Saved ridgeline plot to {output_path}")
    plt.close()

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
        plot_throughput_boxplot(df, meta)
        plot_throughput_ridgeline(df, meta)
        plot_throughput_timeseries(df, meta)
    
if __name__ == "__main__":
    main()