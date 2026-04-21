"""
Mock coverage report generator for testing and demonstration.
Creates realistic coverage reports for various DV scenarios.
"""

def get_simple_fifo_report():
    """Simple FIFO coverage report - good for initial testing."""
    return """
FUNCTIONAL COVERAGE REPORT
==========================
Design: Simple FIFO
Date: 2024-01-15
Total Coverage: 78.5%

Coverage Group: fifo_operations
--------------------------------
Coverage: 82.5% (33/40 bins hit)

Bin Category: write_scenarios (85% coverage)
  ✓ write_when_empty
  ✓ write_when_half_full  
  ✓ write_consecutive_2
  ✓ write_consecutive_5
  ✗ write_consecutive_max_depth (UNCOVERED)
  ✗ write_when_full (UNCOVERED)
  ✗ write_after_reset (UNCOVERED)

Bin Category: read_scenarios (80% coverage)
  ✓ read_when_full
  ✓ read_when_half_full
  ✓ read_consecutive_2
  ✗ read_consecutive_until_empty (UNCOVERED)
  ✗ read_when_empty (UNCOVERED)

Bin Category: mixed_operations (75% coverage)
  ✓ alternating_rd_wr_empty_start
  ✓ alternating_rd_wr_half_full
  ✗ alternating_rd_wr_at_full (UNCOVERED)
  ✗ simultaneous_rd_wr_transitions (UNCOVERED)

Cross Coverage: fifo_state x operation_type
----------------------------------------------
Coverage: 70% (14/20 combinations hit)

UNCOVERED Crosses:
  ✗ (FULL, WRITE) - Write attempted when FIFO is full
  ✗ (EMPTY, READ) - Read attempted when FIFO is empty
  ✗ (ALMOST_FULL, SIMULTANEOUS_RD_WR)
  ✗ (ALMOST_EMPTY, SIMULTANEOUS_RD_WR)
  ✗ (RESET, WRITE) - Write immediately after reset
  ✗ (RESET, READ) - Read immediately after reset

Coverage Summary:
-----------------
Total Bins: 40
Covered: 33
Uncovered: 7
Coverage %: 82.5%

Cross Products: 20
Covered: 14
Uncovered: 6
Coverage %: 70%
"""


def get_axi4_lite_report():
    """AXI4-Lite protocol coverage - more complex scenario."""
    return """
FUNCTIONAL COVERAGE REPORT
==========================
Design: AXI4-Lite Master Interface
Date: 2024-01-15
Total Coverage: 72.3%

Coverage Group: axi_write_transactions
---------------------------------------
Coverage: 75% (15/20 bins hit)

Bin Category: write_response (80% coverage)
  ✓ OKAY_response
  ✓ SLVERR_response
  ✗ DECERR_response (UNCOVERED)
  ✗ back_to_back_SLVERR (UNCOVERED)

Bin Category: write_address_patterns (70% coverage)
  ✓ aligned_4byte
  ✓ aligned_8byte
  ✓ sequential_addresses
  ✗ unaligned_address (UNCOVERED)
  ✗ address_wraparound (UNCOVERED)
  ✗ max_address_value (UNCOVERED)

Bin Category: write_data_patterns (75% coverage)
  ✓ all_zeros
  ✓ all_ones
  ✓ alternating_bits
  ✗ random_sparse_data (UNCOVERED)

Coverage Group: axi_read_transactions
--------------------------------------
Coverage: 68% (17/25 bins hit)

Bin Category: read_response (65% coverage)
  ✓ OKAY_with_valid_data
  ✓ SLVERR_response
  ✗ DECERR_response (UNCOVERED)
  ✗ back_to_back_errors (UNCOVERED)
  ✗ error_after_multiple_okay (UNCOVERED)

Bin Category: read_latency (70% coverage)
  ✓ zero_wait_states
  ✓ single_wait_state
  ✓ multiple_wait_states
  ✗ maximum_wait_states (UNCOVERED)
  ✗ variable_latency_pattern (UNCOVERED)

Cross Coverage: write_resp x read_resp
---------------------------------------
Coverage: 60% (9/15 combinations hit)

UNCOVERED Crosses:
  ✗ (SLVERR, DECERR) - Write error followed by decode error on read
  ✗ (DECERR, DECERR) - Consecutive decode errors
  ✗ (OKAY, DECERR) - Successful write then decode error on read
  ✗ (SLVERR, SLVERR) - Back-to-back slave errors
  ✗ (OKAY, SLVERR) - Multiple scenarios
  ✗ (DECERR, OKAY) - Recovery from decode error

Coverage Group: protocol_violations
------------------------------------
Coverage: 85% (17/20 bins hit)

UNCOVERED Bins:
  ✗ valid_during_reset
  ✗ address_change_during_data_phase
  ✗ premature_ready_deassertion

Coverage Summary:
-----------------
Total Coverage Groups: 4
Average Coverage: 72.3%
Total Bins Defined: 80
Bins Covered: 58
Bins Uncovered: 22
"""


def get_minimal_report():
    """Minimal coverage report for quick testing."""
    return """
COVERAGE REPORT - Counter Module
=================================

Coverage Group: counter_values
  Total: 60% (3/5 bins)
  ✓ count_zero
  ✓ count_mid_range
  ✓ count_near_max
  ✗ count_max_value (UNCOVERED)
  ✗ count_overflow (UNCOVERED)

Coverage Group: control_signals
  Total: 66% (2/3 bins)
  ✓ reset_active
  ✓ enable_high
  ✗ enable_toggle_during_count (UNCOVERED)
"""


def save_sample_reports():
    """Save sample reports to data directory."""
    import os
    
    os.makedirs("data", exist_ok=True)
    
    reports = {
        "data/sample_coverage_simple.txt": get_minimal_report(),
        "data/sample_coverage_fifo.txt": get_simple_fifo_report(),
        "data/sample_coverage_axi4.txt": get_axi4_lite_report(),
    }
    
    for filepath, content in reports.items():
        with open(filepath, "w") as f:
            f.write(content)
    
    print("✓ Sample coverage reports created in data/ directory")
    return list(reports.keys())


if __name__ == "__main__":
    files = save_sample_reports()
    print(f"\nCreated {len(files)} sample reports:")
    for f in files:
        print(f"  - {f}")
