#!/bin/python3

import sys
import os
import math
import datetime
import re
from statistics import mean
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from collections import defaultdict


def print_usage():
    print("Incorrect usage")
    print("arg1: path/to/data_dir")


def parse_log(log: str):
    latency = {}
    throughput = {}

    blocks = re.split(r"\n(?=TIME:)", log)
    for block in blocks:
        t_match = re.search(r"TIME:\s*(\d+)", block)
        if not t_match:
            continue
        ts = int(t_match.group(1))

        # throughput: iperf sender summary only
        thr_match = re.search(
            r"\.*(\d+\.?\d+)\s+([KM]bits)\/sec\s+receiver",
            block,
        )
        if thr_match:
            if thr_match.group(2) == "Kbits":
                throughput[ts] = float(thr_match.group(1))
            elif thr_match.group(2) == "Mbits":
                throughput[ts] = float(thr_match.group(1)) * 1024
            else:
                print(
                    f"Found unkown uni while parsing throughput: {thr_match.group(2)}"
                )

        # latency: average RTT from hping results
        rtts = [float(x) for x in re.findall(r"rtt=([\d.]+)\s*ms", block)]
        if rtts:
            latency[ts] = mean(rtts)

    return {
        "latency": latency,  # time -> avg RTT (ms)
        "throughput": throughput,  # time -> Mbits/sec
    }


def avg_metrics_by_app(data: dict) -> dict:
    """
    Returns:
    {
      "app-X": {
         "latency": <average across all clients & machines>,
         "throughput": <average across all clients & machines>,
         "clients": <number of unique clients>
      },
      ...
    }
    """
    sums = defaultdict(
        lambda: {
            "latency": 0.0,
            "throughput": 0.0,
            "lat_count": 0,
            "thr_count": 0,
            "clients": 0,
        }
    )

    for machine in data.values():
        for app, app_data in machine.items():
            clients = (app_data or {}).get("clients", {})
            sums[app]["clients"] += len(clients)

            for client in clients.values():
                lat = client.get("latency", {})
                thr = client.get("throughput", {})

                sums[app]["latency"] += sum(lat.values())
                sums[app]["lat_count"] += len(lat)

                sums[app]["throughput"] += sum(thr.values())
                sums[app]["thr_count"] += len(thr)

    out = {}
    for app, s in sums.items():
        out[app] = {
            "latency": (s["latency"] / s["lat_count"]) if s["lat_count"] else None,
            "throughput": (s["throughput"] / s["thr_count"])
            if s["thr_count"]
            else None,
            "clients": s["clients"],
        }

    return out


def plot_app_metrics(app_metrics: dict, save_to_path: str):
    apps = list(app_metrics.keys())
    latencies = [app_metrics[a]["latency"] for a in apps]
    throughputs = [app_metrics[a]["throughput"] for a in apps]

    x = range(len(apps))
    width = 0.35

    plt.figure()
    plt.bar([i - width / 2 for i in x], latencies, width=width, label="Latency")
    plt.bar([i + width / 2 for i in x], throughputs, width=width, label="Throughput")

    plt.xticks(x, apps, rotation=45)
    plt.ylabel("Average Value")
    plt.title("Average Latency and Throughput per App")
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_to_path, dpi=200)
    plt.close()


