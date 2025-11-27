"""
Configuration file for SDN-AI Traffic Engineering System
"""

# Network Topology Configuration
TOPOLOGY = {
    'num_switches': 4,
    'num_hosts_per_switch': 2,
    'link_bandwidth': 10,  # Mbps
    'link_delay': '10ms',
    'link_loss': 0,  # packet loss percentage
}

# Controller Configuration
CONTROLLER = {
    'host': '127.0.0.1',
    'port': 6633,
    'monitoring_interval': 5,  # seconds
    'flow_idle_timeout': 30,
    'flow_hard_timeout': 0,
}

# AI Models Configuration
AI_MODELS = {
    'lstm': {
        'sequence_length': 10,
        'hidden_size': 64,
        'num_layers': 2,
        'dropout': 0.2,
        'learning_rate': 0.001,
        'batch_size': 32,
        'epochs': 100,
    },
    'dqn': {
        'state_size': 20,  # based on network size
        'action_size': 4,  # number of possible paths
        'hidden_layers': [128, 64],
        'learning_rate': 0.001,
        'gamma': 0.95,  # discount factor
        'epsilon_start': 1.0,
        'epsilon_end': 0.01,
        'epsilon_decay': 0.995,
        'memory_size': 10000,
        'batch_size': 64,
        'target_update_frequency': 10,
    },
    'traffic_classifier': {
        'model_type': 'random_forest',
        'n_estimators': 100,
        'max_depth': 10,
        'features': ['packet_size', 'inter_arrival_time', 'protocol', 
                     'packet_count', 'byte_count', 'duration'],
    }
}

# QoS Configuration
QOS = {
    'classes': {
        'voip': {
            'priority': 1,
            'min_bandwidth': 100,  # Kbps
            'max_latency': 50,  # ms
            'queue_id': 0,
        },
        'video': {
            'priority': 2,
            'min_bandwidth': 500,  # Kbps
            'max_latency': 100,  # ms
            'queue_id': 1,
        },
        'web': {
            'priority': 3,
            'min_bandwidth': 200,  # Kbps
            'max_latency': 200,  # ms
            'queue_id': 2,
        },
        'best_effort': {
            'priority': 4,
            'min_bandwidth': 0,
            'max_latency': None,
            'queue_id': 3,
        }
    },
    'queue_config': {
        'type': 'linux-htb',
        'max_rate': 10000000,  # 10 Mbps in bps
    }
}

# Traffic Classification Thresholds
TRAFFIC_CLASSIFICATION = {
    'elephant_flow_threshold': 1000000,  # bytes (1MB)
    'elephant_flow_duration': 5,  # seconds
    'ddos_packet_threshold': 1000,  # packets per second
    'ddos_detection_window': 10,  # seconds
}

# Data Collection Configuration
DATA_COLLECTION = {
    'enable_port_stats': True,
    'enable_flow_stats': True,
    'enable_latency_measurement': True,
    'save_to_file': True,
    'save_interval': 60,  # seconds
    'data_directory': 'data/collected/',
    'csv_format': True,
    'influxdb': {
        'enabled': False,
        'host': 'localhost',
        'port': 8086,
        'database': 'sdn_traffic',
    }
}

# Reinforcement Learning Environment
RL_ENVIRONMENT = {
    'reward_weights': {
        'max_utilization': -1.0,  # minimize max link utilization
        'avg_delay': -0.5,  # minimize average delay
        'packet_loss': -2.0,  # heavily penalize packet loss
    },
    'episode_length': 1000,  # steps
    'training_episodes': 1000,
    'test_episodes': 100,
}

# Paths
PATHS = {
    'data_collected': 'data/collected/',
    'data_processed': 'data/processed/',
    'models': 'data/models/',
    'logs': 'logs/',
    'results': 'results/',
}

# Logging Configuration
LOGGING = {
    'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'logs/sdn_controller.log',
    'max_bytes': 10485760,  # 10MB
    'backup_count': 5,
}

# Performance Metrics
METRICS = {
    'window_size': 100,  # samples for moving average
    'report_interval': 30,  # seconds
    'metrics_to_track': [
        'throughput',
        'latency',
        'packet_loss',
        'link_utilization',
        'flow_count',
        'queue_depth',
    ]
}
