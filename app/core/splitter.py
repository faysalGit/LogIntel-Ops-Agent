import re
from typing import List, Dict, Any, Tuple

class LogMetadataSplitter:
    """
    Production-grade Log Processing and Micro-Chunking Engine.
    Provides pre-flight file validation checks and strict line-by-line 
    isolation to prevent data bleeding across different transactional boundaries.
    """
    def __init__(self):
        # Strict whole-word word-boundary regex patterns for log level signatures
        self.log_level_pattern = re.compile(r'\b(INFO|WARN|ERROR|DEBUG|FATAL|CRITICAL)\b')
        # Standard ISO-like timestamp signature pattern (e.g., 2026-08-16 14:15:22)
        self.timestamp_pattern = re.compile(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}')
        # Job ID extraction pattern with word boundary guards
        self.job_id_pattern = re.compile(r'\bjob[-_\s]?id\s*[:=\s]*\s*([0-9]+)\b', re.IGNORECASE)

    def validate_log_cleanliness(self, log_text: str) -> Tuple[bool, str]:
        """
        Pre-flight sanity check to ensure the uploaded file contains genuine operational log patterns.
        Prevents arbitrary text, markdown documentation, or random files from corrupting indices.
        """
        if not log_text.strip():
            return False, "The uploaded file is completely empty."

        # Scan the first 50 lines to establish a structural profile sample matrix
        lines = log_text.splitlines()[:50]
        sample_text = "\n".join(lines)

        timestamp_matches = len(self.timestamp_pattern.findall(sample_text))
        loglevel_matches = len(self.log_level_pattern.findall(sample_text))

        # Strict validation constraint matching whole word bounded logs
        if timestamp_matches == 0 and loglevel_matches == 0:
            return False, "Structural log signatures (Timestamps or Log Levels) are entirely missing."

        return True, "Pre-flight log validation checks passed successfully."

    def parse_raw_text(self, log_text: str) -> List[Dict[str, Any]]:
        """
        Processes logs line-by-line into isolated micro-chunks based on timestamp occurrences.
        Guarantees separate errors or timestamps never bleed into neighboring context records.
        """
        lines = log_text.splitlines()
        chunks = []
        current_chunk_lines = []
        
        for line in lines:
            # If a line contains a fresh timestamp anchoring token, commit previous block context
            if self.timestamp_pattern.search(line) and current_chunk_lines:
                chunk_payload = self._build_chunk_payload(current_chunk_lines)
                if chunk_payload:
                    chunks.append(chunk_payload)
                current_chunk_lines = [line]
            else:
                current_chunk_lines.append(line)
                
        # Commit trailing block elements leftover in loop queues
        if current_chunk_lines:
            chunk_payload = self._build_chunk_payload(current_chunk_lines)
            if chunk_payload:
                chunks.append(chunk_payload)
                
        return chunks

    def _build_chunk_payload(self, line_buffer: List[str]) -> Dict[str, Any]:
        """Assembles buffered line sequences into structured micro-chunks with isolated metadata arrays."""
        combined_text = "\n".join(line_buffer).strip()
        if not combined_text:
            return {}

        # Extract structural tracking tokens specific to this text boundary frame
        job_ids = [int(jid) for jid in self.job_id_pattern.findall(combined_text)]
        log_levels = list(set(self.log_level_pattern.findall(combined_text)))
        
        has_stack_trace = "exception" in combined_text.lower() or "at " in combined_text.lower()
        
        # Grab first timestamp match as chronological bounding anchor
        ts_match = self.timestamp_pattern.search(combined_text)
        timestamp_boundary = ts_match.group(0) if ts_match else "N/A"

        return {
            "text": combined_text,
            "metadata": {
                "job_ids": job_ids,
                "log_levels": log_levels,
                "has_stack_trace": has_stack_trace,
                "timestamp_boundary": timestamp_boundary
            }
        }
