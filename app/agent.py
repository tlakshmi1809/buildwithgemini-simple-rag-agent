# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Tuple

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from app.intent import classify_intent

# Path to local knowledge base and metadata
KNOWLEDGE_BASE_DIR = Path(__file__).parent.parent / "knowledge_base"
METADATA_FILE = KNOWLEDGE_BASE_DIR / "metadata.json"


def _load_metadata() -> Dict[str, Any]:
    """Loads the knowledge base metadata index if available."""
    if METADATA_FILE.exists():
        try:
            return json.loads(METADATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"documents": []}


def _build_intent_fallback_message(
    intent_type: str, target_categories: List[str], query: str
) -> str:
    """Generates structured, intent-aware fallback guidance when no passages match."""
    metadata = _load_metadata()
    available_docs = metadata.get("documents", [])

    categories_map = {
        "hr_policies": {
            "label": "HR & Corporate Policies",
            "covered": [
                "Flexible Working Hours & Remote Work (up to 3 days remote)",
                "Travel Expense Reimbursement ($75/day meal allowance, economy flights)",
            ],
            "suggestions": [
                "What is the remote work policy?",
                "How much is the travel meal allowance?",
            ],
            "contact": "For unlisted HR inquiries, contact People Ops at hr@novasmart.com.",
        },
        "technical_docs": {
            "label": "Technical Documentation (ADK & agents-cli)",
            "covered": [
                "Agent Development Kit (ADK) features and architecture",
                "agents-cli commands (scaffold, run, eval, deploy)",
                "Vertex AI RAG Engine serverless vector search",
            ],
            "suggestions": [
                "What is ADK?",
                "How do I scaffold a project using agents-cli?",
                "What is Vertex AI RAG Engine?",
            ],
            "contact": "For technical support, check developer docs or contact dev-support@novasmart.com.",
        },
        "security_governance": {
            "label": "Security & AI Governance",
            "covered": [
                "Mandatory Agent Registry registration for production agents",
                "Distinct Agent Identity (no shared service accounts)",
                "Least-privilege IAM policy enforcement",
            ],
            "suggestions": [
                "What is the policy for agent identities?",
                "What are the Agent Registry rules?",
            ],
            "contact": "For security escalations, contact Platform Security at sec-team@novasmart.com.",
        },
    }

    fallback_info = categories_map.get(
        intent_type,
        {
            "label": "General Knowledge Base",
            "covered": [
                "ADK & agents-cli technical documentation",
                "NovaSmart HR, hybrid work, and travel expense policies",
                "AI Security and Governance requirements",
            ],
            "suggestions": [
                "What is ADK?",
                "What is the travel meal allowance?",
                "What is the AI governance policy?",
            ],
            "contact": "Please rephrase your question or contact support.",
        },
    )

    lines = [
        f"=== Fallback Mode Active (Intent: '{intent_type}' | Target Categories: {target_categories}) ===",
        f"Notice: No exact document matches were found in the knowledge base for query: '{query}'.",
        "",
        f"📌 **Domain Area**: {fallback_info['label']}",
        "📋 **Available Topics Covered in Knowledge Base**:",
    ]
    for topic in fallback_info["covered"]:
        lines.append(f"  - {topic}")

    lines.extend(["", "💡 **Suggested Queries to Try**:"])
    for sug in fallback_info["suggestions"]:
        lines.append(f"  • \"{sug}\"")

    lines.extend(["", f"✉️ **Help & Contact**: {fallback_info['contact']}"])

    return "\n".join(lines)


