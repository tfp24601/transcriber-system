"""
On-demand diarization module with VRAM management
"""
import logging
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
import gc

logger = logging.getLogger(__name__)

# Global model cache - only loaded when needed
_diarization_model = None
_model_device = None


def load_diarization_model(hf_token: str, device: str = "cuda"):
    """
    Load pyannote diarization model on-demand
    
    Args:
        hf_token: Hugging Face token for model access
        device: Device to load model on (cuda/cpu)
    
    Returns:
        Loaded diarization pipeline
    """
    global _diarization_model, _model_device
    
    if _diarization_model is not None and _model_device == device:
        logger.info("Diarization model already loaded")
        return _diarization_model
    
    try:
        import torch
        from pyannote.audio import Pipeline
        
        logger.info(f"Loading pyannote diarization model on {device}...")
        model_name = os.getenv("DIARIZATION_MODEL", "pyannote/speaker-diarization-3.1")
        
        # Try new API first (token=), fall back to old API (use_auth_token=)
        try:
            pipeline = Pipeline.from_pretrained(
                model_name,
                token=hf_token
            )
        except TypeError:
            # Fallback for older pyannote versions
            pipeline = Pipeline.from_pretrained(
                model_name,
                use_auth_token=hf_token
            )
        
        # Try to move to GPU, but fall back to CPU if there are issues
        if device == "cuda" and torch.cuda.is_available():
            try:
                pipeline.to(torch.device("cuda"))
                _model_device = "cuda"
                logger.info("Diarization model loaded on CUDA")
            except RuntimeError as e:
                if "cuDNN" in str(e) or "CUDNN" in str(e):
                    logger.warning(f"cuDNN error when moving to GPU: {e}")
                    logger.warning("Falling back to CPU for diarization")
                    _model_device = "cpu"
                    # Pipeline is already on CPU by default
                else:
                    raise
        else:
            _model_device = "cpu"
            logger.info("Diarization model loaded on CPU")
        
        _diarization_model = pipeline
        logger.info("Diarization model loaded successfully")
        return _diarization_model
        
    except Exception as e:
        logger.error(f"Failed to load diarization model: {e}")
        raise


def unload_diarization_model():
    """
    Unload diarization model and free VRAM
    """
    global _diarization_model, _model_device
    
    if _diarization_model is None:
        logger.info("No diarization model to unload")
        return
    
    try:
        import torch
        
        logger.info("Unloading diarization model...")
        
        # Delete the model
        del _diarization_model
        _diarization_model = None
        _model_device = None
        
        # Force garbage collection
        gc.collect()
        
        # Clear CUDA cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        
        logger.info("Diarization model unloaded and VRAM freed")
        
    except Exception as e:
        logger.error(f"Error unloading diarization model: {e}")


def diarize_audio(
    audio_path: str,
    hf_token: str,
    min_speakers: Optional[int] = None,
    max_speakers: Optional[int] = None,
    device: str = "cuda",
    auto_unload: bool = True
) -> List[Dict[str, Any]]:
    """
    Perform speaker diarization on audio file
    
    Args:
        audio_path: Path to audio file
        hf_token: Hugging Face token
        min_speakers: Minimum number of speakers
        max_speakers: Maximum number of speakers
        device: Device to use (cuda/cpu)
        auto_unload: Whether to unload model after processing
    
    Returns:
        List of diarization segments with speaker labels
    """
    try:
        # Load model
        pipeline = load_diarization_model(hf_token, device)
        
        # Run diarization
        logger.info(f"Running diarization on {audio_path}...")
        diarization = pipeline(
            audio_path,
            min_speakers=min_speakers,
            max_speakers=max_speakers
        )
        
        # Convert to list of segments
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                "start": turn.start,
                "end": turn.end,
                "speaker": speaker
            })
        
        logger.info(f"Diarization complete: {len(segments)} segments found")
        
        # Auto-unload if requested
        if auto_unload:
            unload_diarization_model()
        
        return segments
        
    except Exception as e:
        logger.error(f"Diarization failed: {e}")
        # Attempt cleanup even on error
        if auto_unload:
            try:
                unload_diarization_model()
            except:
                pass
        raise


def assign_speakers_to_segments(
    transcription_segments: List[Dict[str, Any]],
    diarization_segments: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Assign speaker labels to transcription segments based on time overlap
    
    Args:
        transcription_segments: List of transcription segments with start/end times
        diarization_segments: List of diarization segments with speaker labels
    
    Returns:
        Transcription segments with speaker labels added
    """
    logger.info("Assigning speakers to transcription segments...")
    
    for seg in transcription_segments:
        seg_start = seg.get("start", 0)
        seg_end = seg.get("end", 0)
        
        # Find best matching speaker based on time overlap
        best_speaker = "SPEAKER_UNKNOWN"
        max_overlap = 0
        
        for diar_seg in diarization_segments:
            overlap_start = max(seg_start, diar_seg["start"])
            overlap_end = min(seg_end, diar_seg["end"])
            overlap = max(0, overlap_end - overlap_start)
            
            if overlap > max_overlap:
                max_overlap = overlap
                best_speaker = diar_seg["speaker"]
        
        seg["speaker"] = best_speaker
    
    logger.info("Speaker assignment complete")
    return transcription_segments


def is_model_loaded() -> bool:
    """Check if diarization model is currently loaded"""
    return _diarization_model is not None


def get_vram_usage() -> Dict[str, Any]:
    """Get current VRAM usage information"""
    try:
        import torch
        
        if not torch.cuda.is_available():
            return {"available": False}
        
        return {
            "available": True,
            "device_name": torch.cuda.get_device_name(0),
            "allocated_gb": torch.cuda.memory_allocated(0) / 1024**3,
            "reserved_gb": torch.cuda.memory_reserved(0) / 1024**3,
            "model_loaded": is_model_loaded()
        }
    except:
        return {"available": False}
