# 🚀 Getting Started Guide

Welcome! This guide will get you up and running in 30 minutes.

---

## ⚡ Quick Start (5 minutes)

```bash
# 1. Navigate to project
cd coverage-gap-analyzer

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up API key
cp .env.template .env
# Edit .env and add your Anthropic API key

# 5. Verify setup
python setup.py

# 6. Run first analysis
python agent.py
```

**Expected output:** Analysis report in `outputs/coverage_analysis_TIMESTAMP.md`

---

## 📚 First Steps Tutorial

### Step 1: Understand the Sample Data (5 minutes)

```bash
# Generate sample reports
python mock_data.py

# View the samples
cat data/sample_coverage_simple.txt
cat data/sample_coverage_fifo.txt
```

**What to notice:**
- Coverage groups and categories
- UNCOVERED markers (✗)
- Cross-coverage sections
- Overall coverage percentages

### Step 2: Run the Parser (5 minutes)

```bash
# Test the parser standalone
python coverage_parser.py
```

**What happens:**
1. Loads sample FIFO report
2. Extracts all coverage gaps
3. Organizes by group and category
4. Displays summary statistics

**Try editing:** Modify `mock_data.py` to add your own coverage bins and re-run.

### Step 3: Run the Full Agent (10 minutes)

```bash
# Run with default sample
python agent.py

# Run with specific report
python agent.py --report data/sample_coverage_axi4.txt

# Interactive mode (shows full report in terminal)
python agent.py --interactive
```

**Watch the agent work:**
1. Parse coverage report
2. Analyze each gap (LLM call)
3. Generate test suggestion (LLM call)
4. Assemble final report

**Output location:** `outputs/coverage_analysis_TIMESTAMP.md`

### Step 4: Examine the Output (5 minutes)

Open the generated report in `outputs/`. You should see:

```markdown
# Coverage Gap Analysis Report

**Generated:** 2024-01-15 14:30:00
**Design:** Simple FIFO
**Current Coverage:** 78.5%
**Total Gaps Analyzed:** 7

---

## Gap 1: `write_consecutive_max_depth`

**Coverage Group:** fifo_operations
**Category:** write_scenarios

### Analysis
[LLM-generated analysis of why this gap exists]

### Suggested Test Scenario
[LLM-generated test code and explanation]

---
```

### Step 5: Customize for Your Protocol (Variable)

1. **Create your coverage report:**
   ```bash
   # Create data/my_protocol.txt with your coverage data
   # Follow the format from sample_coverage_simple.txt
   ```

2. **Modify prompts in agent.py:**
   ```python
   # Line ~80: Update ANALYSIS_PROMPT for your protocol
   # Line ~100: Update SUGGESTION_PROMPT with protocol context
   ```

3. **Run analysis:**
   ```bash
   python agent.py --report data/my_protocol.txt
   ```

---

## 🎓 Understanding the Code

### Architecture Overview

```
agent.py                 → LangGraph state machine (main logic)
    ↓
coverage_parser.py      → Extract gaps from reports
    ↓
Agent State             → Flows through graph nodes
    ↓
4 Nodes:
  1. parse_coverage_node    → Extract gaps
  2. analyze_gap_node       → Understand each gap
  3. suggest_test_node      → Generate test code
  4. generate_report_node   → Assemble markdown
    ↓
outputs/                → Final reports
```

### Key Files to Understand

1. **agent.py** (Main agent)
   - `AgentState`: What data flows through the graph
   - `parse_coverage_node`: Entry point
   - `should_continue`: Loop control logic
   - `build_agent_graph`: Defines node connections

2. **coverage_parser.py** (Parsing)
   - `CoverageGap`: Data structure for a gap
   - `CoverageParser.parse()`: Main parsing logic
   - Multiple parsing strategies (markers, cross-coverage, etc.)

3. **mock_data.py** (Test data)
   - Example coverage report generators
   - Shows expected format

---

## 🔧 Customization Guide

### Change 1: Add Your Protocol Name

**File:** `agent.py`, line ~95

```python
# Before
SUGGESTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are a senior Design Verification engineer...")
    
# After
SUGGESTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are a senior Design Verification engineer specializing in PCIe Gen5 protocol...")
```

### Change 2: Add Protocol-Specific Examples

**File:** `agent.py`, add few-shot examples to prompts

```python
SUGGESTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a senior DV engineer.
    
Example 1:
Gap: pcie_dllp_ack_timeout
Suggestion: Create sequence that...

Example 2:
Gap: link_training_failure
Suggestion: Configure phy to...

Now for the actual gap:"""),
    ("user", "...")
])
```

### Change 3: Parse Different Coverage Format

**File:** `coverage_parser.py`, add new method

```python
def _parse_my_format(self):
    """Parse coverage in MySimulator format."""
    # Add custom parsing logic
    pass
```

### Change 4: Change LLM Model

**File:** `agent.py`, line ~19

```python
# Before
LLM_MODEL = "claude-sonnet-4-20250514"

# After
LLM_MODEL = "claude-opus-4-20250514"  # More powerful
# or
LLM_MODEL = "claude-haiku-4-20250301"  # Faster/cheaper
```

---

## 🐛 Troubleshooting

### Issue: "ANTHROPIC_API_KEY not found"
**Solution:** 
```bash
cp .env.template .env
# Edit .env and add your real API key
```

### Issue: "No module named 'langchain'"
**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: "No coverage gaps found"
**Solution:** 
- Check your report format matches expected patterns
- Look for UNCOVERED or ✗ markers
- Run `python coverage_parser.py` to debug parsing

### Issue: LLM responses are generic
**Solution:**
- Add protocol-specific context to prompts
- Include few-shot examples
- Increase temperature for more creative suggestions
- Consider adding RAG (Phase 2)

---

## 📖 Next Steps

1. ✅ **You are here:** MVP working with mock data

2. **Week 2-3:** Customize for your protocol
   - Add your coverage reports
   - Modify prompts with protocol details
   - Test on real (or realistic) data

3. **Week 4-6:** Add RAG (see ROADMAP.md Phase 2)
   - Load protocol specification PDFs
   - Set up vector database
   - Retrieve spec context for gaps

4. **Week 7+:** Add simulation loop (ROADMAP.md Phase 3)
   - Generate runnable SV code
   - Integrate with simulator
   - Measure coverage improvement

---

## 💡 Tips for Success

1. **Start small:** Get MVP working perfectly before adding complexity
2. **Iterate on prompts:** Prompt engineering is 80% of the quality
3. **Test incrementally:** Verify each component works before combining
4. **Document as you go:** Future you will thank you
5. **Use the roadmap:** Don't skip phases

---

## 🤝 Getting Help

- Read `ROADMAP.md` for detailed technical guidance
- Check `COMPARISON.md` to understand vs. GitHub repo
- Examine sample outputs in `outputs/`
- Run `python setup.py` to verify installation

---

**You're ready to build!** Start with `python agent.py` and go from there. 🚀
