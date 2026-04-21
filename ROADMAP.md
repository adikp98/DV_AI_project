# 🗺️ Project Roadmap & Learning Path

This document outlines a structured path from MVP to production-ready coverage analyzer.

---

## 🎯 Current Status: MVP (Weeks 1-2)

**What's Built:**
- ✅ Basic LangGraph agent with multi-step workflow
- ✅ Coverage report parsing for common formats
- ✅ LLM-powered gap analysis and test suggestion
- ✅ Markdown report generation
- ✅ Sample data for testing

**What You Can Do Now:**
1. Run analysis on mock coverage reports
2. Understand agent state transitions
3. Customize prompts for different protocols
4. Modify report formats

**Skills You'll Learn:**
- LangChain/LangGraph fundamentals
- Prompt engineering for technical tasks
- State machine design
- Coverage report parsing

---

## 📈 Phase 1: Enhance Core Agent (Weeks 3-4)

### 1.1 Improved Parsing
**Goal:** Handle real simulator output formats

**Tasks:**
- [ ] Add VCS URG (Unified Report Generator) parser
- [ ] Add Questa coverage database (UCDB) text export parser
- [ ] Add Verilator coverage parser (LCOV format)
- [ ] Create format auto-detection

**Files to modify:** `coverage_parser.py`

**Learning:** Regular expressions, data structure design

### 1.2 Better Prompting
**Goal:** More accurate and protocol-aware suggestions

**Tasks:**
- [ ] Add protocol-specific prompt templates (AXI, AHB, APB, etc.)
- [ ] Implement few-shot examples in prompts
- [ ] Add chain-of-thought reasoning steps
- [ ] Create evaluation metrics for suggestion quality

**Files to modify:** `agent.py` (prompt templates)

**Learning:** Advanced prompt engineering, few-shot learning

### 1.3 Enhanced Reporting
**Goal:** Richer, more actionable outputs

**Tasks:**
- [ ] Add coverage trend visualization (if historical data)
- [ ] Group gaps by difficulty/priority
- [ ] Add execution time estimates
- [ ] Generate summary dashboard

**Files to modify:** `agent.py` (report generation)

**Learning:** Data visualization, markdown formatting

---

## 🧠 Phase 2: Add RAG (Retrieval-Augmented Generation) (Weeks 5-7)

### 2.1 Document Ingestion
**Goal:** Load protocol specifications into vector database

**Tasks:**
- [ ] Implement PDF loader for specs (PyPDF2)
- [ ] Create document chunking strategy
- [ ] Set up ChromaDB for local vector storage
- [ ] Use sentence-transformers for embeddings (free, local)

**New files:** `ingest.py`, `rag_retrieval.py`

**Learning:** Vector databases, embeddings, semantic search

### 2.2 Context Retrieval
**Goal:** Pull relevant spec sections for each gap

**Tasks:**
- [ ] Implement MMR (Maximal Marginal Relevance) retrieval
- [ ] Add query expansion for better search
- [ ] Create spec-to-gap relevance scoring
- [ ] Handle multi-document specs

**Files to modify:** `agent.py` (add retrieval node)

**Learning:** Information retrieval, similarity metrics

### 2.3 Grounded Suggestions
**Goal:** Cite spec sections in test suggestions

**Tasks:**
- [ ] Modify prompts to include retrieved context
- [ ] Add page/section citations to output
- [ ] Implement citation verification
- [ ] Handle conflicting spec interpretations

**Files to modify:** `agent.py` (prompts and report)

**Learning:** Grounded generation, citation tracking

**Example Enhancement:**
```python
# Before (no RAG)
suggestion = llm.invoke(f"Suggest test for {gap}")

# After (with RAG)
spec_context = vectorstore.similarity_search(gap, k=5)
suggestion = llm.invoke(f"Given spec: {spec_context}, suggest test for {gap}")
```

---

## 🔄 Phase 3: Simulation Loop (Weeks 8-11)

### 3.1 Stimulus Generation
**Goal:** Generate actual runnable SV/UVM code

**Tasks:**
- [ ] Create SV code generation templates
- [ ] Implement UVM sequence skeleton generator
- [ ] Add constraint randomization syntax
- [ ] Generate complete test files (not just snippets)

**New files:** `codegen.py`

**Learning:** Code generation, templating, SV/UVM syntax

### 3.2 Simulator Integration
**Goal:** Run simulations programmatically

**Tasks:**
- [ ] Implement Verilator wrapper (open-source, easiest)
- [ ] Add subprocess management for simulator execution
- [ ] Parse simulation logs for errors
- [ ] Implement timeout and retry logic

**New files:** `simulator.py`

**Learning:** Subprocess management, error handling, log parsing

### 3.3 Coverage Feedback Loop
**Goal:** Iteratively improve coverage

