# ==============================================================================
# Script Name: setup_project.ps1
# Description: Initializes a professional, modular production directory 
#              structure for the LogIntel-Ops-Agent RAG ecosystem on Windows.
# Usage: .\setup_project.ps1
# ==============================================================================

$ProjectName = "LogIntel-Ops-Agent"

Write-Host "Initializing project structure for: $ProjectName..." -ForegroundColor Green

# 1. Create Base Directories
New-Item -ItemType Directory -Force -Path "$ProjectName\app\core" | Out-Null
New-Item -ItemType Directory -Force -Path "$ProjectName\app\api" | Out-Null
New-Item -ItemType Directory -Force -Path "$ProjectName\app\services" | Out-Null
New-Item -ItemType Directory -Force -Path "$ProjectName\app\ui" | Out-Null
New-Item -ItemType Directory -Force -Path "$ProjectName\data\vector_store" | Out-Null
New-Item -ItemType Directory -Force -Path "$ProjectName\data\raw_logs" | Out-Null
New-Item -ItemType Directory -Force -Path "$ProjectName\tests" | Out-Null

# 2. Initialize Python Package Files (__init__.py)
New-Item -ItemType File -Force -Path "$ProjectName\app\__init__.py" | Out-Null
New-Item -ItemType File -Force -Path "$ProjectName\app\core\__init__.py" | Out-Null
New-Item -ItemType File -Force -Path "$ProjectName\app\api\__init__.py" | Out-Null
New-Item -ItemType File -Force -Path "$ProjectName\app\services\__init__.py" | Out-Null
New-Item -ItemType File -Force -Path "$ProjectName\app\ui\__init__.py" | Out-Null

# 3. Create Core Module Shells
# Core Config and Orchestration Layer
$ConfigContent = @'
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "LogIntel-Ops-Agent"
    VECTOR_DB_PATH: str = os.path.join("data", "vector_store")
    LLM_MODEL: str = "gpt-4o"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    SPLUNK_API_URL: str = ""
    GMAIL_SENDER: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
'@
Set-Content -Path "$ProjectName\app\core\config.py" -Value $ConfigContent -Encoding utf8

# Custom Log Chunking / Metadata Parsing Layer
$SplitterContent = @'
import re
from typing import List, Dict, Any

class LogMetadataSplitter:
    """
    Production-grade log splitter designed to extract Trace IDs, Job IDs,
    and preserve stack traces across chunk boundaries.
    """
    def __init__(self, chunk_size: int = 500):
        self.chunk_size = chunk_size

    def split_log_file(self, content: str) -> List[Dict[str, Any]]:
        chunks = []
        # TODO: Implement regex matching for timestamps, job IDs, and stack frames
        return chunks
'@
Set-Content -Path "$ProjectName\app\core\splitter.py" -Value $SplitterContent -Encoding utf8

# 4. Create Requirements File (Production-grade dependencies)
$RequirementsContent = @'
# Core Frameworks
langchain>=0.2.0
llamainindex>=0.10.0
pydantic-settings>=2.2.0

# User Interface
gradio>=4.0.0

# Vector Databases
chromadb>=0.5.0

# Utilities
python-dotenv>=1.0.1
requests>=2.31.0
'@
Set-Content -Path "$ProjectName\requirements.txt" -Value $RequirementsContent -Encoding utf8

# 5. Create Root Application File (Gradio Launch Shell)
$MainContent = @'
import gradio as gr
from app.core.config import settings

def analyze_log_input(file_obj, url_str, chat_history):
    if file_obj:
        return f"Successfully received file: {file_obj.name}. Parsing traces..."
    if url_str:
        return f"Ingesting log streams from external provider URL: {url_str}..."
    return "Please upload a file or supply a valid Splunk/log URL."

with gr.Blocks(title=settings.PROJECT_NAME) as demo:
    gr.Markdown(f"# 🛠️ {settings.PROJECT_NAME} - Production RAG Panel")
    
    with gr.Row():
        with gr.Column(scale=1):
            log_file = gr.File(label="Drop Raw Log Files (.log, .txt, .json)")
            log_url = gr.Textbox(label="Or Provide Log URL (Splunk / Datadog)", placeholder="https://...")
            submit_btn = gr.Button("Ingest & Process Logs", variant="primary")
            
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(label="Agent Conversation Hub")
            msg = gr.Textbox(label="Ask about JobIDs, stack traces, or request an incident email draft...")
            clear = gr.ClearButton([msg, chatbot])

    submit_btn.click(analyze_log_input, inputs=[log_file, log_url, chatbot], outputs=[chatbot])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=8000)
'@
Set-Content -Path "$ProjectName\app\main.py" -Value $MainContent -Encoding utf8

# 6. Create Readme File
$ReadmeContent = @'
# LogIntel-Ops-Agent

Production-grade RAG and Agentic workflow application engineered to analyze massive application logs for deep troubleshooting.

## High-Level Architecture
- `/app/core`: Configuration pipelines, custom regex semantic chunking logic, and LLM orchestration.
- `/app/services`: Integrations with external collectors (Splunk, email SMTP clients).
- `/app/ui`: Gradio web engine interface layout block definitions.
'@
Set-Content -Path "$ProjectName\README.md" -Value $ReadmeContent -Encoding utf8

Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "Project structure successfully built!" -ForegroundColor Cyan
Write-Host "Next step: Run 'pip install -r requirements.txt' inside your python environment." -ForegroundColor Cyan
Write-Host "==============================================================================" -ForegroundColor Cyan
