"""
GPU monitoring utilities for VRAM usage tracking
"""
import subprocess
import re
from typing import List, Dict, Any, Optional


def get_gpu_processes() -> List[Dict[str, Any]]:
    """
    Get detailed information about all GPU processes
    
    Returns:
        List of process dictionaries with PID, name, VRAM, and command
    """
    try:
        # Get GPU processes
        result = subprocess.run(
            ['nvidia-smi', '--query-compute-apps=pid,used_memory', '--format=csv,noheader'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return []
        
        processes = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
                
            parts = line.split(',')
            if len(parts) < 2:
                continue
                
            pid = parts[0].strip()
            mem_str = parts[1].strip()
            mem_mb = int(re.search(r'\d+', mem_str).group())
            
            # Get process command
            try:
                cmd_result = subprocess.run(
                    ['ps', '-p', pid, '-o', 'args='],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                cmd = cmd_result.stdout.strip()
                
                # Identify the process
                name = _identify_process(cmd, pid)
                
                processes.append({
                    'pid': int(pid),
                    'name': name,
                    'vram_mb': mem_mb,
                    'vram_gb': round(mem_mb / 1024, 2),
                    'command': cmd[:100]
                })
            except Exception:
                continue
        
        # Sort by VRAM usage (descending)
        processes.sort(key=lambda x: x['vram_mb'], reverse=True)
        return processes
        
    except Exception:
        return []


def _identify_process(cmd: str, pid: str) -> str:
    """Identify what a process is based on its command line"""
    cmd_lower = cmd.lower()
    
    if 'transcriber' in cmd_lower or 'whisper' in cmd_lower:
        return "🎙️ Transcriber (Whisper)"
    elif 'open-webui' in cmd_lower or 'open_webui' in cmd_lower:
        return "🤖 Open WebUI"
    elif 'uvicorn' in cmd_lower and '8000' in cmd:
        return "🗄️ Supabase Kong (API Gateway)"
    elif 'uvicorn' in cmd_lower:
        return "🔧 API Server"
    elif 'main.py' in cmd and 'listen' in cmd:
        return "🤖 LLM Server"
    elif 'rustdesk' in cmd_lower:
        return "🖥️ RustDesk"
    elif 'multiprocessing' in cmd or 'spawn_main' in cmd:
        return "⚙️ Worker Process"
    elif 'python' in cmd_lower:
        # Try to extract script name
        match = re.search(r'([^/\s]+\.py)', cmd)
        if match:
            return f"🐍 {match.group(1)}"
        return "🐍 Python Process"
    else:
        # Get process name from command
        parts = cmd.split()
        if parts:
            name = parts[0].split('/')[-1]
            return f"❓ {name[:20]}"
        return "❓ Unknown"


def get_gpu_memory_info() -> Dict[str, Any]:
    """
    Get overall GPU memory information
    
    Returns:
        Dictionary with total, used, free memory in MB and GB
    """
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.used,memory.free,memory.total,name', '--format=csv,noheader,nounits'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return {}
        
        parts = result.stdout.strip().split(',')
        if len(parts) < 4:
            return {}
        
        used_mb = int(parts[0].strip())
        free_mb = int(parts[1].strip())
        total_mb = int(parts[2].strip())
        gpu_name = parts[3].strip()
        
        return {
            'gpu_name': gpu_name,
            'total_mb': total_mb,
            'total_gb': round(total_mb / 1024, 2),
            'used_mb': used_mb,
            'used_gb': round(used_mb / 1024, 2),
            'free_mb': free_mb,
            'free_gb': round(free_mb / 1024, 2),
            'usage_percent': round((used_mb / total_mb) * 100, 1)
        }
    except Exception:
        return {}


def get_full_gpu_status() -> Dict[str, Any]:
    """
    Get complete GPU status including processes and memory
    
    Returns:
        Dictionary with memory info and process list
    """
    memory_info = get_gpu_memory_info()
    processes = get_gpu_processes()
    
    # Calculate process VRAM total
    process_vram_mb = sum(p['vram_mb'] for p in processes)
    
    return {
        'memory': memory_info,
        'processes': processes,
        'process_count': len(processes),
        'process_vram_mb': process_vram_mb,
        'process_vram_gb': round(process_vram_mb / 1024, 2),
        'available': bool(memory_info)
    }
