"""
Coverage report parsing utilities.
Handles different coverage report formats and extracts structured data.
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class CoverageGap:
    """Represents a single uncovered coverage bin or cross."""
    name: str
    category: str
    coverage_group: str
    description: Optional[str] = None
    cross_type: Optional[str] = None  # For cross-coverage items
    
    def __str__(self):
        return f"{self.coverage_group}.{self.category}.{self.name}"


class CoverageParser:
    """Parse coverage reports and extract uncovered bins."""
    
    def __init__(self, report_text: str):
        self.report_text = report_text
        self.gaps: List[CoverageGap] = []
        
    def parse(self) -> List[CoverageGap]:
        """Main parsing method - tries multiple strategies."""
        # Strategy 1: Look for explicit UNCOVERED markers
        self._parse_uncovered_markers()
        
        # Strategy 2: Look for cross-coverage gaps
        self._parse_cross_coverage()
        
        # Strategy 3: Look for ✗ symbols
        self._parse_x_markers()
        
        return self.gaps
    
    def _parse_uncovered_markers(self):
        """Parse lines with UNCOVERED keyword."""
        current_group = "unknown"
        current_category = "unknown"
        
        lines = self.report_text.split('\n')
        
        for i, line in enumerate(lines):
            # Track current coverage group
            if "Coverage Group:" in line:
                current_group = line.split("Coverage Group:")[-1].strip()
            
            # Track current category
            if "Bin Category:" in line or "Category:" in line:
                match = re.search(r'Category:\s*(\w+)', line)
                if match:
                    current_category = match.group(1)
            
            # Find UNCOVERED bins
            if "UNCOVERED" in line or "✗" in line:
                # Extract bin name
                # Patterns: "✗ bin_name (UNCOVERED)" or "UNCOVERED: bin_name"
                match = re.search(r'[✗×x]\s*([a-zA-Z0-9_]+)', line)
                if not match:
                    match = re.search(r'UNCOVERED:\s*([a-zA-Z0-9_]+)', line)
                
                if match:
                    bin_name = match.group(1)
                    
                    # Try to extract description (text after the bin name)
                    desc_match = re.search(r'[-–]\s*(.+)$', line)
                    description = desc_match.group(1).strip() if desc_match else None
                    
                    gap = CoverageGap(
                        name=bin_name,
                        category=current_category,
                        coverage_group=current_group,
                        description=description
                    )
                    
                    if gap not in self.gaps:  # Avoid duplicates
                        self.gaps.append(gap)
    
    def _parse_cross_coverage(self):
        """Parse cross-coverage gaps."""
        lines = self.report_text.split('\n')
        in_cross_section = False
        current_group = "cross_coverage"
        
        for line in lines:
            if "Cross Coverage:" in line or "UNCOVERED Crosses:" in line:
                in_cross_section = True
                # Extract cross name if present
                match = re.search(r'Cross Coverage:\s*(.+)', line)
                if match:
                    current_group = f"cross_{match.group(1).strip()}"
                continue
            
            if in_cross_section:
                # Stop at next section
                if line.strip() and line.strip()[0].isupper() and "✗" not in line:
                    if "Coverage" in line or "Total" in line or "Summary" in line:
                        in_cross_section = False
                        continue
                
                # Parse cross patterns like: ✗ (STATE, ACTION)
                match = re.search(r'[✗×x]\s*\(([^)]+)\)', line)
                if match:
                    cross_value = match.group(1)
                    
                    # Extract description
                    desc_match = re.search(r'[-–]\s*(.+)$', line)
                    description = desc_match.group(1).strip() if desc_match else None
                    
                    gap = CoverageGap(
                        name=cross_value.replace(",", "_").replace(" ", ""),
                        category="cross",
                        coverage_group=current_group,
                        description=description,
                        cross_type=cross_value
                    )
                    
                    if gap not in self.gaps:
                        self.gaps.append(gap)
    
    def _parse_x_markers(self):
        """Fallback: parse any line with ✗ or × that we might have missed."""
        # This catches any remaining gaps not caught by other methods
        lines = self.report_text.split('\n')
        
        for line in lines:
            if "✗" in line or "×" in line:
                # Skip if already processed
                if any(gap.name in line for gap in self.gaps):
                    continue
                
                # Extract any identifier
                match = re.search(r'[✗×]\s*([a-zA-Z0-9_\(\),\s]+?)(?:\s*[-–(]|$)', line)
                if match:
                    name = match.group(1).strip()
                    
                    # Skip very short or very long matches
                    if 3 < len(name) < 60:
                        gap = CoverageGap(
                            name=name.replace(" ", "_"),
                            category="unknown",
                            coverage_group="unknown",
                            description=None
                        )
                        
                        if gap not in self.gaps:
                            self.gaps.append(gap)
    
    def get_summary(self) -> Dict:
        """Get summary statistics about parsed gaps."""
        groups = {}
        for gap in self.gaps:
            if gap.coverage_group not in groups:
                groups[gap.coverage_group] = []
            groups[gap.coverage_group].append(gap)
        
        return {
            "total_gaps": len(self.gaps),
            "groups": groups,
            "group_count": len(groups),
            "categories": list(set(gap.category for gap in self.gaps))
        }


def extract_coverage_metrics(report_text: str) -> Dict:
    """Extract overall coverage percentage and metrics."""
    metrics = {
        "total_coverage": None,
        "bins_covered": None,
        "bins_total": None,
        "design_name": None
    }
    
    # Extract total coverage percentage
    match = re.search(r'Total Coverage:\s*(\d+\.?\d*)%', report_text)
    if match:
        metrics["total_coverage"] = float(match.group(1))
    
    # Extract bin counts
    match = re.search(r'Bins Covered:\s*(\d+)', report_text)
    if match:
        metrics["bins_covered"] = int(match.group(1))
    
    match = re.search(r'Total Bins.*:\s*(\d+)', report_text)
    if match:
        metrics["bins_total"] = int(match.group(1))
    
    # Extract design name
    match = re.search(r'Design:\s*(.+)', report_text)
    if match:
        metrics["design_name"] = match.group(1).strip()
    
    return metrics


if __name__ == "__main__":
    # Test the parser with sample data
    from mock_data import get_simple_fifo_report
    
    report = get_simple_fifo_report()
    parser = CoverageParser(report)
    gaps = parser.parse()
    
    print(f"Found {len(gaps)} coverage gaps:\n")
    for i, gap in enumerate(gaps, 1):
        print(f"{i}. {gap}")
        if gap.description:
            print(f"   Description: {gap.description}")
    
    print(f"\nSummary:")
    summary = parser.get_summary()
    print(f"  Total gaps: {summary['total_gaps']}")
    print(f"  Coverage groups: {summary['group_count']}")
    print(f"  Categories: {', '.join(summary['categories'])}")
