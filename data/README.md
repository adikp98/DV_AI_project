# Data Directory

This directory contains coverage reports for analysis.

## Sample Reports

Run `python mock_data.py` to generate sample coverage reports:

- `sample_coverage_simple.txt` - Minimal example (5 gaps)
- `sample_coverage_fifo.txt` - FIFO design (13 gaps)
- `sample_coverage_axi4.txt` - AXI4-Lite protocol (22 gaps)

## Adding Your Own Reports

Place your coverage reports here with any naming convention.

### Supported Formats

The parser looks for these patterns:

```
✗ uncovered_bin_name
UNCOVERED: bin_name
✗ (CROSS_A, CROSS_B) - description
```

### Example Format

```
COVERAGE REPORT
===============

Coverage Group: my_group
  Bin Category: my_category
    ✓ covered_bin_1
    ✓ covered_bin_2
    ✗ uncovered_bin_name (UNCOVERED)
    ✗ another_uncovered_bin

Cross Coverage: state x operation
  ✗ (STATE_A, OP_X)
  ✗ (STATE_B, OP_Y)
```

### Tips

1. Include group/category headers for better organization
2. Add descriptions after bin names (optional but helpful)
3. Include overall coverage percentage (optional)
4. Use consistent marker symbols (✗ or UNCOVERED keyword)
