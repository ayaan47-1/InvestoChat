# Questions for AI Professor

**Context**: RAG system for real estate brochures with moderate retrieval scores (0.35-0.58 for semantic queries)

---

## 🔥 Priority Questions

### 1. Retrieval Strategy

**Current**: OpenAI text-embedding-3-small (generic model trained on web data)

**Issues**: Marketing brochure language ≠ direct user questions → low similarity scores

**Questions**:
- Fine-tune sentence-transformers on 100-500 real estate Q&A pairs vs use larger generic model?
- Expected improvement from domain fine-tuning vs effort investment?
- ColBERT or other late-interaction models worth exploring?

### 2. Reranking vs Better Embeddings

**Option A**: Add cross-encoder reranking (ms-marco-MiniLM)
- Effort: Medium (3-4 hours)
- Expected gain: +10-15%
- Latency impact: +100ms

**Option B**: Fine-tune embeddings
- Effort: High (8-12 hours)
- Expected gain: +20-40%
- Latency impact: None

**Question**: Which should I prioritize first?

### 3. Evaluation Methodology

**Current**: No systematic evaluation (just similarity scores)

**Questions**:
- Best metrics for real estate Q&A? (MRR, NDCG@k, Recall@k?)
- How many labeled query-document pairs needed for reliable evaluation?
- Use GPT-4 as judge vs manual annotation?

---

## 🔧 Technical Questions

### Hybrid Retrieval
- BM25 + dense retrieval fusion: Worth implementing vs current SQL fallback?
- How to weight reciprocal rank fusion (RRF) without labeled data?

### Chunking Strategy
- Page-level (current) vs paragraph-level with 100-char overlap?
- Semantic chunking (LLM-based) worth the cost?
- Hierarchical retrieval for 80-page brochures?

### Query Expansion
- Rule-based templates vs LLM-based expansion?
- Pseudo-relevance feedback applicable here?

### Multimodal
- CLIP embeddings for floor plan images vs image captioning first?
- How to fuse text + image retrieval scores?

---

## 📊 Specific Scenarios

### Scenario 1: Factual Queries
**"Where is TARC Ishva?"** → 0.26 (documents) vs 0.75 (curated facts)

**Question**: Is curated facts the right approach, or should document retrieval work better?

### Scenario 2: Missing Data
**"What is Estate 360's payment plan?"** → No data in brochure

**Question**: Placeholder approach (returns "not found" with 0.50-0.57 similarity) vs confidence threshold detection?

### Scenario 3: Semantic Gap
**User**: "What facilities are there?"
**Brochure**: "Club Ishva - gracious exclusive opulence..."

**Question**: How to bridge this gap without fine-tuning?

---

## 🚀 Production Considerations

### Scaling
- PostgreSQL pgvector vs Pinecone/Weaviate for 20+ projects?
- Current: Query embedding (200ms) + Search (50ms) + LLM (800ms) = 1s
- Target: <500ms
- Where to optimize?

### Model Selection
- Smaller fine-tuned (all-MiniLM-L6-v2) vs larger generic (text-embedding-3-large)?
- Accuracy vs latency vs cost trade-off?

---

## 💡 Key Insight to Discuss

**My Solution So Far**:
- Curated facts for high-frequency queries (0.75 scores) ✅
- Table standardization with placeholders ✅
- Multi-path retrieval (facts → documents → SQL) ✅

**Remaining Gap**:
- Semantic queries still 0.35-0.58 (want 0.60-0.70)
- Need guidance on best path forward: embeddings vs reranking vs chunking

**Your Recommendation?**

---

## Research Potential

If novel contributions emerge:
1. Hybrid RAG with graceful degradation (placeholders)
2. Multi-source retrieval coordination (facts + tables + docs + images)
3. Domain-specific retrieval benchmarking

**Question**: Worth pursuing as research contribution?
