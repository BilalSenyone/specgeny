# Lesson 11: RAG for Document Understanding

> **Story Context**: Users upload templates, PDFs, design docs, and process descriptions. SpecBot needs to understand these documents to generate accurate specifications. This lesson teaches RAG (Retrieval-Augmented Generation) - combining vector search with LLMs to intelligently extract information from uploaded documents.

---

## 🎯 Learning Objectives

By the end of this lesson, you will:

1. Understand RAG architecture and when to use it
2. Implement document chunking strategies
3. Create vector embeddings for semantic search
4. Build vector stores with ChromaDB/Pinecone
5. Implement retrieval-augmented generation workflows
6. Optimize retrieval quality with hybrid search
7. Handle multi-modal documents (text, images, tables)

**Time**: ~4 hours

---

## 📖 Key Concepts

### What is RAG?

**Traditional LLM**:
```
User: "What are the authentication requirements?"
LLM: "I don't have access to your specific requirements."
```

**RAG-Enhanced LLM**:
```
User: "What are the authentication requirements?"
System:
  1. Convert question to embedding
  2. Search vector store for relevant chunks
  3. Retrieve top 5 most similar chunks
  4. Send chunks + question to LLM
LLM: "Based on your specification document, the authentication
      requirements are: FR-001: Email/password auth, FR-002: OAuth..."
```

### RAG Pipeline

```
┌─────────────┐
│  Documents  │
└──────┬──────┘
       │ 1. Chunk
       ▼
┌──────────────┐
│    Chunks    │
└──────┬───────┘
       │ 2. Embed
       ▼
┌──────────────┐
│ Vector Store │  ◄── 4. Retrieve similar chunks
└──────┬───────┘
       │
       │ 3. Query
       │
┌──────┴───────┐
│     Query    │
└──────┬───────┘
       │ 5. Generate
       ▼
┌──────────────┐
│   LLM + RAG  │
└──────────────┘
```

### When to Use RAG

