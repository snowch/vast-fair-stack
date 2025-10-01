#!/bin/bash
# run_jupyterlab.sh - For VAST Fair Stack Demo

cd ~/vast-fair-stack

# Activate virtual environment
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️  No virtual environment found!"
    echo "Run ./setup.sh first to install dependencies"
    exit 1
fi

# Check if JupyterLab is installed
if ! command -v jupyter-lab &> /dev/null; then
    echo "📦 Installing JupyterLab..."
    pip install jupyterlab ipykernel
fi

# Get the VM's IP address
VM_IP=$(hostname -I | awk '{print $1}')

echo "=================================================="
echo "Starting JupyterLab Server"
echo "=================================================="
echo ""
echo "Access from your browser:"
echo "  http://${VM_IP}:8888"
echo "  or"
echo "  http://localhost:8888 (if on same machine)"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================================="
echo ""

export PYTHONPATH="${PWD}/lib:${PYTHONPATH:-}"

# Run JupyterLab
jupyter lab \
    --ip=0.0.0.0 \
    --port=8888 \
    --no-browser \
    --allow-root \
    --ServerApp.allow_origin='*' \
    --ServerApp.token='' \
    --ServerApp.password=''

# Note: Token/password disabled for demo convenience
# For production, remove those last two lines and set a password
