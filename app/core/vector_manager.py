import os
import json
import re
from typing import List, Dict, Any

class LogVectorManager:
    """
    A Production-grade, Pure-Python Log Ingestion and Indexing Engine.
    Handles local log indexing, structured metadata filtering, and 
    automated diagnostic analysis generation.
    """
    def __init__(self, database_dir: str = os.path.join("data", "vector_store")):
        self.database_dir = database_dir
        self.index_file_path = os.path.join(self.database_dir, "log_index.json")
        
        # Ensure storage directory exists
        os.makedirs(self.database_dir, exist_ok=True)
        
        # Initialize database file if it does not exist
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
        Saves structured text segments and their parsed metadata tracks 
        directly into the local database store.
        """
        if not chunks:
            return
            
        current_db = self._load_db()
        
        for idx, chunk in enumerate(chunks):
            raw_metadata = chunk.get("metadata", {})
            job_list = raw_metadata.get("job_ids", [])
            trace_list = raw_metadata.get("trace_ids", [])
            
            record = {
                "id": f"id_{document_source}_{idx}_{len(current_db)}",
                "text": chunk.get("text", ""),
                "metadata": {
                    "source": document_source,
                    "has_stack_trace": bool(raw_metadata.get("has_stack_trace", False)),
                    "timestamp_boundary": str(raw_metadata.get("timestamp_boundary", "N/A")),
                    "job_ids": [str(j) for j in job_list],
                    "trace_ids": [str(t) for t in trace_list],
                    "log_levels": raw_metadata.get("log_levels", ["INFO"])
                }
            }
            current_db.append(record)
            
        self._save_db(current_db)

    def query_logs(self, query_text: str, target_job_id: str = None, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Queries log records using strict metadata filtering and keyword relevance scoring.
        """
        records = self._load_db()
        matched_records = []
        
        # Clean query tokens for simple scoring
        query_words = set(re.findall(r'\w+', query_text.lower()))
        
        for rec in records:
            meta = rec["metadata"]
            
            # Strict Metadata Filtering if a JobID is targeted
            if target_job_id:
                if str(target_job_id) not in meta["job_ids"]:
                    continue  # Skip logs that do not match the requested JobID
            
            log_text_lower = rec["text"].lower()
            score = 0
            
            for word in query_words:
                if word in log_text_lower:
                    score += 1
            
            if "error" in log_text_lower or "exception" in log_text_lower:
                score += 2
            if meta["has_stack_trace"]:
                score += 3
                
            matched_records.append((score, rec))
            
        # Sort records by highest score first
        matched_records.sort(key=lambda x: x[0], reverse=True)
        
        output_hits = []
        for score, rec in matched_records[:limit]:
            flattened_meta = rec["metadata"].copy()
            flattened_meta["job_ids"] = ",".join(flattened_meta["job_ids"])
            flattened_meta["trace_ids"] = ",".join(flattened_meta["trace_ids"])
            
            output_hits.append({
                "text": rec["text"],
                "metadata": flattened_meta
            })
            
        return output_hits

    def synthesize_diagnostic_analysis(self, job_id: str, sql_data: Dict[str, Any], log_hits: List[Dict[str, Any]]) -> str:
        """
        Synthesizes a human-readable diagnostic analysis based on retrieved log fragments.
        """
        log_context_str = ""
        valid_hits_count = 0
        
        for hit in log_hits:
            text_content = hit.get("text", "")
            if "No log traces matching" in text_content or not text_content.strip():
                continue
            log_context_str += f"--- Log Segment (Source: {hit['metadata']['source']}) ---\n{text_content}\n\n"
            valid_hits_count += 1

        sql_summary = ""
        if sql_data:
            sql_summary = (
                f"### 🗄️ Relational SQL Job Registry Details:\n"
                f"- **Job Name:** {sql_data.get('job_name')}\n"
                f"- **Triggered By:** {sql_data.get('triggered_by')}\n"
                f"- **Target Environment:** {sql_data.get('environment')}\n"
                f"- **Execution Start Time:** {sql_data.get('start_time')}\n"
                f"- **Database Core Registry Status:** {sql_data.get('status')}\n\n"
            )

        if valid_hits_count == 0:
            if sql_data:
                return (
                    f"{sql_summary}⚠️ **RAG System Notice:** Relational registry data pulled successfully from SQL, "
                    f"but zero matching error log lines exist in the file storage index for JobID `{job_id}`."
                )
            return f"🔍 LogIntel Agent Status: Operational search finished. No log traces matching JobID {job_id} exist in the active database store."

        ai_response = (
            f"## 🛠️ Combined Diagnostic Matrix for Job {job_id}\n\n"
            f"{sql_summary}"
            f"### 📄 Retrieved RAG Log Context:\n```text\n{log_context_str}```\n"
            f"#### 🧠 AI System Diagnostic Analysis:\n"
        )
        
        log_lower = log_context_str.lower()
        if "outofmemoryerror" in log_lower:
            ai_response += "❌ **Identified Root Cause:** The process terminated due to physical Java Heap space exhaustion (`OutOfMemoryError`). Remediation: Scale up container memory limits or inspect code for memory leaks."
        elif "sockettimeoutexception" in log_lower:
            ai_response += "❌ **Identified Root Cause:** Network layer timeout failure (`SocketTimeoutException`). Remediation: Check upstream service availability and review connection pool timeout configs."
        elif "nullpointerexception" in log_lower:
            ai_response += "❌ **Identified Root Cause:** Unhandled runtime exception (`NullPointerException`). Remediation: Fix code object initialization references at the designated stack file line."
        elif "filenotfoundexception" in log_lower:
            ai_response += "❌ **Identified Root Cause:** Resource resolution error (`FileNotFoundException`). Remediation: Verify that all expected JSON or properties configuration files are correctly mounted in the deployment container path."
        else:
            ai_response += "✅ **Analysis:** Log entries successfully recovered. Review the contextual trace above for standard execution verification."

        return ai_response
