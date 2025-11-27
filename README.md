# SDN AI-Powered Traffic Engineering System

## 🎯 Tổng quan

Dự án ứng dụng AI để tối ưu hóa định tuyến và quản lý traffic trên mạng SDN với ba chức năng chính:
- **Traffic Prediction**: Dự đoán traffic sử dụng LSTM
- **Load Balancing**: Cân bằng tải thông minh với Deep Reinforcement Learning (DQN)
- **QoS Optimization**: Tối ưu hóa chất lượng dịch vụ động

## 🚀 Quick Start

### ⚠️ Python 3.13 Issue?
**Lỗi khi `pip install`?** → Xem [PYTHON_FIX.md](PYTHON_FIX.md) hoặc chạy:
```bash
./fix_python.sh
```

### 📖 Hướng dẫn theo Platform:
- 🐧 **Linux (Kali/Ubuntu)**: Xem [QUICK_START.md](QUICK_START.md) ← **KHUYẾN NGHỊ**
- 🪟 **Windows (WSL2)**: Xem [QUICK_START.md](QUICK_START.md) 
- 📋 **Chi tiết đầy đủ**: Xem [PLATFORM_GUIDE.md](PLATFORM_GUIDE.md)

### ⚡ Nếu đang dùng Kali Linux/Ubuntu:
```bash
git clone <repo-url>
cd SDN-AI-TrafficEngineering
chmod +x fix_python.sh check_system.sh start.sh
./fix_python.sh             # Fix Python 3.13 (nếu cần)
./check_system.sh           # Kiểm tra system
source venv/bin/activate    # Activate environment
./start.sh setup            # Cài đặt
./start.sh controller       # Chạy controller
```

### ⚡ Nếu đang dùng Windows:
```powershell
# Bước 1: Cài WSL2 (PowerShell as Admin)
wsl --install -d Ubuntu-20.04
# Bước 2: Restart, mở Ubuntu, chạy như Linux
```

## Kiến trúc Hệ thống

```
┌─────────────────────────────────────────┐
│      AI Intelligence Layer              │
│  - Traffic Prediction (LSTM)            │
│  - Load Balancing (DQN Agent)           │
│  - Traffic Classification               │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│     SDN Controller (Ryu)                │
│  - Network Monitoring                   │
│  - Flow Management                      │
│  - QoS Policy Enforcement               │
└───────────────┬─────────────────────────┘
                │ OpenFlow 1.3
┌───────────────▼─────────────────────────┐
│     Infrastructure Layer                │
│  - Open vSwitch                         │
│  - Queues & Meters                      │
└─────────────────────────────────────────┘
```

## Cấu trúc Dự án

```
SDN-AI-TrafficEngineering/
├── controller/
│   ├── monitor.py              # Traffic monitoring & data collection
│   ├── routing_manager.py      # Routing logic & flow installation
│   ├── qos_manager.py          # QoS configuration & enforcement
│   └── main_controller.py      # Main Ryu application
├── ai_models/
│   ├── traffic_predictor.py    # LSTM traffic prediction
│   ├── dqn_agent.py            # DQN load balancing agent
│   ├── traffic_classifier.py   # ML-based traffic classification
│   └── model_trainer.py        # Training utilities
├── environment/
│   ├── mininet_topo.py         # Mininet topology setup
│   ├── traffic_generator.py    # Traffic generation scripts
│   └── config.py               # Network configuration
├── utils/
│   ├── data_processor.py       # Data preprocessing
│   ├── metrics.py              # Performance metrics
│   └── logger.py               # Logging utilities
├── data/
│   ├── collected/              # Collected traffic data
│   ├── processed/              # Preprocessed data
│   └── models/                 # Trained models
├── tests/
│   └── test_scenarios.py       # Testing scenarios
├── requirements.txt
└── README.md
```

## Yêu cầu Hệ thống

### ✅ Linux (Khuyến nghị - Native Performance)
- **OS**: Ubuntu 20.04+, **Kali Linux 2022+**, Debian 11+
- **RAM**: Tối thiểu 8GB (khuyến nghị 16GB)
- **Python**: 3.8+
- **SDN Controller**: Ryu 4.34+
- **Network Emulator**: Mininet 2.3.0+
- **Open vSwitch**: 2.13+

### ⚠️ Windows (Cần WSL2 hoặc VM)
- **OS**: Windows 10/11
- **WSL2**: Ubuntu 20.04+ **BẮT BUỘC** để chạy Mininet
- **RAM**: Tối thiểu 16GB
- **Python**: 3.8+ (cài trong WSL2)

### 📝 Lưu ý Quan trọng
- 🐧 **Mininet và Open vSwitch CHỈ chạy native trên Linux**
- 🪟 Trên Windows **PHẢI dùng WSL2** hoặc Virtual Machine (VirtualBox/VMware)
- ✨ **Kali Linux và Ubuntu cho performance tốt nhất**
- 📖 Xem chi tiết: [PLATFORM_GUIDE.md](PLATFORM_GUIDE.md)

## Cài đặt

### Bước 0: Kiểm tra Hệ thống

```bash
# Kiểm tra compatibility
chmod +x check_system.sh
./check_system.sh
```

### Bước 1: Cài đặt Dependencies

#### 🐧 Trên Linux (Kali/Ubuntu/Debian):

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Cài đặt Python và pip
sudo apt-get install python3 python3-pip python3-venv -y

