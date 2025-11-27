"""
Main SDN Controller with AI Integration
Tích hợp tất cả các module: Monitor, Traffic Prediction, DQN Load Balancing, QoS
"""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import hub
from ryu.lib.packet import packet, ethernet, ipv4, tcp, udp, ether_types
from ryu.topology import event as topo_event
from ryu.topology.api import get_switch, get_link

import networkx as nx
import numpy as np
import time
import os

import sys
sys.path.append('..')

from controller.monitor import NetworkMonitor
from controller.qos_manager import QoSManager
from ai_models.traffic_predictor import TrafficPredictor
from ai_models.dqn_agent import DQNAgent
from environment.config import CONTROLLER, AI_MODELS, PATHS, TRAFFIC_CLASSIFICATION


class IntelligentSDNController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    
    def __init__(self, *args, **kwargs):
        super(IntelligentSDNController, self).__init__(*args, **kwargs)
        
        self.mac_to_port = {}
        self.datapaths = {}
        
        # Network topology graph
        self.network_graph = nx.DiGraph()
        self.topology_data = {}
        
        # Initialize modules
        self.logger.info("Initializing Intelligent SDN Controller...")
        
        # Monitor
        self.monitor = NetworkMonitor(*args, **kwargs)
        
        # QoS Manager
        self.qos_manager = QoSManager(*args, **kwargs)
        
        # AI Models
        self._init_ai_models()
        
        # Control flags
        self.ai_enabled = True
        self.qos_enabled = True
        self.load_balancing_enabled = True
        
        # Statistics
        self.packet_in_count = 0
        self.flow_installed_count = 0
        self.congestion_events = 0
        
        # Start AI decision thread
        self.ai_thread = hub.spawn(self._ai_decision_loop)
        
        self.logger.info("✓ Intelligent SDN Controller initialized successfully!")
    
    def _init_ai_models(self):
        """Initialize AI models"""
        try:
            # Traffic Predictor (LSTM)
            self.logger.info("Loading Traffic Predictor (LSTM)...")
            lstm_config = AI_MODELS['lstm']
            self.traffic_predictor = TrafficPredictor(
                sequence_length=lstm_config['sequence_length'],
                hidden_size=lstm_config['hidden_size'],
                num_layers=lstm_config['num_layers']
            )
            
            # Try to load pre-trained model
            model_path = os.path.join(PATHS['models'], 'lstm_traffic_predictor.pth')
            if os.path.exists(model_path):
                self.traffic_predictor.load_model(model_path)
                self.logger.info("✓ Pre-trained LSTM model loaded")
            else:
                self.logger.info("⚠ No pre-trained LSTM model found. Will use untrained model.")
            
            # DQN Agent for Load Balancing
            self.logger.info("Loading DQN Agent...")
            dqn_config = AI_MODELS['dqn']
            self.dqn_agent = DQNAgent(
                state_size=dqn_config['state_size'],
                action_size=dqn_config['action_size'],
                hidden_layers=dqn_config['hidden_layers']
            )
            
            # Try to load pre-trained agent
            agent_path = os.path.join(PATHS['models'], 'dqn_load_balancer.pth')
            if os.path.exists(agent_path):
                self.dqn_agent.load(agent_path)
                self.logger.info("✓ Pre-trained DQN agent loaded")
            else:
                self.logger.info("⚠ No pre-trained DQN agent found. Will use untrained agent.")
            
            self.logger.info("✓ AI models initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing AI models: {e}")
            self.ai_enabled = False
    
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """Handle switch connection"""
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        self.logger.info(f"Switch connected: {datapath.id:016x}")
        
        # Install table-miss flow entry (send to controller)
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                         ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
        
        # Configure QoS for this switch
        if self.qos_enabled:
            hub.spawn_after(2, self._configure_switch_qos, datapath.id)
    
    def _configure_switch_qos(self, dpid):
        """Configure QoS for a switch"""
        try:
            # Get switch ports (assuming 3 ports for simplicity)
            ports = [1, 2, 3]
            self.qos_manager.configure_switch_qos(dpid, ports)
        except Exception as e:
            self.logger.error(f"Error configuring QoS for switch {dpid:016x}: {e}")
    
    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        """Handle switch state changes"""
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.info(f'Register datapath: {datapath.id:016x}')
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.info(f'Unregister datapath: {datapath.id:016x}')
                del self.datapaths[datapath.id]
    
    @set_ev_cls(topo_event.EventSwitchEnter)
    def get_topology_data(self, ev):
        """Discover network topology"""
        switch_list = get_switch(self, None)
        switches = [switch.dp.id for switch in switch_list]
        
        links_list = get_link(self, None)
        links = [(link.src.dpid, link.dst.dpid, {
            'port': link.src.port_no,
            'dst_port': link.dst.port_no
        }) for link in links_list]
        
        # Build network graph
        self.network_graph.clear()
        self.network_graph.add_nodes_from(switches)
        self.network_graph.add_edges_from(links)
        
        self.logger.info(f"Topology discovered: {len(switches)} switches, {len(links)} links")
    
    def add_flow(self, datapath, priority, match, actions, buffer_id=None, idle_timeout=0, hard_timeout=0):
        """Add flow entry to switch"""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                   priority=priority, match=match,
                                   instructions=inst,
                                   idle_timeout=idle_timeout,
                                   hard_timeout=hard_timeout)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                   match=match, instructions=inst,
                                   idle_timeout=idle_timeout,
                                   hard_timeout=hard_timeout)
        
        datapath.send_msg(mod)
        self.flow_installed_count += 1
    
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """Handle PacketIn messages"""
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # Ignore LLDP packets
            return
        
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        
        self.packet_in_count += 1
        
        # Learn MAC address
        self.mac_to_port[dpid][eth.src] = in_port
        
        # Determine output port
        if eth.dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][eth.dst]
        else:
            out_port = ofproto.OFPP_FLOOD
        
        actions = [parser.OFPActionOutput(out_port)]
        
        # Install flow if destination is known
        if out_port != ofproto.OFPP_FLOOD:
            # Check if this is an elephant flow
            if self._is_elephant_flow(pkt):
                self.logger.info(f"Elephant flow detected: {eth.src} -> {eth.dst}")
                
                # Use AI load balancing if enabled
                if self.load_balancing_enabled and self.ai_enabled:
                    out_port = self._ai_route_selection(datapath, eth.src, eth.dst, in_port)
                    actions = [parser.OFPActionOutput(out_port)]
            
            # Apply QoS if enabled
            if self.qos_enabled:
                qos_class = self.qos_manager.classify_traffic(pkt)
                queue_id = self.qos_manager.get_queue_id_for_class(qos_class)
                
                # Add queue action
                actions.insert(0, parser.OFPActionSetQueue(queue_id))
                
                self.logger.debug(f"QoS applied: class={qos_class}, queue={queue_id}")
            
            match = parser.OFPMatch(in_port=in_port, eth_dst=eth.dst, eth_src=eth.src)
            
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id,
                            idle_timeout=CONTROLLER['flow_idle_timeout'])
                return
            else:
                self.add_flow(datapath, 1, match, actions,
                            idle_timeout=CONTROLLER['flow_idle_timeout'])
        
        # Send packet out
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                 in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
    
    def _is_elephant_flow(self, pkt):
        """Determine if flow is an elephant flow"""
        # Simplified detection - in practice, track flow statistics
        # Here we check packet size as a heuristic
        eth = pkt.get_protocol(ethernet.ethernet)
        
        # Check if it's a TCP flow (more likely to be elephant)
        tcp_pkt = pkt.get_protocol(tcp.tcp)
        if tcp_pkt:
            # Check for typical elephant flow ports (file transfer, etc.)
            if tcp_pkt.dst_port in [20, 21, 22, 873, 3306]:  # FTP, SSH, rsync, MySQL
                return True
        
        return False
    
    def _ai_route_selection(self, datapath, src_mac, dst_mac, in_port):
        """Use DQN agent to select optimal route"""
        try:
            # Get current network state
            network_state = self.monitor.get_network_state()
            utilization = self.monitor.get_bandwidth_utilization()
            
            # Convert to state vector for DQN
            state_vector = self._build_state_vector(network_state, utilization)
            
            # Get action from DQN agent
            action = self.dqn_agent.select_action(state_vector, training=False)
            
            # Map action to output port (simplified)
            # In practice, action represents path selection
            # Here we use a simple mapping
            available_ports = [1, 2, 3]
            if action < len(available_ports):
                out_port = available_ports[action]
            else:
                out_port = available_ports[0]
            
            self.logger.info(f"AI routing decision: port {out_port} (action {action})")
            
            return out_port
            
        except Exception as e:
            self.logger.error(f"Error in AI route selection: {e}")
            return 1  # Fallback to default port
    
    def _build_state_vector(self, network_state, utilization):
        """Build state vector for DQN from network state"""
        state_vector = []
        
        # Add link utilizations
        for dpid, ports in utilization.items():
            for port_no, util in ports.items():
                state_vector.append(util['avg_utilization'])
        
        # Pad or truncate to match DQN state size
        state_size = AI_MODELS['dqn']['state_size']
        while len(state_vector) < state_size:
            state_vector.append(0.0)
        
        return np.array(state_vector[:state_size], dtype=np.float32)
    
    def _ai_decision_loop(self):
        """AI decision loop running in background"""
        while True:
            try:
                hub.sleep(10)  # Run every 10 seconds
                
                if not self.ai_enabled:
                    continue
                
                # Get current network state
                network_state = self.monitor.get_network_state()
                
                # Get traffic data for prediction
                traffic_data = self.monitor.get_traffic_data_for_prediction()
                
                if len(traffic_data) >= 10:
                    # Predict future congestion
                    sequence = traffic_data[-10:]
                    congestion_info = self.traffic_predictor.detect_congestion(
                        sequence, threshold=80.0
                    )
                    
                    if congestion_info['congestion_detected']:
                        self.logger.warning(
                            f"⚠ Congestion predicted! "
                            f"Max utilization will reach {congestion_info['max_predicted_utilization']:.1f}%"
                        )
                        self.congestion_events += 1
                        
                        # Take proactive action (e.g., reroute flows)
                        self._handle_predicted_congestion(congestion_info)
                
            except Exception as e:
                self.logger.error(f"Error in AI decision loop: {e}")
    
    def _handle_predicted_congestion(self, congestion_info):
        """Handle predicted congestion proactively"""
        self.logger.info("Taking proactive action for predicted congestion...")
        
        # Get elephant flows
        elephant_flows = self.monitor.get_elephant_flows()
        
        # Reroute elephant flows to alternate paths
        for flow in elephant_flows[:3]:  # Reroute top 3 elephant flows
            self.logger.info(f"Rerouting elephant flow: {flow['byte_count']} bytes")
            # In practice, compute alternate path and install new flows
    
    def get_statistics(self):
        """Get controller statistics"""
        return {
            'packet_in_count': self.packet_in_count,
            'flow_installed_count': self.flow_installed_count,
            'congestion_events': self.congestion_events,
            'active_switches': len(self.datapaths),
            'ai_enabled': self.ai_enabled,
            'qos_enabled': self.qos_enabled,
            'load_balancing_enabled': self.load_balancing_enabled
        }
    
    def print_statistics(self):
        """Print controller statistics"""
        stats = self.get_statistics()
        
        self.logger.info("="*60)
        self.logger.info("Controller Statistics:")
        self.logger.info(f"  Packet-In processed: {stats['packet_in_count']}")
        self.logger.info(f"  Flows installed: {stats['flow_installed_count']}")
        self.logger.info(f"  Congestion events detected: {stats['congestion_events']}")
        self.logger.info(f"  Active switches: {stats['active_switches']}")
        self.logger.info(f"  AI enabled: {stats['ai_enabled']}")
        self.logger.info(f"  QoS enabled: {stats['qos_enabled']}")
        self.logger.info(f"  Load balancing enabled: {stats['load_balancing_enabled']}")
        self.logger.info("="*60)


# For standalone testing
if __name__ == "__main__":
    from ryu.cmd import manager
    
    print("""
╔════════════════════════════════════════════════════════════╗
║     Intelligent SDN Controller with AI Integration         ║
║  - Traffic Prediction (LSTM)                               ║
║  - Load Balancing (Deep Q-Network)                         ║
║  - QoS Optimization                                        ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    manager.main()
