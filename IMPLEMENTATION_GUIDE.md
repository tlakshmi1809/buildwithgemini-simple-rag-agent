# Optimized RAG Agent: Technical Implementation & Architecture Guide

This document provides a comprehensive technical overview of the **Intent-Aware, Metadata-Filtered Retrieval-Augmented Generation (RAG) Agent** built using Google's **Agent Development Kit (ADK)** and managed with **`agents-cli`**.

---

## 📌 1. Executive Summary

Traditional RAG systems suffer from query noise, irrelevant passage retrieval, and unhelpful "no results found" error responses. This project solves those limitations by introducing a 3-tier optimization pipeline:

1. **Structured Knowledge Base Metadata**: Document-level and section-level tagging, categorization, and summaries (`knowledge_base/metadata.json`).
2. **Pre-Search User Intent Classification**: Automatic mapping of user prompts to domain categories and tags before document retrieval (`app/intent.py`).
3. **Multi-Tier Search Engine & Fallback Architecture**: A 4-step progressive search strategy that degrades gracefully when exact matches are missing (`app/agent.py`).

---

## 🏗️ 2. High-Level Architecture Diagram

```
                       ┌────────────────────────┐
                       │   Incoming User Query   │
                       └───────────┬────────────┘
                                   │
                                   ▼
                       ┌────────────────────────┐
                       │  Intent Classification │  (app/intent.py)
                       │  - Category Detection  │
                       │  - Tag Extraction      │
                       └───────────┬────────────┘
                                   │
                                   ▼
                       ┌────────────────────────┐
                       │ Metadata Filter Engine │  (knowledge_base/metadata.json)
                       │  - Category Filter     │
                       │  - Tag Overlap Score   │
                       └───────────┬────────────┘
                                   │
                                   ▼
          ┌──────────────────────────────────────────────────┐
          │      4-Tier Progressive Retrieval Pipeline       │
          ├──────────────────────────────────────────────────┤
          │ Tier 1: Strict Category & Tag Filtered Search    │
          │ Tier 2: Cross-Category Relaxation Search         │
          │ Tier 3: Metadata Header & Summary Partial Match   │
          │ Tier 4: Intent-Aware Structured Guidance Prompt │
          └────────────────────────┬─────────────────────────┘
                                   │
                                   ▼
                       ┌────────────────────────┐
                       │   Gemini 3.6 Flash     │  Grounded Response
                       │   Grounded Synthesis   │  with Source Citations
                       └────────────────────────┘
```

---

## 📁 3. Directory Anatomy

```
simple-rag-agent/
├── app/
│   ├── agent.py               # Root ADK agent and multi-tier retrieval engine
│   ├── intent.py              # User intent classification module
│   ├── fast_api_app.py        # FastAPI server entrypoint
│   └── app_utils/             # ADK application utilities
├── knowledge_base/
│   ├── metadata.json          # Structured document metadata index
│   ├── adk_and_gemini.txt     # Technical documentation corpus
│   └── nova_corp_policies.txt # HR & Governance policies corpus
├── tests/                     # Unit and integration test suite
├── IMPLEMENTATION_GUIDE.md    # Detailed technical architecture guide (This file)
├── GEMINI.md                  # Development guidelines
├── pyproject.toml             # Dependencies (google-adk, a2a-sdk, etc.)
└── agents-cli-manifest.yaml   # Deployment manifest
```

---

## 🏷️ 4. Metadata Schema Specification

Knowledge base documents are enriched with structural metadata in `knowledge_base/metadata.json`:

```json
{
  "version": "1.0",
  "documents": [
    {
      "file_name": "nova_corp_policies.txt",
      "doc_id": "doc_nova_policies",
      "title": "NovaSmart Corporate Policies & FAQ",
      "category": "hr_policies",
      "tags": ["remote_work", "travel_expenses", "meal_allowance", "ai_governance"],
      "sections": [
        {
          "section_id": "travel_reimbursement",
          "header": "Travel Expense Reimbursement",
          "category": "hr_policies",
          "tags": ["travel_expenses", "meal_allowance", "reimbursement", "flights"],
          "summary": "Expense report 30-day submission limit, $75 daily meal allowance, economy flights."
        }
      ]
    }
  ]
}
```

---

## 🎯 5. Intent Classification Module (`app/intent.py`)

The intent classifier maps incoming user queries into structured `QueryIntent` objects:

```python
@dataclass
class QueryIntent:
    intent_type: str            # e.g., "hr_policies", "technical_docs", "security_governance"
    target_categories: List[str] # Filter categories e.g. ["hr_policies"]
    extracted_tags: List[str]    # Extracted keyword tags e.g. ["travel_expenses", "meal_allowance"]
    confidence: float           # Classification confidence score
```

### Supported Intent Domains:
* **`technical_docs`**: Target categories `["technical_docs"]`. Tags: `adk`, `agents-cli`, `rag_engine`, `deploy`.
* **`hr_policies`**: Target categories `["hr_policies"]`. Tags: `remote_work`, `travel_expenses`, `meal_allowance`.
* **`security_governance`**: Target categories `["security_governance"]`. Tags: `agent_registry`, `agent_identity`, `iam`.
* **`general_faq`**: Fallback domain for uncategorized general queries.

---

## 🔍 6. Multi-Tier Retrieval Engine & Fallback Flow (`app/agent.py`)

When `consult_knowledge_base(query)` is invoked by the Gemini agent, it calculates a composite relevance score for each candidate paragraph:

$$\text{Composite Score} = (\text{Keyword Overlap} \times 1.0) + (\text{Tag Overlap} \times 2.0) + \text{Category Match Score}$$

### Progressive Fallback Tiers:

1. **Tier 1 (Strict Category & Tag Search)**:
   Filters search candidates strictly within `target_categories` and requires word/tag matches.
2. **Tier 2 (Category Relaxation Fallback)**:
   If Tier 1 returns 0 matches, category restrictions are removed to search across all documents.
3. **Tier 3 (Partial Metadata Title & Summary Match)**:
   Matches search keywords against document titles, headers, and section summaries.
4. **Tier 4 (Intent-Aware Guidance Prompt)**:
   If no text passages match, returns structured domain guidance:
   - Lists topics covered in that intent domain.
   - Recommends 2–3 actionable suggested queries.
   - Provides domain support contacts (e.g. `hr@novasmart.com`, `sec-team@novasmart.com`).

---

## 💻 7. Local Execution & Testing

### Installation
```bash
cd simple-rag-agent
agents-cli install
```

### Test Queries via CLI

**1. HR Policy Query (Tier 1 Match)**:
```bash
agents-cli run "What is the daily meal allowance for business travel?"
```

**2. Technical Documentation Query (Tier 1 Match)**:
```bash
agents-cli run "How do I scaffold a project using agents-cli?"
```

**3. Unhandled Query (Tier 4 Fallback Trigger)**:
```bash
agents-cli run "What is the pet policy in the office?"
```

### Web Interactive Playground
```bash
agents-cli playground
```

---

## 🚀 8. Deployment Options

This agent is production-ready for deployment to Google Cloud:

* **Vertex AI Agent Runtime**:
  ```bash
  agents-cli deploy
  ```
* **Cloud Run**:
  ```bash
  agents-cli deploy --target cloud-run
  ```
