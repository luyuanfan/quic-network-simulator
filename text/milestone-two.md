# Cloud Computing Project: Milestone Two

Link to our codebase: https://github.com/luyuanfan/cloud-project. Below is our new progress since the last milestone.

For the experiment framework, we added a single-click installer script `install.sh` that sets up the environment (assuming use of the gradx network, which has all dependencies satisfied). This scripts installs, builds, and configure OMNeT++, INET, and INET-QUIC. We also added `setenv.sh` `build.sh` `run.sh` to simplify the development pipeline. A detailed `README` that documents the workflow and perks of our set up is included. 

As a recap, our project's goal is to design a deficit round robin scheduler (`DrrScheduler`) for the QUIC protocol that collaborates with the application layer to classify traffic by type (e.g., video streaming vs. text); we also aim to implement a scheduling policy that prioritizes latency-sensitive flows (short flows over long flow) at endhosts. Below is a more thorough description of our algorithm policy and mechanism that we mapped out for this milestone. 

Our DRR algorithm classifies streams into 5 priority classes, based on their estimated flow size. Applications annotate each stream with such a priority information. Then, all streams emitted from the application layer are scheduled by our QUIC `DrrScheduler` after going into the transport layer. Inside of the scheduler, all incoming packets are enqueued and ordered in the sequence that they arrive in. As they arrive, we assign a quantum to each stream. Quantum is just an integer value that reflects priority, and it determines how many packets from this stream can be sent out when it comes to its turn. Then, streams are sent out in a FIFO fashion. 

For the actual implementation, we define our scheduler class `DrrScheduler` and created the `.h` `.cc` `.ned` files. Member vairables include:
- quantums (`int*`): how many bytes each input is allowed to send per round 
- deficits (`int*`): leftover allowance from previous rounds
- currentIndex (`int`): tracks which input queue to schedule next
- collections (`vector<IPacketCollection*>`): pointers to the actual packets in queue

Class methods are kept the same as INET's default round robin scheduler. 

For testing the scheduler, we use a simple bottleneck topology to isolate its effects, and a leaf-spine topology to inspect interactions with load balancing. Links are symmetric, with equal uplink and downlink capacities. The traffic is modeled after pFabric, with 80% of flows being short and 20% long. 

We are working on finishing up the `DrrScheduler` implementation and gather simulation analytics by the next milestone. An updated version of our project report is included below. 