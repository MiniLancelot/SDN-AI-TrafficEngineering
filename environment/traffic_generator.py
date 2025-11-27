"""
Traffic Generator for Testing
Tạo các luồng traffic khác nhau để test hệ thống
"""

import subprocess
import time
import random
import argparse
from datetime import datetime


class TrafficGenerator:
    """Generate various types of network traffic"""
    
    def __init__(self, mininet_hosts=['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'h8']):
        self.hosts = mininet_hosts
        self.running = False
    
    def run_cmd(self, cmd):
        """Execute command"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.stdout, result.stderr
        except Exception as e:
            print(f"Error executing command: {e}")
            return None, str(e)
    
    def get_host_ip(self, host_name):
        """Get IP address of Mininet host"""
        # Assuming IP format 10.0.0.X where X is the host number
        host_num = int(host_name[1:])
        return f"10.0.0.{host_num}"
    
    def generate_tcp_traffic(self, src_host, dst_host, duration=10, bandwidth='5M'):
        """
        Generate TCP traffic using iperf
        Args:
            src_host: source host name (e.g., 'h1')
            dst_host: destination host name (e.g., 'h2')
            duration: duration in seconds
            bandwidth: bandwidth limit (e.g., '5M' for 5 Mbps)
        """
        dst_ip = self.get_host_ip(dst_host)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] TCP traffic: {src_host} -> {dst_host} ({bandwidth})")
        
        # Start iperf server on destination
        server_cmd = f"mininet> {dst_host} iperf -s -p 5001 &"
        
        # Start iperf client on source
        client_cmd = f"mininet> {src_host} iperf -c {dst_ip} -t {duration} -b {bandwidth} -p 5001"
        
        print(f"Run on Mininet CLI:")
        print(f"  {dst_host} iperf -s -p 5001 &")
        print(f"  {src_host} iperf -c {dst_ip} -t {duration} -b {bandwidth} -p 5001")
        
        return server_cmd, client_cmd
    
    def generate_udp_traffic(self, src_host, dst_host, duration=10, bandwidth='3M'):
        """
        Generate UDP traffic (simulating VoIP/Video)
        Args:
            src_host: source host name
            dst_host: destination host name
            duration: duration in seconds
            bandwidth: bandwidth limit
        """
        dst_ip = self.get_host_ip(dst_host)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] UDP traffic: {src_host} -> {dst_host} ({bandwidth})")
        
        print(f"Run on Mininet CLI:")
        print(f"  {dst_host} iperf -s -u -p 5002 &")
        print(f"  {src_host} iperf -c {dst_ip} -u -t {duration} -b {bandwidth} -p 5002")
    
    def generate_ping_traffic(self, src_host, dst_host, count=10):
        """Generate ICMP ping traffic"""
        dst_ip = self.get_host_ip(dst_host)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ICMP ping: {src_host} -> {dst_host}")
        print(f"Run on Mininet CLI:")
        print(f"  {src_host} ping -c {count} {dst_ip}")
    
    def generate_http_traffic(self, src_host, dst_host, num_requests=100):
        """Simulate HTTP traffic using wget"""
        dst_ip = self.get_host_ip(dst_host)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] HTTP traffic: {src_host} -> {dst_host}")
        print(f"Run on Mininet CLI:")
        print(f"  {dst_host} python -m http.server 8000 &")
        print(f"  {src_host} for i in {{1..{num_requests}}}; do wget -q -O /dev/null http://{dst_ip}:8000; done")
    
    def generate_elephant_flow(self, src_host, dst_host, size_mb=100):
        """
        Generate large elephant flow
        Args:
            src_host: source host
            dst_host: destination host
            size_mb: size in megabytes
        """
        dst_ip = self.get_host_ip(dst_host)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ELEPHANT FLOW: {src_host} -> {dst_host} ({size_mb}MB)")
        print(f"Run on Mininet CLI:")
        print(f"  {dst_host} nc -l 9999 > /dev/null &")
        print(f"  {src_host} dd if=/dev/zero bs=1M count={size_mb} | nc {dst_ip} 9999")
    
    def generate_mice_flows(self, num_flows=50):
        """Generate multiple small mice flows"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Generating {num_flows} mice flows...")
        
        for i in range(num_flows):
            src = random.choice(self.hosts)
            dst = random.choice([h for h in self.hosts if h != src])
            
            # Small ping
            print(f"  {src} ping -c 3 {self.get_host_ip(dst)} &")
    
    def scenario_normal_traffic(self):
        """Normal traffic scenario: mixed traffic types"""
        print("\n=== SCENARIO: Normal Traffic ===")
        
        # Background web traffic
        self.generate_http_traffic('h1', 'h3', num_requests=50)
        
        # Some VoIP calls (UDP)
        self.generate_udp_traffic('h2', 'h4', duration=30, bandwidth='128K')
        
        # Video streaming
        self.generate_tcp_traffic('h5', 'h7', duration=60, bandwidth='2M')
        
        # File transfer
        self.generate_tcp_traffic('h6', 'h8', duration=45, bandwidth='5M')
    
    def scenario_congestion(self):
        """Congestion scenario: multiple large flows"""
        print("\n=== SCENARIO: Network Congestion ===")
        
        # Multiple elephant flows competing for bandwidth
        self.generate_elephant_flow('h1', 'h8', size_mb=50)
        self.generate_elephant_flow('h2', 'h7', size_mb=50)
        self.generate_elephant_flow('h3', 'h6', size_mb=50)
        
        # Plus background traffic
        self.generate_tcp_traffic('h4', 'h5', duration=60, bandwidth='8M')
    
    def scenario_voip_priority(self):
        """VoIP priority scenario: test QoS"""
        print("\n=== SCENARIO: VoIP Priority Test ===")
        
        # VoIP traffic (should get high priority)
        self.generate_udp_traffic('h1', 'h2', duration=60, bandwidth='128K')
        
        # Competing bulk transfer (should be deprioritized)
        self.generate_tcp_traffic('h3', 'h4', duration=60, bandwidth='10M')
        
        print("\nVoIP should maintain low latency despite bulk transfer")
    
    def scenario_load_balancing(self):
        """Load balancing scenario: test path diversity"""
        print("\n=== SCENARIO: Load Balancing Test ===")
        
        # Multiple flows that should be balanced across paths
        pairs = [
            ('h1', 'h8'),
            ('h2', 'h7'),
            ('h3', 'h6'),
            ('h4', 'h5')
        ]
        
        for src, dst in pairs:
            self.generate_tcp_traffic(src, dst, duration=120, bandwidth='4M')
        
        print("\nFlows should be distributed across multiple paths")
    
    def scenario_ddos_simulation(self):
        """DDoS simulation: many flows to single target"""
        print("\n=== SCENARIO: DDoS Simulation ===")
        
        target = 'h8'
        attackers = ['h1', 'h2', 'h3', 'h4', 'h5']
        
        print(f"DDoS attack: Multiple hosts flooding {target}")
        
        for attacker in attackers:
            # High rate UDP flood
            self.generate_udp_traffic(attacker, target, duration=30, bandwidth='8M')
        
        print("\nController should detect and rate-limit malicious flows")
    
    def run_scenario(self, scenario_name, duration=120):
        """
        Run a predefined scenario
        Args:
            scenario_name: name of scenario
            duration: how long to run (seconds)
        """
        print(f"\n{'='*60}")
        print(f"Running scenario: {scenario_name}")
        print(f"Duration: {duration} seconds")
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        scenarios = {
            'normal': self.scenario_normal_traffic,
            'congestion': self.scenario_congestion,
            'voip': self.scenario_voip_priority,
            'loadbalance': self.scenario_load_balancing,
            'ddos': self.scenario_ddos_simulation,
        }
        
        if scenario_name in scenarios:
            scenarios[scenario_name]()
        else:
            print(f"Unknown scenario: {scenario_name}")
            print(f"Available scenarios: {', '.join(scenarios.keys())}")
        
        print(f"\n{'='*60}")
        print(f"Instructions printed. Execute commands in Mininet CLI.")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description='Traffic Generator for SDN Testing')
    parser.add_argument('--scenario', type=str, default='normal',
                       choices=['normal', 'congestion', 'voip', 'loadbalance', 'ddos'],
                       help='Traffic scenario to run')
    parser.add_argument('--duration', type=int, default=120,
                       help='Duration in seconds')
    parser.add_argument('--hosts', type=str, nargs='+',
                       default=['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'h8'],
                       help='List of Mininet hosts')
    
    args = parser.parse_args()
    
    print("""
╔════════════════════════════════════════════════════════════╗
║          SDN-AI Traffic Generator                          ║
║  Generate traffic scenarios for testing SDN controller     ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    generator = TrafficGenerator(hosts=args.hosts)
    generator.run_scenario(args.scenario, duration=args.duration)
    
    print("\nNOTE: This script generates instructions for traffic generation.")
    print("You need to execute the commands in the Mininet CLI.")
    print("\nAlternatively, you can use the provided bash script to automate this:")
    print("  ./scripts/run_traffic.sh <scenario>")


if __name__ == '__main__':
    main()
