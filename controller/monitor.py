"""
Network Monitor - Thu thập dữ liệu traffic từ OpenFlow switches
Thực hiện thu thập port statistics, flow statistics và đo độ trễ
"""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import hub
from ryu.lib.packet import packet, ethernet, ipv4, tcp, udp

import time
import json
import csv
import os
from datetime import datetime
from collections import defaultdict

import sys
sys.path.append('..')
from environment.config import DATA_COLLECTION, CONTROLLER


class NetworkMonitor(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(NetworkMonitor, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)
        
        # Data structures for statistics
        self.port_stats = {}  # {dpid: {port_no: stats}}
        self.flow_stats = {}  # {dpid: [flow_entries]}
        self.port_speed = {}  # {dpid: {port_no: (tx_bytes, rx_bytes, timestamp)}}
        self.link_latency = {}  # {(src_dpid, dst_dpid): latency}
        
        # Traffic matrix
        self.traffic_matrix = defaultdict(lambda: defaultdict(int))
        
        # Flow tracking for elephant flow detection
        self.flow_records = {}  # {flow_key: {'bytes': x, 'packets': y, 'start_time': t}}
        
        # Data collection configuration
        self.save_to_file = DATA_COLLECTION['save_to_file']
        self.save_interval = DATA_COLLECTION['save_interval']
        self.data_dir = DATA_COLLECTION['data_directory']
        self.monitoring_interval = CONTROLLER['monitoring_interval']
        
        # Create data directory if not exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.logger.info("Network Monitor initialized")

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        """Handle switch connection/disconnection"""
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.info('Register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.info('Unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _monitor(self):
        """Main monitoring loop"""
        last_save_time = time.time()
        
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            
            hub.sleep(self.monitoring_interval)
            
            # Periodically save data to file
            if self.save_to_file:
                current_time = time.time()
                if current_time - last_save_time >= self.save_interval:
                    self._save_statistics()
                    last_save_time = current_time

    def _request_stats(self, datapath):
        """Request statistics from a switch"""
        self.logger.debug('Send stats request to datapath: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Request port statistics
        if DATA_COLLECTION['enable_port_stats']:
            req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
            datapath.send_msg(req)

        # Request flow statistics
        if DATA_COLLECTION['enable_flow_stats']:
            req = parser.OFPFlowStatsRequest(datapath)
            datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        """Handle port statistics reply"""
        body = ev.msg.body
        dpid = ev.msg.datapath.id
        
        self.logger.debug('PortStats received from datapath: %016x', dpid)
        
        if dpid not in self.port_stats:
            self.port_stats[dpid] = {}
        
        current_time = time.time()
        
        for stat in sorted(body, key=lambda x: x.port_no):
            port_no = stat.port_no
            
            # Calculate bandwidth utilization
            if dpid in self.port_speed and port_no in self.port_speed[dpid]:
                old_tx, old_rx, old_time = self.port_speed[dpid][port_no]
                time_diff = current_time - old_time
                
                if time_diff > 0:
                    tx_speed = (stat.tx_bytes - old_tx) * 8 / time_diff / 1000000  # Mbps
                    rx_speed = (stat.rx_bytes - old_rx) * 8 / time_diff / 1000000  # Mbps
                    
                    self.port_stats[dpid][port_no] = {
                        'tx_bytes': stat.tx_bytes,
                        'rx_bytes': stat.rx_bytes,
                        'tx_packets': stat.tx_packets,
                        'rx_packets': stat.rx_packets,
                        'tx_errors': stat.tx_errors,
                        'rx_errors': stat.rx_errors,
                        'tx_dropped': stat.tx_dropped,
                        'rx_dropped': stat.rx_dropped,
                        'tx_speed_mbps': tx_speed,
                        'rx_speed_mbps': rx_speed,
                        'timestamp': current_time
                    }
                    
                    self.logger.info('Port %s of Switch %016x: TX %.2f Mbps, RX %.2f Mbps',
                                   port_no, dpid, tx_speed, rx_speed)
            
            # Update speed tracking
            if dpid not in self.port_speed:
                self.port_speed[dpid] = {}
            self.port_speed[dpid][port_no] = (stat.tx_bytes, stat.rx_bytes, current_time)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        """Handle flow statistics reply"""
        body = ev.msg.body
        dpid = ev.msg.datapath.id
        
        self.logger.debug('FlowStats received from datapath: %016x', dpid)
        
        flows = []
        for stat in sorted([flow for flow in body if flow.priority == 1],
                          key=lambda flow: (flow.match.get('in_port', 0),
                                          flow.match.get('eth_dst', '0'))):
            
            flow_info = {
                'dpid': dpid,
                'table_id': stat.table_id,
                'duration_sec': stat.duration_sec,
                'priority': stat.priority,
                'idle_timeout': stat.idle_timeout,
                'hard_timeout': stat.hard_timeout,
                'packet_count': stat.packet_count,
                'byte_count': stat.byte_count,
                'match': stat.match,
                'instructions': stat.instructions,
                'timestamp': time.time()
            }
            
            flows.append(flow_info)
            
            # Detect elephant flows
            if stat.byte_count > 1000000:  # > 1MB
                self.logger.warning('Elephant flow detected on switch %016x: %d bytes',
                                  dpid, stat.byte_count)
        
        self.flow_stats[dpid] = flows

    def get_network_state(self):
        """
        Get current network state for AI models
        Returns: dictionary with network statistics
        """
        state = {
            'timestamp': time.time(),
            'datapaths': list(self.datapaths.keys()),
            'port_stats': self.port_stats,
            'flow_stats': self.flow_stats,
            'traffic_matrix': dict(self.traffic_matrix),
            'link_latency': self.link_latency
        }
        return state

    def get_bandwidth_utilization(self):
        """
        Calculate bandwidth utilization for all links
        Returns: dict {dpid: {port: utilization_percentage}}
        """
        utilization = {}
        
        for dpid, ports in self.port_stats.items():
            utilization[dpid] = {}
            for port_no, stats in ports.items():
                if 'tx_speed_mbps' in stats and 'rx_speed_mbps' in stats:
                    # Assume 10 Mbps link capacity (configurable)
                    link_capacity = 10.0
                    tx_util = (stats['tx_speed_mbps'] / link_capacity) * 100
                    rx_util = (stats['rx_speed_mbps'] / link_capacity) * 100
                    utilization[dpid][port_no] = {
                        'tx_utilization': tx_util,
                        'rx_utilization': rx_util,
                        'avg_utilization': (tx_util + rx_util) / 2
                    }
        
        return utilization

    def get_elephant_flows(self, threshold_bytes=1000000):
        """
        Identify elephant flows (flows with large byte counts)
        Args:
            threshold_bytes: minimum bytes to be considered elephant flow
        Returns: list of elephant flows
        """
        elephant_flows = []
        
        for dpid, flows in self.flow_stats.items():
            for flow in flows:
                if flow['byte_count'] >= threshold_bytes:
                    elephant_flows.append({
                        'dpid': dpid,
                        'match': flow['match'],
                        'byte_count': flow['byte_count'],
                        'packet_count': flow['packet_count'],
                        'duration': flow['duration_sec']
                    })
        
        return elephant_flows

    def _save_statistics(self):
        """Save collected statistics to CSV files"""
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save port statistics
        port_stats_file = os.path.join(self.data_dir, f'port_stats_{timestamp_str}.csv')
        with open(port_stats_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['dpid', 'port_no', 'tx_bytes', 'rx_bytes', 'tx_packets', 
                           'rx_packets', 'tx_speed_mbps', 'rx_speed_mbps', 'timestamp'])
            
            for dpid, ports in self.port_stats.items():
                for port_no, stats in ports.items():
                    writer.writerow([
                        dpid, port_no, stats.get('tx_bytes', 0), stats.get('rx_bytes', 0),
                        stats.get('tx_packets', 0), stats.get('rx_packets', 0),
                        stats.get('tx_speed_mbps', 0), stats.get('rx_speed_mbps', 0),
                        stats.get('timestamp', time.time())
                    ])
        
        # Save flow statistics
        flow_stats_file = os.path.join(self.data_dir, f'flow_stats_{timestamp_str}.csv')
        with open(flow_stats_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['dpid', 'duration_sec', 'priority', 'packet_count', 
                           'byte_count', 'match', 'timestamp'])
            
            for dpid, flows in self.flow_stats.items():
                for flow in flows:
                    writer.writerow([
                        dpid, flow['duration_sec'], flow['priority'],
                        flow['packet_count'], flow['byte_count'],
                        str(flow['match']), flow['timestamp']
                    ])
        
        self.logger.info('Statistics saved to %s', self.data_dir)

    def get_traffic_data_for_prediction(self, window_size=10):
        """
        Get traffic data formatted for LSTM prediction
        Args:
            window_size: number of time steps
        Returns: list of traffic values for each time step
        """
        # This will be used by the traffic predictor
        # Returns bandwidth utilization over time
        traffic_data = []
        
        utilization = self.get_bandwidth_utilization()
        for dpid, ports in utilization.items():
            for port_no, util in ports.items():
                traffic_data.append(util['avg_utilization'])
        
        return traffic_data
