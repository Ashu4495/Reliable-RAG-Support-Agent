import pytest
from pathlib import Path
from app.rag import KnowledgeBaseRetriever, DocumentChunk

def test_frontmatter_parsing_and_chunking():
    retriever = KnowledgeBaseRetriever()
    assert len(retriever.chunks) > 0

    # Verify 01-returns-policy-current.md is loaded and active
    current_return_chunks = [c for c in retriever.chunks if c.filename == "01-returns-policy-current.md"]
    assert len(current_return_chunks) > 0
    top_chunk = current_return_chunks[0]
    assert top_chunk.status == "active"
    assert top_chunk.policy_authority == "official"
    assert top_chunk.doc_id == "RET-2026-01"

def test_authority_ranking():
    retriever = KnowledgeBaseRetriever()
    # Query for standard return window
    results = retriever.retrieve("How long to return an unused backpack?", top_k=4)
    assert len(results) > 0
    top_chunk, score = results[0]
    assert top_chunk.filename == "01-returns-policy-current.md"
    assert top_chunk.status == "active"

    # Verify migration draft note is not top result
    filenames = [c.filename for c, s in results]
    assert "14-internal-content-migration-notes.md" not in filenames[:2]

def test_conflict_detection():
    retriever = KnowledgeBaseRetriever()
    results = retriever.retrieve("Can I wash the Breeze Tumbler in the dishwasher?", top_k=4)
    chunks = [c for c, s in results]
    conflict = retriever.detect_active_source_conflict(chunks)
    assert conflict is not None
    assert conflict["conflict_type"] == "breeze_tumbler_cleaning"
    assert conflict["source1"] == "11-product-care.md"
    assert conflict["source2"] == "12-breeze-tumbler-product-card.md"

def test_citation_formatting():
    chunk = DocumentChunk(
        doc_id="TEST-01",
        filename="01-returns-policy-current.md",
        title="Returns Policy",
        heading="Standard return window",
        content="30 days",
        status="active",
        policy_authority="official",
        effective_date="2026-04-01",
        audience="customer",
    )
    assert chunk.citation == "01-returns-policy-current.md → Standard return window"
