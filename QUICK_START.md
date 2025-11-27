# ⚡ Quick Start - Platform Specific

## TL;DR - Chạy Nhanh theo Platform

### 🐧 Trên Kali Linux / Ubuntu (Native - TỐT NHẤT):

```bash
# 1. Clone project
git clone <repo-url>
cd SDN-AI-TrafficEngineering

# 2. Check Python version (QUAN TRỌNG!)
python3 --version

# 3. Install system packages
sudo apt-get update
sudo apt-get install -y mininet openvswitch-switch

# 4. Install build dependencies for Python (QUAN TRỌNG!)
sudo apt-get install -y build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev curl \
    libncursesw5-dev xz-utils tk-dev libxml2-dev \
    libxmlsec1-dev libffi-dev liblzma-dev

# 5. Install pyenv (RECOMMENDED)
curl https://pyenv.run | bash

# Configure pyenv (QUAN TRỌNG!)
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# Add to bashrc for next time
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

# 5. Install Python 3.11 via pyenv
pyenv install 3.11.9
cd SDN-AI-TrafficEngineering
echo "3.11.9" > .python-version  # Set Python version for this directory

# 7. Setup Python environment
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 8. Run
./start.sh setup      # Lần đầu tiên
./start.sh controller # Terminal 1
./start.sh mininet    # Terminal 2 (sử dụng sudo)
```

**⚠️ RYU COMPATIBILITY**: Project dùng Ryu fork (faucetsdn) vì official Ryu có issues với setuptools mới.

**✅ Đây là cách KHUYẾN NGHỊ nhất!**

---

### 🪟 Trên Windows (Cần WSL2):

```powershell
# ===== TRONG POWERSHELL (as Administrator) =====

# 1. Install WSL2
wsl --install -d Ubuntu-20.04

# 2. Restart computer
Restart-Computer

# 3. Open Ubuntu from Start Menu

# ===== SAU KHI VÀO UBUNTU WSL =====

# 4. Clone project (trong Ubuntu)
cd ~
git clone <repo-url>
cd SDN-AI-TrafficEngineering

# 5. Check system
chmod +x check_system.sh start.sh
./check_system.sh

# 6. Install system packages
sudo apt-get update
sudo apt-get install -y mininet openvswitch-switch build-essential

# 7. Install pyenv and Python 3.11
curl https://pyenv.run | bash
exec $SHELL
pyenv install 3.11.9
cd SDN-AI-TrafficEngineering
pyenv local 3.11.9

# 8. Setup Python (QUAN TRỌNG - fix Python 3.13 issue)
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 8. Run (TẤT CẢ trong Ubuntu WSL)
./start.sh setup
./start.sh controller
# Mở terminal WSL mới:
./start.sh mininet
```

**⚠️ LƯU Ý**: 
- TẤT CẢ commands phải chạy trong Ubuntu WSL, KHÔNG chạy trong PowerShell!
- Access files Windows từ WSL: `/mnt/c/Users/YourName/...`
- Access files WSL từ Windows: `\\wsl$\Ubuntu-20.04\home\username\...`

---

## 🔍 Kiểm tra Platform hiện tại

```bash
# Xem đang chạy OS gì
cat /etc/os-release

# Kiểm tra có phải WSL không
cat /proc/version

# Check Mininet
which mn
sudo mn --version

# Check OVS
which ovs-vsctl
sudo ovs-vsctl --version

# Check Python
python3 --version
which python3
```

---

## 📊 So sánh Nhanh

| Tính năng | Kali/Ubuntu | Windows WSL2 | Windows Native |
|-----------|-------------|--------------|----------------|
| **Mininet** | ✅ Native | ✅ Via WSL | ❌ Không |
| **Performance** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ |
| **Setup** | Dễ | Trung bình | Không thể |
| **Khuyến nghị** | **CỰC TỐT** | Tốt | ❌ |

---

## ❓ FAQs

