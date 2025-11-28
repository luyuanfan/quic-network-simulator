#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "../helper/quic-network-simulator-helper.h"
#include "../helper/quic-point-to-point-helper.h"

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("ns3 leaf-spine simulator");


int main(int argc, char *argv[]) {
	// basic params
  std::string delay, bandwidth, queue;
	// leaf-spine params 
  uint32_t nLeaf  = 4;  // number of leaf switches
  uint32_t nSpine = 2;  // number of spine switches

	CommandLine cmd;
  cmd.AddValue("delay", "delay of the p2p link", delay);
  cmd.AddValue("bandwidth", "bandwidth of the p2p link", bandwidth);
  cmd.AddValue("queue", "queue size of the p2p link (in packets)", queue);
	cmd.AddValue("nLeaf",   "Number of leaf switches", nLeaf);
  cmd.AddValue("nSpine",  "Number of spine switches", nSpine);
  cmd.Parse (argc, argv);

  NS_ABORT_MSG_IF(delay.length() == 0, "Missing parameter: delay");
  NS_ABORT_MSG_IF(bandwidth.length() == 0, "Missing parameter: bandwidth");
  NS_ABORT_MSG_IF(queue.length() == 0, "Missing parameter: queue");

  QuicNetworkSimulatorHelper sim;

	// create switch nodes (leaf and spine switches)
	NodeContainer leafSwitches;
	NodeContainer spineSwitches;
	leafSwitches.Create(nLeaf);
	leafSwitches.Create(nSpine);

	// define link from any leaf to any spine with the params we gave
	QuicPointToPointHelper leafSpineLink;
	leafSpineLink.SetDeviceAttribute("DataRate", StringValue(bandwidth));
  leafSpineLink.SetChannelAttribute("Delay", StringValue(delay));
  leafSpineLink.SetQueueSize(StringValue(queue + "p"));

	// define link from any endhost to any leaf with the params we gave 
	QuicPointToPointHelper leafEndhostLink;
	leafEndhostLink.SetDeviceAttribute("DataRate", StringValue(bandwidth));
  leafEndhostLink.SetChannelAttribute("Delay", StringValue(delay));
  leafEndhostLink.SetQueueSize(StringValue(queue + "p"));

	// connect these switches together with these links
	for (uint32_t i = 0; i < leafSwitches.GetN(); i++) {
		for (uint32_t j = 0; j < spineSwitches.GetN(); j++) {
			leafSpineLink.Install(leafSwitches.Get(i), spineSwitches.Get(j));
		}
	}

	// attach quic simulator endpoints
	// the install method does: 
	//   - create a NIC on node A
	//   - create a NIC on node B
	//   - create a ethernet channel between these two nodes 
	// leftNode is this framework's client location
	// rightNode is this framework's server location 
	// we want the traffic to pass though the spine so we pick the two nodes below
	leafEndhostLink.Install(sim.GetLeftNode(), leafSwitches.Get(0));
	leafEndhostLink.Install(sim.GetRightNode(), leafSwitches.Get(nLeaf - 1));

	sim.Run(Seconds(3600));
	return 0;
}