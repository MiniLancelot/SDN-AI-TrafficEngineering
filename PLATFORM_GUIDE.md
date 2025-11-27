# Hướng dẫn Chạy trên Các Hệ điều hành

## 🐧 Linux (Kali/Ubuntu/Debian) - KHUYẾN NGHỊ

### Tại sao nên dùng Linux?
- ✅ Mininet và Open vSwitch chạy native
- ✅ Performance tốt nhất
- ✅ Không cần virtualization
- ✅ Dễ debug và monitor

### Cài đặt trên Kali Linux:

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install dependencies
sudo apt install -y \
    python3 python3-pip python3-venv \
    mininet openvswitch-switch \
    build-essential git

# 3. Fix Mininet nếu cần (Kali specific)
sudo apt install --reinstall mininet

# 4. Clone project
cd ~/
git clone <your-repo-url>
cd SDN-AI-TrafficEngineering

# 5. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 6. Install Python packages
pip install --upgrade pip
pip install -r requirements.txt

# 7. Test installation
sudo mn --test pingall
```

### Chạy trên Kali Linux:

```bash
# Terminal 1: Start Controller
cd ~/SDN-AI-TrafficEngineering
source venv/bin/activate
ryu-manager controller/main_controller.py

# Terminal 2: Start Mininet
sudo python3 environment/mininet_topo.py

# Terminal 3: Monitor (optional)
python3 -c "from utils.metrics import MetricsTracker; MetricsTracker().print_statistics()"
```

---

## 🪟 Windows - Cần WSL2 hoặc VM

### Option 1: Sử dụng WSL2 (Khuyến nghị cho Windows)

**Bước 1**: Cài đặt WSL2

```powershell
# Mở PowerShell as Administrator
wsl --install -d Ubuntu-20.04

# Hoặc nếu đã có WSL1, upgrade lên WSL2
wsl --set-default-version 2
wsl --set-version Ubuntu-20.04 2

# Restart máy
```

**Bước 2**: Cấu hình Ubuntu trong WSL2

```bash
# Mở Ubuntu từ Start Menu hoặc:
wsl -d Ubuntu-20.04

# Update và install
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv mininet openvswitch-switch

# Clone project (có thể access Windows files từ /mnt/c/)
cd ~
git clone <your-repo-url>
cd SDN-AI-TrafficEngineering

# Setup như trên Linux
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Bước 3**: Chạy project trong WSL2

```bash
# Tất cả commands chạy trong WSL2 Ubuntu terminal
# Giống hệt như trên Kali Linux
```

**Lưu ý WSL2**:
- 🔥 Mininet CHỈ chạy được trong WSL2, KHÔNG chạy native trên Windows
- File Windows: `/mnt/c/Users/YourName/...`
- File Linux: `~/` hoặc `/home/username/...`
- Nên clone code vào Linux filesystem để performance tốt hơn

### Option 2: VirtualBox/VMware

```powershell
# 1. Download Kali Linux VM image
# https://www.kali.org/get-kali/#kali-virtual-machines

# 2. Import vào VirtualBox/VMware

# 3. Start VM và follow hướng dẫn Linux ở trên
```

### Option 3: Docker (Experimental)

```powershell
# 1. Install Docker Desktop for Windows

# 2. Pull image
docker pull iwaseyusuke/mininet

# 3. Run
docker run -it --privileged --name sdn-mininet iwaseyusuke/mininet bash

# 4. Trong container, follow Linux instructions
```

---

## 🍎 macOS - Cần VM

```bash
# macOS không hỗ trợ Mininet native
# Khuyến nghị: Dùng VirtualBox + Ubuntu VM
# Hoặc: Docker với cấu hình tương tự Windows
```

---

## 📋 So sánh Performance

| Platform | Mininet | Performance | Khuyến nghị |
|----------|---------|------------|-------------|
| **Kali Linux** | ✅ Native | ⭐⭐⭐⭐⭐ | **TỐT NHẤT** |
| **Ubuntu** | ✅ Native | ⭐⭐⭐⭐⭐ | Rất tốt |
| **Windows + WSL2** | ✅ Via WSL | ⭐⭐⭐⭐ | Tốt |
| **Windows + VM** | ✅ Via VM | ⭐⭐⭐ | OK |
| **Windows Native** | ❌ No | ❌ | Không thể |
| **macOS + VM** | ✅ Via VM | ⭐⭐⭐ | OK |

---

## 🚀 Quick Start theo Platform

### Trên Kali/Ubuntu:
```bash
chmod +x start.sh
./start.sh setup      # Chỉ lần đầu
./start.sh controller # Terminal 1
# Mở terminal mới:
./start.sh mininet    # Terminal 2
```

### Trên Windows (WSL2):
```powershell
# PowerShell
wsl -d Ubuntu-20.04

# Trong WSL Ubuntu terminal:
cd ~/SDN-AI-TrafficEngineering
chmod +x start.sh
./start.sh setup
./start.sh controller
```

---

## 🔧 Troubleshooting theo Platform

### Kali Linux Issues:

**Problem**: `sudo mn` không tìm thấy
```bash
# Solution:
sudo apt install --reinstall mininet
sudo apt install mininet
```

**Problem**: Permission denied
```bash
# Add user to groups
sudo usermod -aG sudo $USER
sudo usermod -aG docker $USER
newgrp docker
```

### Windows WSL2 Issues:

**Problem**: "WSL 2 requires an update to its kernel component"
```powershell
# Download và cài WSL2 kernel update
# https://aka.ms/wsl2kernel
```

**Problem**: Cannot connect to X server
```powershell
# Install VcXsrv or X410
# Start X server trước khi chạy GUI apps

# Trong WSL:
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0
```

**Problem**: OVS không start được
```bash
# Trong WSL:
sudo service openvswitch-switch start
sudo ovs-vsctl show
```

---

## 💡 Khuyến nghị Cuối cùng

### Nếu bạn đang dùng:
- ✅ **Kali Linux / Ubuntu**: Chạy trực tiếp, tốt nhất!
- ✅ **Windows có WSL2**: Dùng WSL2, khá tốt
- ⚠️ **Windows không WSL2**: Cài VM với Kali/Ubuntu
- ⚠️ **macOS**: Dùng VM hoặc Docker

### Development Setup:
- **IDE trên Windows** + **Execution trong WSL2** = Best of both worlds
- VS Code có WSL extension rất tốt
- PyCharm Professional cũng support WSL2

---

## 📞 Cần Help?

```bash
# Check system compatibility
./check_system.sh

# Test Mininet
sudo mn --test pingall

# Test OVS
sudo ovs-vsctl show

# Test Python packages
python3 -c "import torch, tensorflow, ryu; print('OK')"
```
