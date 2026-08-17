import re
from typing import Dict, Any, List

# Import our dedicated, fully decoupled manager modules
from app.core.vector_manager import LogVectorManager
from app.core.sql_manager import LogSQLManager
from app.core.email_operation import LogEmailOperator

class LogAgentOrchestrator:
    """
    Enterprise-grade AI Agent Orchestrator ("The Brain").
    Enforces strict, mutually exclusive architectural routing rules:
    - Negative Feedback: Intercepted at topmost priority to handle criticism humbly.
    - Conversational Phrases: Intercepted to return polite, helpful AI dialogue.
    - Time Queries: Intercepted to output ONLY clean dates and times.
    - Session State Tracking: Remembers the last queried JobID across conversational turns.
    - Decoupled Delegation: Offloads database, email, and indexing lookups to separate handlers.
    """
    def __init__(self):
        self.log_manager = LogVectorManager()
        self.sql_manager = LogSQLManager()
        self.email_operator = LogEmailOperator()
        
        # Stateful session variable to remember context across multiple chat prompts
        self.last_job_id = None

    def extract_job_id(self, text: str) -> str:
        """Extracts the first continuous sequence of numeric digits from user prompt queries."""
        cleaned_text = text.lower().strip()
        numbers = re.findall(r'\d+', cleaned_text)
        if numbers:
            return numbers[0]
        return ""

    def extract_timestamp(self, log_text: str) -> str:
        """Extracts standard YYYY-MM-DD HH:MM:SS timestamps from a log string."""
        match = re.search(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', log_text)
        return match.group(0) if match else "Unknown Time"

    def analyze_and_respond(self, user_message: str) -> str:
        """
        Parses conversational inputs, manages session context memory, 
        and routes queries dynamically using a strict mutual exclusion hierarchy.
        """
        try:
            # Step 1: Extract any explicit Job ID from the current message
            current_extracted_id = self.extract_job_id(user_message)
            message_lower = user_message.lower().strip()
            
            # Step 2: Context State Sync Engine
            if current_extracted_id:
                self.last_job_id = current_extracted_id
                target_job_id = current_extracted_id
                using_memory_fallback = False
            elif self.last_job_id:
                target_job_id = self.last_job_id
                using_memory_fallback = True
            else:
                target_job_id = None
                using_memory_fallback = False

            # Step 3: Compute Intent Request Flags
            is_negative_feedback = any(
                phrase in message_lower for phrase in [
                    "dumb", "dump", "stupid", "can't do good job", "cant do good job",
                    "bad job", "useless", "not intelligent", "idiot", "poor work"
                ]
            )
            is_compliment_or_greeting = any(
                phrase in message_lower for phrase in [
                    "i love you", "thank you", "thanks", "nice work", 
                    "great job", "awesome", "hello", "hi", "good job"
                ]
            )
            is_time_request = (
                "time" in message_lower or 
                "when" in message_lower or 
                "date" in message_lower
            )
            is_email_request = (
                "email" in message_lower or 
                "draft" in message_lower or 
                "notify" in message_lower or
                "create an email" in message_lower
            )
            is_sql_request = (
                "pull job records" in message_lower or 
                "job table" in message_lower or 
                "select" in message_lower or
                "metadata" in message_lower
            )

            # ==============================================================================
            # CRITICAL INTENT ROUTING LAYER (MUTUALLY EXCLUSIVE HIERARCHY)
            # ==============================================================================
            
            # PRIORITY 1: NEGATIVE FEEDBACK INTERCEPTOR (Handles complaints and insults politely)
            if is_negative_feedback:
                return (
                    "😔 **LogIntel Agent:** I am still learning and working hard to improve. "
                    "Tell me how I can help you better. Let's see what questions you have, "
                    "and I will try my absolute best to answer them accurately!"
                )

            # PRIORITY 2: CONVERSATIONAL COMPLIMENTS & GREETINGS
            if is_compliment_or_greeting:
                if "love" in message_lower:
                    return (
                        "❤️ **LogIntel Agent:** Thank you so much! I am thrilled to hear that. "
                        "I am always here to keep your pipelines stable, help you analyze micro-chunk log traces, "
                        "and extract registry records from your SSMS database tables!"
                    )
                if "thank" in message_lower or "thanks" in message_lower:
                    return (
                        "✨ **LogIntel Agent:** You are very welcome! It is my absolute pleasure to assist you. "
                        "Let me know what operational triage task or database audit query we should tackle next!"
                    )
                return (
                    "🚀 **LogIntel Agent:** Thank you! I try my absolute best to make diagnostic monitoring easy and clean. "
                    "Let me know if you want to ingest a new production log matrix, check a specific failure timeframe, "
                    "or pull records from the job table!"
                )

            # PRIORITY 3: TIME-SPECIFIC EXTRACTION (Blocks full log text leaks entirely)
            if is_time_request:
                log_hits = self.log_manager.query_logs(query_text="error failure failed timestamp", target_job_id=target_job_id, limit=5)
                valid_traces = [h for h in log_hits if "No log traces" not in h.get("text", "")]
                
                if not valid_traces:
                    return f"### ⏰ LogIntel Failure Time Report\n\nNo matching operational error events were located for JobID `{target_job_id or 'Global'}` to isolate timestamps."

                output_report = f"### ⏰ LogIntel Failure Time Report\n\nI scanned the tracking entries and isolated the exact timestamps for the encountered failures:\n\n"
                for idx, hit in enumerate(valid_traces):
                    timestamp = self.extract_timestamp(hit["text"])
                    log_summary_line = hit["text"].split("\n")[0][:100]
                    display_id = target_job_id or self.extract_job_id(log_summary_line) or "Unknown"
                    
                    output_report += f"{idx + 1}. 📅 **Date/Time:** `{timestamp}` | 🆔 **JobID:** `{display_id}`\n   - *Incident Status:* `{log_summary_line}...`\n"
                
                if using_memory_fallback:
                    output_report += f"\n*Context Note: Automatically tracking context for session history JobID {target_job_id}.*"
                return output_report

            # PRIORITY 4: AUTOMATED INCIDENT EMAIL GENERATION
            if is_email_request:
                if not target_job_id:
                    global_errors = self.log_manager.query_logs(query_text="error exception failed", target_job_id=None)
                    if global_errors and "No log traces" not in global_errors[0].get("text", ""):
                        candidate_numbers = re.findall(r'\d+', global_errors[0]["text"])
                        if candidate_numbers:
                            target_job_id = candidate_numbers[0]
                            self.last_job_id = target_job_id
                
                if not target_job_id:
                    return (
                        "### 📧 LogIntel Incident Email Engine\n\n"
                        "⚠️ **Operation Postponed:** I cannot compile an email alert notice because no active JobID context "
                        "is stored in this chat session, and no operational errors exist in the local index.\n\n"
                        "Please ask a targeted diagnostic question first (e.g., *'What happened to job 1234?'*) to establish context."
                    )
                
                sql_data = self.sql_manager.query_sql_job_details(target_job_id)
                log_hits = self.log_manager.query_logs(query_text="error failure stack trace", target_job_id=target_job_id)
                return self.email_operator.compile_incident_email(target_job_id, sql_data, log_hits)

            # PRIORITY 5: EXPLICIT SQL DATA DICTIONARY AUDIT REGISTRY EXTRACTION
            if is_sql_request:
                if not target_job_id:
                    return (
                        "### 🗄️ SSMS Relational Database Lookup System\n\n"
                        "ℹ️ **Query Blocked:** You requested rows from table `[BICS].[dbo].[Job]`, but did not supply a JobID number.\n\n"
                        "Please issue the query matching this pattern: *'pull job records from job table for 1234'*."
                    )
                
                sql_data = self.sql_manager.query_sql_job_details(target_job_id)
                if not sql_data:
                    return f"❌ **SQL Database Alert:** No master registration entries found inside table `[BICS].[dbo].[Job]` for ID `{target_job_id}`."
                return self.sql_manager.format_sql_audit_report(target_job_id, sql_data)

            # PRIORITY 6: GLOBAL SYSTEM SCAN MODE (NO JOB ID PROVIDED AT ALL)
            if not target_job_id:
                global_hits = self.log_manager.query_logs(query_text=user_message, target_job_id=None, limit=5)
                valid_traces = [h for h in global_hits if "No log traces" not in h.get("text", "")]
                if not valid_traces:
                    return (
                        "### 🔍 LogIntel Agent: Global Operational Status\n\n"
                        "Inspection completed across all active tracking segments. No explicit JobID token was detected in your prompt, "
                        "and zero matching error traces were found inside the data index storage file."
                    )
                
                summary_output = (
                    f"### 🔍 LogIntel Agent: Global Cross-Job Historical Search\n"
                    f"No explicit JobID was targeted. I performed a comprehensive scan across all indexed log files matching your parameters: *'{user_message}'*.\n\n"
                    f"**Top Relevant Operational Events Recovered:**\n\n"
                )
                for idx, hit in enumerate(valid_traces):
                    text_snippet = hit["text"][:200].replace('\n', '  \n')
                    source = hit["metadata"].get("source", "unknown_source.log")
                    summary_output += f"#### Event {idx + 1} (Source Reference: `{source}`)\n```text\n{text_snippet}...\n```\n\n"
                return summary_output

            # PRIORITY 7: DEFAULT RAG WORKFLOW (TARGETED LOG FILE ANALYSIS)
            log_hits = self.log_manager.query_logs(query_text=user_message, target_job_id=target_job_id)
            context_notice = ""
            if using_memory_fallback:
                context_notice = f"ℹ️ *Context Note: No JobID was detected in your prompt. I am automatically maintaining context from our session history for **JobID {target_job_id}**.*\n\n"
                
            analysis_output = self.log_manager.synthesize_diagnostic_analysis(target_job_id, {}, log_hits)
            return f"{context_notice}{analysis_output}"

        except Exception as e:
            return f"⚠ Internal Agent Error during routing isolation execution: {str(e)}"
