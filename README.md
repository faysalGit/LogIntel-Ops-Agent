## LogIntel-Ops-Agent: Enterprise Log Analysis RAG Engine
LogIntel-Ops-Agent is a production-ready, highly localized Retrieval-Augmented Generation (RAG) system engineered to parse application logs, isolate critical process tags (such as Job IDs and Trace IDs), preserve complex multi-line exception stack traces, and execute intelligent automated diagnostic and triage workflows.

##  System Architecture
The architecture follows a strict, decoupled pipeline built to maximize deterministic context processing while remaining completely immune to native operating system binary execution conflicts:

```
[ Raw Log Data Input ] ──► Local File Drop / Remote URL Stream Connection
                                    │
                                    ▼
[ Pre-flight Validator ] ─► Whole-word Regular Expression Pattern Checks
                                    │
                                    ▼
[ Micro-Chunk Splitter ] ─► Line-by-Line Timestamp Boundary Isolation
                                    │
                                    ▼
[ Local Vector Store ] ──► Pure-Python JSON Indexing Database File
                                    │
                                    ▼
[ Intelligent Agent ] ───► Intent Extraction, Factual Context Lookup & Triage Synthesis
                                    │
                                    ▼
[ System Dashboard UI ] ──► Gradio Web Engine Interface Workspace
```

<img width="1536" height="1024" alt="LogIntel-Ops-Agent-Architecture" src="https://github.com/user-attachments/assets/c988321d-7524-4c3e-bff1-ee40275a498b" />


**1. Data Ingestion Control Pipeline:** Accepts application logs via a local drag-and-drop file container component or via an automated HTTP remote connection stream parser (requests).

**2. Deterministic Pre-flight Line-Isolated Validation:** Prior to storage allocation, chunks pass through a strict regex-driven pre-flight boundary inspection matrix to detect and discard non-log textual anomalies (such as generic essays, code documentation files, or raw notes).

**3. Metadata-Aware Log Splitting:** Real-time log text streams are processed line-by-line using a micro-chunking methodology, automatically isolating structural anchors (such as full-word timestamps, severity log levels, and targeted transaction values) to prevent data bleed between unrelated logs.

**4. Pure-Python Flat-File Indexing Storage Engine:** Standardizes document index structures into an efficient JSON mapping matrix on the local hard drive, ranking textual context using explicit string-digit tokens and logical error weight boosts.

**5. Intelligent Orchestration Core Agent:** A regex-driven extraction router that isolates structural keywords and queries specific database boundaries before formatting human-like diagnostic synthesis parameters or corporate incident report emails.

**6 Unified Diagnostic Workspace Frontend:** A localized browser console environment managing view layouts, history state structures, and processing event logs.

## Technological Stack & Tool Integrations

**LLM (Large Language Model Core):** Utilizes advanced conversational reasoning nodes (configured for models like gpt-4o or similar high-capacity architectures via environment property settings) to handle zero-shot exception synthesis, root-cause evaluation, and markdown email generation.

**LangChain Framework Layout:** Orchestrates modular prompt execution sequences, workflow variable injections, and structural multi-turn interaction contexts.

**LlamaIndex Philosophy:** Inspires the programmatic extraction of multi-line log fragments, structured metadata groupings, and systemic document chunk boundary rules.

**Pure-Python Log Vector Database Manager:** A specialized, localized database engine built natively from core Python libraries (json, os, re) to safely map documents, handle strict metadata filtering, and calculate keyword scoring records without risk of compiled C++ link collisions (onnxruntime or chromadb DLL faults).

**Gradio Web Engine Interface Layout:** Assembles the graphic workspace layout panels (gr.Blocks, gr.Row, gr.Column, gr.ChatInterface) to render interactive streaming nodes directly inside browser ports.

## Model Configuration
The orchestration framework separates data routing parameters dynamically to ensure optimal context delivery:

**Context Generation Model:** gpt-4o (or preferred enterprise local/cloud container API endpoints specified inside app/core/config.py).

**Relevance Ranking Matrix:** Pure-Python native tokenization algorithm executing precise full-word matching filters alongside structural error weight boosts (+2 for explicit ERROR/EXCEPTION tokens, and +3 for live multi-line stack traces).

## Getting Started
**Installation**
Ensure your local Python interpreter version is 3.10+ and execute package allocations from the project root directory:

```
pip install -r requirements.txt
```

**Starting the Workspace**
Launch the master production interface web server directly from your terminal console:
```
python -m app.main
```

Open your local internet web browser and navigate to the diagnostic port: http://localhost:8000
