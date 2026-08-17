import pandas as pd

# Advanced Monkeypatch Guardrail: Intercepts and fixes Gradio's internal telemetry bug with modern Pandas versions
_orig_df_infer = pd.DataFrame.infer_objects
def _patched_df_infer(self, *args, **kwargs):
    kwargs.pop('copy', None)  # Remove the 'copy' parameter causing the Pandas mismatch crash
    return _orig_df_infer(self, *args, **kwargs)
pd.DataFrame.infer_objects = _patched_df_infer

_orig_series_infer = pd.Series.infer_objects
def _patched_series_infer(self, *args, **kwargs):
    kwargs.pop('copy', None)  # Remove the 'copy' parameter causing the Pandas mismatch crash
    return _orig_series_infer(self, *args, **kwargs)
pd.Series.infer_objects = _patched_series_infer

import gradio as gr
from app.core.splitter import LogMetadataSplitter
from app.core.vector_manager import LogVectorManager
from app.core.agent_manager import LogAgentOrchestrator

# Initialize core framework instances
splitter = LogMetadataSplitter()
vector_manager = LogVectorManager()
agent = LogAgentOrchestrator()

def process_log_ingestion(file_obj, url_input):
    """Handles parsing and ingestion loops for text files or remote endpoints cleanly."""
    try:
        if file_obj is not None:
            if isinstance(file_obj, list):
                file_path = file_obj[0].name if file_obj else None
            else:
                file_path = file_obj.name if hasattr(file_obj, 'name') else str(file_obj)
                
            if not file_path:
                return "❌ Ingestion Error: No valid file path extracted."
                
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read()
                
            source_name = file_path.split("/")[-1].split("\\")[-1]
            is_valid, validation_msg = splitter.validate_log_cleanliness(raw_text)
            if not is_valid:
                return f"⚠️ [PRE-FLIGHT BLOCKED] Ingestion rejected: {validation_msg}"
                
            chunks = splitter.parse_raw_text(raw_text)
            vector_manager.add_log_chunks(chunks, source_name)
            return f"✅ Ingestion successful! Indexed {len(chunks)} segments from '{source_name}' directly into store."
            
        elif url_input and url_input.strip():
            import requests
            url_clean = url_input.strip()
            try:
                response = requests.get(url_clean, timeout=10)
                if response.status_code != 200:
                    return f"❌ Network Error: Server returned status {response.status_code}."
                
                raw_text = response.text
                is_valid, validation_msg = splitter.validate_log_cleanliness(raw_text)
                if not is_valid:
                    return f"⚠️ [PRE-FLIGHT BLOCKED] Rejected: {validation_msg}"
                    
                chunks = splitter.parse_raw_text(raw_text)
                vector_manager.add_log_chunks(chunks, f"network_stream_{url_clean[:15]}.log")
                return f"✅ Ingestion successful! Indexed {len(chunks)} remote records."
            except Exception as net_err:
                return f"⚠ Network Connectivity Error: {str(net_err)}"
                
        return "ℹ️ Awaiting Input: Drop a log file or supply a stream URL."
    except Exception as e:
        return f"❌ System Ingestion Exception: {str(e)}"

def chat_respond(user_message, chat_history):
    """Processes chat entry inputs and logs responses into role-based conversation matrices."""
    # Defensive Guardrail: Convert explicit None parameters to empty strings to prevent execution faults
    if user_message is None:
        user_message = ""
    else:
        user_message = str(user_message)
        
    if not user_message.strip():
        return "", chat_history, chat_history
        
    bot_response = agent.analyze_and_respond(user_message)
    
    # Format message histories to precisely align with Gradio 6 array matrices
    if chat_history is None:
        chat_history = []
        
    chat_history.append({"role": "user", "content": user_message})
    chat_history.append({"role": "assistant", "content": bot_response})
    
    return "", chat_history, chat_history

# Initialize dashboard interface layout workspace
with gr.Blocks(analytics_enabled=False) as demo:
    gr.Markdown("# 🚀 LogIntel-Ops-Agent — System Diagnostic Workspace")
    
    with gr.Row():
        # Left Panel: Data Ingestion Control
        with gr.Column(scale=1):
            gr.Markdown("### 📥 Data Ingestion Control Pipeline")
            file_dropper = gr.File(label="Drop Raw Logs", file_count="single")
            url_field = gr.Textbox(label="Log Stream URL", placeholder="https://splunk-export.internal")
            ingest_btn = gr.Button("Execute Storage Ingestion", variant="primary")
            status_box = gr.Textbox(label="Ingestion Event Status Logs", interactive=False, placeholder="System ready...")
            
            ingest_btn.click(
                fn=process_log_ingestion,
                inputs=[file_dropper, url_field],
                outputs=status_box
            )
            
        # Right Panel: Core AI Assistant Chat Console
        with gr.Column(scale=2):
            gr.Markdown("### 💬 Intelligent Core Assistant")
            chatbot = gr.Chatbot(label="Agent Evaluation Streaming Output", height=480)
            state_history = gr.State([])  # Synchronizes multi-turn memory strings
            
            with gr.Row():
                txt_input = gr.Textbox(
                    show_label=False,
                    placeholder="Ask about a JobID, query a table, check timestamps, or request an email...",
                    scale=4,
                    elem_id="chat-input"  # Linked to focus handler
                )
                submit_btn = gr.Button("Send", scale=1, variant="primary")
            
            # Ironclad Client-Side JavaScript Target Element Pointer:
            # Instead of manually guessing container dimensions or scroll heights which change dynamically
            # as a markdown table initializes, this method queries for the very last message container row 
            # inside Gradio's chat view wrapper and tells the browser engine to natively scroll it 
            # into view via a continuous, 1-second multi-tick loop framework.
            focus_js = """
            (msg, history) => {
                setTimeout(() => {
                    // Refocus input text bar area instantly
                    const el = document.querySelector('#chat-input textarea') || document.querySelector('#chat-input input');
                    if (el) el.focus();
                }, 50);
                
                // Active polling script targeting the actual message elements directly
                let scrollCount = 0;
                const scrollInterval = setInterval(() => {
                    // Query for the final message wrapper row node inside the chatbot component view
                    const items = document.querySelectorAll('.message-wrap > div, .chatbot .message, [data-testid="chatbot"] .message, .bot-message');
                    if (items.length > 0) {
                        // Force native browser execution to snap view bounds down to the end of the final response row
                        items[items.length - 1].scrollIntoView({ behavior: 'smooth', block: 'end' });
                    }
                    
                    // Comprehensive secondary container container scroll backup
                    const scrollContainers = document.querySelectorAll('.message-wrap, .scrollable-default, .chatbot .wrap, .chatbot');
                    scrollContainers.forEach(container => {
                        container.scrollTop = container.scrollHeight;
                    });
                    
                    scrollCount++;
                    if (scrollCount >= 10) { // Runs for 1 full second to completely match table load durations
                        clearInterval(scrollInterval);
                    }
                }, 100);
                
                return [msg, history];
            }
            """
            
            submit_btn.click(
                fn=chat_respond,
                inputs=[txt_input, state_history],
                outputs=[txt_input, chatbot, state_history],
                js=focus_js
            )
            
            txt_input.submit(
                fn=chat_respond,
                inputs=[txt_input, state_history],
                outputs=[txt_input, chatbot, state_history],
                js=focus_js
            )

if __name__ == "__main__":
    # Theme configuration explicitly passed directly into launch() to clear Gradio 6 startup warnings
    custom_theme = gr.themes.Default(primary_hue="blue", secondary_hue="slate")
    demo.launch(server_port=8000, theme=custom_theme, share=True)
