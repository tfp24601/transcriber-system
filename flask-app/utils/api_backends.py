"""
API backend integrations for OpenAI Whisper and AssemblyAI
"""
import logging
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
import time

logger = logging.getLogger(__name__)


def transcribe_with_openai(
    audio_path: str,
    api_key: str,
    model: str = "whisper-1",
    language: Optional[str] = None,
    temperature: float = 0.0,
    response_format: str = "verbose_json"
) -> Dict[str, Any]:
    """
    Transcribe audio using OpenAI Whisper API
    
    Args:
        audio_path: Path to audio file
        api_key: OpenAI API key
        model: Model name (whisper-1)
        language: Language code (optional)
        temperature: Sampling temperature
        response_format: Response format (verbose_json includes timestamps)
    
    Returns:
        Dict with transcript and segments
    """
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=api_key)
        
        logger.info(f"Transcribing with OpenAI Whisper API: {audio_path}")
        
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                language=language if language and language != "auto" else None,
                temperature=temperature,
                response_format=response_format
            )
        
        # Parse response based on format
        if response_format == "verbose_json":
            result = {
                "text": transcript.text,
                "language": transcript.language,
                "duration": transcript.duration,
                "segments": [
                    {
                        "start": seg["start"],
                        "end": seg["end"],
                        "text": seg["text"]
                    }
                    for seg in (transcript.segments or [])
                ]
            }
        else:
            result = {
                "text": transcript.text if hasattr(transcript, "text") else str(transcript),
                "segments": []
            }
        
        logger.info("OpenAI transcription complete")
        return result
        
    except Exception as e:
        logger.error(f"OpenAI transcription failed: {e}")
        raise


def diarize_with_assemblyai(
    audio_path: str,
    api_key: str,
    min_speakers: Optional[int] = None,
    max_speakers: Optional[int] = None
) -> Dict[str, Any]:
    """
    Transcribe and diarize audio using AssemblyAI
    
    Args:
        audio_path: Path to audio file
        api_key: AssemblyAI API key
        min_speakers: Minimum number of speakers
        max_speakers: Maximum number of speakers
    
    Returns:
        Dict with transcript and diarized segments
    """
    try:
        import assemblyai as aai
        
        aai.settings.api_key = api_key
        
        logger.info(f"Transcribing and diarizing with AssemblyAI: {audio_path}")
        
        config = aai.TranscriptionConfig(
            speaker_labels=True,
            speakers_expected=max_speakers
        )
        
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_path, config=config)
        
        if transcript.status == aai.TranscriptStatus.error:
            raise Exception(f"AssemblyAI error: {transcript.error}")
        
        # Wait for completion with polling
        while transcript.status not in [aai.TranscriptStatus.completed, aai.TranscriptStatus.error]:
            logger.info("Waiting for AssemblyAI transcription...")
            time.sleep(3)
            transcript = transcriber.get_transcript(transcript.id)
        
        if transcript.status == aai.TranscriptStatus.error:
            raise Exception(f"AssemblyAI error: {transcript.error}")
        
        # Build segments with speaker labels
        segments = []
        for utterance in (transcript.utterances or []):
            segments.append({
                "start": utterance.start / 1000.0,  # Convert ms to seconds
                "end": utterance.end / 1000.0,
                "text": utterance.text,
                "speaker": f"SPEAKER_{utterance.speaker}"
            })
        
        result = {
            "text": transcript.text,
            "segments": segments,
            "speakers_detected": len(set(s["speaker"] for s in segments))
        }
        
        logger.info(f"AssemblyAI diarization complete: {result['speakers_detected']} speakers")
        return result
        
    except Exception as e:
        logger.error(f"AssemblyAI diarization failed: {e}")
        raise
