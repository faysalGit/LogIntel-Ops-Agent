import os
import gradio as gr
from app.core.splitter import LogMetadataSplitter
from app.core.vector_manager import LogVectorManager
from app.core.agent_manager import LogAgentOrchestrator

# Initialize core system modules cleanly
splitter = LogMetadataSplitter()
vector_manager = LogVectorManager()
agent = LogAgentOrchestrator()

def process_log_ingestion(file_obj, url_str):
    """
    Handles user data input routes from both local file uploads and remote network stream URLs.
    Ensures safe extraction across all variations of Gradio file container objects.
    """
    if file_obj is not None:
        try:
            # Type-agnostic checking to safely extract path strings across all Gradio sub-versions
            if isinstance(file_obj, str):
                file_path = file_obj
            elif hasattr(file_obj, "name"):
                file_path = file_obj.name
            elif isinstance(file_obj, dict) and "name" in file_obj:
                file_path = file_obj["name"]
            elif isinstance(file_obj, list) and len(file_obj) > 0:
                item = file_obj[0]
                file_path = item.name if hasattr(item, "name") else str(item)
            else:
                return "❌ Ingestion Failed: Unable to parse file component object structure."

            if not os.path.exists(file_path):
                return f"❌ Ingestion Failed: Targeted file path does not exist: {file_path}"

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_content = f.read()

            if not raw_content.strip():
                return "❌ Ingestion Failed: The provided file buffer is entirely empty."

            # Process through our strict line-isolated micro-chunk parsing engine
            parsed_chunks = splitter.parse_raw_text(raw_content)
            if not parsed_chunks:
                return (
                    "⚠ Ingestion Blocked: The pre-flight validator rejected this file. "
                    "It does not contain standard log structural anchors (Whole-word Timestamps/Log Levels)."
                )

            # Commit clean structured frames to the pure-python index storage file
            base_filename = os.path.basename(file_path)
            vector_manager.add_log_chunks(parsed_chunks, document_source=base_filename)
            
            return (
                f"✅ Ingestion successful! Extracted and stored {len(parsed_chunks)} "
                f"isolated log frame(s) from '{base_filename}' directly into the data store."
            )

        except Exception as e:
            return f"❌ System Ingestion Exception encountered: {str(e)}"

    if url_str and url_str.strip():
        target_url = url_str.strip()
        try:
            import requests
            headers = {"User-Agent": "LogIntelOpsAgent/1.0"}
            response = requests.get(target_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return f"❌ Network Ingestion Failed: Remote server responded with HTTP Status {response.status_code}"
                
            remote_text = response.text
            if not remote_text.strip():
                return "❌ Network Ingestion Failed: Stream target returned empty text headers."

            parsed_chunks = splitter.parse_raw_text(remote_text)
            if not parsed_chunks:
                return "⚠ Ingestion Blocked: Remote link text failed structural log validity validation constraints."

            vector_manager.add_log_chunks(parsed_chunks, document_source=target_url)
            return (
                f"✅ Ingestion successful! Captured and indexed {len(parsed_chunks)} "
                f"context frames from remote stream gateway."
            )

        except Exception as e:
            return f"⚠ Network Connectivity Error while streaming from URL endpoint: {str(e)}"

    return "❌ Operation Rejected: Please supply an active file drop or paste a stream link URL."

def core_agent_response_wrapper(message, history):
    """
    Direct interface processing link required by gr.ChatInterface.
    Gradio completely orchestrates history tracking and schema updates in the background.
    """
    if not message.strip():
        return ""
    
    # Pass user string directly to the factual prompt agent module
    return agent.analyze_and_respond(message)

# Assembling the Unified UI Layout Workspace Panel
with gr.Blocks() as demo:
    gr.Markdown("# 🛠️ LogIntel-Ops-Agent — Production Workspace")
    gr.Markdown(
        "Modular production-grade RAG workspace engine engineered to systematically parse application logs, "
        "isolate unique process IDs, and generate automated diagnostic summaries."
    )
    
    with gr.Row():
        # Left Ingestion Control Panel (1/3 of screen width)
        with gr.Column(scale=1):
            gr.Markdown("### 📥 Data Ingestion Control Pipeline")
            file_uploader = gr.File(label="Drop Raw Logs (.log, .txt, .md)", file_count="single")
            url_textbox = gr.Textbox(
                label="Or Enter Remote Log Stream URL", 
                placeholder="https://internal-log-server.net..."
            )
            ingest_button = gr.Button("Execute Storage Ingestion", variant="primary")
            
            gr.Markdown("#### 📊 Processing Engine Status")
            status_monitor = gr.Textbox(
                label="Ingestion Event Status Logs", 
                placeholder="Awaiting data ingestion payloads...", 
                interactive=False
            )
            
        # Right Factual AI Chat Console (2/3 of screen width) using official ChatInterface standard
        with gr.Column(scale=2):
            gr.Markdown("### 🧠 LogIntel Core Diagnostic Console")
            
            # FIXED: Removed theme from Blocks and clear_btn from ChatInterface to ensure universal version compatibility.
            gr.ChatInterface(
                fn=core_agent_response_wrapper
            )

    # Bind ingestion layout action
    ingest_button.click(
        fn=process_log_ingestion, 
        inputs=[file_uploader, url_textbox], 
        outputs=status_monitor
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=8000)
