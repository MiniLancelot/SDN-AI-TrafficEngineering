"""
QoS Manager - Quản lý Quality of Service động
Cấu hình Queues, Meters và áp dụng chính sách QoS
"""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, tcp, udp, ether_types
import subprocess
import json

import sys
sys.path.append('..')
from environment.config import QOS, TRAFFIC_CLASSIFICATION


class QoSManager(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    
    def __init__(self, *args, **kwargs):
        super(QoSManager, self).__init__(*args, **kwargs)
        
        self.qos_config = QOS
        self.traffic_classes = QOS['classes']
        
        # Track configured switches and ports
        self.configured_switches = set()
        self.configured_ports = {}  # {(dpid, port): qos_id}
        
        # Meter tables for rate limiting
        self.meters = {}  # {dpid: {meter_id: config}}
        self.next_meter_id = {}  # {dpid: next_available_meter_id}
        
        # Flow to QoS class mapping
        self.flow_qos_mapping = {}  # {flow_key: qos_class}
        
        self.logger.info("QoS Manager initialized")
    
    def configure_switch_qos(self, dpid, ports):
        """
        Configure QoS for a switch
        Args:
            dpid: datapath ID
            ports: list of port numbers to configure
        """
        self.logger.info(f"Configuring QoS for switch {dpid:016x}")
        
        for port in ports:
            self._configure_port_queues(dpid, port)
        
        self.configured_switches.add(dpid)
    
    def _configure_port_queues(self, dpid, port):
        """
        Configure queues for a port using ovs-vsctl
        Args:
            dpid: datapath ID
            port: port number
        """
        switch_name = f"s{dpid}"  # Assuming Mininet naming convention
        port_name = f"{switch_name}-eth{port}"
        
        try:
            # Create QoS configuration
            qos_config = self.qos_config['queue_config']
            max_rate = qos_config['max_rate']
            
            # Build ovs-vsctl command to create QoS and queues
            # Priority queue (Queue 0) - VoIP/Control
            # Guaranteed bandwidth queue (Queue 1) - Video
            # Standard queue (Queue 2) - Web
            # Best effort queue (Queue 3) - File transfer
            
            cmd = [
                'ovs-vsctl', 'set', 'port', port_name, 'qos=@newqos', '--',
                '--id=@newqos', 'create', 'qos', f'type={qos_config["type"]}',
                f'other-config:max-rate={max_rate}',
                'queues=0=@q0,1=@q1,2=@q2,3=@q3', '--',
                '--id=@q0', 'create', 'queue',
                'other-config:min-rate=1000000',  # VoIP: 1 Mbps min
                'other-config:priority=100', '--',
                '--id=@q1', 'create', 'queue',
                'other-config:min-rate=5000000',  # Video: 5 Mbps min
                'other-config:priority=80', '--',
                '--id=@q2', 'create', 'queue',
                'other-config:min-rate=2000000',  # Web: 2 Mbps min
                'other-config:priority=50', '--',
                '--id=@q3', 'create', 'queue',
                'other-config:priority=10'  # Best effort: lowest priority
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.configured_ports[(dpid, port)] = True
                self.logger.info(f"QoS configured for {port_name}")
            else:
                self.logger.error(f"Failed to configure QoS for {port_name}: {result.stderr}")
        
        except Exception as e:
            self.logger.error(f"Error configuring queues: {e}")
    
    def classify_traffic(self, pkt):
        """
        Classify traffic based on packet characteristics
        Args:
            pkt: parsed packet
        Returns:
            QoS class name
        """
        eth = pkt.get_protocol(ethernet.ethernet)
        
        # Check IP packet
        if eth.ethertype == ether_types.ETH_TYPE_IP:
            ip = pkt.get_protocol(ipv4.ipv4)
            
            if ip:
                # Check TCP/UDP ports for application identification
                tcp_pkt = pkt.get_protocol(tcp.tcp)
                udp_pkt = pkt.get_protocol(udp.udp)
                
                if tcp_pkt:
                    dst_port = tcp_pkt.dst_port
                    
                    # HTTP/HTTPS - Web traffic
                    if dst_port in [80, 443, 8080]:
                        return 'web'
                    # FTP/SSH - File transfer
                    elif dst_port in [20, 21, 22]:
                        return 'best_effort'
                    # Database
                    elif dst_port in [3306, 5432, 27017]:
                        return 'web'
                
                elif udp_pkt:
                    dst_port = udp_pkt.dst_port
                    
                    # VoIP (SIP, RTP)
                    if dst_port in range(5060, 5065) or dst_port in range(10000, 20000):
                        return 'voip'
                    # DNS
                    elif dst_port == 53:
                        return 'web'
                    # Video streaming (RTSP, etc.)
                    elif dst_port in [554, 1935]:
                        return 'video'
        
        # Default to best effort
        return 'best_effort'
    
    def get_queue_id_for_class(self, qos_class):
        """
        Get queue ID for a QoS class
        Args:
            qos_class: QoS class name
        Returns:
            queue ID
        """
        if qos_class in self.traffic_classes:
            return self.traffic_classes[qos_class]['queue_id']
        return 3  # Default to best effort queue
    
    def install_qos_flow(self, datapath, match, queue_id, priority=1):
        """
        Install flow entry with QoS (queue assignment)
        Args:
            datapath: switch datapath
            match: OpenFlow match
            queue_id: queue ID to use
            priority: flow priority
        """
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # Actions: set queue and output to port
        actions = [
            parser.OFPActionSetQueue(queue_id),
            parser.OFPActionOutput(ofproto.OFPP_NORMAL)
        ]
        
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        
        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=inst,
            idle_timeout=30,
            hard_timeout=0
        )
        
        datapath.send_msg(mod)
        self.logger.info(f"QoS flow installed on switch {datapath.id:016x} with queue {queue_id}")
    
    def add_meter(self, datapath, meter_id, rate_kbps, burst_size_kb=100):
        """
        Add meter entry for rate limiting
        Args:
            datapath: switch datapath
            meter_id: meter ID
            rate_kbps: rate limit in Kbps
            burst_size_kb: burst size in Kb
        """
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # Create meter bands
        bands = [
            parser.OFPMeterBandDrop(
                rate=rate_kbps,
                burst_size=burst_size_kb
            )
        ]
        
        # Create meter mod message
        req = parser.OFPMeterMod(
            datapath=datapath,
            command=ofproto.OFPMC_ADD,
            flags=ofproto.OFPMF_KBPS,
            meter_id=meter_id,
            bands=bands
        )
        
        datapath.send_msg(req)
        
        # Track meter
        dpid = datapath.id
        if dpid not in self.meters:
            self.meters[dpid] = {}
        
        self.meters[dpid][meter_id] = {
            'rate_kbps': rate_kbps,
            'burst_size_kb': burst_size_kb
        }
        
        self.logger.info(f"Meter {meter_id} added to switch {dpid:016x}: {rate_kbps} Kbps")
    
    def install_flow_with_meter(self, datapath, match, meter_id, out_port, priority=1):
        """
        Install flow with meter (rate limiting)
        Args:
            datapath: switch datapath
            match: OpenFlow match
            meter_id: meter ID
            out_port: output port
            priority: flow priority
        """
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # Instructions: apply meter, then output
        inst = [
            parser.OFPInstructionMeter(meter_id),
            parser.OFPInstructionActions(
                ofproto.OFPIT_APPLY_ACTIONS,
                [parser.OFPActionOutput(out_port)]
            )
        ]
        
        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=inst,
            idle_timeout=30,
            hard_timeout=0
        )
        
        datapath.send_msg(mod)
        self.logger.info(f"Flow with meter {meter_id} installed on switch {datapath.id:016x}")
    
    def get_next_meter_id(self, dpid):
        """Get next available meter ID for a switch"""
        if dpid not in self.next_meter_id:
            self.next_meter_id[dpid] = 1
        
        meter_id = self.next_meter_id[dpid]
        self.next_meter_id[dpid] += 1
        return meter_id
    
    def apply_qos_policy(self, datapath, pkt_in, pkt):
        """
        Apply QoS policy to incoming packet
        Args:
            datapath: switch datapath
            pkt_in: PacketIn message
            pkt: parsed packet
        """
        # Classify traffic
        qos_class = self.classify_traffic(pkt)
        
        # Get appropriate queue
        queue_id = self.get_queue_id_for_class(qos_class)
        
        # Extract match fields
        eth = pkt.get_protocol(ethernet.ethernet)
        
        parser = datapath.ofproto_parser
        match = parser.OFPMatch(
            in_port=pkt_in.match['in_port'],
            eth_dst=eth.dst,
            eth_src=eth.src
        )
        
        # Install flow with QoS
        self.install_qos_flow(datapath, match, queue_id, priority=10)
        
        self.logger.info(f"Applied QoS policy: class={qos_class}, queue={queue_id}")
    
    def limit_flow_rate(self, datapath, match, rate_limit_kbps, out_port):
        """
        Apply rate limiting to a flow (e.g., for DDoS mitigation)
        Args:
            datapath: switch datapath
            match: flow match
            rate_limit_kbps: rate limit in Kbps
            out_port: output port
        """
        # Get next meter ID
        meter_id = self.get_next_meter_id(datapath.id)
        
        # Add meter
        self.add_meter(datapath, meter_id, rate_limit_kbps)
        
        # Install flow with meter
        self.install_flow_with_meter(datapath, match, meter_id, out_port, priority=100)
        
        self.logger.warning(f"Rate limiting applied: {rate_limit_kbps} Kbps")
    
    def get_qos_statistics(self, dpid):
        """
        Get QoS statistics for a switch
        Args:
            dpid: datapath ID
        Returns:
            dict with QoS stats
        """
        switch_name = f"s{dpid}"
        
        try:
            # Get queue statistics using ovs-ofctl
            cmd = ['ovs-ofctl', 'dump-queues', switch_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return {
                    'dpid': dpid,
                    'output': result.stdout,
                    'configured': (dpid in self.configured_switches)
                }
            else:
                self.logger.error(f"Failed to get QoS stats: {result.stderr}")
                return None
        
        except Exception as e:
            self.logger.error(f"Error getting QoS statistics: {e}")
            return None


def setup_qos_for_mininet(controller_ip='127.0.0.1', controller_port=6633):
    """
    Helper function to setup QoS in Mininet environment
    Call this after starting Mininet topology
    """
    import time
    
    print("Setting up QoS for Mininet switches...")
    
    # Wait for switches to connect
    time.sleep(2)
    
    # Configure QoS for switches s1, s2, s3, s4
    for switch_id in range(1, 5):
        switch_name = f"s{switch_id}"
        
        # Configure QoS on ports 1, 2, 3
        for port in range(1, 4):
            port_name = f"{switch_name}-eth{port}"
            
            cmd = [
                'ovs-vsctl', 'set', 'port', port_name, 'qos=@newqos', '--',
                '--id=@newqos', 'create', 'qos', 'type=linux-htb',
                'other-config:max-rate=10000000',
                'queues=0=@q0,1=@q1,2=@q2,3=@q3', '--',
                '--id=@q0', 'create', 'queue', 'other-config:min-rate=1000000', '--',
                '--id=@q1', 'create', 'queue', 'other-config:min-rate=5000000', '--',
                '--id=@q2', 'create', 'queue', 'other-config:min-rate=2000000', '--',
                '--id=@q3', 'create', 'queue'
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✓ QoS configured for {port_name}")
                else:
                    print(f"✗ Failed to configure {port_name}: {result.stderr}")
            except Exception as e:
                print(f"✗ Error configuring {port_name}: {e}")
    
    print("QoS setup completed!")


if __name__ == "__main__":
    # Example: Setup QoS for Mininet
    # Run this after starting your Mininet topology
    setup_qos_for_mininet()