def plot_machine_metrics(data_dir, save_to_path):
    machines = list(data_dir.keys())

    fig, axes = plt.subplots(
        len(machines), 1, sharex=True, figsize=(12, 4 * len(machines))
    )
    COLORS = [
        "tab:blue",
        "tab:orange",
        "tab:green",
        "tab:red",
        "tab:purple",
        "tab:brown",
        "tab:pink",
        "tab:gray",
        "tab:olive",
        "tab:cyan",
    ]

    def app_color(app_name):
        # extract number from "app-X"
        n = int(re.search(r"\d+", app_name).group())
        return COLORS[n % len(COLORS)]

    if len(machines) == 1:
        axes = [axes]

    for ax, machine in zip(axes, machines):
        ax2 = ax.twinx()

        for app, app_data in data_dir[machine].items():
            clients = app_data.get("clients")
            if not clients:
                continue
            for client in clients:
                client_data = clients[client]
                lat = client_data.get("latency", {})
                thr = client_data.get("throughput", {})
                color = app_color(app)

                if lat:
                    x, y = zip(*sorted(lat.items()))
                    x = [datetime.datetime.fromtimestamp(t) for t in x]
                    ax.plot(
                        x, y, color=color, marker="o", label=f"{app}-{client} latency"
                    )

                if thr:
                    x, y = zip(*sorted(thr.items()))
                    x = [datetime.datetime.fromtimestamp(t) for t in x]
                    ax2.plot(
                        x,
                        y,
                        color=color,
                        linestyle="--",
                        marker="x",
                        label=f"{app}-{client} throughput",
                    )

        ax.set_ylabel("Latency (ms)")
        ax.set_ylim(1, max_rtt)
        ax.set_yscale("log")
        ax2.set_ylabel("Throughput (Kbit/s)")
        ax2.set_ylim(0, 1100)
        ax.set_title(machine)
        ax.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.5)
        ax2.grid(False)

        lines, labels = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines + lines2, labels + labels2, loc="upper left")
        ax.set_xlim(start_time, end_time)

    axes[-1].set_xlabel("Time")
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    plt.tight_layout()
    plt.savefig(save_to_path, dpi=200)
    plt.close()


def avg_across_apps(app_metrics: dict) -> dict:
    """
    Weighted by number of clients per app.

    Expects:
    {
      "app-X": {
         "latency": <avg>,
         "throughput": <avg>,
         "clients": <num_clients>
      },
      ...
    }

    Returns:
    {
      "latency": <weighted average>,
      "throughput": <weighted average>
    }
    """
    total_lat = 0.0
    total_thr = 0.0
    total_clients = 0

    for m in app_metrics.values():
        c = m.get("clients", 0) or 0
        if c <= 0:
            continue

        total_lat += (m.get("latency", 0.0) or 0.0) * c
        total_thr += (m.get("throughput", 0.0) or 0.0) * c
        total_clients += c

    if total_clients == 0:
        return {"latency": None, "throughput": None}

    return {
        "latency": total_lat / total_clients,
        "throughput": total_thr / total_clients,
    }


if len(sys.argv) < 2:
    print_usage()
    exit(1)

data_dir = os.fsencode(sys.argv[1])
start_time = math.inf
end_time = 0
max_rtt = 0

structured_data_by_machines = {}

# Find start and end times
# Iterate over all manager/worker files which contains app logs and find the earliest and latest timestamps
# Also parse the logfiles
for file in os.listdir(data_dir):
    filename = os.fsdecode(file)
    if not (filename.startswith("manager") or filename.startswith("worker")):
        continue
    if not filename.split("#")[1].startswith("app"):
        continue
    # For now, only investigate the client logfiles
    if "client" not in filename:
        continue
    with open(os.fsdecode(data_dir) + "/" + filename) as file_content:
        file_content = list(file_content)
        log_data = parse_log("\n".join(file_content))
        machine = filename.split("#")[0]
        if machine not in structured_data_by_machines:
            structured_data_by_machines[machine] = {}
        app = "app-" + filename.split("#")[1].split("-")[1]
        if app not in structured_data_by_machines[machine]:
            structured_data_by_machines[machine][app] = {"clients": {}, "server": None}
        structured_data_by_machines[machine][app]["clients"][
            filename.split("-")[-1].split(".")[0]
        ] = log_data

        for line in file_content:
            if line.startswith("TIME"):
                TIME = int(line.split(" ")[1])
                if TIME < start_time:
                    start_time = TIME
                elif TIME > end_time:
                    end_time = TIME
            # Find max delay
            elif "rtt=" in line:
                rtt = float(line.split("rtt=")[1].split(" ")[0])
                if rtt > max_rtt:
                    max_rtt = rtt


start_time = datetime.datetime.fromtimestamp(start_time)
end_time = datetime.datetime.fromtimestamp(end_time)
print(f"start time: {start_time}")
print(f"end time: {end_time}")

plot_machine_metrics(
    structured_data_by_machines, data_dir.decode() + "/../results/network_metrics.png"
)
plot_app_metrics(
    avg_metrics_by_app(structured_data_by_machines),
    data_dir.decode() + "/../results/app_metrics.png",
)
print(avg_across_apps(avg_metrics_by_app(structured_data_by_machines)))
