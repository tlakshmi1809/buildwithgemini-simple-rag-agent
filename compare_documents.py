#!/usr/bin/env python3
"""
Document Index Matching Utility

Compares two lists:
- List 1: Full document file paths (e.g., '/data/docs/policies/travel_policy.pdf')
- List 2: Target document file names (e.g., 'travel_policy.pdf')

Filters and returns matching items from List 1 for indexing.
"""

from pathlib import Path
from typing import List, Dict, Any


def filter_documents_for_indexing(
    full_paths: List[str], 
    target_doc_names: List[str], 
    case_sensitive: bool = False
) -> List[Dict[str, Any]]:
    """Compares full file paths against target document names and extracts details for indexing.

    Args:
        full_paths: List of full file paths (1st list).
        target_doc_names: List of document file names to filter by (2nd list).
        case_sensitive: Whether matching should be case-sensitive (default: False).

    Returns:
        List of dictionaries containing document details (full path, doc name, extension, directory)
        for all documents that match items in target_doc_names.
    """
    # Normalize target document names for fast O(1) set lookup
    if not case_sensitive:
        target_set = {name.strip().lower() for name in target_doc_names}
    else:
        target_set = {name.strip() for name in target_doc_names}

    matched_documents = []

    for path_str in full_paths:
        path_obj = Path(path_str.strip())
        doc_name = path_obj.name  # Extracts filename with extension (e.g., 'travel_policy.pdf')

        lookup_key = doc_name.lower() if not case_sensitive else doc_name

        if lookup_key in target_set:
            matched_documents.append({
                "full_path": str(path_obj.resolve()),
                "document_name": doc_name,
                "stem": path_obj.stem,           # Filename without extension
                "extension": path_obj.suffix,    # File extension (.pdf, .txt, etc.)
                "parent_dir": str(path_obj.parent),
                "is_exists": path_obj.exists()   # Checks if file physically exists on disk
            })

    return matched_documents


# Example Usage & Demonstration
if __name__ == "__main__":
    # 1st List: Full document paths
    list_1_full_paths = [
        "/var/data/knowledge_base/adk_and_gemini.txt",
        "/var/data/knowledge_base/nova_corp_policies.txt",
        "/var/data/knowledge_base/security_guidelines.pdf",
        "/var/data/knowledge_base/obsolete_notes.doc",
    ]

    # 2nd List: Target document names to match for indexing
    list_2_target_names = [
        "nova_corp_policies.txt",
        "security_guidelines.pdf",
        "non_existent_doc.txt",
    ]

    print("--- Comparing Document Lists for Indexing ---")
    indexed_docs = filter_documents_for_indexing(list_1_full_paths, list_2_target_names)

    print(f"\nFound {len(indexed_docs)} matching documents for indexing:\n")
    for idx, doc in enumerate(indexed_docs, 1):
        print(f"[{idx}] Document Name : {doc['document_name']}")
        print(f"    Full Path     : {doc['full_path']}")
        print(f"    Extension     : {doc['extension']}")
        print(f"    Directory     : {doc['parent_dir']}")
        print("-" * 50)
