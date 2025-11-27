# Hướng dẫn Triển khai Chi tiết

## Mục lục
1. [Cài đặt Môi trường](#1-cài-đặt-môi-trường)
2. [Cấu hình Hệ thống](#2-cấu-hình-hệ-thống)
3. [Huấn luyện AI Models](#3-huấn-luyện-ai-models)
4. [Chạy Hệ thống](#4-chạy-hệ-thống)
5. [Testing và Đánh giá](#5-testing-và-đánh-giá)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Cài đặt Môi trường

### 1.1. Yêu cầu Hệ thống
- **OS**: Ubuntu 20.04 LTS hoặc mới hơn
- **RAM**: Tối thiểu 8GB (khuyến nghị 16GB)
- **CPU**: 4 cores hoặc nhiều hơn
- **Disk**: 20GB trống
- **Python**: 3.8 trở lên

### 1.2. Cài đặt Dependencies

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Python và pip
sudo apt-get install python3 python3-pip python3-dev -y

# Install Mininet
sudo apt-get install mininet -y

# Install Open vSwitch
sudo apt-get install openvswitch-switch openvswitch-common -y

# Verify installations
sudo mn --version
sudo ovs-vsctl --version
```

### 1.3. Cài đặt Python Packages

```bash
cd SDN-AI-TrafficEngineering

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Install Ryu Controller
pip install ryu
```

### 1.4. Kiểm tra Cài đặt

```bash
# Test Mininet
sudo mn --test pingall

# Test OVS
sudo ovs-vsctl show

# Test Ryu
ryu-manager --version

# Test Python packages
python -c "import torch; import tensorflow; import ryu; print('All packages OK')"
```

---

## 2. Cấu hình Hệ thống

### 2.1. Cấu hình Network Topology

Chỉnh sửa file `environment/config.py`:

```python
TOPOLOGY = {
    'num_switches': 4,
    'num_hosts_per_switch': 2,
    'link_bandwidth': 10,  # Mbps
    'link_delay': '10ms',
    'link_loss': 0,
}
```

### 2.2. Cấu hình AI Models

```python
AI_MODELS = {
    'lstm': {
        'sequence_length': 10,
        'hidden_size': 64,
        'num_layers': 2,
        'learning_rate': 0.001,
        'epochs': 100,
    },
    'dqn': {
        'state_size': 20,
        'action_size': 4,
        'learning_rate': 0.001,
        'gamma': 0.95,
        'epsilon_start': 1.0,
    }
}
```

### 2.3. Cấu hình QoS Classes

```python
QOS = {
    'classes': {
        'voip': {
            'priority': 1,
            'min_bandwidth': 100,  # Kbps
            'max_latency': 50,  # ms
            'queue_id': 0,
        },
        # ... other classes
    }
}
```

---

## 3. Huấn luyện AI Models

### 3.1. Thu thập Dữ liệu Training

**Terminal 1: Khởi động Controller**
```bash
cd SDN-AI-TrafficEngineering
source venv/bin/activate
ryu-manager controller/monitor.py
```

**Terminal 2: Khởi động Mininet**
```bash
sudo python environment/mininet_topo.py
```

**Terminal 3: Generate Traffic**
```bash
# In Mininet CLI
mininet> h1 iperf -s &
mininet> h2 iperf -c 10.0.0.1 -t 300 -b 5M

# Hoặc sử dụng traffic generator
python environment/traffic_generator.py --scenario normal --duration 3600
```

Dữ liệu sẽ được lưu trong `data/collected/`

### 3.2. Huấn luyện LSTM Traffic Predictor

```bash
python ai_models/traffic_predictor.py
```

Hoặc với dữ liệu custom:

```python
from ai_models.traffic_predictor import TrafficPredictor
import pandas as pd

# Load data
data = pd.read_csv('data/collected/port_stats_*.csv')
traffic_values = data['tx_speed_mbps'].values

# Split data
train_size = int(0.8 * len(traffic_values))
train_data = traffic_values[:train_size]
test_data = traffic_values[train_size:]

# Train
predictor = TrafficPredictor(sequence_length=10)
predictor.train(train_data, epochs=100)

# Save model
predictor.save_model('data/models/lstm_traffic_predictor.pth')
```

### 3.3. Huấn luyện DQN Load Balancing Agent

```bash
python ai_models/dqn_agent.py
```

Hoặc với environment tùy chỉnh:

```python
from ai_models.dqn_agent import DQNAgent, NetworkEnvironment

# Create environment
env = NetworkEnvironment(num_links=12, num_paths=4)

# Create agent
agent = DQNAgent(state_size=20, action_size=4)

# Train
for episode in range(1000):
    total_reward = agent.train_episode(env, max_steps=100)
    if (episode + 1) % 100 == 0:
        print(f"Episode {episode + 1}: Reward = {total_reward:.2f}")

# Save agent
agent.save('data/models/dqn_load_balancer.pth')
```

---

## 4. Chạy Hệ thống

### 4.1. Khởi động Controller với AI

**Terminal 1: SDN Controller**
```bash
cd SDN-AI-TrafficEngineering
source venv/bin/activate
ryu-manager controller/main_controller.py --verbose
```

Output mong đợi:
```
╔════════════════════════════════════════════════════════════╗
║     Intelligent SDN Controller with AI Integration         ║
║  - Traffic Prediction (LSTM)                               ║
║  - Load Balancing (Deep Q-Network)                         ║
║  - QoS Optimization                                        ║
╚════════════════════════════════════════════════════════════╝

Loading Traffic Predictor (LSTM)...
✓ Pre-trained LSTM model loaded
Loading DQN Agent...
✓ Pre-trained DQN agent loaded
✓ AI models initialized
✓ Intelligent SDN Controller initialized successfully!
```

### 4.2. Khởi động Network Topology

**Terminal 2: Mininet**
```bash
sudo python environment/mininet_topo.py
```

Trong Mininet CLI:
```bash
mininet> net
mininet> pingall
```

### 4.3. Cấu hình QoS

**Terminal 3: QoS Setup**
```bash
python controller/qos_manager.py
```

Hoặc trong Mininet CLI, sau khi controller đã khởi động:
```bash
# QoS sẽ được tự động cấu hình bởi controller
# Kiểm tra QoS configuration:
mininet> sh ovs-vsctl list qos
mininet> sh ovs-vsctl list queue
```

### 4.4. Generate Traffic và Test

**Terminal 4: Traffic Generator**
```bash
python environment/traffic_generator.py --scenario loadbalance --duration 300
```

Trong Mininet CLI, chạy các lệnh được đề xuất:
```bash
# Example: Load balancing scenario
mininet> h1 iperf -s -p 5001 &
mininet> h8 iperf -c 10.0.0.1 -t 120 -b 4M -p 5001 &

mininet> h2 iperf -s -p 5002 &
mininet> h7 iperf -c 10.0.0.2 -t 120 -b 4M -p 5002 &

# ... và các flows khác
```

---

## 5. Testing và Đánh giá

### 5.1. Monitor Real-time Performance

**Terminal 5: Metrics Monitoring**
```python
from utils.metrics import MetricsTracker
import time

tracker = MetricsTracker()

# Run monitoring loop
while True:
    # Get metrics from controller
    # (In practice, you'd query the controller)
    
    tracker.record_throughput(5_000_000)  # bytes/sec
    tracker.record_latency(15.5)  # ms
    tracker.record_packet_loss(0.01)  # 1%
    tracker.record_link_utilization(65.0)  # 65%
    
    tracker.print_statistics()
    time.sleep(30)
```

### 5.2. Các Scenarios Testing

#### Scenario 1: Normal Traffic
```bash
python environment/traffic_generator.py --scenario normal
```

#### Scenario 2: Network Congestion
```bash
python environment/traffic_generator.py --scenario congestion
```

#### Scenario 3: QoS Priority Test
```bash
python environment/traffic_generator.py --scenario voip
```

#### Scenario 4: Load Balancing
```bash
python environment/traffic_generator.py --scenario loadbalance
```

#### Scenario 5: DDoS Detection
```bash
python environment/traffic_generator.py --scenario ddos
```

### 5.3. Thu thập Kết quả

```bash
# Export controller statistics
# (Trong controller, thêm API để export stats)

# Visualize metrics
python utils/metrics.py --visualize --input results/metrics.json

# Compare baseline vs AI-optimized
python utils/metrics.py --compare \
    --baseline results/baseline.json \
    --optimized results/ai_optimized.json
```

### 5.4. Benchmark Tests

Chạy benchmark script:

```bash
#!/bin/bash
# benchmark.sh

echo "Running benchmark tests..."

# Test 1: Baseline (no AI)
echo "Test 1: Baseline routing"
# Disable AI in config
python run_test.py --duration 300 --output results/baseline.json

# Test 2: AI-optimized
echo "Test 2: AI-optimized routing"
# Enable AI in config
python run_test.py --ai-enabled --duration 300 --output results/ai_optimized.json

# Test 3: With QoS
echo "Test 3: AI + QoS"
python run_test.py --ai-enabled --qos-enabled --duration 300 --output results/ai_qos.json

echo "Benchmark completed!"
```

---

## 6. Troubleshooting

### 6.1. Mininet Issues

**Problem**: `sudo mn -c` không clean được network

**Solution**:
```bash
sudo pkill -9 -f mininet
sudo mn -c
sudo fuser -k 6633/tcp
```

**Problem**: Open vSwitch không khởi động

**Solution**:
```bash
sudo service openvswitch-switch restart
sudo ovs-vsctl show
```

### 6.2. Controller Issues

**Problem**: Controller không kết nối được với switches

**Solution**:
```bash
# Check controller port
netstat -tulpn | grep 6633

# Check Mininet controller setting
sudo mn --controller=remote,ip=127.0.0.1,port=6633 --test pingall
```

**Problem**: AI models không load được

**Solution**:
```bash
# Check model files exist
ls -lh data/models/

# Check PyTorch installation
python -c "import torch; print(torch.__version__)"

# Retrain models if necessary
python ai_models/traffic_predictor.py
python ai_models/dqn_agent.py
```

### 6.3. QoS Issues

**Problem**: QoS queues không được tạo

**Solution**:
```bash
# Manual QoS setup
sudo ovs-vsctl set port s1-eth1 qos=@newqos -- \
  --id=@newqos create qos type=linux-htb \
  other-config:max-rate=10000000 \
  queues=0=@q0,1=@q1,2=@q2,3=@q3 -- \
  --id=@q0 create queue other-config:min-rate=1000000 -- \
  --id=@q1 create queue other-config:min-rate=5000000 -- \
  --id=@q2 create queue other-config:min-rate=2000000 -- \
  --id=@q3 create queue

# Verify
sudo ovs-vsctl list qos
sudo ovs-vsctl list queue
```

**Problem**: Traffic không được phân loại đúng

**Solution**:
- Kiểm tra traffic classification logic trong `qos_manager.py`
- Test với specific ports:
  ```bash
  # VoIP test (UDP port 5060)
  mininet> h1 iperf -s -u -p 5060 &
  mininet> h2 iperf -c 10.0.0.1 -u -p 5060 -b 128K
  ```

### 6.4. Performance Issues

**Problem**: Hệ thống chậm, high latency

**Solution**:
- Giảm monitoring interval trong config
- Disable AI tạm thời để test
- Check CPU/Memory usage:
  ```bash
  top
  htop
  ```

**Problem**: DQN agent không hội tụ

**Solution**:
- Tăng số episodes training
- Điều chỉnh learning rate
- Kiểm tra reward function
- Sử dụng smaller network nếu cần

---

## 7. Advanced Configuration

### 7.1. Multiple Controllers (High Availability)

```python
# In mininet_topo.py
net.addController('c0', controller=RemoteController, ip='192.168.1.100', port=6633)
net.addController('c1', controller=RemoteController, ip='192.168.1.101', port=6633)
```

### 7.2. Distributed Training

```bash
# Train on multiple GPUs
CUDA_VISIBLE_DEVICES=0,1 python ai_models/model_trainer.py --distributed
```

### 7.3. Real Hardware Deployment

```bash
# Configure physical switches instead of OVS
# Update controller to use physical switch IPs
# Deploy controller on dedicated server
```

---

## 8. Best Practices

1. **Always backup** trained models trước khi retrain
2. **Log everything** - enable verbose logging
3. **Monitor resources** - CPU, memory, network
4. **Test incrementally** - test từng module trước khi integrate
5. **Use version control** cho configs và code
6. **Document changes** khi customize

---

## 9. Kết luận

Hệ thống SDN-AI Traffic Engineering đã sẵn sàng. Các bước tiếp theo:

1. ✓ Thu thập dữ liệu training
2. ✓ Huấn luyện AI models
3. ✓ Deploy và test
4. ✓ Đánh giá performance
5. → Optimize và improve

**Good luck!** 🚀
