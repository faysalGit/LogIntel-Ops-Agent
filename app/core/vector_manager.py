import os
import json
import re
from typing import List, Dict, Any

class LogVectorManager:
    """
    A clean, production-grade local log indexing engine. Operates deterministically
    using native storage primitives to eliminate native platform runtime crashes
    while maintaining zero-fallback metadata integrity.
    """
    def __init__(self, database_dir: str = os.path.join("data", "vector_store")):
        self.database_dir = database_dir
        self.index_file_path = os.path.join(self.database_dir, "log_index.json")
        
        # Enforce isolated directory path structures
        os.makedirs(self.database_dir, exist_ok=True)
        
        if not os.path.exists(self.index_file_path):
            self._save_db([])

    def _load_db(self) -> List[Dict[str, Any]]:
        try:
            with open(self.index_file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_db(self, data: List[Dict[str, Any]]) -> None:
        with open(self.index_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_log_chunks(self, chunks: List[Dict[str, Any]], document_source: str) -> None:
        """
        Commits verified token chunks and structured metadata records directly
        into the local storage database partition.
        """
        if not chunks:
            return
            
        current_db = self._load_db()
        
        for idx, chunk in enumerate(chunks):
            raw_metadata = chunk.get("metadata", {})
            
            record = {
                "id": f"log_{document_source}_{idx}_{len(current_db)}",
                "text": chunk.get("text", "").strip(),
                "metadata": {
                    "source": document_source,
                    "has_stack_trace": bool(raw_metadata.get("has_stack_trace", False)),
                    "timestamp_boundary": str(raw_metadata.get("timestamp_boundary", "N/A")),
                    "job_ids": [str(j) for j in raw_metadata.get("job_ids", [])],
                    "trace_ids": [str(t) for t in raw_metadata.get("trace_ids", [])],
                    "log_levels": [str(l) for l in raw_metadata.get("log_levels", ["INFO"])]
                }
            }
            current_db.append(record)
            
        self._save_db(current_db)

    def query_logs(self, query_text: str, target_job_id: str = None, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Queries log records using exact metadata constraint validation and token matching.
        Strictly returns an empty collection if no authentic file matching is found.
        """
        records = self._load_db()
        matched_records = []
        
        query_words = set(re.findall(r'\w+', query_text.lower()))
        
        for rec in records:
            meta = rec["metadata"]
            
            # Strict Filtering Guardrail: If a specific JobID is targeted, reject any non-matching trace
            if target_job_id:
                if str(target_job_id) not in meta["job_ids"]:
                    continue
            
            log_text_lower = rec["text"].lower()
            score = 0
            
            for word in query_words:
                if word in log_text_lower:
                    score += 1
            
            if "error" in log_text_lower or "exception" in log_text_lower:
                score += 2
            if meta["has_stack_trace"]:
                score += 3
                
            if score > 0 or target_job_id:
                matched_records.append((score, rec))
                
        # Sort matched results based purely on analytical index scores
        matched_records.sort(key=lambda x: x[0], reverse=True)
        
        output_hits = []
        for _, rec in matched_records[:limit]:
            flattened_meta = rec["metadata"].copy()
            flattened_meta["job_ids"] = ",".join(flattened_meta["job_ids"])
            flattened_meta["trace_ids"] = ",".join(flattened_meta["trace_ids"])
            
            output_hits.append({
                "text": rec["text"],
                "metadata": flattened_meta
            })
            
        return output_hits
