"""
Main LangGraph agent for coverage gap analysis.
Multi-step agent that parses coverage, analyzes gaps, and generates test suggestions.
"""

import os
from typing import TypedDict, List, Dict, Annotated
from datetime import datetime
from dotenv import load_dotenv

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

from coverage_parser import CoverageParser, CoverageGap, extract_coverage_metrics

# Load environment variables
load_dotenv()

# Configuration
LLM_MODEL = "claude-sonnet-4-20250514"
OUTPUT_DIR = "outputs"


# ============================================================
# Agent State Definition
# ============================================================
class AgentState(TypedDict):
    """State that flows through the agent graph."""
    # Input
    coverage_report: str
    
    # Intermediate state
    parsed_gaps: List[CoverageGap]
    current_gap_index: int
    design_metrics: Dict
    
    # Per-gap analysis
    gap_analyses: Dict[str, str]  # gap_name -> detailed analysis
    gap_suggestions: Dict[str, str]  # gap_name -> test suggestion
    
    # Output
    final_report: str
    metadata: Dict


# ============================================================
# Initialize LLM
# ============================================================
def get_llm(temperature: float = 0.0):
    """Initialize Claude LLM."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not found in environment. "
            "Create a .env file with: ANTHROPIC_API_KEY=your-key-here"
        )
    
    return ChatAnthropic(
        model=LLM_MODEL,
        temperature=temperature,
        max_tokens=2048
    )


# ============================================================
# Node 1: Parse Coverage Report
# ============================================================
def parse_coverage_node(state: AgentState) -> AgentState:
    """Parse the coverage report and extract gaps."""
    print("\n" + "="*70)
    print("NODE: Parse Coverage Report")
    print("="*70)
    
    report = state["coverage_report"]
    
    # Parse gaps
    parser = CoverageParser(report)
    gaps = parser.parse()
    
    # Extract metrics
    metrics = extract_coverage_metrics(report)
    
    print(f"✓ Found {len(gaps)} coverage gaps")
    print(f"✓ Design: {metrics.get('design_name', 'Unknown')}")
    print(f"✓ Overall coverage: {metrics.get('total_coverage', 'N/A')}%")
    
    # Print gap summary
    summary = parser.get_summary()
    print(f"\nGaps by coverage group:")
    for group, group_gaps in summary['groups'].items():
        print(f"  - {group}: {len(group_gaps)} gaps")
    
    return {
        **state,
        "parsed_gaps": gaps,
        "current_gap_index": 0,
        "design_metrics": metrics,
        "gap_analyses": {},
        "gap_suggestions": {},
    }


# ============================================================
# Node 2: Analyze Single Gap
# ============================================================
ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert Design Verification engineer analyzing coverage gaps.

Given a coverage gap, provide a detailed technical analysis of:
1. What this coverage point represents from a verification perspective
2. Why it might not have been hit by random testing
3. What specific design behavior or corner case it targets

Be concise but technical. Use 2-3 sentences max."""),
    ("user", """Coverage Gap: {gap_name}
Coverage Group: {coverage_group}
Category: {category}
Description: {description}

Provide your analysis:""")
])

def analyze_gap_node(state: AgentState) -> AgentState:
    """Analyze the current coverage gap in detail."""
    idx = state["current_gap_index"]
    gap = state["parsed_gaps"][idx]
    
    print(f"\n[{idx + 1}/{len(state['parsed_gaps'])}] Analyzing: {gap.name}")
    
    llm = get_llm(temperature=0.1)
    chain = ANALYSIS_PROMPT | llm
    
    response = chain.invoke({
        "gap_name": gap.name,
        "coverage_group": gap.coverage_group,
        "category": gap.category,
        "description": gap.description or "No description provided"
    })
    
    analysis = response.content.strip()
    
    new_analyses = {**state["gap_analyses"], str(gap): analysis}
    
    return {**state, "gap_analyses": new_analyses}


# ============================================================
# Node 3: Generate Test Suggestion
# ============================================================
SUGGESTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a senior Design Verification engineer writing test scenarios.

Given a coverage gap and its analysis, suggest a SPECIFIC, CONCRETE test scenario that would hit this coverage point.

Your suggestion should include:
1. A brief scenario description (1-2 sentences)
2. A pseudocode or SystemVerilog/UVM code sketch showing the key test logic
3. Any important configuration or constraint details

Format your code snippets in markdown code blocks with ```systemverilog or ```python.
Be specific - no generic "write a test" suggestions. Give actual implementation ideas."""),
    ("user", """Coverage Gap: {gap_name}
Coverage Group: {coverage_group}
Category: {category}

Gap Analysis:
{analysis}

