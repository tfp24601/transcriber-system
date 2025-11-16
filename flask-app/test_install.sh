#!/bin/bash

echo "🔍 Transcriber Installation Test"
echo "================================"
echo ""

# Check Python version
echo "1️⃣  Checking Python version..."
python_version=$(python3 --version 2>&1)
echo "   ✓ $python_version"
echo ""

# Check virtual environment
echo "2️⃣  Checking virtual environment..."
if [ -d ".venv" ]; then
    echo "   ✓ Virtual environment exists"
else
    echo "   ❌ Virtual environment not found"
    echo "   Run: python3 -m venv .venv"
    exit 1
fi
echo ""

# Check .env file
echo "3️⃣  Checking environment configuration..."
if [ -f ".env" ]; then
    echo "   ✓ .env file exists"
    
    # Check for API keys
    if grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
        echo "   ✓ OpenAI API key configured"
    else
        echo "   ℹ️  OpenAI API key not set (optional)"
    fi
    
    if grep -q "ASSEMBLYAI_API_KEY=" .env 2>/dev/null && ! grep -q "ASSEMBLYAI_API_KEY=your" .env; then
        echo "   ✓ AssemblyAI API key configured"
    else
        echo "   ℹ️  AssemblyAI API key not set (optional)"
    fi
    
    if grep -q "HF_TOKEN=hf_" .env 2>/dev/null; then
        echo "   ✓ Hugging Face token configured"
    else
        echo "   ℹ️  Hugging Face token not set (needed for local diarization)"
    fi
else
    echo "   ⚠️  .env file not found"
    echo "   Run: cp .env.example .env"
    echo "   Then edit .env with your API keys"
fi
echo ""

# Check GPU
echo "4️⃣  Checking GPU availability..."
if command -v nvidia-smi &> /dev/null; then
    gpu_info=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
    if [ ! -z "$gpu_info" ]; then
        echo "   ✓ GPU detected: $gpu_info"
    else
        echo "   ⚠️  nvidia-smi found but no GPU detected"
    fi
else
    echo "   ℹ️  nvidia-smi not found (CPU mode only)"
fi
echo ""

# Check dependencies
echo "5️⃣  Checking Python dependencies..."
source .venv/bin/activate 2>/dev/null

if python -c "import flask" 2>/dev/null; then
    echo "   ✓ Flask installed"
else
    echo "   ❌ Flask not installed"
    echo "   Run: pip install -r requirements.txt"
fi

if python -c "import faster_whisper" 2>/dev/null; then
    echo "   ✓ faster-whisper installed"
else
    echo "   ❌ faster-whisper not installed"
fi

if python -c "import openai" 2>/dev/null; then
    echo "   ✓ openai installed"
else
    echo "   ℹ️  openai not installed (needed for OpenAI backend)"
fi

if python -c "import assemblyai" 2>/dev/null; then
    echo "   ✓ assemblyai installed"
else
    echo "   ℹ️  assemblyai not installed (needed for AssemblyAI backend)"
fi

if python -c "import pyannote.audio" 2>/dev/null; then
    echo "   ✓ pyannote.audio installed"
else
    echo "   ℹ️  pyannote.audio not installed (needed for local diarization)"
fi

echo ""
echo "6️⃣  Checking application files..."
if [ -f "app.py" ]; then
    echo "   ✓ app.py exists"
else
    echo "   ❌ app.py not found"
fi

if [ -d "utils" ]; then
    echo "   ✓ utils/ directory exists"
else
    echo "   ❌ utils/ directory not found"
fi

if [ -d "templates" ]; then
    echo "   ✓ templates/ directory exists"
else
    echo "   ❌ templates/ directory not found"
fi

echo ""
echo "================================"
echo "✅ Installation test complete!"
echo ""
echo "To start the application:"
echo "  1. Activate venv: source .venv/bin/activate"
echo "  2. Configure .env file with your API keys"
echo "  3. Run: python app.py"
echo "  4. Visit: http://localhost:5000"
echo ""