# Cài đặt Mininet
sudo apt-get install mininet -y

# Cài đặt Open vSwitch
sudo apt-get install openvswitch-switch openvswitch-common -y

# Verify
sudo mn --version
sudo ovs-vsctl --version
```

#### 🪟 Trên Windows (WSL2):

```powershell
# Bước 1: Cài WSL2 (PowerShell as Administrator)
wsl --install -d Ubuntu-20.04

# Bước 2: Restart máy, sau đó mở Ubuntu từ Start Menu

# Bước 3: Trong Ubuntu WSL, chạy các lệnh Linux ở trên
sudo apt-get update
sudo apt-get install python3 python3-pip mininet openvswitch-switch -y
```

**Chi tiết cho từng platform**: Xem [PLATFORM_GUIDE.md](PLATFORM_GUIDE.md)

### Bước 2: Cài đặt Python Packages

```bash
# Cài đặt Python packages
pip install -r requirements.txt

# Cài đặt Mininet
sudo apt-get install mininet

# Cài đặt Open vSwitch
sudo apt-get install openvswitch-switch

# Cài đặt Ryu Controller
pip install ryu
```

### 2. Cấu hình Môi trường

```bash
# Clone repository
cd SDN-AI-TrafficEngineering

# Tạo thư mục data
mkdir -p data/{collected,processed,models}

# Kiểm tra Mininet
sudo mn --test pingall

# Kiểm tra OVS
sudo ovs-vsctl show
```

## Sử dụng

### 1. Thu thập Dữ liệu Training

```bash
# Khởi động controller ở chế độ monitor
ryu-manager controller/monitor.py

# Trong terminal khác, khởi động Mininet
sudo python environment/mininet_topo.py

# Sinh traffic để thu thập dữ liệu
python environment/traffic_generator.py --duration 3600
```

### 2. Huấn luyện AI Models

```bash
# Huấn luyện LSTM traffic predictor
python ai_models/model_trainer.py --model lstm --epochs 100

# Huấn luyện DQN agent
python ai_models/model_trainer.py --model dqn --episodes 1000
```

### 3. Chạy Hệ thống Hoàn chỉnh

```bash
# Terminal 1: Khởi động controller với AI
ryu-manager controller/main_controller.py

# Terminal 2: Khởi động Mininet topology
sudo python environment/mininet_topo.py

# Terminal 3: Monitor performance
python utils/metrics.py --monitor
```

## Các Tính năng Chính

### 1. Traffic Prediction (Dự đoán Traffic)
- Sử dụng LSTM để dự đoán traffic matrix
- Phát hiện xu hướng tắc nghẽn trước khi xảy ra
- Cập nhật dự đoán mỗi 5 giây

### 2. Load Balancing với Deep Q-Network
- Agent RL tối ưu hóa định tuyến dựa trên trạng thái mạng real-time
- Phân biệt Elephant flows và Mice flows
- Reward function: minimize max link utilization

### 3. QoS Optimization
- Tự động phân loại traffic (VoIP, Video, Web, File Transfer)
- Cấu hình Queues động với HTB (Hierarchical Token Bucket)
- Áp dụng Meters để kiểm soát lưu lượng

## Đánh giá Hiệu năng

Hệ thống được đánh giá dựa trên các metrics:
- **Throughput**: Tổng băng thông đạt được
- **Latency**: Độ trễ end-to-end
- **Packet Loss**: Tỷ lệ mất gói
- **Load Balance Index**: Độ đồng đều phân phối tải
- **QoS Metrics**: Jitter, delay variation

## 📚 Documentation

- **[PLATFORM_COMPATIBILITY.md](PLATFORM_COMPATIBILITY.md)** - ⭐ Code chạy trên platform nào?
- **[QUICK_START.md](QUICK_START.md)** - 🚀 Bắt đầu nhanh theo từng OS
- **[PLATFORM_GUIDE.md](PLATFORM_GUIDE.md)** - 📖 Hướng dẫn chi tiết cho mỗi platform  
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - 🔧 Triển khai và cấu hình đầy đủ

### 🎯 Đọc tài liệu nào?

- ❓ **"Code chạy được trên Kali/Windows không?"** → [PLATFORM_COMPATIBILITY.md](PLATFORM_COMPATIBILITY.md)
- 🚀 **"Làm sao để chạy nhanh nhất?"** → [QUICK_START.md](QUICK_START.md)
- 📖 **"Hướng dẫn chi tiết cho OS của tôi"** → [PLATFORM_GUIDE.md](PLATFORM_GUIDE.md)
- 🔧 **"Cấu hình và tối ưu"** → [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

## Tài liệu Tham khảo

- OpenFlow Switch Specification v1.3
- Ryu SDN Framework Documentation
- Deep Q-Learning for Network Routing
- Traffic Engineering in SDN: A Survey

## Roadmap

- [x] Thiết lập kiến trúc cơ bản
- [x] Module monitor và data collection  
- [x] LSTM traffic predictor
- [x] DQN load balancing agent
- [x] QoS manager với OVSDB
- [x] Testing framework và scenarios
- [x] Multi-platform support (Kali/Ubuntu/Windows WSL2)
- [ ] Real hardware deployment
- [ ] Advanced RL algorithms (PPO, A3C)
- [ ] Distributed controller support

## License

MIT License

## Tác giả

Network Engineering Project - DUT Year 5
