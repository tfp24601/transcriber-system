#!/bin/bash
# Helper script to install cuDNN 9 for CUDA 12
# Created: October 2, 2025

set -euo pipefail

echo "=================================================="
echo "cuDNN 9 Installation Helper"
echo "=================================================="
echo ""

# Check if we're in Downloads directory
if [ ! -f cudnn-local-repo-ubuntu2404-9.*.deb ]; then
    echo "ERROR: cuDNN 9 .deb file not found in current directory!"
    echo ""
    echo "Please download cuDNN 9 first:"
    echo "1. Visit: https://developer.nvidia.com/cudnn-downloads"
    echo "2. Login with NVIDIA Developer account (free)"
    echo "3. Select: Linux → x86_64 → Ubuntu → 24.04 → deb (local)"
    echo "4. Download the file to ~/Downloads/"
    echo "5. cd ~/Downloads && run this script again"
    echo ""
    exit 1
fi

# Get the filename
DEB_FILE=$(ls cudnn-local-repo-ubuntu2404-9.*.deb)
echo "Found cuDNN package: $DEB_FILE"
echo ""

# Confirm with user
read -p "Install cuDNN 9? This will replace cuDNN 8.9.2. (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Installation cancelled."
    exit 0
fi

echo ""
echo "Step 1: Removing cuDNN 8.9.2..."
sudo apt remove --purge nvidia-cudnn -y

echo ""
echo "Step 2: Installing cuDNN 9 repository..."
sudo dpkg -i "$DEB_FILE"

echo ""
echo "Step 3: Adding cuDNN GPG key..."
sudo cp /var/cudnn-local-repo-*/cudnn-*-keyring.gpg /usr/share/keyrings/

echo ""
echo "Step 4: Updating package list..."
sudo apt update

echo ""
echo "Step 5: Installing libcudnn9-cuda-12..."
sudo apt install libcudnn9-cuda-12 -y

echo ""
echo "Step 6: Verifying installation..."
ldconfig -p | grep cudnn | head -5

echo ""
echo "=================================================="
echo "cuDNN 9 Installation Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Restart Gunicorn:"
echo "   cd /home/ben/SolWorkingFolder/CustomSoftware/transcriber/flask-app"
echo "   pkill gunicorn"
echo "   ./run_gunicorn.sh"
echo ""
echo "2. Test transcription:"
echo "   Visit: http://localhost:5000"
echo "   Or: curl http://localhost:5000/healthz"
echo ""
