# 🏗️ System Architecture

Visual guide to understanding the coverage gap analyzer architecture.

---

## 🔄 Agent Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    COVERAGE GAP ANALYZER                         │
│                     LangGraph Agent Flow                         │
└─────────────────────────────────────────────────────────────────┘

INPUT: Coverage Report (Text File)
    │
    │  Contains: Coverage groups, bins, crosses, metrics
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  NODE 1: Parse Coverage Report                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  • Read report text                                        │ │
│  │  • Extract uncovered bins (✗ markers, UNCOVERED keyword)  │ │
│  │  • Parse cross-coverage gaps                              │ │
│  │  • Extract metrics (overall coverage %)                   │ │
│  │  • Organize by coverage group & category                  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Output: List of CoverageGap objects                             │
└─────────────────────────────────────────────────────────────────┘
    │
    │  State: {parsed_gaps: [gap1, gap2, ...], current_gap_index: 0}
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  NODE 2: Analyze Gap                                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  LLM Call 1: Deep Analysis                                 │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │  Prompt: "Analyze this coverage gap"                 │ │ │
│  │  │  Input:                                               │ │ │
│  │  │    - Gap name                                         │ │ │
│  │  │    - Coverage group                                   │ │ │
│  │  │    - Category                                         │ │ │
│  │  │    - Description (if any)                            │ │ │
│  │  │                                                       │ │ │
│  │  │  Output: Technical analysis (2-3 sentences)          │ │ │
│  │  │    - What it represents                              │ │ │
│  │  │    - Why it's uncovered                              │ │ │
│  │  │    - What corner case it targets                     │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Output: gap_analyses[gap] = analysis_text                       │
└─────────────────────────────────────────────────────────────────┘
    │
    │  State: {gap_analyses: {gap1: "analysis...", ...}}
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  NODE 3: Suggest Test                                            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  LLM Call 2: Test Generation                               │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │  Prompt: "Suggest test scenario"                     │ │ │
│  │  │  Input:                                               │ │ │
│  │  │    - Gap name                                         │ │ │
│  │  │    - Analysis from Node 2                            │ │ │
│  │  │    - Coverage group context                          │ │ │
│  │  │                                                       │ │ │
│  │  │  Output: Test suggestion with code                   │ │ │
│  │  │    - Scenario description                            │ │ │
│  │  │    - SystemVerilog/UVM code sketch                   │ │ │
│  │  │    - Configuration details                           │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Output: gap_suggestions[gap] = suggestion_text                  │
│          current_gap_index += 1                                  │
└─────────────────────────────────────────────────────────────────┘
    │
    │  State: {gap_suggestions: {gap1: "test code...", ...}}
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  CONDITIONAL EDGE: More gaps?                                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  if current_gap_index < len(parsed_gaps):                 │ │
│  │      → LOOP BACK to Node 2 (next gap)                     │ │
│  │  else:                                                     │ │
│  │      → CONTINUE to Node 4 (done)                          │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
    │
    │  All gaps processed
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  NODE 4: Generate Report                                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  • Create markdown document                                │ │
│  │  • Add header with metadata                               │ │
│  │  • For each gap:                                           │ │
│  │      - Gap details                                         │ │
│  │      - Analysis from Node 2                                │ │
│  │      - Test suggestion from Node 3                         │ │
│  │  • Add summary and next steps                             │ │
│  │  • Save to outputs/ with timestamp                        │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
OUTPUT: coverage_analysis_TIMESTAMP.md
```

---

## 📊 State Management

```python
AgentState = {
    # Input
    "coverage_report": str,           # Original text
    
    # Parsed data
    "parsed_gaps": List[CoverageGap], # All gaps found
    "design_metrics": Dict,           # Overall coverage %
    
    # Loop control
    "current_gap_index": int,         # Which gap we're on
    
    # LLM outputs (accumulate as we go)
    "gap_analyses": Dict,             # gap → analysis
    "gap_suggestions": Dict,          # gap → test code
    
    # Final output
    "final_report": str,              # Markdown text
    "metadata": Dict                  # Timestamps, counts
}
```

**State flows through the graph:**
- Each node receives state
- Each node returns updated state
- State is immutable (functional style)
- Loop doesn't lose previous results

---

## 🔌 Module Dependencies

```
agent.py (Main orchestrator)
    ├─→ langchain_anthropic (Claude API)
    ├─→ langgraph (State machine)
    ├─→ coverage_parser.py (Parse logic)
    │       ├─→ CoverageGap (Data class)
    │       └─→ CoverageParser (Parser class)
    ├─→ mock_data.py (Sample data)
    └─→ dotenv (Environment vars)

coverage_parser.py (Standalone module)
    ├─→ re (Regex)
    ├─→ dataclasses (CoverageGap)
    └─→ typing (Type hints)

