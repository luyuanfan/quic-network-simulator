# Load Balancing System Design

## 1. Priority Metadata System

In the starting stage of this project, we have two priority levels:

- **High priority**: Latency-sensitive flows
- **Low priority**: Best-effort flows

### Metadata Structure

The metadata structure contains:

- `priority`: enum { HIGH, LOW }
- `flow_size`: integer (bytes)

**Implementation**: Use INET's packet tagging mechanism to attach metadata.

## 2. Track Per-Server Load State
```
ServerState {
    activeFlows: integer
    totalBytes: integer
    ecnState: enum { GREEN, RED }
    estimatedLoad = totalBytes / timeWindow
}
```

Where:

- **Green**: No or occasional ECN marks in last T seconds
- **Red**: Frequent ECN marks (≥ 5% of packets)

## 3. Load Balancing

The load balancer first considers latency sensitivity, then considers flow size.

### Algorithm
```
IF priority == High:
    IF flow_size is elephant:
        Randomly select two GREEN servers and pick the less loaded server
    ELIF flow_size is mice:
        ECMP, if the picked server is RED, linear probe until we find a green server

ELIF priority == Low:
    IF flow_size is elephant:
        Select the least loaded server from the server state
    ELIF flow_size is small:
        ECMP
```

### Congestion Awareness

- **ECN signal**: Backend servers mark packets with ECN when queue depth > fixed threshold

## 4. Performance Metrics

To measure the effectiveness of this system, we use:

- **Latency** for high-priority flows
- **Throughput** for low-priority flows

as core metrics.
