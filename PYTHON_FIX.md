# 🐍 Python 3.13 Compatibility Fix

## ⚠️ Problem

```
AttributeError: 'types.SimpleNamespace' object has no attribute 'get_script_args'
```

**Root Cause**: Official Ryu 4.34 has setuptools compatibility issues (affects Python 3.11+)

---

## ✅ Solution - Quick Fix (2 minutes)

### Option A: Use Ryu Fork (RECOMMENDED - FASTEST)

```bash
# Activate venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install from requirements.txt (already uses Ryu fork)
pip install -r requirements.txt

# Verify
python -c "import ryu; print('Ryu OK!')"
```

**✅ Xong! Requirements.txt đã dùng faucetsdn/ryu fork.**

---

## 🔧 Alternative: Manual Install with pyenv

### Step 1: Install build dependencies and pyenv

```bash
# Install build dependencies (CRITICAL - must do first!)
sudo apt-get update
sudo apt-get install -y build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev curl wget llvm \
    libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
    libffi-dev liblzma-dev

# Install pyenv
curl https://pyenv.run | bash

# Add to shell config
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

# Reload shell
exec $SHELL
```

### Step 2: Install Python 3.11

```bash
# Load pyenv for current session (CRITICAL STEP!)
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# Install Python 3.11.9
pyenv install 3.11.9

# Set version for this project directory
cd SDN-AI-TrafficEngineering
echo "3.11.9" > .python-version

# Verify
python --version  # Should show: Python 3.11.9
```

### Step 3: Recreate Virtual Environment

```bash
# Remove old venv (if exists)
rm -rf venv

# Create new venv with Python 3.11
python -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install requirements
pip install -r requirements.txt

# Verify Ryu
python -c "import ryu; print('Ryu OK!')"
```

---

## 🎯 Complete Setup Script

Copy-paste này vào terminal:

```bash
#!/bin/bash
set -e

echo "🔧 Fixing Python 3.13 compatibility issue..."

# 1. Install pyenv
if ! command -v pyenv &> /dev/null; then
    echo "📦 Installing pyenv..."
    curl https://pyenv.run | bash
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
    
    # Add to bashrc
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
    echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
    echo 'eval "$(pyenv init -)"' >> ~/.bashrc
fi

# 2. Install Python 3.11
echo "🐍 Installing Python 3.11.9..."
pyenv install -s 3.11.9
pyenv local 3.11.9

# 3. Recreate venv
echo "🔄 Recreating virtual environment..."
rm -rf venv
python -m venv venv
source venv/bin/activate

# 4. Install packages
echo "📦 Installing Python packages..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# 5. Verify
echo "✅ Verifying installation..."
python -c "import ryu; print('✓ Ryu installed successfully')"
python -c "import torch; print('✓ PyTorch installed successfully')"

echo ""
echo "🎉 Setup complete!"
echo "Run: source venv/bin/activate"
```

Save as `fix_python.sh` and run:

```bash
chmod +x fix_python.sh
./fix_python.sh
```

---

## 🔍 Alternative Solutions

### Option B: Build Python 3.11 from Source (if pyenv fails)

```bash
# Install build dependencies
sudo apt-get update
sudo apt-get install -y build-essential zlib1g-dev libncurses5-dev \
    libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev \
    libsqlite3-dev wget libbz2-dev

# Download and build Python 3.11
cd /tmp
wget https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz
tar -xf Python-3.11.9.tgz
cd Python-3.11.9
./configure --enable-optimizations
make -j $(nproc)
sudo make altinstall

# Verify
python3.11 --version

# Use it for the project
cd ~/SDN-AI-TrafficEngineering
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Option C: Use Ryu Fork (experimental)

```bash
# Activate venv
source venv/bin/activate

# Install dependencies first (skip ryu)
grep -v "^ryu" requirements.txt | grep -v "^#" | grep -v "^git+" | pip install -r /dev/stdin

# Install Ryu fork that MAY support Python 3.13
pip install git+https://github.com/faucetsdn/ryu.git@master

# Verify
python -c "import ryu; print('Ryu fork installed')"
```

**⚠️ Warning**: Option C is experimental and may have bugs!

---

## 🧪 Verify Everything Works

```bash
# Activate venv
source venv/bin/activate

# Check Python version
python --version  # Should be 3.11.x

# Check all packages
python -c "
import sys
import ryu
import torch
import tensorflow
print(f'Python: {sys.version}')
print(f'Ryu: {ryu.__version__}')
print(f'PyTorch: {torch.__version__}')
print(f'TensorFlow: {tensorflow.__version__}')
print('✅ All packages OK!')
"

# Test Ryu
ryu-manager --version
```

Expected output:
```
Python: 3.11.9 ...
Ryu: 4.34
PyTorch: 2.x.x
TensorFlow: 2.x.x
✅ All packages OK!
```

---

## 📚 Why This Happens

**Ryu 4.34** uses deprecated setuptools APIs in `ryu/hooks.py`. The `easy_install.get_script_args` was removed from setuptools.

**Timeline**:
- Ryu 4.34: Released ~2020
- Setuptools 60+: Removed deprecated APIs
- Impact: Affects Python 3.11, 3.12, 3.13 with newer setuptools

**Solution**: Use faucetsdn/ryu fork which has the fix (already in requirements.txt!)

---

## 🎓 Understanding pyenv

**pyenv** là tool để manage multiple Python versions:

```bash
# List available versions
pyenv install --list | grep "3.11"

# Install specific version
pyenv install 3.11.9

# Set global default
pyenv global 3.11.9

# Set for current directory (creates .python-version file)
pyenv local 3.11.9

# Check which Python is active
pyenv version

# List installed versions
pyenv versions
```

**Advantages**:
- ✅ No sudo needed
- ✅ Multiple Python versions coexist
- ✅ Per-project Python version
- ✅ Easy to switch
- ✅ Doesn't affect system Python

---

## 🔧 Troubleshooting

### Error: "pyenv: command not found" after installation

```bash
# Manually set PATH
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# Then reload
exec $SHELL
```

### Error: "BUILD FAILED" when installing Python

```bash
# Install build dependencies
sudo apt-get update
sudo apt-get install -y make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
    libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
    libffi-dev liblzma-dev

# Try again
pyenv install 3.11.9
```

### Error: "No module named '_ctypes'" when running Python

```bash
# Install libffi
sudo apt-get install libffi-dev -y

# Rebuild Python
pyenv uninstall 3.11.9
pyenv install 3.11.9
```

---

## ✅ Final Checklist

- [ ] pyenv installed
- [ ] Python 3.11.9 installed via pyenv
- [ ] `.python-version` file exists in project directory
- [ ] `python --version` shows 3.11.9
- [ ] Virtual environment recreated
- [ ] All packages installed successfully
- [ ] `import ryu` works without error
- [ ] Ready to run the controller!

---

## 🚀 Next Steps

After fixing Python:

1. **Test Controller**:
   ```bash
   ./start.sh setup
   ./start.sh controller
   ```

2. **Read Documentation**:
   - [QUICK_START.md](QUICK_START.md) - Fast setup
   - [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Detailed guide

3. **Run First Test**:
   ```bash
   # Terminal 1
   ./start.sh controller
   
   # Terminal 2
   sudo ./start.sh mininet
   ```

---

**🎉 You're all set! Happy coding!**
