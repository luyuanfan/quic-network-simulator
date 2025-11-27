# Implementing a pFabric-inspired scheduler in QUIC

## Main idea

We recognizes that datacenter workloads are dominated by large numbers of short flows. These flows are more latency sensitive than long flows (e.g., google drive backup) because they tend to belong to more interactive tasks (e.g., a single webpage request). Therefore, reducing the flow completion time (FCT) of short flow is essential to improving overall application responsiveness and datacenter performance.

To achieve this, we want to bring pFabric's scheduling logic into QUIC: a priority-based scheduling and dropping mechanism implemented at each switch on the network. **Instead of focusing on flow scheduling, we focus on stream scheduling.**

## Priority assessment

Priority is high when the value is small. 
We directly use flow size as the priority value. Larger flow size gets larger priority value. 

## Priority Metadata System

The metadata contains:
- stream_id (integer): steam identifier
- flow_size (integer): size of flow in bytes

We use INET's packet tagging mechanism to attach metadata.

## Pseudocode
The scheduling and dropping mechanism at switches is described as follows:

### Enqueueing
```
when a new packet p arrives at a switch
    if the buffer is not full {
        queue.append(p)
    }
    if the buffer is full {
        if p->priority is lower than all buffered packets {
            drop p
        }
        if p->priority is higher than all buffered packets {
            lowest_priority_packet = packet with largest priority value
            queue.drop(lowest_priority_packet)
            queue.append(p)
        }
    }
```

### Dequeueing
```
when switch is ready to dequeue a packet p:

    flow_id = p.flow_id

    highest_priority_packet = packet with smallest priority value
    target_flow = highest_priority_packet.flow_id

    # starvation prevention
    # among all packets from the same flow, pick the earliest one
    earliest_packet_in_flow = earliest arrived packet with flow_id == target_flow

    send out earliest_packet_in_flow
    remove earliest_packet_in_flow from queue 
```

## Topology

Leaf-spine topology. Each leaf switch has 16 10Gbps downlinks to hosts and 4 40Gbps uplinks to the spine. Full mesh where each leaf connects to every spine switch, so there's full connectivity and multiple equal paths.

We chose this topology because it is a commonly used datacenter topology according to pFabric paper and the one they used for simulations. 

> We use the leaf-spine topology shown in Fig- ure 3. This is a commonly used datacenter topology. The fabric interconnects 144 hosts through 9 leaf (or top-of-rack) switches connected to 4 spine switches in a full mesh. Each leaf switch has 16 10Gbps downlinks (to the hosts) and 4 40Gbps uplinks (to the spine) resulting in a non-oversubscribed (full bisection bandwidth) fabric. The end-to-end round-trip latency across the spine (4 hops) is ∼14.6μs of which 10μs is spent in the hosts (the round-trip la- tency across 2 hops under a Leaf is ∼13.3μs).

## Load balancing

Packet spraying or ECMP depending on which one has an INET implementation. 

## Performance metrics

- TCP
- Throughput

## Schemes compared

- vanilla QUIC