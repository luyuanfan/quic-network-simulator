import os 
import itertools
import argparse
import subprocess

''' docker configurations '''
CLIENT_IMAGE = "quic-go-datacenter"
SERVER_IMAGE = "quic-go-datacenter"

''' scheduler configurations '''
# scheduler modules
SCHEDULERS = [
    "drr",
    "abs",
    "wfq",
    "rr"
]
# drr quantums
QUANTUMS = [
    (1 * 1200, 8 * 1200, 128 * 1200),
    (1 * 1200, 8 * 1200, 64 * 1200),
    (1 * 1200, 8 * 1200, 32 * 1200),
    # (3 * 1200, 2 * 1200, 1 * 1200)
]

''' network configurations '''
# stream attributes
NFLOWS = 300
SLRATIO = 0.9
SHORT_SIZE = 100 * 1024 # 100KB 
LONG_SIZE = 1 * 1024 * 1024 # 1MB
CONCURRENCY = [
    "40",
    "60"
]
# link delay (unit: ms)
DELAYS = [
    "20"
]
# link max bandwidth (unit: Mbps)
BANDWIDTHS = [
    "8"
]
# length of switch queue (unit: number of packet)
QUEUE_LENGTHS = [
    "5",
    "20",    
]

''' run one docker compose experiment '''
def run_one_experiment(scenario, delay, bw, qlen, scheduler, con, dtype, count, quantum=None):

    if scheduler == "drr" and quantum is None:
        raise ValueError("quantum is not defined when scheduler is DRR")

    # process parameters for file naming
    if scenario == "b":
        scenario = "simple-p2p"
    elif scenario == "d":
        scenario = "datacenter"

    quantum_tag = ""
    if quantum is not None:
        q0, q1, q2 = quantum
        quantum_tag = f"_q{q0}-{q1}-{q2}"
    
    experiment_name = (
        f"sc-{scenario}_d{delay}_bw{bw}_ql{qlen}_sch-{scheduler}{quantum_tag}_con{con}"
    )
    logfile = f"{experiment_name}.csv"

    log_dir = os.path.join("logs", "server")
    os.makedirs(log_dir, exist_ok=True)
    host_log_path = os.path.join(log_dir, logfile)
    if os.path.exists(host_log_path):
        os.remove(host_log_path)


    print(f"\n===== running experiment {experiment_name} =====\n")

    ''' define env for docker compose '''

    ns3_scenario = (
        f"{scenario} "
        f"--delay={delay}ms "
        f"--bandwidth={bw}Mbps "
        f"--queue={qlen}"
    )
    ns3_server_params = (
        f"-scheduler {scheduler} "
        f"-shortSize {SHORT_SIZE} "
        f"-longSize {LONG_SIZE} "
        f"-logfile /logs/{logfile}"
    )
    ns3_client_params = (
        f"-ip server4:4242 "
        f"-nflows {NFLOWS} "
        f"-shortFrac {SLRATIO} "
        f"-shortSize {SHORT_SIZE} "
        f"-longSize {LONG_SIZE} "
        f"-scheduler {scheduler} "
        f"-concurrency {con} "
        f"-dataType {dtype}"
    )
    if scheduler == "drr":
        q0, q1, q2 = quantum
        ns3_client_params += f" -quantum0 {q0} -quantum1 {q1} -quantum2 {q2}"

    env = os.environ.copy()
    env["CLIENT"] = CLIENT_IMAGE
    env["SERVER"] = SERVER_IMAGE
    env["SCENARIO"] = ns3_scenario
    env["SERVER_PARAMS"] = ns3_server_params
    env["CLIENT_PARAMS"] = ns3_client_params

    subprocess.run(["docker-compose", "down", "-v"], check=False, env=env)

    if count == 1: 
        subprocess.run(
            ["docker-compose", "build", "--no-cache", "client"],
            env=env,
        )

        subprocess.run(
            ["docker-compose", "build", "--no-cache", "server"],
            env=env,
        )

    print(f"[SIMULATOR] Running experiment {count}")

    subprocess.run(
        ["docker-compose", "up", "--abort-on-container-exit"],
        check=True,
        env=env,
    )


def main():

    parser = argparse.ArgumentParser(
        description="usage help:\n"
        " 'run_grid.py --topo b' for simple bottleneck experiments\n"
        " 'run_grid.py --topo d' for datacenter experiments\n"
        " 'run_grid.py --sched drr' for schedulers (drr, wfq, abs, rr)\n"
        " 'run_grid.py --dtype threePoints' for synthetic data sample method ('threePoints' or 'logUniform')"
    )

    parser.add_argument("--topo", "-t", type=str, default="b")
    parser.add_argument("--sched", "-s", type=str, default="drr")
    parser.add_argument("--dtype", "-d", type=str, default="threePoints")
    args = parser.parse_args()

    scenario = args.topo
    scheduler = args.sched
    dtype = args.dtype

    exp_counter = 0
    
    if scheduler == "drr": # if scheduler is DRR, add quanta to grid
        for delay, bw, qlen, quantum, con in itertools.product(DELAYS, BANDWIDTHS, QUEUE_LENGTHS, QUANTUMS, CONCURRENCY):
            exp_counter += 1
            run_one_experiment(scenario, delay, bw, qlen, scheduler, con, dtype, exp_counter, quantum)
    else: # otherwise use only network parameters 
        for delay, bw, qlen, con in itertools.product(DELAYS, BANDWIDTHS, QUEUE_LENGTHS, CONCURRENCY):
            exp_counter += 1
            run_one_experiment(scenario, delay, bw, qlen, scheduler, con, dtype, exp_counter)

if __name__ == "__main__":
    main()