mock_data.py (Standalone module)
    └─→ No external deps
```

**Key Design:** Parser is independent of LLM logic

---

## 🎯 Extension Points

Where to add new features:

### 1. Add New Parser Strategy
```python
# coverage_parser.py
class CoverageParser:
    def _parse_my_format(self):
        """Add new parsing logic here"""
        pass
```

### 2. Add RAG Retrieval Node
```python
# agent.py - Insert between parse and analyze
def retrieve_spec_context(state):
    """Pull relevant spec sections"""
    # Vector search here
    return updated_state

graph.add_node("retrieve", retrieve_spec_context)
graph.add_edge("parse", "retrieve")
graph.add_edge("retrieve", "analyze")
```

### 3. Add Simulation Node
```python
# agent.py - After suggest node
def run_simulation(state):
    """Execute generated test in simulator"""
    # subprocess.run("vsim ...")
    # Parse coverage output
    return updated_state

graph.add_node("simulate", run_simulation)
graph.add_edge("suggest", "simulate")
```

### 4. Add Planning Node
```python
# agent.py - Before analyze
def plan_gap_order(state):
    """Prioritize which gaps to tackle first"""
    # Sort gaps by difficulty/priority
    return updated_state

graph.add_node("plan", plan_gap_order)
graph.add_edge("parse", "plan")
```

---

## 🚦 Control Flow Patterns

### Current: Linear Loop
```
Parse → [Analyze → Suggest] × N → Report
```

### Phase 2: With RAG
```
Parse → [Retrieve → Analyze → Suggest] × N → Report
```

### Phase 3: With Simulation
```
Parse → [Analyze → Suggest → Simulate → Measure] × N → Report
         ↑                                          │
         └──────── Loop if coverage improved ───────┘
```

### Phase 4: Advanced
```
Parse → Plan → [Retrieve → Analyze → Suggest → Simulate] × N
                ↑                                    │
                └──── Reflect & Re-prioritize ──────┘
                                 ↓
                            Final Report
```

---

## 💾 Data Flow

```
Coverage Report File
    │
    ▼
[coverage_parser.py]
    │
    ├─→ List[CoverageGap]
    │      ├─ name: str
    │      ├─ category: str
    │      ├─ coverage_group: str
    │      └─ description: str
    │
    └─→ Dict (metrics)
           ├─ total_coverage: float
           ├─ bins_covered: int
           └─ design_name: str
         │
         ▼
[LangGraph State Machine]
         │
         ├─→ For each gap:
         │      ├─ LLM Analysis → str
         │      └─ LLM Suggestion → str
         │
         ▼
[Markdown Generator]
         │
         ▼
coverage_analysis_TIMESTAMP.md
```

---

## 🎨 Prompt Flow

```
Gap Data → ANALYSIS_PROMPT → Claude Sonnet 4
              │
              ├─ System: "You are a senior DV engineer..."
              ├─ User: "Coverage Gap: {gap_name}..."
              │
              ▼
         Analysis Text (2-3 sentences)
              │
              ▼
Gap + Analysis → SUGGESTION_PROMPT → Claude Sonnet 4
                     │
                     ├─ System: "Suggest specific test..."
                     ├─ User: "Gap: {gap}, Analysis: {analysis}"
                     │
                     ▼
                Test Scenario + Code
```

**Key Pattern:** Second prompt builds on first

---

## 🔄 Execution Timeline

```
T=0s    User runs: python agent.py
T=1s    Load coverage report
T=2s    Parse report → Find 7 gaps
T=3s    Start loop, Gap 1/7
T=4s    LLM call: Analyze Gap 1
T=7s    LLM response received
T=8s    LLM call: Suggest test for Gap 1
T=12s   LLM response received
T=13s   Gap 2/7...
...
T=90s   All 7 gaps processed
T=91s   Generate markdown report
T=92s   Save to outputs/
T=93s   Done!
```

**Bottleneck:** LLM calls (~4s each)  
**Optimization:** Could parallelize analyze+suggest

---

## 📈 Scalability Considerations

### Current (MVP)
- Sequential processing
- In-memory state
- Single report at a time
- ~1 min for 10 gaps

### Phase 2 (RAG)
- Add vector DB overhead
- ~2 min for 10 gaps
- Handles large specs

### Phase 3 (Simulation)
- Simulation time dominates
- ~30 min for 10 gaps (with sims)
- Parallelization critical

### Phase 4 (Production)
- Queue system
- Batch processing
- Caching of analyses
- Multi-threading

---

This architecture is designed to be:
- ✅ **Simple** to understand (4 clear nodes)
- ✅ **Extensible** (add nodes without rewriting)
- ✅ **Debuggable** (explicit state at each step)
- ✅ **Educational** (clear progression path)

Ready to dive into the code? Start with `agent.py` and trace the flow!
