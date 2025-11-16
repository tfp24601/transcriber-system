"""
Output formatters for transcripts
"""
from typing import List, Dict, Any
from datetime import timedelta


def format_timestamp(seconds: float) -> str:
    """Format seconds as HH:MM:SS"""
    td = timedelta(seconds=seconds)
    hours = int(td.total_seconds() // 3600)
    minutes = int((td.total_seconds() % 3600) // 60)
    secs = int(td.total_seconds() % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_srt_timestamp(seconds: float) -> str:
    """Format seconds as SRT timestamp (HH:MM:SS,mmm)"""
    millis = int(seconds * 1000)
    hours, remainder = divmod(millis, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def segments_to_markdown(
    segments: List[Dict[str, Any]],
    include_timestamps: bool = True,
    include_speakers: bool = False
) -> str:
    """
    Format segments as Markdown
    
    Args:
        segments: List of segments with text, start, end, and optionally speaker
        include_timestamps: Whether to include timestamps
        include_speakers: Whether to include speaker labels
    
    Returns:
        Markdown formatted string
    """
    lines = ["# Transcript\n"]
    
    current_speaker = None
    speaker_block = []
    
    for seg in segments:
        text = seg.get("text", "").strip()
        if not text:
            continue
        
        start = seg.get("start", 0)
        end = seg.get("end", 0)
        speaker = seg.get("speaker")
        
        # Handle speaker changes
        if include_speakers and speaker:
            if speaker != current_speaker:
                # Flush previous speaker block
                if speaker_block:
                    lines.append(" ".join(speaker_block))
                    lines.append("")
                    speaker_block = []
                
                # Start new speaker block
                current_speaker = speaker
                lines.append(f"## {speaker}\n")
            
            # Add text with optional timestamp
            if include_timestamps:
                lines.append(f"**[{format_timestamp(start)}]** {text}")
            else:
                # Flowing text - just concatenate with space
                lines.append(text)
        else:
            # No speakers, just flowing text
            if include_timestamps:
                lines.append(f"**[{format_timestamp(start)}]** {text}")
            else:
                # Pure flowing text - join all segments into paragraphs
                lines.append(text)
    
    # Flush final speaker block if any
    if speaker_block:
        lines.append(" ".join(speaker_block))
    
    # Join everything - if no timestamps/speakers, join with spaces for flowing text
    if not include_timestamps and not include_speakers:
        # Group into paragraphs by combining all segments
        return "# Transcript\n\n" + " ".join(seg.get("text", "").strip() for seg in segments if seg.get("text", "").strip())
    
    return "\n".join(lines)


def segments_to_plain_text(
    segments: List[Dict[str, Any]],
    include_timestamps: bool = False,
    include_speakers: bool = False
) -> str:
    """
    Format segments as plain text
    
    Args:
        segments: List of segments
        include_timestamps: Whether to include timestamps
        include_speakers: Whether to include speaker labels
    
    Returns:
        Plain text string
    """
    lines = []
    
    for seg in segments:
        text = seg.get("text", "").strip()
        if not text:
            continue
        
        parts = []
        
        if include_timestamps:
            start = seg.get("start", 0)
            parts.append(f"[{format_timestamp(start)}]")
        
        if include_speakers and "speaker" in seg:
            parts.append(f"{seg['speaker']}:")
        
        parts.append(text)
        lines.append(" ".join(parts))
    
    return "\n".join(lines)


def segments_to_srt(segments: List[Dict[str, Any]]) -> str:
    """
    Format segments as SRT subtitles
    
    Args:
        segments: List of segments with start, end, and text
    
    Returns:
        SRT formatted string
    """
    blocks = []
    
    for idx, seg in enumerate(segments, start=1):
        text = seg.get("text", "").strip()
        if not text:
            continue
        
        start = seg.get("start", 0)
        end = seg.get("end", 0)
        
        # Include speaker if available
        if "speaker" in seg:
            text = f"{seg['speaker']}: {text}"
        
        block = f"{idx}\n{format_srt_timestamp(start)} --> {format_srt_timestamp(end)}\n{text}\n"
        blocks.append(block)
    
    return "\n".join(blocks)
