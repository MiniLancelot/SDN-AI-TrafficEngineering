#!/bin/bash
# fix_python.sh - Automatic Python 3.13 compatibility fix
# Usage: ./fix_python.sh

set -e  # Exit on error

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Python 3.13 Compatibility Fix for Ryu SDN Controller    ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check current Python version
CURRENT_PYTHON=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "📍 Current Python version: ${YELLOW}${CURRENT_PYTHON}${NC}"

if [[ "$CURRENT_PYTHON" == 3.13* ]]; then
    echo -e "${RED}⚠️  Python 3.13 detected - Ryu compatibility issue!${NC}"
    echo -e "${YELLOW}   Fixing by installing Python 3.11 via pyenv...${NC}"
else
    echo -e "${GREEN}✓ Python version compatible${NC}"
    read -p "Continue with setup anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

echo ""

# 1. Install pyenv
echo -e "${GREEN}📦 Step 1/5: Installing pyenv...${NC}"
if command -v pyenv &> /dev/null; then
    echo -e "${YELLOW}   pyenv already installed${NC}"
else
    echo -e "   Downloading and installing pyenv..."
    curl -fsSL https://pyenv.run | bash
    
    # Setup pyenv for current session
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
    
    # Add to bashrc
    if ! grep -q "PYENV_ROOT" ~/.bashrc; then
        echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
        echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
        echo 'eval "$(pyenv init -)"' >> ~/.bashrc
        echo -e "${GREEN}   ✓ pyenv configuration added to ~/.bashrc${NC}"
    fi
fi

# Check if pyenv is available
if ! command -v pyenv &> /dev/null; then
    # Try to load pyenv manually
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
fi

if ! command -v pyenv &> /dev/null; then
    echo -e "${RED}✗ Failed to install pyenv${NC}"
    echo -e "${YELLOW}Please install manually:${NC}"
    echo -e "  curl https://pyenv.run | bash"
    exit 1
fi

echo -e "${GREEN}   ✓ pyenv installed${NC}"
echo ""

# 2. Install build dependencies
echo -e "${GREEN}📦 Step 2/5: Installing build dependencies...${NC}"
sudo apt-get update -qq
sudo apt-get install -y -qq \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    wget \
    curl \
    llvm \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libffi-dev \
    liblzma-dev \
    > /dev/null 2>&1

echo -e "${GREEN}   ✓ Build dependencies installed${NC}"
echo ""

# 3. Install Python 3.11
echo -e "${GREEN}🐍 Step 3/5: Installing Python 3.11.9...${NC}"
if pyenv versions | grep -q "3.11.9"; then
    echo -e "${YELLOW}   Python 3.11.9 already installed${NC}"
else
    echo -e "   This may take 5-10 minutes..."
    pyenv install 3.11.9
    echo -e "${GREEN}   ✓ Python 3.11.9 installed${NC}"
fi

# Set local version
pyenv local 3.11.9
echo -e "${GREEN}   ✓ Python 3.11.9 set for this directory${NC}"
echo ""

# 4. Verify Python version
PYENV_PYTHON=$(python --version 2>&1 | awk '{print $2}')
echo -e "   Active Python: ${GREEN}${PYENV_PYTHON}${NC}"

if [[ "$PYENV_PYTHON" != 3.11* ]]; then
    echo -e "${RED}✗ Python version mismatch!${NC}"
    echo -e "${YELLOW}Expected: 3.11.x, Got: ${PYENV_PYTHON}${NC}"
    exit 1
fi
echo ""

# 5. Recreate virtual environment
echo -e "${GREEN}🔄 Step 4/5: Setting up virtual environment...${NC}"
if [ -d "venv" ]; then
    echo -e "${YELLOW}   Removing old venv...${NC}"
    rm -rf venv
fi

echo -e "   Creating new venv with Python 3.11..."
python -m venv venv

echo -e "   Activating venv..."
source venv/bin/activate

echo -e "${GREEN}   ✓ Virtual environment created${NC}"
echo ""

# 6. Install Python packages
echo -e "${GREEN}📦 Step 5/5: Installing Python packages...${NC}"
echo -e "   This may take a few minutes..."

pip install --upgrade pip setuptools wheel --quiet

echo -e "   Installing requirements..."
if pip install -r requirements.txt --quiet; then
    echo -e "${GREEN}   ✓ All packages installed successfully${NC}"
else
    echo -e "${RED}✗ Package installation failed${NC}"
    echo -e "${YELLOW}Try running: pip install -r requirements.txt${NC}"
    exit 1
fi
echo ""

# 7. Verify installation
echo -e "${GREEN}✅ Verifying installation...${NC}"

# Check Ryu
if python -c "import ryu" 2>/dev/null; then
    RYU_VERSION=$(python -c "import ryu; print(ryu.__version__)" 2>/dev/null)
    echo -e "   ${GREEN}✓ Ryu ${RYU_VERSION}${NC}"
else
    echo -e "   ${RED}✗ Ryu import failed${NC}"
fi

# Check PyTorch
if python -c "import torch" 2>/dev/null; then
    TORCH_VERSION=$(python -c "import torch; print(torch.__version__)" 2>/dev/null)
    echo -e "   ${GREEN}✓ PyTorch ${TORCH_VERSION}${NC}"
else
    echo -e "   ${YELLOW}⚠ PyTorch not available${NC}"
fi

# Check TensorFlow
if python -c "import tensorflow" 2>/dev/null; then
    TF_VERSION=$(python -c "import tensorflow; print(tensorflow.__version__)" 2>/dev/null)
    echo -e "   ${GREEN}✓ TensorFlow ${TF_VERSION}${NC}"
else
    echo -e "   ${YELLOW}⚠ TensorFlow not available${NC}"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                   Setup Complete! 🎉                       ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "📝 ${YELLOW}Next steps:${NC}"
echo -e "   1. Activate venv:  ${GREEN}source venv/bin/activate${NC}"
echo -e "   2. Run setup:      ${GREEN}./start.sh setup${NC}"
echo -e "   3. Start system:   ${GREEN}./start.sh controller${NC}"
echo ""
echo -e "📚 ${YELLOW}Documentation:${NC}"
echo -e "   - Quick start: ${GREEN}cat QUICK_START.md${NC}"
echo -e "   - Full guide:  ${GREEN}cat DEPLOYMENT_GUIDE.md${NC}"
echo -e "   - Python fix:  ${GREEN}cat PYTHON_FIX.md${NC}"
echo ""

# Check if we need to reload shell for pyenv
if [[ ":$PATH:" != *":$HOME/.pyenv/bin:"* ]]; then
    echo -e "${YELLOW}⚠️  Important: Reload your shell for pyenv to work in new terminals:${NC}"
    echo -e "   ${GREEN}exec \$SHELL${NC}"
    echo ""
fi

echo -e "${GREEN}Happy coding! 🚀${NC}"
