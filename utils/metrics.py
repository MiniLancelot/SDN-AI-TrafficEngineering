"""
Performance Metrics Tracker
"""

import time
import numpy as np
from collections import deque
import matplotlib.pyplot as plt
import json
import os


class MetricsTracker:
    """Track and visualize network performance metrics"""
    
    def __init__(self, window_size=100):
        self.window_size = window_size
        
        # Metrics buffers
        self.throughput_buffer = deque(maxlen=window_size)
        self.latency_buffer = deque(maxlen=window_size)
        self.packet_loss_buffer = deque(maxlen=window_size)
        self.link_utilization_buffer = deque(maxlen=window_size)
        self.timestamps = deque(maxlen=window_size)
        
        # Statistics
        self.start_time = time.time()
        self.total_packets = 0
        self.total_bytes = 0
        self.dropped_packets = 0
    
    def record_throughput(self, bytes_per_second):
        """Record throughput measurement"""
        mbps = (bytes_per_second * 8) / 1_000_000  # Convert to Mbps
        self.throughput_buffer.append(mbps)
        self.timestamps.append(time.time() - self.start_time)
    
    def record_latency(self, latency_ms):
        """Record latency measurement"""
        self.latency_buffer.append(latency_ms)
    
    def record_packet_loss(self, loss_rate):
        """Record packet loss rate (0-1)"""
        self.packet_loss_buffer.append(loss_rate * 100)  # Convert to percentage
    
    def record_link_utilization(self, utilization):
        """Record link utilization (0-100)"""
        self.link_utilization_buffer.append(utilization)
    
    def get_statistics(self):
        """Get current statistics"""
        return {
            'avg_throughput_mbps': np.mean(list(self.throughput_buffer)) if self.throughput_buffer else 0,
            'avg_latency_ms': np.mean(list(self.latency_buffer)) if self.latency_buffer else 0,
            'avg_packet_loss_pct': np.mean(list(self.packet_loss_buffer)) if self.packet_loss_buffer else 0,
            'avg_link_utilization_pct': np.mean(list(self.link_utilization_buffer)) if self.link_utilization_buffer else 0,
            'max_throughput_mbps': max(self.throughput_buffer) if self.throughput_buffer else 0,
            'max_latency_ms': max(self.latency_buffer) if self.latency_buffer else 0,
            'max_link_utilization_pct': max(self.link_utilization_buffer) if self.link_utilization_buffer else 0,
            'total_packets': self.total_packets,
            'total_bytes': self.total_bytes,
            'dropped_packets': self.dropped_packets,
            'uptime_seconds': time.time() - self.start_time
        }
    
    def print_statistics(self):
        """Print current statistics"""
        stats = self.get_statistics()
        
        print("\n" + "="*60)
        print("Network Performance Metrics")
        print("="*60)
        print(f"Uptime: {stats['uptime_seconds']:.1f} seconds")
        print(f"\nThroughput:")
        print(f"  Average: {stats['avg_throughput_mbps']:.2f} Mbps")
        print(f"  Peak: {stats['max_throughput_mbps']:.2f} Mbps")
        print(f"\nLatency:")
        print(f"  Average: {stats['avg_latency_ms']:.2f} ms")
        print(f"  Peak: {stats['max_latency_ms']:.2f} ms")
        print(f"\nPacket Loss:")
        print(f"  Average: {stats['avg_packet_loss_pct']:.2f}%")
        print(f"\nLink Utilization:")
        print(f"  Average: {stats['avg_link_utilization_pct']:.2f}%")
        print(f"  Peak: {stats['max_link_utilization_pct']:.2f}%")
        print(f"\nTraffic:")
        print(f"  Total Packets: {stats['total_packets']}")
        print(f"  Total Bytes: {stats['total_bytes']:,}")
        print(f"  Dropped Packets: {stats['dropped_packets']}")
        print("="*60 + "\n")
    
    def plot_metrics(self, save_path=None):
        """Plot metrics over time"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Network Performance Metrics', fontsize=16)
        
        timestamps = list(self.timestamps)
        
        # Throughput
        if self.throughput_buffer:
            axes[0, 0].plot(timestamps, list(self.throughput_buffer), 'b-', linewidth=2)
            axes[0, 0].set_title('Throughput')
            axes[0, 0].set_xlabel('Time (s)')
            axes[0, 0].set_ylabel('Mbps')
            axes[0, 0].grid(True, alpha=0.3)
        
        # Latency
        if self.latency_buffer:
            axes[0, 1].plot(timestamps[-len(self.latency_buffer):], 
                          list(self.latency_buffer), 'g-', linewidth=2)
            axes[0, 1].set_title('Latency')
            axes[0, 1].set_xlabel('Time (s)')
            axes[0, 1].set_ylabel('ms')
            axes[0, 1].grid(True, alpha=0.3)
        
        # Packet Loss
        if self.packet_loss_buffer:
            axes[1, 0].plot(timestamps[-len(self.packet_loss_buffer):], 
                          list(self.packet_loss_buffer), 'r-', linewidth=2)
            axes[1, 0].set_title('Packet Loss')
            axes[1, 0].set_xlabel('Time (s)')
            axes[1, 0].set_ylabel('%')
            axes[1, 0].grid(True, alpha=0.3)
        
        # Link Utilization
        if self.link_utilization_buffer:
            axes[1, 1].plot(timestamps[-len(self.link_utilization_buffer):], 
                          list(self.link_utilization_buffer), 'm-', linewidth=2)
            axes[1, 1].axhline(y=80, color='orange', linestyle='--', label='Warning (80%)')
            axes[1, 1].axhline(y=95, color='red', linestyle='--', label='Critical (95%)')
            axes[1, 1].set_title('Link Utilization')
            axes[1, 1].set_xlabel('Time (s)')
            axes[1, 1].set_ylabel('%')
            axes[1, 1].legend()
            axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Plot saved to {save_path}")
        else:
            plt.show()
    
    def save_to_json(self, filepath):
        """Save metrics to JSON file"""
        data = {
            'statistics': self.get_statistics(),
            'throughput': list(self.throughput_buffer),
            'latency': list(self.latency_buffer),
            'packet_loss': list(self.packet_loss_buffer),
            'link_utilization': list(self.link_utilization_buffer),
            'timestamps': list(self.timestamps)
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Metrics saved to {filepath}")
    
    def load_from_json(self, filepath):
        """Load metrics from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.throughput_buffer = deque(data['throughput'], maxlen=self.window_size)
        self.latency_buffer = deque(data['latency'], maxlen=self.window_size)
        self.packet_loss_buffer = deque(data['packet_loss'], maxlen=self.window_size)
        self.link_utilization_buffer = deque(data['link_utilization'], maxlen=self.window_size)
        self.timestamps = deque(data['timestamps'], maxlen=self.window_size)
        
        print(f"Metrics loaded from {filepath}")


