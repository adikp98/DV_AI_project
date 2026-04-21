# 🎯 Coverage Gap Analyzer

> An AI-powered assistant that analyzes functional coverage reports and suggests targeted test scenarios to close coverage gaps.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-Latest-green)](https://www.langchain.com/)
[![Claude](https://img.shields.io/badge/LLM-Claude-purple)](https://www.anthropic.com/)

---

## 📋 Overview

Design verification engineers spend significant time analyzing coverage reports to identify test gaps and create new test scenarios. This tool automates that process using LLM-powered analysis.

**Key Features:**
- 📊 Parses functional coverage reports (multiple formats supported)
- 🔍 Identifies uncovered bins and cross-coverage gaps
- 💡 Suggests specific test scenarios to hit uncovered cases
- 🤖 Uses LangGraph for multi-step agentic reasoning
- 📝 Generates detailed analysis reports in Markdown

---

## 🏗️ Architecture

```
Coverage Report → Parse Gaps → Analyze Each Gap → Generate Suggestions → Final Report
                      ↓              ↓                    ↓
                   LLM Extract    Context Builder    Stimulus Generator
```

**Current Version (MVP):**
- Static coverage report analysis
- Mock data for initial testing
- Single-step LLM analysis

**Planned Expansions:**
1. RAG integration with protocol specifications
2. Integration with actual simulators (Verilator, Icarus)
3. Iterative simulation loop with coverage feedback
4. Multi-protocol support

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Anthropic API key ([get one here](https://console.anthropic.com))

### Installation

```bash
# 1. Clone or download this project
cd coverage-gap-analyzer

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up API key
echo "ANTHROPIC_API_KEY=your-key-here" > .env
```

### Run the Analyzer

```bash
# Run with sample coverage report
python agent.py

# Run with your own coverage report
python agent.py --report path/to/your/coverage_report.txt

# Interactive mode
python agent.py --interactive
```

---

## 📁 Project Structure

```
coverage-gap-analyzer/
├── agent.py              # Main LangGraph agent implementation
├── coverage_parser.py    # Coverage report parsing utilities
├── mock_data.py          # Sample coverage reports generator
├── utils.py              # Helper functions
├── requirements.txt      # Python dependencies
├── .env                  # API keys (not committed)
├── data/
│   ├── sample_coverage.txt        # Example coverage report
│   └── sample_coverage_complex.txt # More complex example
├── outputs/
│   └── analysis_report.md         # Generated analysis reports
└── README.md
```

---

## 🎯 Usage Examples

### Example 1: Basic Analysis

```python
from agent import CoverageAgent

agent = CoverageAgent()
result = agent.analyze("data/sample_coverage.txt")
print(result['report'])
```

### Example 2: Custom Coverage Report

Create your own coverage report in this format:

```
COVERAGE REPORT - Simple FIFO Design
=====================================

Coverage Group: fifo_operations
  - empty_to_full: 85% (17/20 bins hit)
    UNCOVERED: consecutive_writes_max_depth
    UNCOVERED: write_when_full
    UNCOVERED: alternating_rd_wr_full
  
  - full_to_empty: 90% (18/20 bins hit)
    UNCOVERED: consecutive_reads_empty
    UNCOVERED: read_when_empty

Cross Coverage: fifo_states x operations
  - 75% coverage (12/16 combinations hit)
    UNCOVERED: (FULL, WRITE)
    UNCOVERED: (EMPTY, READ)
    UNCOVERED: (ALMOST_FULL, WRITE)
    UNCOVERED: (ALMOST_EMPTY, READ)
```

---

## 🛠️ Customization

### Adding Your Own Protocol

1. Update `mock_data.py` with your protocol's coverage structure
2. Modify `coverage_parser.py` to handle your report format
3. Customize prompts in `agent.py` for protocol-specific context

### Adding Simulation Integration

See `docs/SIMULATION_INTEGRATION.md` (coming soon) for:
- Connecting to Verilator/Icarus
- Parsing VCS/Questa UCDB files
- Building iterative coverage closure loop

---

## 🎓 Learning Path

This project is designed to teach you:

**Phase 1: Core Concepts (Current MVP)**
- ✅ LangChain basics and prompt engineering
- ✅ LangGraph for multi-step agent workflows
- ✅ Coverage report parsing and analysis

**Phase 2: RAG Integration (Next)**
- 📚 Vector databases (ChromaDB/Pinecone)
- 🔍 Document retrieval and chunking
- 🧠 Context-aware stimulus generation

**Phase 3: Simulation Loop (Advanced)**
- 🔄 Subprocess management for simulators
- 📊 Coverage delta calculation
- 🎯 Iterative test generation

**Phase 4: Production Features**
- 🌐 Web UI with Streamlit/Gradio
- 📈 Metrics and benchmarking
- 🔐 Multi-user support

---

## 📊 Sample Output

```markdown
# Coverage Gap Analysis Report

**Total gaps analyzed:** 7
**Analysis date:** 2024-01-15

---

## 1. `consecutive_writes_max_depth`

**Gap Description:** This bin tracks the scenario where writes occur 
continuously until FIFO reaches maximum depth without any intervening reads.

**Suggested Test Scenario:**
Create a directed sequence that:
1. Initializes FIFO to empty state
2. Performs continuous write operations (no reads)
3. Writes exactly FIFO_DEPTH transactions
4. Verifies full flag assertion on final write

**Sample Code Sketch:**
```systemverilog
class fifo_max_depth_seq extends base_sequence;
  task body();
    for (int i = 0; i < FIFO_DEPTH; i++) begin
      `uvm_do_with(req, {operation == WRITE;})
    end
  endtask
endclass
```

---
```

---

## 🤝 Contributing

This is a portfolio/learning project. Suggestions welcome!

---

## 📜 License

MIT License - feel free to use and modify.

---

## 👤 Author

Built following the coverage-driven verification roadmap.

**Next Steps:**
1. ⭐ Star this repo if you find it useful
2. 📧 Open an issue with questions or suggestions
3. 🔄 Fork and customize for your own protocols