### Q: Lỗi "AttributeError: 'types.SimpleNamespace' object has no attribute 'get_script_args'"?
**A**: Lỗi Ryu với setuptools mới. Requirements.txt đã dùng Ryu fork để fix. Nếu vẫn lỗi:
```bash
# Upgrade pip and setuptools
pip install --upgrade pip setuptools wheel

# Install Ryu fork directly
pip install git+https://github.com/faucetsdn/ryu.git@master

# Then install other packages
grep -v "^git+" requirements.txt | grep -v "^#" | pip install -r /dev/stdin
```

### Q: Tôi đang dùng Windows, có chạy được không?
**A**: CÓ, nhưng PHẢI cài WSL2 với Ubuntu. Không thể chạy native trên Windows.

### Q: Kali Linux có tốt hơn Ubuntu không?
**A**: Kali và Ubuntu đều TỐT NHẤT. Performance tương đương.

### Q: Lỗi "ModuleNotFoundError: No module named '_bz2'" hoặc "Missing the OpenSSL lib"?
**A**: Thiếu build dependencies. Cài trước khi build Python:
```bash
sudo apt-get install -y build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev curl \
    libncursesw5-dev xz-utils tk-dev libxml2-dev \
    libxmlsec1-dev libffi-dev liblzma-dev
# Sau đó: pyenv install 3.11.9
```

### Q: Lỗi "pyenv: no such command `local'"?
**A**: Pyenv chưa được load. Chạy:
```bash
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
# Sau đó thử lại: echo "3.11.9" > .python-version
```

### Q: Python 3.13 có chạy được không?
**A**: CÓ! Project đã dùng Ryu fork (faucetsdn) trong requirements.txt. Python 3.11-3.13 đều OK.

### Q: Tôi có thể dev trên Windows IDE và run trên WSL2?
**A**: CÓ! VS Code có extension WSL rất tốt. PyCharm Professional cũng support.

### Q: Docker có chạy được không?
**A**: CÓ, nhưng cần `--privileged` mode. Xem [PLATFORM_GUIDE.md](PLATFORM_GUIDE.md)

### Q: macOS thì sao?
**A**: Cần VM (VirtualBox/VMware) với Ubuntu. Không native support.

### Q: Code có khác gì giữa Linux và Windows WSL2?
**A**: KHÔNG khác! Code giống hệt nhau. WSL2 là Linux environment.

---

## 🚨 Common Mistakes

### ❌ SAI: Chạy Python script trực tiếp trên PowerShell
```powershell
# ❌ SAI - Sẽ không có Mininet
PS> python controller/main_controller.py
```

### ✅ ĐÚNG: Chạy trong WSL Ubuntu
```bash
# ✅ ĐÚNG
wsl -d Ubuntu-20.04
cd ~/SDN-AI-TrafficEngineering
python3 controller/main_controller.py
```

### ❌ SAI: Clone code vào Windows folder khi dùng WSL
```bash
# ❌ SAI - Slow performance
cd /mnt/c/Users/YourName/Documents
git clone ...
```

### ✅ ĐÚNG: Clone vào Linux filesystem
```bash
# ✅ ĐÚNG - Fast performance
cd ~
git clone ...
```

---

## 🎯 Recommendation Cuối cùng

### Nếu bạn CÓ thể chọn:
1. **🥇 Kali Linux (dual boot/native)** - Performance TỐT NHẤT
2. **🥈 Ubuntu (dual boot/native)** - Performance TỐT NHẤT
3. **🥉 Windows + WSL2** - Performance TỐT
4. **❌ Windows native** - KHÔNG THỂ chạy Mininet

### Nếu bạn ĐANG DÙNG Windows:
- ✅ Cài WSL2 với Ubuntu 20.04
- ✅ Hoặc dùng VirtualBox/VMware với Kali Linux
- ❌ ĐỪNG cố chạy native trên Windows (waste time!)

---

## 📱 Contact & Support

- 📖 Full guide: [PLATFORM_GUIDE.md](PLATFORM_GUIDE.md)
- 🚀 Deployment: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- 🔧 Issues: Check `./check_system.sh` output

**Good luck!** 🎉