def compare_scenarios(baseline_file, optimized_file):
    """Compare baseline vs AI-optimized performance"""
    # Load data
    with open(baseline_file, 'r') as f:
        baseline = json.load(f)
    
    with open(optimized_file, 'r') as f:
        optimized = json.load(f)
    
    # Create comparison plot
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Performance Comparison: Baseline vs AI-Optimized', fontsize=16)
    
    metrics = [
        ('throughput', 'Throughput (Mbps)', 0, 0),
        ('latency', 'Latency (ms)', 0, 1),
        ('packet_loss', 'Packet Loss (%)', 1, 0),
        ('link_utilization', 'Link Utilization (%)', 1, 1)
    ]
    
    for metric, ylabel, row, col in metrics:
        axes[row, col].plot(baseline['timestamps'], baseline[metric], 
                          'b-', label='Baseline', linewidth=2)
        axes[row, col].plot(optimized['timestamps'], optimized[metric], 
                          'g-', label='AI-Optimized', linewidth=2)
        axes[row, col].set_title(ylabel)
        axes[row, col].set_xlabel('Time (s)')
        axes[row, col].set_ylabel(ylabel)
        axes[row, col].legend()
        axes[row, col].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Calculate improvements
    improvements = {}
    for metric, _, _, _ in metrics:
        baseline_avg = np.mean(baseline[metric])
        optimized_avg = np.mean(optimized[metric])
        
        if metric in ['latency', 'packet_loss']:
            # Lower is better
            improvement = ((baseline_avg - optimized_avg) / baseline_avg) * 100
        else:
            # Higher is better
            improvement = ((optimized_avg - baseline_avg) / baseline_avg) * 100
        
        improvements[metric] = improvement
    
    print("\n" + "="*60)
    print("Performance Improvements with AI Optimization")
    print("="*60)
    for metric, improvement in improvements.items():
        print(f"{metric.capitalize()}: {improvement:+.2f}%")
    print("="*60 + "\n")
    
    return fig


if __name__ == "__main__":
    # Test metrics tracker
    print("Testing Metrics Tracker...")
    
    tracker = MetricsTracker(window_size=50)
    
    # Simulate some metrics
    for i in range(50):
        tracker.record_throughput(5_000_000 + np.random.randint(-1_000_000, 1_000_000))
        tracker.record_latency(10 + np.random.rand() * 5)
        tracker.record_packet_loss(0.01 + np.random.rand() * 0.02)
        tracker.record_link_utilization(50 + np.random.rand() * 30)
        time.sleep(0.01)
    
    # Print statistics
    tracker.print_statistics()
    
    # Save metrics
    tracker.save_to_json('results/test_metrics.json')
    
    print("\n✓ Metrics tracker test completed!")