Provide your test scenario and code suggestion:""")
])

def suggest_test_node(state: AgentState) -> AgentState:
    """Generate a test suggestion for the current gap."""
    idx = state["current_gap_index"]
    gap = state["parsed_gaps"][idx]
    gap_str = str(gap)
    
    print(f"  → Generating test suggestion...")
    
    llm = get_llm(temperature=0.3)  # Slightly higher temp for creativity
    chain = SUGGESTION_PROMPT | llm
    
    response = chain.invoke({
        "gap_name": gap.name,
        "coverage_group": gap.coverage_group,
        "category": gap.category,
        "analysis": state["gap_analyses"][gap_str]
    })
    
    suggestion = response.content.strip()
    
    new_suggestions = {**state["gap_suggestions"], gap_str: suggestion}
    
    # Move to next gap
    return {
        **state,
        "gap_suggestions": new_suggestions,
        "current_gap_index": idx + 1
    }


# ============================================================
# Conditional Edge: Check if more gaps to process
# ============================================================
def should_continue(state: AgentState) -> str:
    """Decide whether to continue processing gaps or move to report generation."""
    if state["current_gap_index"] < len(state["parsed_gaps"]):
        return "continue"
    return "generate_report"


# ============================================================
# Node 4: Generate Final Report
# ============================================================
def generate_report_node(state: AgentState) -> AgentState:
    """Assemble the final markdown report."""
    print("\n" + "="*70)
    print("NODE: Generate Final Report")
    print("="*70)
    
    gaps = state["parsed_gaps"]
    metrics = state["design_metrics"]
    
    # Build report
    lines = []
    lines.append("# Coverage Gap Analysis Report\n")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    if metrics.get("design_name"):
        lines.append(f"**Design:** {metrics['design_name']}\n")
    
    if metrics.get("total_coverage"):
        lines.append(f"**Current Coverage:** {metrics['total_coverage']}%\n")
    
    lines.append(f"**Total Gaps Analyzed:** {len(gaps)}\n")
    lines.append("\n---\n")
    
    # Add each gap
    for i, gap in enumerate(gaps, 1):
        gap_str = str(gap)
        
        lines.append(f"\n## Gap {i}: `{gap.name}`\n")
        lines.append(f"**Coverage Group:** {gap.coverage_group}  ")
        lines.append(f"**Category:** {gap.category}\n")
        
        if gap.description:
            lines.append(f"\n*{gap.description}*\n")
        
        lines.append("\n### Analysis\n")
        lines.append(state["gap_analyses"].get(gap_str, "No analysis available") + "\n")
        
        lines.append("\n### Suggested Test Scenario\n")
        lines.append(state["gap_suggestions"].get(gap_str, "No suggestion available") + "\n")
        
        lines.append("\n---\n")
    
    # Add footer
    lines.append("\n## Next Steps\n")
    lines.append("1. Review each suggested test scenario\n")
    lines.append("2. Implement the test sequences in your testbench\n")
    lines.append("3. Run simulation and verify coverage improvement\n")
    lines.append("4. Iterate on gaps that remain uncovered\n")
    
    report = "\n".join(lines)
    
    # Save report
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{OUTPUT_DIR}/coverage_analysis_{timestamp}.md"
    
    with open(output_file, "w") as f:
        f.write(report)
    
    print(f"✓ Report saved to: {output_file}")
    
    metadata = {
        "output_file": output_file,
        "timestamp": timestamp,
        "gaps_analyzed": len(gaps)
    }
    
    return {**state, "final_report": report, "metadata": metadata}


# ============================================================
# Build Agent Graph
# ============================================================
def build_agent_graph():
    """Construct the LangGraph state machine."""
    
    # Create graph
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("parse", parse_coverage_node)
    graph.add_node("analyze", analyze_gap_node)
    graph.add_node("suggest", suggest_test_node)
    graph.add_node("report", generate_report_node)
    
    # Define edges
    graph.set_entry_point("parse")
    graph.add_edge("parse", "analyze")
    graph.add_edge("analyze", "suggest")
    
    # Conditional edge: loop or finish
    graph.add_conditional_edges(
        "suggest",
        should_continue,
        {
            "continue": "analyze",
            "generate_report": "report"
        }
    )
    
    graph.add_edge("report", END)
    
    return graph.compile()


# ============================================================
# Main Execution
# ============================================================
class CoverageAgent:
    """High-level interface to the coverage analysis agent."""
    
    def __init__(self):
        self.agent = build_agent_graph()
    
    def analyze(self, report_path: str = None, report_text: str = None) -> Dict:
        """
        Analyze a coverage report.
        
        Args:
            report_path: Path to coverage report file
            report_text: Or provide report text directly
            
        Returns:
            Dictionary with analysis results
        """
        if report_path:
            with open(report_path, "r") as f:
                report_text = f.read()
        elif not report_text:
            raise ValueError("Must provide either report_path or report_text")
        
        # Initialize state
        initial_state = {
            "coverage_report": report_text,
            "parsed_gaps": [],
            "current_gap_index": 0,
            "design_metrics": {},
            "gap_analyses": {},
            "gap_suggestions": {},
            "final_report": "",
            "metadata": {}
        }
        
        # Run agent
        print("\n" + "="*70)
        print("STARTING COVERAGE GAP ANALYSIS")
        print("="*70)
        
        result = self.agent.invoke(initial_state)
        
        print("\n" + "="*70)
        print("ANALYSIS COMPLETE")
        print("="*70)
        print(f"✓ Analyzed {len(result['parsed_gaps'])} gaps")
        print(f"✓ Report: {result['metadata']['output_file']}")
        
        return result


def main():
    """Main entry point for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Coverage Gap Analyzer")
    parser.add_argument(
        "--report",
        default="data/sample_coverage_fifo.txt",
        help="Path to coverage report file"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive mode - display report in terminal"
    )
    
    args = parser.parse_args()
    
    # Check if report exists, if not create sample data
    if not os.path.exists(args.report):
        print(f"Report not found: {args.report}")
        print("Creating sample data...")
        from mock_data import save_sample_reports
        save_sample_reports()
    
    # Run analysis
    agent = CoverageAgent()
    result = agent.analyze(report_path=args.report)
    
    # Display report if interactive
    if args.interactive:
        print("\n" + "="*70)
        print("GENERATED REPORT")
        print("="*70)
        print(result["final_report"])


if __name__ == "__main__":
    main()
