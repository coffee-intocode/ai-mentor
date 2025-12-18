Production checklist and recommendations
Optimal RAG pipeline (2025)

Preprocessing: Apply contextual retrieval (Anthropic's method) to chunks before embedding
Embedding: voyage-3.5 (API) or Qwen3-Embedding-8B (self-hosted) at 1024 dimensions
Index: HNSW on pgvector with m=16, ef_construction=64
First-stage retrieval: Hybrid (dense + BM25) with RRF fusion
Reranking: Cohere Rerank 3 or mxbai-rerank-large-v2, top 5-10 results
Generation: Claude 3.5 or GPT-4o with 20 context chunks anthropic

Key metrics to track

Hit rate: Does relevant chunk appear in top-k?
Precision@k: Fraction of retrieved chunks actually relevant
Faithfulness: Does LLM answer align with retrieved content?
Latency breakdown: Embedding, retrieval, reranking, generation times

Common pitfalls to avoid

Skipping reranking: Embeddings optimize recall, not precision—reranking improves final quality by 15-30%
Over-chunking: 512 tokens with 10-20% overlap is a solid default; smaller chunks rarely help
Single retrieval method: Hybrid (dense + sparse) consistently outperforms either alone anthropic
Ignoring context loss: Use late chunking or contextual retrieval for documents with cross-references
Wrong index operator: Match index operator class (vector_cosine_ops) to your query operator

Conclusion
Building production RAG in 2025 requires thoughtful selection across multiple components: embedding models have largely commoditized with open-source matching proprietary quality; HNSW indexing on pgvector handles most scales; and hybrid retrieval with reranking has emerged as the clear winner for retrieval accuracy.
The highest-impact improvements come from preprocessing (contextual retrieval reduces failures 67%) and retrieval strategy (hybrid + reranking), not from chasing marginal embedding model improvements. anthropic Start with the recommended defaults—voyage-3.5-lite embeddings, 512-token recursive chunks, HNSW index, hybrid retrieval with Cohere reranking—then iterate based on your specific metrics.
For multimodal applications, the text-grounding approach (transcribe/describe → text embeddings) remains most production-ready, while native multimodal models like Twelve Labs Marengo are maturing for specialized use cases. The tooling has matured sufficiently that a well-architected FastAPI + Supabase stack can serve production RAG workloads up to millions of documents without requiring specialized vector database infrastructure.