✅ **Use RAG when**:
- Documents too large for context window
- Need to search across many documents
- Content changes frequently (don't want to fine-tune)
- Want to cite sources
- Building Q&A systems

❌ **Don't use RAG when**:
- Documents fit in context window easily
- Need full document context (not just snippets)
- Can't handle occasional retrieval failures
- Latency is critical (<100ms responses)

---

## 💻 Code Examples

### Example 1: Basic RAG with ChromaDB

```python
"""
src/examples/ex36_basic_rag.py

Simple RAG implementation with ChromaDB
"""

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import ChatPromptTemplate

class RAGState(TypedDict):
    question: str
    retrieved_chunks: List[str]
    answer: str
    sources: List[str]

# Sample document
SAMPLE_SPEC = """
# User Authentication Specification

## Functional Requirements

FR-001: The system SHALL authenticate users via email and password.

FR-002: The system SHALL support OAuth 2.0 authentication with Google and GitHub providers.

FR-003: The system SHALL implement Multi-Factor Authentication (MFA) using TOTP.

FR-004: The system SHALL enforce password complexity requirements:
- Minimum 12 characters
- At least one uppercase letter
- At least one number
- At least one special character

## Security Requirements

SEC-001: Passwords SHALL be hashed using bcrypt with cost factor 12.

SEC-002: Session tokens SHALL expire after 24 hours of inactivity.

SEC-003: Failed login attempts SHALL be rate-limited to 5 attempts per 15 minutes.

## Performance Requirements

PERF-001: Authentication SHALL complete within 500ms for 95% of requests.

PERF-002: The system SHALL support 1000 concurrent authentication requests.
"""

def setup_vector_store() -> Chroma:
    """Initialize vector store with document"""

    # 1. Split document into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n## ", "\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_text(SAMPLE_SPEC)

    # 2. Create embeddings
    embeddings = OpenAIEmbeddings()

    # 3. Create vector store
    vectorstore = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        collection_name="spec_demo"
    )

    return vectorstore

# Initialize vector store
vectorstore = setup_vector_store()

def retrieve_relevant_chunks(state: RAGState) -> RAGState:
    """Retrieve relevant chunks for question"""
    question = state["question"]

    # Semantic search in vector store
    results = vectorstore.similarity_search(
        question,
        k=3  # Top 3 most relevant chunks
    )

    chunks = [doc.page_content for doc in results]
    sources = [f"Chunk {i+1}" for i in range(len(results))]

    print(f"Retrieved {len(chunks)} relevant chunks")

    return {
        "retrieved_chunks": chunks,
        "sources": sources
    }

def generate_answer(state: RAGState) -> RAGState:
    """Generate answer using retrieved context"""
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a requirements analyst. Answer the question
        using ONLY the provided context. If the context doesn't contain
        the answer, say "I don't have information about that in the provided context."

        Always cite which requirements you're referring to (e.g., FR-001)."""),
        ("user", """Context:
        {context}

        Question: {question}

        Answer:""")
    ])

    context = "\n\n".join(state["retrieved_chunks"])

    response = llm.invoke(
        prompt.format_messages(
            context=context,
            question=state["question"]
        )
    )

    return {"answer": response.content}

# Build RAG workflow
workflow = StateGraph(RAGState)
workflow.add_node("retrieve", retrieve_relevant_chunks)
workflow.add_node("generate", generate_answer)

workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)

app = workflow.compile()

# Test
questions = [
    "What authentication methods are supported?",
    "What are the password requirements?",
    "How long do session tokens last?",
]

for question in questions:
    print(f"\n{'='*60}")
    print(f"Q: {question}")
    print(f"{'='*60}")

    result = app.invoke({
        "question": question,
        "retrieved_chunks": [],
        "answer": "",
        "sources": []
    })

    print(f"A: {result['answer']}")
    print(f"Sources: {', '.join(result['sources'])}")
```

### Example 2: Advanced Chunking Strategies

```python
"""
src/examples/ex37_chunking_strategies.py

Compare different chunking strategies for optimal retrieval
"""

from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    MarkdownTextSplitter,
    TokenTextSplitter
)

SAMPLE_DOC = """
# Section 1: Authentication

The system provides multiple authentication methods.

## 1.1 Email Authentication
Users can authenticate using email and password. Passwords must meet complexity requirements.

## 1.2 OAuth Authentication
OAuth 2.0 is supported for Google and GitHub providers.

# Section 2: Security

## 2.1 Password Hashing
Passwords are hashed using bcrypt with cost factor 12.

## 2.2 Session Management
Session tokens expire after 24 hours.
"""

def compare_chunking_strategies():
    """Compare different chunking approaches"""

    strategies = {
        "Recursive (500 chars)": RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        ),
        "Markdown Headers": MarkdownTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        ),
        "Token-based (100 tokens)": TokenTextSplitter(
            chunk_size=100,
            chunk_overlap=10
        ),
        "Semantic (by section)": RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=["\n# ", "\n## ", "\n### ", "\n\n", "\n", " "]
        )
    }

    for name, splitter in strategies.items():
        chunks = splitter.split_text(SAMPLE_DOC)

        print(f"\n{'='*60}")
        print(f"Strategy: {name}")
        print(f"{'='*60}")
        print(f"Number of chunks: {len(chunks)}")
        print(f"\nChunk 1:")
        print(chunks[0][:200] + "..." if len(chunks[0]) > 200 else chunks[0])

compare_chunking_strategies()

# Best practices for chunking
def optimal_chunking(document: str, doc_type: str) -> List[str]:
    """Choose optimal chunking strategy based on document type"""

    if doc_type == "specification":
        # Preserve requirement structure
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            separators=[
                "\n## ",  # Section headers
                "\n\n",   # Paragraphs
                "\nFR-",  # Functional requirements
                "\nNFR-", # Non-functional requirements
                "\n",
                " "
            ]
        )
    elif doc_type == "markdown":
        splitter = MarkdownTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
    elif doc_type == "code":
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=50,
            separators=[
                "\nclass ",
                "\ndef ",
                "\n\n",
                "\n",
                " "
            ]
        )
    else:
        # Default
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )

    return splitter.split_text(document)
```

### Example 3: Hybrid Search (Semantic + Keyword)

```python
"""
src/examples/ex38_hybrid_search.py

Combine semantic search with keyword search for better retrieval
"""

from typing import TypedDict, List
from rank_bm25 import BM25Okapi
import numpy as np

class HybridRAGState(TypedDict):
    question: str
    retrieved_chunks: List[str]
    retrieval_scores: List[float]
    answer: str

class HybridRetriever:
    """Combine semantic and keyword-based retrieval"""

    def __init__(self, chunks: List[str], embeddings):
        self.chunks = chunks
        self.embeddings = embeddings

        # Create vector store for semantic search
        self.vectorstore = Chroma.from_texts(
            texts=chunks,
            embedding=embeddings
        )

        # Create BM25 index for keyword search
        tokenized_chunks = [chunk.split() for chunk in chunks]
        self.bm25 = BM25Okapi(tokenized_chunks)

    def retrieve(self, query: str, k: int = 5, alpha: float = 0.5) -> List[dict]:
        """
        Hybrid retrieval: semantic + keyword

        Args:
            query: Search query
            k: Number of results to return
            alpha: Weight for semantic search (1-alpha for keyword search)
        """

        # 1. Semantic search
        semantic_results = self.vectorstore.similarity_search_with_score(
            query, k=k*2
        )

        # Normalize scores to 0-1
        semantic_scores = {}
        max_score = max(score for _, score in semantic_results)
        for doc, score in semantic_results:
            normalized = 1 - (score / max_score)  # Lower distance = higher score
            semantic_scores[doc.page_content] = normalized

        # 2. Keyword search (BM25)
        tokenized_query = query.split()
        bm25_scores = self.bm25.get_scores(tokenized_query)

        # Normalize BM25 scores
        max_bm25 = max(bm25_scores)
        if max_bm25 > 0:
            bm25_scores = bm25_scores / max_bm25

        # 3. Combine scores
        combined_scores = {}
        for i, chunk in enumerate(self.chunks):
            semantic_score = semantic_scores.get(chunk, 0)
            keyword_score = bm25_scores[i]

            combined = alpha * semantic_score + (1 - alpha) * keyword_score
            combined_scores[chunk] = combined

        # 4. Sort and return top k
        sorted_chunks = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:k]

        return [
            {"content": chunk, "score": score}
            for chunk, score in sorted_chunks
        ]

# Example usage
chunks = [
    "FR-001: The system SHALL authenticate users via email and password.",
    "FR-002: The system SHALL support OAuth 2.0 authentication.",
    "SEC-001: Passwords SHALL be hashed using bcrypt with cost factor 12.",
    "PERF-001: Authentication SHALL complete within 500ms.",
    "The authentication system provides multiple login methods including email/password and OAuth."
]

retriever = HybridRetriever(chunks, OpenAIEmbeddings())

# Test queries
queries = [
    "password hashing",        # Keyword match with SEC-001
    "how do users log in",     # Semantic match with FR-001, FR-002
    "OAuth authentication"     # Both keyword and semantic
]

for query in queries:
    print(f"\nQuery: {query}")
    print("-" * 60)

    results = retriever.retrieve(query, k=3, alpha=0.7)

    for i, result in enumerate(results):
        print(f"{i+1}. (Score: {result['score']:.3f}) {result['content'][:80]}...")
```

---

## 🏋️ Hands-On Exercise: Multi-Document RAG System

**Objective**: Build a RAG system that handles multiple uploaded specification documents.

### Requirements

Create a system that:
1. Accepts multiple document uploads (PDFs, Markdown, plain text)
2. Chunks and indexes each document separately
3. Retrieves relevant chunks across all documents
4. Tracks which document each chunk came from
5. Generates answers with proper source citations
6. Handles document updates (re-indexing)

### Starter Code

Create `src/exercises/ex11_multi_doc_rag.py`:

```python
"""
Exercise 11: Multi-Document RAG System

Build RAG system for multiple specification documents
"""

from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, START, END
import operator

class MultiDocRAGState(TypedDict):
    query: str
    documents: List[dict]  # [{"id": "doc1", "title": "...", "content": "..."}]
    retrieved_chunks: Annotated[List[dict], operator.add]
    answer: str
    source_documents: List[str]

# TODO: Implement DocumentIndexer class
class DocumentIndexer:
    """Index and retrieve from multiple documents"""

    def __init__(self):
        self.vectorstore = None
        self.document_metadata = {}

    def add_document(self, doc_id: str, title: str, content: str):
        """Add document to index"""
        # TODO: Chunk document
        # TODO: Add metadata (doc_id, title, chunk_index)
        # TODO: Add to vector store
        pass

    def update_document(self, doc_id: str, content: str):
        """Update existing document"""
        # TODO: Remove old chunks
        # TODO: Re-index new content
        pass

    def retrieve(self, query: str, k: int = 5) -> List[dict]:
        """Retrieve chunks with source tracking"""
        # TODO: Search vector store
        # TODO: Include metadata in results
        # TODO: Return [{chunk, doc_id, doc_title, score}]
        pass

# TODO: Implement nodes
# 1. index_documents - Index all uploaded documents
# 2. retrieve_chunks - Find relevant chunks across documents
# 3. rank_by_relevance - Re-rank results
# 4. generate_answer - Generate answer with citations

# TODO: Build workflow

# Test with sample documents
test_docs = [
    {
        "id": "auth_spec",
        "title": "Authentication Specification",
        "content": "FR-001: System SHALL authenticate via email..."
    },
    {
        "id": "security_spec",
        "title": "Security Requirements",
        "content": "SEC-001: Passwords SHALL be hashed with bcrypt..."
    },
    {
        "id": "api_spec",
        "title": "API Specification",
        "content": "API-001: Authentication endpoint SHALL be /auth/login..."
    }
]
```

---

## 🚀 Challenge: RAG with Confidence Scoring

**Advanced**: Build a RAG system that provides confidence scores and knows when to say "I don't know".

### Challenge Requirements

Create a system that:
1. **Scores retrieval quality** (how relevant are retrieved chunks?)
2. **Assesses answer confidence** (does context support the answer?)
3. **Detects hallucinations** (is answer consistent with context?)
4. **Provides alternatives** when confidence is low
5. **Explains reasoning** (why this answer, which sources support it)

---

## 🎓 Key Takeaways

### RAG Best Practices

✅ **DO**:
- Experiment with chunk sizes (300-1000 chars typical)
- Use semantic chunking (preserve logical boundaries)
- Include metadata with chunks (source, page number, section)
- Implement hybrid search for better recall
- Test retrieval quality before adding LLM
- Cache embeddings to save costs

❌ **DON'T**:
- Use fixed chunk size for all document types
- Forget to handle chunk overlap
- Ignore retrieval quality metrics
- Skip document preprocessing (clean text)
- Store sensitive data in vector stores without encryption
- Assume retrieval is always correct

### Optimal Chunk Sizes by Content Type

| Content Type | Optimal Size | Overlap | Notes |
|--------------|-------------|---------|-------|
| Specifications | 500-800 chars | 100 | Preserve requirements |
| Technical docs | 800-1200 chars | 150 | Larger context needed |
| Code | 300-600 chars | 50 | Preserve functions |
| Conversational | 200-400 chars | 50 | Quick retrieval |

---

## 🔄 Story Progress: SpecBot v0.11

**What we built**: SpecBot now understands uploaded documents!

```python
# SpecBot v0.11 - RAG Integration

# User uploads template + reference docs
indexer = DocumentIndexer()
indexer.add_document("template", "Template.docx", template_content)
indexer.add_document("style_guide", "StyleGuide.pdf", style_content)
indexer.add_document("examples", "Examples.md", examples_content)

# User asks: "How should requirements be formatted?"
retrieved = indexer.retrieve(query, k=5)

# Generate answer using retrieved context
answer = llm_with_context(query, retrieved)
# "Based on your style guide (StyleGuide.pdf, Section 3),
#  requirements should use SHALL for mandatory items..."

# Accurate answers from user's own documents!
```

**Next Step**: Lesson 12 teaches multi-document synthesis - combining information from multiple sources to generate comprehensive specifications.

---

**Continue to [Lesson 12: Multi-Document Synthesis →](./12-multi-document-synthesis.md)**
