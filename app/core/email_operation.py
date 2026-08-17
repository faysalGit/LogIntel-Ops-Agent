from typing import Dict, Any, List

class LogEmailOperator:
    def compile_incident_email(self, job_id: str, sql_data: Dict[str, Any], log_hits: List[Dict[str, Any]]) -> str:
        job_name = sql_data.get("job_name", "Unknown-Job")
        env = sql_data.get("environment", "Production")
        log_text = log_hits[0]["text"] if log_hits else "No log traces found."
        
        return (
            f"### 📧 Drafted Incident Resolution Notification Email\n\n"
            f"**Subject:** [INCIDENT ALERT] Failure Notice: {job_name} (JobID: {job_id})\n\n"
            f"--- START OF EMAIL ---\n"
            f"Team,\n\n"
            f"JobID {job_id} failed in the {env} environment.\n\n"
            f"**Log Snippet:**\n```text\n{log_text}\n```\n"
            f"--- END OF EMAIL ---"
        )
