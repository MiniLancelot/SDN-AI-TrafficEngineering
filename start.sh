#!/bin/bash

# Quick Start Script for SDN-AI Traffic Engineering System
# This script helps you quickly set up and run the system

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     SDN-AI Traffic Engineering - Quick Start              ║"
echo "║  AI-powered Traffic Prediction, Load Balancing & QoS      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    local missing_deps=()
    
    if ! command_exists python3; then
        missing_deps+=("python3")
    fi
    
    if ! command_exists pip3; then
        missing_deps+=("python3-pip")
    fi
    
    if ! command_exists mn; then
        missing_deps+=("mininet")
    fi
    
    if ! command_exists ovs-vsctl; then
        missing_deps+=("openvswitch-switch")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        print_info "Please install them first:"
        echo "  sudo apt-get install ${missing_deps[*]}"
        exit 1
    fi
    
    print_success "All prerequisites met!"
}

# Setup virtual environment
setup_venv() {
    print_info "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_info "Virtual environment already exists"
    fi
    
    source venv/bin/activate
    
    print_info "Installing Python packages..."
    pip install -r requirements.txt -q
    
    print_success "Python environment ready!"
}

# Create necessary directories
create_directories() {
    print_info "Creating directories..."
    
    mkdir -p data/{collected,processed,models}
    mkdir -p logs
    mkdir -p results
    
    print_success "Directories created!"
}

# Clean up Mininet
cleanup_mininet() {
    print_info "Cleaning up Mininet..."
    sudo mn -c 2>/dev/null || true
    sudo pkill -9 -f mininet 2>/dev/null || true
    sudo fuser -k 6633/tcp 2>/dev/null || true
    print_success "Mininet cleaned!"
}

# Start controller
start_controller() {
    print_info "Starting SDN Controller..."
    
    source venv/bin/activate
    
    # Kill existing controller if any
    pkill -9 -f "ryu-manager" 2>/dev/null || true
    
    # Start controller in background
    nohup ryu-manager controller/main_controller.py > logs/controller.log 2>&1 &
    
    sleep 3
    
    if pgrep -f "ryu-manager" > /dev/null; then
        print_success "Controller started! (PID: $(pgrep -f ryu-manager))"
        print_info "Log file: logs/controller.log"
    else
        print_error "Failed to start controller"
        exit 1
    fi
}

# Start Mininet
start_mininet() {
    print_info "Starting Mininet topology..."
    
    print_warning "This will open a new terminal with Mininet CLI"
    print_info "Run 'pingall' in Mininet CLI to test connectivity"
    
    # Open in new terminal
    if command_exists gnome-terminal; then
        gnome-terminal -- bash -c "sudo python environment/mininet_topo.py; exec bash"
    elif command_exists xterm; then
        xterm -e "sudo python environment/mininet_topo.py" &
    else
        print_warning "No terminal emulator found. Run manually:"
        echo "  sudo python environment/mininet_topo.py"
    fi
}

# Train models
train_models() {
    print_info "Training AI models..."
    
    source venv/bin/activate
    
    print_info "Training LSTM Traffic Predictor..."
    python ai_models/traffic_predictor.py
    
    print_info "Training DQN Load Balancing Agent..."
    python ai_models/dqn_agent.py
    
    print_success "Models trained and saved!"
}

# Generate traffic
generate_traffic() {
    local scenario=${1:-normal}
    local duration=${2:-120}
    
    print_info "Generating traffic (scenario: $scenario, duration: ${duration}s)..."
    
    source venv/bin/activate
    python environment/traffic_generator.py --scenario "$scenario" --duration "$duration"
}

# Show status
show_status() {
    echo ""
    print_info "System Status:"
    echo "----------------------------------------"
    
    # Check controller
    if pgrep -f "ryu-manager" > /dev/null; then
        echo -e "  Controller: ${GREEN}RUNNING${NC} (PID: $(pgrep -f ryu-manager))"
    else
        echo -e "  Controller: ${RED}STOPPED${NC}"
    fi
    
    # Check Mininet
    if pgrep -f "mininet" > /dev/null; then
        echo -e "  Mininet: ${GREEN}RUNNING${NC}"
    else
        echo -e "  Mininet: ${RED}STOPPED${NC}"
    fi
    
    # Check models
    if [ -f "data/models/lstm_traffic_predictor.pth" ]; then
        echo -e "  LSTM Model: ${GREEN}AVAILABLE${NC}"
    else
        echo -e "  LSTM Model: ${YELLOW}NOT TRAINED${NC}"
    fi
    
    if [ -f "data/models/dqn_load_balancer.pth" ]; then
        echo -e "  DQN Agent: ${GREEN}AVAILABLE${NC}"
    else
        echo -e "  DQN Agent: ${YELLOW}NOT TRAINED${NC}"
    fi
    
    echo "----------------------------------------"
}

# Stop all services
stop_all() {
    print_info "Stopping all services..."
    
    pkill -9 -f "ryu-manager" 2>/dev/null || true
    sudo mn -c 2>/dev/null || true
    sudo pkill -9 -f mininet 2>/dev/null || true
    
    print_success "All services stopped!"
}

# Main menu
show_menu() {
    echo ""
    echo "Choose an option:"
    echo "  1) Full Setup (install + train + run)"
    echo "  2) Start Controller"
    echo "  3) Start Mininet"
    echo "  4) Train AI Models"
    echo "  5) Generate Traffic"
    echo "  6) Show Status"
    echo "  7) Stop All"
    echo "  8) Cleanup"
    echo "  9) Exit"
    echo ""
}

# Main script
main() {
    if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
        echo "Usage: $0 [option]"
        echo ""
        echo "Options:"
        echo "  setup       - Setup environment"
        echo "  controller  - Start controller"
        echo "  mininet     - Start Mininet"
        echo "  train       - Train AI models"
        echo "  traffic     - Generate traffic"
        echo "  status      - Show status"
        echo "  stop        - Stop all services"
        echo "  cleanup     - Clean up Mininet"
        echo ""
        exit 0
    fi
    
    case "$1" in
        setup)
            check_prerequisites
            create_directories
            setup_venv
            ;;
        controller)
            start_controller
            ;;
        mininet)
            cleanup_mininet
            start_mininet
            ;;
        train)
            train_models
            ;;
        traffic)
            generate_traffic "${2:-normal}" "${3:-120}"
            ;;
        status)
            show_status
            ;;
        stop)
            stop_all
            ;;
        cleanup)
            cleanup_mininet
            ;;
        *)
            # Interactive mode
            while true; do
                show_menu
                read -p "Enter choice [1-9]: " choice
                
                case $choice in
                    1)
                        check_prerequisites
                        create_directories
                        setup_venv
                        train_models
                        start_controller
                        start_mininet
                        ;;
                    2)
                        start_controller
                        ;;
                    3)
                        cleanup_mininet
                        start_mininet
                        ;;
                    4)
                        train_models
                        ;;
                    5)
                        read -p "Enter scenario (normal/congestion/voip/loadbalance/ddos): " scenario
                        read -p "Enter duration (seconds): " duration
                        generate_traffic "$scenario" "$duration"
                        ;;
                    6)
                        show_status
                        ;;
                    7)
                        stop_all
                        ;;
                    8)
                        cleanup_mininet
                        ;;
                    9)
                        print_info "Goodbye!"
                        exit 0
                        ;;
                    *)
                        print_error "Invalid choice"
                        ;;
                esac
                
                echo ""
                read -p "Press Enter to continue..."
            done
            ;;
    esac
}

# Run main
main "$@"
