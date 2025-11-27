#!/bin/bash

# System Compatibility Checker
# Kiểm tra xem hệ thống có đủ yêu cầu để chạy SDN-AI Traffic Engineering không

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     System Compatibility Checker                           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Detect OS
echo -e "${BLUE}[INFO]${NC} Detecting operating system..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
    echo -e "${GREEN}✓${NC} OS: $OS $VER"
else
    echo -e "${RED}✗${NC} Cannot detect OS"
    OS="Unknown"
fi

# Check if running in WSL
if grep -qE "(Microsoft|WSL)" /proc/version &> /dev/null ; then
    echo -e "${YELLOW}⚠${NC} Running in WSL"
    WSL=true
else
    WSL=false
fi

# Check Python
echo ""
echo -e "${BLUE}[INFO]${NC} Checking Python..."
if command -v python3 &> /dev/null; then
    PY_VER=$(python3 --version | awk '{print $2}')
    PY_MAJOR=$(echo $PY_VER | cut -d. -f1)
    PY_MINOR=$(echo $PY_VER | cut -d. -f2)
    
    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 8 ]; then
        echo -e "${GREEN}✓${NC} Python $PY_VER"
    else
        echo -e "${YELLOW}⚠${NC} Python $PY_VER (需要 >= 3.8)"
    fi
else
    echo -e "${RED}✗${NC} Python not found"
fi

# Check pip
if command -v pip3 &> /dev/null; then
    echo -e "${GREEN}✓${NC} pip3 installed"
else
    echo -e "${RED}✗${NC} pip3 not found"
fi

# Check Mininet
echo ""
echo -e "${BLUE}[INFO]${NC} Checking Mininet..."
if command -v mn &> /dev/null; then
    MN_VER=$(mn --version 2>&1 | head -n1 | awk '{print $2}')
    echo -e "${GREEN}✓${NC} Mininet $MN_VER"
else
    echo -e "${RED}✗${NC} Mininet not found"
    echo -e "   Install: ${YELLOW}sudo apt-get install mininet${NC}"
fi

# Check Open vSwitch
echo ""
echo -e "${BLUE}[INFO]${NC} Checking Open vSwitch..."
if command -v ovs-vsctl &> /dev/null; then
    OVS_VER=$(ovs-vsctl --version | head -n1 | awk '{print $NF}')
    echo -e "${GREEN}✓${NC} Open vSwitch $OVS_VER"
    
    # Check if OVS is running
    if sudo ovs-vsctl show &> /dev/null; then
        echo -e "${GREEN}✓${NC} OVS service is running"
    else
        echo -e "${YELLOW}⚠${NC} OVS service not running"
        echo -e "   Start: ${YELLOW}sudo service openvswitch-switch start${NC}"
    fi
else
    echo -e "${RED}✗${NC} Open vSwitch not found"
    echo -e "   Install: ${YELLOW}sudo apt-get install openvswitch-switch${NC}"
fi

# Check system resources
echo ""
echo -e "${BLUE}[INFO]${NC} Checking system resources..."

# RAM
TOTAL_RAM=$(free -g | awk '/^Mem:/{print $2}')
if [ "$TOTAL_RAM" -ge 8 ]; then
    echo -e "${GREEN}✓${NC} RAM: ${TOTAL_RAM}GB (OK)"
else
    echo -e "${YELLOW}⚠${NC} RAM: ${TOTAL_RAM}GB (Recommended >= 8GB)"
fi

# CPU cores
CPU_CORES=$(nproc)
if [ "$CPU_CORES" -ge 4 ]; then
    echo -e "${GREEN}✓${NC} CPU Cores: $CPU_CORES (OK)"
else
    echo -e "${YELLOW}⚠${NC} CPU Cores: $CPU_CORES (Recommended >= 4)"
fi

# Disk space
DISK_AVAIL=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$DISK_AVAIL" -ge 20 ]; then
    echo -e "${GREEN}✓${NC} Disk Space: ${DISK_AVAIL}GB available (OK)"
else
    echo -e "${YELLOW}⚠${NC} Disk Space: ${DISK_AVAIL}GB (Recommended >= 20GB)"
fi

# Check Python packages
echo ""
echo -e "${BLUE}[INFO]${NC} Checking Python packages..."

check_python_package() {
    if python3 -c "import $1" &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1 not installed"
    fi
}

check_python_package "torch"
check_python_package "tensorflow"
check_python_package "numpy"
check_python_package "pandas"
check_python_package "sklearn"

# Check if Ryu is installed
if python3 -c "import ryu" &> /dev/null; then
    echo -e "${GREEN}✓${NC} ryu"
else
    echo -e "${RED}✗${NC} ryu not installed"
    echo -e "   Install: ${YELLOW}pip3 install ryu${NC}"
fi

# Network tests
echo ""
echo -e "${BLUE}[INFO]${NC} Running network tests..."

# Check if can run sudo
if sudo -n true 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Sudo access available"
    
    # Quick Mininet test
    if command -v mn &> /dev/null; then
        echo -e "${BLUE}[INFO]${NC} Testing Mininet (quick test)..."
        if timeout 10 sudo mn -c &> /dev/null; then
            echo -e "${GREEN}✓${NC} Mininet cleanup successful"
        else
            echo -e "${YELLOW}⚠${NC} Mininet cleanup had issues"
        fi
    fi
else
    echo -e "${YELLOW}⚠${NC} Need sudo for full testing"
fi

# Summary
echo ""
echo "════════════════════════════════════════════════════════════"
echo -e "${BLUE}Summary:${NC}"
echo "════════════════════════════════════════════════════════════"

if [ "$WSL" = true ]; then
    echo -e "${YELLOW}Platform:${NC} WSL (Windows Subsystem for Linux)"
    echo -e "${YELLOW}Note:${NC} Running in WSL environment"
else
    echo -e "${GREEN}Platform:${NC} Native Linux"
fi

echo ""
echo -e "${BLUE}Recommendations:${NC}"

if [[ "$OS" == *"Kali"* ]] || [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
    echo -e "${GREEN}✓${NC} Your OS ($OS) is perfect for this project!"
else
    echo -e "${YELLOW}⚠${NC} Consider using Ubuntu/Kali Linux for best results"
fi

if ! command -v mn &> /dev/null || ! command -v ovs-vsctl &> /dev/null; then
    echo -e "${RED}!${NC} Missing critical components (Mininet/OVS)"
    echo -e "   Run: ${YELLOW}sudo apt-get install mininet openvswitch-switch${NC}"
fi

if ! python3 -c "import torch, tensorflow, ryu" &> /dev/null; then
    echo -e "${YELLOW}⚠${NC} Missing Python packages"
    echo -e "   Run: ${YELLOW}pip3 install -r requirements.txt${NC}"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo -e "${GREEN}Check completed!${NC}"
echo "════════════════════════════════════════════════════════════"
