"""
Mininet Topology for SDN-AI Traffic Engineering
Tạo topology mạng để test hệ thống
"""

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink

import sys
sys.path.append('..')
from environment.config import TOPOLOGY, CONTROLLER as CTRL_CONFIG


def create_simple_topology():
    """
    Create a simple topology: 4 switches in a mesh, 2 hosts per switch
    
    Topology:
            h1        h3        h5        h7
            |         |         |         |
           s1 ------ s2 ------ s3 ------ s4
            |         |         |         |
            h2        h4        h6        h8
    """
    net = Mininet(
        controller=RemoteController,
        switch=OVSKernelSwitch,
        link=TCLink,
        autoSetMacs=True
    )
    
    info('*** Adding controller\n')
    controller = net.addController(
        'c0',
        controller=RemoteController,
        ip=CTRL_CONFIG['host'],
        port=CTRL_CONFIG['port']
    )
    
    info('*** Adding switches\n')
    switches = []
    for i in range(1, 5):
        switch = net.addSwitch(f's{i}', protocols='OpenFlow13')
        switches.append(switch)
    
    info('*** Adding hosts\n')
    hosts = []
    for i in range(1, 9):
        host = net.addHost(f'h{i}', ip=f'10.0.0.{i}/24')
        hosts.append(host)
    
    info('*** Creating links\n')
    link_config = {
        'bw': TOPOLOGY['link_bandwidth'],
        'delay': TOPOLOGY['link_delay'],
        'loss': TOPOLOGY['link_loss']
    }
    
    # Connect hosts to switches
    net.addLink(hosts[0], switches[0], **link_config)  # h1 - s1
    net.addLink(hosts[1], switches[0], **link_config)  # h2 - s1
    net.addLink(hosts[2], switches[1], **link_config)  # h3 - s2
    net.addLink(hosts[3], switches[1], **link_config)  # h4 - s2
    net.addLink(hosts[4], switches[2], **link_config)  # h5 - s3
    net.addLink(hosts[5], switches[2], **link_config)  # h6 - s3
    net.addLink(hosts[6], switches[3], **link_config)  # h7 - s4
    net.addLink(hosts[7], switches[3], **link_config)  # h8 - s4
    
    # Create mesh topology between switches (multiple paths)
    net.addLink(switches[0], switches[1], **link_config)  # s1 - s2
    net.addLink(switches[1], switches[2], **link_config)  # s2 - s3
    net.addLink(switches[2], switches[3], **link_config)  # s3 - s4
    net.addLink(switches[0], switches[2], **link_config)  # s1 - s3 (alternate path)
    net.addLink(switches[1], switches[3], **link_config)  # s2 - s4 (alternate path)
    
    return net


def create_fattree_topology(k=4):
    """
    Create a Fat-Tree topology
    Args:
        k: number of pods (must be even)
    """
    net = Mininet(
        controller=RemoteController,
        switch=OVSKernelSwitch,
        link=TCLink,
        autoSetMacs=True
    )
    
    info('*** Adding controller\n')
    controller = net.addController(
        'c0',
        controller=RemoteController,
        ip=CTRL_CONFIG['host'],
        port=CTRL_CONFIG['port']
    )
    
    info('*** Creating Fat-Tree topology with k=%d\n' % k)
    
    # Core switches
    num_core = (k // 2) ** 2
    core_switches = []
    for i in range(num_core):
        switch = net.addSwitch(f'cs{i+1}', protocols='OpenFlow13')
        core_switches.append(switch)
    
    # Pod switches and hosts
    link_config = {
        'bw': TOPOLOGY['link_bandwidth'],
        'delay': TOPOLOGY['link_delay'],
        'loss': TOPOLOGY['link_loss']
    }
    
    host_id = 1
    for pod in range(k):
        # Aggregation switches in this pod
        agg_switches = []
        for i in range(k // 2):
            switch = net.addSwitch(f'as{pod}_{i}', protocols='OpenFlow13')
            agg_switches.append(switch)
        
        # Edge switches in this pod
        edge_switches = []
        for i in range(k // 2):
            switch = net.addSwitch(f'es{pod}_{i}', protocols='OpenFlow13')
            edge_switches.append(switch)
            
            # Connect hosts to edge switch
            for j in range(k // 2):
                host = net.addHost(f'h{host_id}', ip=f'10.{pod}.{i}.{j+1}/24')
                net.addLink(host, switch, **link_config)
                host_id += 1
        
        # Connect edge to aggregation switches
        for edge_sw in edge_switches:
            for agg_sw in agg_switches:
                net.addLink(edge_sw, agg_sw, **link_config)
        
        # Connect aggregation to core switches
        for i, agg_sw in enumerate(agg_switches):
            for j in range(k // 2):
                core_idx = i * (k // 2) + j
                net.addLink(agg_sw, core_switches[core_idx], **link_config)
    
    return net


def setup_network(net):
    """Setup and start network"""
    info('*** Starting network\n')
    net.start()
    
    info('*** Configuring switches for OpenFlow 1.3\n')
    for switch in net.switches:
        switch.cmd('ovs-vsctl set bridge %s protocols=OpenFlow13' % switch.name)
    
    info('*** Testing connectivity\n')
    net.pingAll()
    
    return net


def run_simple_topology():
    """Run simple topology"""
    setLogLevel('info')
    
    info('*** Creating Simple Mesh Topology\n')
    net = create_simple_topology()
    
    net = setup_network(net)
    
    info('*** Network is ready!\n')
    info('*** Run traffic generator in another terminal:\n')
    info('    python environment/traffic_generator.py\n')
    info('*** Starting CLI\n')
    
    CLI(net)
    
    info('*** Stopping network\n')
    net.stop()


def run_fattree_topology(k=4):
    """Run Fat-Tree topology"""
    setLogLevel('info')
    
    info(f'*** Creating Fat-Tree Topology (k={k})\n')
    net = create_fattree_topology(k)
    
    net = setup_network(net)
    
    info('*** Network is ready!\n')
    info('*** Starting CLI\n')
    
    CLI(net)
    
    info('*** Stopping network\n')
    net.stop()


def cleanup():
    """Cleanup Mininet"""
    info('*** Cleaning up Mininet\n')
    import os
    os.system('sudo mn -c')


if __name__ == '__main__':
    import sys
    
    # Parse arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == 'fattree':
            k = int(sys.argv[2]) if len(sys.argv) > 2 else 4
            run_fattree_topology(k)
        elif sys.argv[1] == 'cleanup':
            cleanup()
        else:
            print("Usage:")
            print("  python mininet_topo.py              # Run simple topology")
            print("  python mininet_topo.py fattree [k]  # Run Fat-Tree with k pods")
            print("  python mininet_topo.py cleanup      # Cleanup Mininet")
    else:
        run_simple_topology()