**Tasks:**
- [ ] Parse simulator coverage output
- [ ] Calculate coverage delta (before vs after)
- [ ] Implement stopping criteria (max iterations, coverage target)
- [ ] Add agent self-reflection on failures

**Files to modify:** `agent.py` (add feedback loop nodes)

**Learning:** Iterative algorithms, convergence criteria

**Architecture:**
```
Initial Coverage Report
         ↓
    [Analyze Gaps] ←──────┐
         ↓                 │
    [Generate Test]        │
         ↓                 │
    [Run Simulation]       │
         ↓                 │
    [Parse Coverage] ──────┤
         ↓                 │
    Coverage improved?     │
         ↓                 │
    [Decide: Continue? ]───┘
         ↓
    Final Report
```

---

## 🚀 Phase 4: Production Features (Weeks 12-16)

### 4.1 Web UI
**Goal:** User-friendly interface

**Tasks:**
- [ ] Create Streamlit app with tabs (Upload, Analyze, Results)
- [ ] Add file upload widget
- [ ] Display analysis progress in real-time
- [ ] Add interactive report viewer

**New files:** `app.py`

**Learning:** Streamlit, web UI design

### 4.2 Evaluation Framework
**Goal:** Measure agent effectiveness

**Tasks:**
- [ ] Create ground-truth test dataset
- [ ] Implement suggestion quality metrics
- [ ] Add coverage closure rate measurement
- [ ] Compare against baseline (random testing)

**New files:** `evaluate.py`, `benchmarks/`

**Learning:** ML evaluation, statistical analysis

### 4.3 Advanced Agent Patterns
**Goal:** More sophisticated reasoning

**Tasks:**
- [ ] Add planning node (prioritize hard gaps first)
- [ ] Implement reflection (learn from failed tests)
- [ ] Add tool use (formal verification, constraint solver)
- [ ] Multi-agent collaboration (different agents for different protocols)

**Files to modify:** `agent.py`

**Learning:** Advanced agent architectures, meta-learning

---

## 📊 Suggested Timeline

| Week | Phase | Milestone |
|------|-------|-----------|
| 1-2 | MVP | Basic agent working with mock data |
| 3-4 | Phase 1 | Handle real simulator formats |
| 5-7 | Phase 2 | RAG integration with specs |
| 8-11 | Phase 3 | Closed-loop simulation |
| 12-14 | Phase 4 | Web UI and evaluation |
| 15-16 | Phase 4 | Polish and documentation |

**Total: ~16 weeks** (part-time, ~10hrs/week)

---

## 🎓 Learning Resources

### LLM & Agents
- LangChain Docs: https://python.langchain.com/docs/get_started/introduction
- LangGraph Tutorial: https://langchain-ai.github.io/langgraph/tutorials/
- Anthropic Prompt Engineering: https://docs.anthropic.com/claude/docs/prompt-engineering

### Design Verification
- ChipNeMo Paper: https://arxiv.org/abs/2311.00176
- Coverage-Driven Verification: IEEE paper on CDV methodologies
- SystemVerilog for Verification: Book by Chris Spear

### RAG
- RAG Tutorial: https://python.langchain.com/docs/tutorials/rag/
- ChromaDB Docs: https://docs.trychroma.com/
- Sentence Transformers: https://www.sbert.net/

---

## 💡 Extension Ideas (Beyond Phase 4)

### Research Directions
1. **Fine-tuning:** Train Code Llama on SV/UVM corpus for better code generation
2. **Formal Integration:** Use formal tools to identify unreachable states
3. **Multi-Modal:** Accept waveform diagrams as input
4. **Constraint Solving:** Use SMT solvers to generate exact stimulus

### Portfolio Enhancements
1. **Blog Series:** Document each phase as blog posts
2. **Video Demo:** Record walkthrough for portfolio
3. **Open Dataset:** Create public DV benchmarks
4. **Publication:** Submit to DAC/DVCon

---

## 📝 Documentation Checklist

As you build, maintain:
- [ ] README with clear setup instructions
- [ ] API documentation (docstrings)
- [ ] Architecture diagrams
- [ ] Usage examples
- [ ] Troubleshooting guide
- [ ] Performance benchmarks
- [ ] Limitations and future work

---

## 🎯 Success Metrics

**MVP Success:**
- ✓ Analyzes mock coverage reports correctly
- ✓ Generates plausible test suggestions
- ✓ Clear, readable output

**Phase 2 Success:**
- ✓ Retrieves relevant spec sections (>80% relevance)
- ✓ Suggestions cite specific protocol requirements

**Phase 3 Success:**
- ✓ Generated tests compile and run
- ✓ Coverage improves by >10% on average
- ✓ Faster than manual test writing

**Phase 4 Success:**
- ✓ Non-technical users can run the tool
- ✓ Quantifiable improvement over random testing
- ✓ Portfolio-ready demo

---

**Next Step:** Start with the MVP (already built!), then pick Phase 1 tasks based on what excites you most.
