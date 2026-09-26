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

from dataclasses import dataclass, field
import re
from typing import List


@dataclass
class QueryIntent:
    intent_type: str
    target_categories: List[str] = field(default_factory=list)
    extracted_tags: List[str] = field(default_factory=list)
    confidence: float = 1.0


# Intent classification rules mapping keywords/patterns to categories and tags
INTENT_PATTERNS = {
    "technical_docs": {
        "keywords": [
            "adk",
            "agents-cli",
            "cli",
            "gemini",
            "rag",
            "rag engine",
            "scaffold",
            "deploy",
            "playground",
            "eval",
            "framework",
            "vector",
            "embedding",
            "sdk",
            "code",
        ],
        "categories": ["technical_docs"],
        "tag_map": {
            "adk": ["adk", "framework"],
            "cli": ["agents-cli", "cli", "scaffold"],
            "rag": ["rag_engine", "vector_search"],
            "deploy": ["deploy", "agents-cli"],
        },
    },
    "hr_policies": {
        "keywords": [
            "remote work",
            "hybrid",
            "working hours",
            "travel",
            "expense",
            "meal",
            "allowance",
            "reimbursement",
            "flight",
            "policy",
            "schedule",
            "hotel",
            "per diem",
        ],
        "categories": ["hr_policies"],
        "tag_map": {
            "remote": ["remote_work", "working_hours"],
            "travel": ["travel_expenses", "reimbursement"],
            "meal": ["meal_allowance", "travel_expenses"],
            "expense": ["travel_expenses", "reimbursement"],
        },
    },
    "security_governance": {
        "keywords": [
            "governance",
            "security",
            "agent registry",
            "agent identity",
            "iam",
            "least privilege",
            "service account",
            "compliance",
            "audit",
        ],
        "categories": ["security_governance"],
        "tag_map": {
            "registry": ["agent_registry", "ai_governance"],
            "identity": ["agent_identity", "iam"],
            "iam": ["iam", "least_privilege"],
            "security": ["security", "ai_governance"],
        },
    },
}


def classify_intent(query: str) -> QueryIntent:
    """Classifies a user query into an intent category and extracts relevant metadata tags.

    Args:
        query: The raw user query string.

    Returns:
        QueryIntent object containing intent_type, target_categories, and extracted_tags.
    """
    query_lower = query.lower()
    query_words = set(re.findall(r"\w+", query_lower))

    best_intent = "general_faq"
    highest_score = 0
    selected_categories = []
    extracted_tags = set()

    for intent_name, config in INTENT_PATTERNS.items():
        score = 0
        matched_tags = set()

        for kw in config["keywords"]:
            if kw in query_lower:
                score += 2 if " " in kw else 1

        for tag_kw, tags in config["tag_map"].items():
            if tag_kw in query_lower or tag_kw in query_words:
                matched_tags.update(tags)

        if score > highest_score:
            highest_score = score
            best_intent = intent_name
            selected_categories = config["categories"]
            extracted_tags = matched_tags

    if highest_score == 0:
        # Uncategorized or general intent
        return QueryIntent(
            intent_type="general_faq",
            target_categories=[],
            extracted_tags=[],
            confidence=0.5,
        )

    return QueryIntent(
        intent_type=best_intent,
        target_categories=selected_categories,
        extracted_tags=list(extracted_tags),
        confidence=min(1.0, 0.5 + (highest_score * 0.15)),
    )