def consult_knowledge_base(query: str) -> str:
    """Search the knowledge base using intent classification, metadata filtering, and multi-tier fallbacks.

    Args:
        query: The topic or question to search for in the document collection.

    Returns:
        Relevant passages from matching documents, or structured fallback guidance if no content matches.
    """
    # 1. Classify User Intent & Extract Filters
    intent_result = classify_intent(query)
    intent_type = intent_result.intent_type
    target_categories = intent_result.target_categories
    extracted_tags = set(intent_result.extracted_tags)

    corpus_name = os.getenv("VERTEX_RAG_CORPUS_NAME")

    # 2. Vertex AI RAG Corpus Search
    if corpus_name:
        try:
            from vertexai.preview import rag
            import vertexai

            project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
            location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
            if project:
                vertexai.init(project=project, location=location)

            resp = rag.retrieval_query(
                text=query,
                rag_resources=[rag.RagResource(rag_corpus=corpus_name)],
                rag_retrieval_config=rag.RagRetrievalConfig(top_k=5),
            )
            contexts = getattr(resp.contexts, "contexts", [])
            passages = [c.text.strip() for c in contexts if getattr(c, "text", "").strip()]
            if passages:
                return (
                    f"[Intent: {intent_type} | Categories: {', '.join(target_categories)}]\n\n"
                    + "\n\n---\n\n".join(passages)
                )
        except Exception:
            pass

    if not KNOWLEDGE_BASE_DIR.exists():
        return "Knowledge base directory not found."

    metadata = _load_metadata()
    doc_metadata_map = {doc["file_name"]: doc for doc in metadata.get("documents", [])}
    query_words = set(re.findall(r"\w+", query.lower()))

    # Function to evaluate candidate paragraphs
    def _search_passages(categories_filter: List[str], require_word_overlap: bool) -> List[Tuple]:
        matches = []
        for file_path in KNOWLEDGE_BASE_DIR.glob("*.txt"):
            file_name = file_path.name
            doc_meta = doc_metadata_map.get(file_name, {})
            doc_category = doc_meta.get("category", "general")
            doc_tags = set(doc_meta.get("tags", []))

            # Apply Category Filter if provided
            if categories_filter and doc_category not in categories_filter:
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                paragraphs = content.split("\n\n")

                for para in paragraphs:
                    para_clean = para.strip()
                    if not para_clean:
                        continue

                    para_words = set(re.findall(r"\w+", para_clean.lower()))
                    keyword_overlap = len(query_words.intersection(para_words))
                    tag_overlap = len(extracted_tags.intersection(doc_tags))

                    if require_word_overlap and (keyword_overlap == 0 and tag_overlap == 0):
                        continue

                    category_score = 3.0 if categories_filter else 1.0
                    composite_score = (keyword_overlap * 1.0) + (tag_overlap * 2.0) + category_score

                    matches.append(
                        (
                            composite_score,
                            file_name,
                            doc_category,
                            list(doc_tags),
                            para_clean,
                        )
                    )
            except Exception:
                continue
        return matches

    # TIER 1 SEARCH: Strict Intent & Category Filtered Search
    candidate_matches = _search_passages(categories_filter=target_categories, require_word_overlap=True)

    # TIER 2 FALLBACK: Category Relaxation (Search across ALL categories if strict category yielded 0 results)
    tier_label = "Tier 1 (Intent & Category Filtered)"
    if not candidate_matches and target_categories:
        candidate_matches = _search_passages(categories_filter=[], require_word_overlap=True)
        tier_label = "Tier 2 Fallback (Broadened Cross-Category Search)"

    # TIER 3 FALLBACK: Partial / Metadata Keyword Search Across Document Summaries & Titles
    if not candidate_matches:
        for file_path in KNOWLEDGE_BASE_DIR.glob("*.txt"):
            file_name = file_path.name
            doc_meta = doc_metadata_map.get(file_name, {})
            doc_title = doc_meta.get("title", "")
            doc_category = doc_meta.get("category", "general")
            doc_tags = doc_meta.get("tags", [])

            # Check if query words appear in document title or section summaries
            title_match = any(q_word in doc_title.lower() for q_word in query_words if len(q_word) > 3)
            if title_match:
                try:
                    content = file_path.read_text(encoding="utf-8")
                    first_para = content.split("\n\n")[0].strip()
                    candidate_matches.append((1.5, file_name, doc_category, doc_tags, first_para))
                except Exception:
                    pass
        if candidate_matches:
            tier_label = "Tier 3 Fallback (Partial Metadata Match)"

    # TIER 4 FALLBACK: Intent-Guided Structured Fallback Response
    if not candidate_matches:
        return _build_intent_fallback_message(intent_type, target_categories, query)

    # Sort matches by composite score (highest relevance first)
    candidate_matches.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, doc_name, cat, tags, text in candidate_matches[:3]:
        tags_str = ", ".join(tags) if tags else "none"
        results.append(
            f"[Source: {doc_name} | Category: {cat} | Tags: {tags_str}]\n{text}"
        )

    header = (
        f"=== Search Metadata: [{tier_label}] | Intent='{intent_type}' | "
        f"Target Categories={target_categories} | Extracted Tags={list(extracted_tags)} ==="
    )
    return f"{header}\n\n" + "\n\n---\n\n".join(results)


root_agent = Agent(
    name="rag_agent",
    model=Gemini(
        model="gemini-3.6-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are an optimized RAG assistant powered by Intent Classification, Metadata Filtering, and Multi-Tier Fallbacks. "
        "Answer user questions using the knowledge base. "
        "Always call consult_knowledge_base to retrieve passages or fallback guidance before answering. "
        "If a fallback message is returned because no content matched the query, explain clearly what topics are covered "
        "and guide the user with the suggested queries."
    ),
    tools=[consult_knowledge_base],
)

app = App(
    root_agent=root_agent,
    name="app",
)
