# Optimized RAG Agent (ADK & agents-cli)

An optimized Retrieval-Augmented Generation (RAG) AI Agent built with Google's **Agent Development Kit (ADK)** and managed using **`agents-cli`**.

It features **Knowledge Base Metadata Indexing**, **User Intent Classification**, and a **4-Tier Progressive Retrieval Engine** with intent-aware fallbacks.

> 📖 **Detailed Architecture Guide**: See [IMPLEMENTATION_GUIDE.md](file:///config/Desktop/Session1/simple-rag-agent/IMPLEMENTATION_GUIDE.md) for full technical documentation, sequence flows, and metadata schemas.

---

## 🌟 Key Features

1. **Structured Knowledge Base Metadata** ([knowledge_base/metadata.json](file:///config/Desktop/Session1/simple-rag-agent/knowledge_base/metadata.json)): Categorized sections with metadata tags (`adk`, `remote_work`, `travel_expenses`, `ai_governance`).
2. **User Intent Classification** ([app/intent.py](file:///config/Desktop/Session1/simple-rag-agent/app/intent.py)): Pre-search classification mapping queries to domain categories (`technical_docs`, `hr_policies`, `security_governance`).
3. **Multi-Tier Fallback Retrieval Engine** ([app/agent.py](file:///config/Desktop/Session1/simple-rag-agent/app/agent.py)): 4-stage search pipeline that degrades gracefully when exact matches are missing, providing guided suggested queries and contact info.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
agents-cli install
```

### 2. Test Queries
```bash
# HR Policy Query
agents-cli run "What is the daily meal allowance for business travel?"

# Technical Query
agents-cli run "How do I scaffold a project using agents-cli?"

# Missing Topic Query (Triggers Intent Fallback)
agents-cli run "What is the pet policy in the office?"
```

### 3. Launch Development Playground
```bash
agents-cli playground
```

---

## 📁 Project Anatomy

```
simple-rag-agent/
├── app/
│   ├── agent.py               # Root ADK agent and multi-tier retrieval engine
│   ├── intent.py              # User intent classification module
│   ├── fast_api_app.py        # FastAPI Backend server
│   └── app_utils/             # App utilities and helpers
├── knowledge_base/
│   ├── metadata.json          # Document metadata registry
│   ├── adk_and_gemini.txt     # ADK & agents-cli documentation
│   └── nova_corp_policies.txt # HR & Governance policies
├── IMPLEMENTATION_GUIDE.md    # Detailed architecture documentation
├── tests/                     # Unit and integration tests
├── GEMINI.md                  # Development guide
└── pyproject.toml             # Project dependencies
```

---

## 🛠️ Commands

| Command | Description |
| ------- | ----------- |
| `agents-cli install` | Install dependencies using `uv` |
| `agents-cli run "<query>"` | Run agent prompt locally |
| `agents-cli playground` | Launch interactive web development UI |
| `agents-cli lint` | Code quality checks |
| `agents-cli eval` | Run evaluation suite |
| `agents-cli deploy` | Deploy to Vertex AI Agent Runtime or Cloud Run |
