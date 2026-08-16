import re
from typing import List, Dict, Any, Tuple

class LogMetadataSplitter:
    """
    A production-grade log parser that enforces strict atomic micro-chunking.
    Ensures each standalone log statement and its localized stack trace forms
    an isolated context boundary, preventing cross-contamination of JobIDs.
    """
    def __init__(self):
        # Match standard ISO timestamps or standard log time brackets
        self.log_start_regex = re.compile(r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})')
        
        # Whole-word only lookups to prevent false-positive substring matches like "OpenAPI"
        self.job_id_regex = re.compile(r'\bjob[-_\s]?id\s*[:=\s]*\s*([0-9]+)\b', re.IGNORECASE)
        self.trace_id_regex = re.compile(r'\btrace[-_\s]?id\s*[:=\s]*\s*([a-zA-Z0-9_-]+)\b', re.IGNORECASE)
        self.loglevel_regex = re.compile(r'\b(INFO|ERROR|WARN|DEBUG|FATAL|CRITICAL)\b')

    def validate_log_file(self, content: str) -> Tuple[bool, str]:
        """
        Runs full pre-flight structural checks on file buffers.
        Rejects non-log text assets cleanly.
        """
        lines = content.splitlines()[:50]
        sample_text = "\n".join(lines)
        
        timestamp_matches = len(self.log_start_regex.findall(sample_text))
        loglevel_matches = len(self.loglevel_regex.findall(sample_text))
        
        if timestamp_matches == 0 and loglevel_matches == 0:
            return False, "Rejected: Missing valid log structural anchoring constraints (Timestamps/Log Levels)."
            
        return True, "Passed structural validation."

    def parse_raw_text(self, content: str) -> List[Dict[str, Any]]:
        """
        Slices log streams line-by-line, grouping stack frames with their parent log line,
        while maintaining zero cross-contamination between adjacent log contexts.
        """
        is_valid, _ = self.validate_log_file(content)
        if not is_valid:
            return []

        raw_lines = content.splitlines()
        atomic_blocks = []
        current_block_lines = []

        # Group lines structurally (Parent entry + its own downstream stack trace lines)
        for line in raw_lines:
            cleaned_line = line.strip()
            if not cleaned_line:
                continue

            # If it's a brand new log line starting with a timestamp, save the previous group
            if self.log_start_regex.match(cleaned_line):
                if current_block_lines:
                    atomic_blocks.append("\n".join(current_block_lines))
                    current_block_lines = []
                current_block_lines.append(cleaned_line)
            else:
                # If it's a stack trace line (e.g., 'at com.ops...'), append to current active log group
                if current_block_lines:
                    current_block_lines.append(line)  # Keep original indentation for trace integrity
                else:
                    current_block_lines.append(cleaned_line)

        # Append final trailing block
        if current_block_lines:
            atomic_blocks.append("\n".join(current_block_lines))

        # Build highly specific, isolated chunks
        processed_chunks = []
        for block_text in atomic_blocks:
            # Extract metadata *strictly* contained inside this individual block text only
            found_jobs = [int(jid) for jid in self.job_id_regex.findall(block_text)]
            found_traces = self.trace_id_regex.findall(block_text)
            found_levels = self.loglevel_regex.findall(block_text)
            
            has_stack = "at " in block_text or "Exception" in block_text or "Error" in block_text
            timestamp_match = self.log_start_regex.match(block_text)
            timestamp_str = timestamp_match.group(1) if timestamp_match else "N/A"

            processed_chunks.append({
                "text": block_text,
                "metadata": {
                    "job_ids": list(set(found_jobs)),
                    "trace_ids": list(set(found_traces)),
                    "log_levels": list(set(found_levels)) if found_levels else ["INFO"],
                    "has_stack_trace": has_stack,
                    "timestamp_boundary": timestamp_str
                }
            })

        return processed_chunks

if __name__ == "__main__":
    parser = LogMetadataSplitter()
    sample_log = (
        "2026-08-16 14:16:05 [worker-3] ERROR - OutOfMemoryError for job_id=145555\n"
        "java.lang.OutOfMemoryError: Java heap space\n"
        "\tat com.ops.engine.Runner.execute(Runner.java:82)\n"
        "2026-08-16 14:16:06 [worker-4] INFO - Status fine for job_id=1234"
    )
    chunks = parser.parse_raw_text(sample_log)
    print(f"Total Chunks Split: {len(chunks)}")
    print(f"Chunk 1 JobIDs: {chunks[0]['metadata']['job_ids']}")
    print(f"Chunk 2 JobIDs: {chunks[1]['metadata']['job_ids']}")
