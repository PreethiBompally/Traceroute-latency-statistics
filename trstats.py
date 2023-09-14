import argparse
import os,re
import json,time
import numpy as np
import plotly.graph_objs as plt
import subprocess

def main():
    parser = argparse.ArgumentParser(description='Traceroute Latency Statistics')
    parser.add_argument('-n', '--num_runs', type=int, default=1, help='Number of times traceroute will run')
    parser.add_argument('-d', '--run_delay', type=int, default=0, help='Number of seconds to wait between two consecutive runs')
    parser.add_argument('-m', '--max_hops', type=int, default=30, help='Number of hops traceroute will run')
    parser.add_argument('-o', '--output', help='Path and name of output JSON file containing the stats')
    parser.add_argument('-g', '--graph', help='Path and name of output PDF file containing stats graph')
    parser.add_argument('-t','--target', required=False,help = 'A target domain name or IP address (required if --test is absent')
    parser.add_argument('--test', required=False, help='Directory containing num_runs text files with traceroute output')

    args = parser.parse_args()
    if(args.target):
        if not os.path.exists(os.getcwd()+'/test_files'):
            subprocess.run(['mkdir', os.getcwd()+'/test_files'])
        for i in range(1, args.num_runs + 1):
            command = f'traceroute -m {args.max_hops} {args.target} > {os.getcwd()}/test_files/tr_run-{i}.out'
            subprocess.run(command, shell=True)
            if i < args.num_runs:
                time.sleep(args.run_delay)
        test_dir = os.getcwd()+'/test_files'
    else:
        test_dir = args.test
    stats = []
    
    latency_pattern = r'(\d+\.\d+)\s*ms'
    hop_pattern = r'\s*(\d+)\s+'
    host_pattern = r'([A-Za-z0-9.-]+) \((\d+\.\d+\.\d+\.\d+)\)'
    avg_latencies = []
    latency_store = {}
    for hop in range(args.max_hops):
        latencies = []
        all_hosts = []
        for filename in os.listdir(test_dir):
            hosts = []
            if filename.endswith(".out") and int(filename[7:-4]) <= args.num_runs:
                with open(os.path.join(test_dir, filename), 'r') as file:
                    traceroute_output = file.read()
                    for line in traceroute_output.splitlines():
                        if(line.startswith(" "+str(hop+1)+" ") or line.startswith(str(hop+1)+" ")):
                            hop_match = re.match(hop_pattern, line)
                            latency_matches = re.findall(latency_pattern, line)
                            ip_matches = re.findall(host_pattern, line)
                           
                            if hop_match and latency_matches and ip_matches:
                                latencies.extend([float(latency) for latency in latency_matches])
                                for match in ip_matches:
                                    hosts.append(f"{match[0]}, ({match[1]})")
                                all_hosts.append(list(set(hosts)))
        if(latencies):
            latency_store[hop+1] = latencies
            stats.append({
                'avg': round(np.mean(latencies), 3),
                'hop': hop + 1,
                'hosts': all_hosts,
                'max': np.max(latencies),
                'med': round(np.median(latencies),3),
                'min': np.min(latencies)
            })
            avg_latencies.append(round(np.mean(latencies), 3))
        else:
            latency_store[hop+1] = [0 for i in range(1, 3)]
            avg_latencies.append(0)

    # Save the statistics in JSON format
    with open(args.output if args.output is not None else os.getcwd()+'/traceroute_statistics.json', 'w') as json_file:
        json.dump(stats, json_file, indent=2)

    hop_labels = [f'hop{i}' for i in range(1, args.max_hops+1)]

    box_traces = []
    fig = plt.Figure()
    for i in range(0,args.max_hops):
        box_traces.append(plt.Box(y=latency_store[i+1], name=hop_labels[i]))
    
    trace_avg = plt.Scatter(
    x=hop_labels,
    y=avg_latencies,
    mode='markers',
    marker=dict(color='black', size=6),
    name='Avg Latency'
    )
    box_traces.append(trace_avg)
    # Create a layout for the plot
    layout = plt.Layout(
        title='Latency Range Box Plot',
        xaxis=dict(title='Hops'),
        yaxis=dict(title='Latency Range')
    )

    # Create a figure and add the box traces
    fig = plt.Figure(data=box_traces, layout=layout)

    # Save the plot to a PDF file
    fig.write_image(args.graph if args.graph is not None else os.getcwd()+'/graph.pdf')

if __name__ == "__main__":
    main()