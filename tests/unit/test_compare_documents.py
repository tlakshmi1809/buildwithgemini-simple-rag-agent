"""Unit tests for compare_documents.py utility."""

import pytest
from compare_documents import filter_documents_for_indexing


def test_filter_documents_exact_match():
    list_1 = [
        "/docs/policy.pdf",
        "/docs/manual.docx",
        "/docs/readme.md",
    ]
    list_2 = ["manual.docx", "readme.md"]

    results = filter_documents_for_indexing(list_1, list_2)

    assert len(results) == 2
    doc_names = [doc["document_name"] for doc in results]
    assert "manual.docx" in doc_names
    assert "readme.md" in doc_names
    assert "policy.pdf" not in doc_names


def test_filter_documents_case_insensitive():
    list_1 = ["/docs/TRAVEL_POLICY.PDF", "/docs/ADK_Guide.txt"]
    list_2 = ["travel_policy.pdf", "adk_guide.txt"]

    # Case insensitive matching (default)
    results = filter_documents_for_indexing(list_1, list_2, case_sensitive=False)
    assert len(results) == 2

    # Case sensitive matching
    results_sensitive = filter_documents_for_indexing(list_1, list_2, case_sensitive=True)
    assert len(results_sensitive) == 0


def test_filter_documents_no_match():
    list_1 = ["/docs/policy.pdf"]
    list_2 = ["unrelated_doc.txt"]

    results = filter_documents_for_indexing(list_1, list_2)
    assert len(results) == 0


def test_filter_documents_metadata_fields():
    list_1 = ["/data/knowledge_base/adk_and_gemini.txt"]
    list_2 = ["adk_and_gemini.txt"]

    results = filter_documents_for_indexing(list_1, list_2)
    assert len(results) == 1

    doc = results[0]
    assert doc["document_name"] == "adk_and_gemini.txt"
    assert doc["stem"] == "adk_and_gemini"
    assert doc["extension"] == ".txt"
    assert doc["parent_dir"].endswith("knowledge_base")


def test_filter_documents_empty_inputs():
    assert filter_documents_for_indexing([], ["doc.txt"]) == []
    assert filter_documents_for_indexing(["/path/doc.txt"], []) == []
