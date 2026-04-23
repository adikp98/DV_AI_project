# Coverage Gap Analysis Report

**Generated:** 2026-04-23 11:56:16

**Design:** Simple FIFO

**Current Coverage:** 78.5%

**Total Gaps Analyzed:** 19


---


## Gap 1: `write_consecutive_max_depth`

**Coverage Group:** fifo_operations  
**Category:** write_scenarios


### Analysis

## Coverage Gap Analysis: write_consecutive_max_depth

**What it represents:**
This coverage point tracks whether the FIFO has been exercised with consecutive write operations that fill it to maximum depth without any intervening reads. It verifies the FIFO's ability to handle sustained write pressure and correctly assert the full flag at maximum capacity.

**Why random testing missed it:**
Random stimulus typically interleaves reads and writes probabilistically, making it statistically unlikely to generate an uninterrupted sequence of exactly `FIFO_DEPTH` consecutive writes. The probability decreases exponentially with FIFO depth (e.g., for 50% read/write probability and depth=16, probability ≈ 0.5^16 ≈ 0.0015%).

**Design behavior targeted:**
This targets the full flag assertion logic, pointer wraparound at maximum depth, and potential overflow protection mechanisms. It's critical for validating that the FIFO correctly transitions from empty-to-full in one continuous write burst and doesn't exhibit off-by-one errors in depth counting or full detection.


### Suggested Test Scenario

## Test Scenario: Maximum Depth Consecutive Write Burst

**Scenario Description:**
Create a directed test that performs exactly `FIFO_DEPTH` consecutive write operations starting from an empty FIFO, with all reads disabled during the write phase. Verify that the full flag asserts on the final write and that all data is correctly stored without overflow.

**Implementation:**

```systemverilog
class fifo_write_consecutive_max_depth_test extends fifo_base_test;
  `uvm_component_utils(fifo_write_consecutive_max_depth_test)
  
  function new(string name = "fifo_write_consecutive_max_depth_test", uvm_component parent = null);
    super.new(name, parent);
  endfunction
  
  virtual task run_phase(uvm_phase phase);
    fifo_sequence seq;
    int fifo_depth;
    
    phase.raise_objection(this);
    
    // Get FIFO depth from configuration
    if (!uvm_config_db#(int)::get(this, "", "fifo_depth", fifo_depth))
      `uvm_fatal(get_type_name(), "FIFO depth not found in config DB")
    
    // Create and configure sequence for consecutive writes
    seq = fifo_sequence::type_id::create("seq");
    seq.num_transactions = fifo_depth;
    seq.operation_mode = WRITE_ONLY;  // Constraint to only writes
    seq.consecutive_mode = 1;          // No delays between transactions
    
    `uvm_info(get_type_name(), 
              $sformatf("Starting %0d consecutive writes to fill FIFO", fifo_depth), 
              UVM_MEDIUM)
    
    seq.start(m_env.m_agent.m_sequencer);
    
    // Small delay to allow final flags to settle
    #100ns;
    
    phase.drop_objection(this);
  endtask
  
endclass

// Specialized sequence for consecutive writes
class fifo_consecutive_write_sequence extends uvm_sequence #(fifo_transaction);
  `uvm_object_utils(fifo_consecutive_write_sequence)
  
  rand int unsigned num_writes;
  rand bit [DATA_WIDTH-1:0] write_data[];
  
  constraint c_num_writes {
    num_writes == `FIFO_DEPTH;  // Parameterized depth
  }
  
  constraint c_data_array {
    write_data.size() == num_writes;
    foreach(write_data[i]) {
      write_data[i] inside {[1:2**DATA_WIDTH-1]};  // Non-zero for easier debug
    }
  }
  
  function new(string name = "fifo_consecutive_write_sequence");
    super.new(name);
  endfunction
  
  virtual task body();
    fifo_transaction txn;
    
    `uvm_info(get_type_name(), 
              $sformatf("Executing %0d consecutive writes", num_writes), 
              UVM_HIGH)
    
    for (int i = 0; i < num_writes; i++) begin
      txn = fifo_transaction::type_id::create($sformatf("write_txn_%0d", i));
      
      start_item(txn);
      assert(txn.randomize() with {
        operation == WRITE;
        write_enable == 1'b1;
        read_enable == 1'b0;
        data == write_data[i];
      });
      finish_item(txn);
      
      // Log progress at key milestones
      if (i == num_writes - 2)
        `uvm_info(get_type_name(), "One write before full", UVM_MEDIUM)
      else if (i == num_writes - 1)
        `uvm_info(get_type_name(), "Final write - FIFO should be FULL", UVM_MEDIUM)
    end
  endtask
  
endclass

// Scoreboard checker for this specific scenario
class fifo_max_depth_checker extends uvm_subscriber #(fifo_transaction);
  `uvm_component_utils(fifo_max_depth_checker)
  
  int write_count;
  int fifo_depth;
  bit full_flag_seen;
  bit full_flag_asserted_at_correct_time;
  
  function new(string name = "fifo_max_depth_checker", uvm_component parent = null);
    super.new(name, parent);
    write_count = 0;
    full_flag_seen = 0;
    full_flag_asserted_at_correct_time = 0;
  endfunction
  
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(int)::get(this, "", "fifo_depth", fifo_depth))
      `uvm_fatal(get_type_name(), "FIFO depth not configured")
  endfunction
  
  virtual function void write(fifo_transaction t);
    if (t.operation == WRITE && t.write_enable) begin
      write_count++;
      
      `uvm_info(get_type_name(), 
                $sformatf("Write #%0d, Full=%0b, Empty=%0b", 
                          write_count, t.full, t.empty), 
                UVM_HIGH)
      
      // Check full flag behavior
      if (write_count == fifo_depth) begin
        if (t.full === 1'b1) begin
          full_flag_asserted_at_correct_time = 1;
          `uvm_info(get_type_name(), 
                    "PASS: Full flag asserted at maximum depth", 
                    UVM_MEDIUM)
        end else begin
          `uvm_error(get_type_name(), 
                     $sformatf("FAIL: Full flag not asserted after %0d writes", fifo_depth))
        end
      end else if (write_count < fifo_depth) begin
        if (t.full === 1'b1) begin
          `uvm_error(get_type_name(), 
                     $sformatf("FAIL: Full flag asserted prematurely at write %0d/%0d", 
                               write_count, fifo_depth))
        end
      end
      
      // Empty flag should be deasserted after first write
      if (write_count >= 1 && t.empty === 1'b1) begin
        `uvm_error(get_type_name(), 
                   "FAIL: Empty flag still asserted after writes")
      end
    end
  endfunction
  
  function void report_phase(uvm_phase phase);
    super.report_phase(phase);
    
    `uvm_info(get_type_name(), 
              $sformatf("Total consecutive writes: %0d (expected: %0d)", 
                        write_count, fifo_depth), 
              UVM_LOW)
    
    if (write_count == fifo_depth && full_flag_asserted_at_correct_time) begin
      `uvm_info(get_type_name(), 
                "=== TEST PASSED: Maximum depth consecutive writes successful ===", 
                UVM_NONE)
    end else begin
      `uvm_error(get_type_name(), 
                 "=== TEST FAILED: Maximum depth consecutive writes check failed ===")
    end
  endfunction
  
endclass
```

**Key Configuration Details:**

```systemverilog
// In test configuration
initial begin
  uvm_config_db#(int)::set(null, "*", "fifo_depth", 16);  // Or parameterized value
  uvm_config_db#(int)::set(null, "*", "data_width", 8);
end

// Coverage collection enhancement
covergroup fifo_operations_cg;
  write_consecutive_cp: coverpoint write_consecutive_count {
    bins max_depth = {`FIFO_DEPTH};
    bins near_max[] = {[`FIFO_DEPTH-2:`FIFO_DEPTH-1]


---


## Gap 2: `write_when_full`

**Coverage Group:** fifo_operations  
**Category:** write_scenarios


### Analysis

## Coverage Gap Analysis: write_when_full

**Verification Perspective:**
This coverage point captures the scenario where a write operation is attempted when the FIFO is at maximum capacity (full flag asserted). This tests the FIFO's overflow protection logic and verifies that the design correctly handles/rejects writes when no storage space is available.

**Why Not Hit by Random Testing:**
Random stimulus has low probability of hitting this corner case because it requires: (1) filling the FIFO to exact capacity through consecutive writes, and (2) attempting an additional write while maintaining the full condition without intervening reads. The timing window is narrow since random reads would typically drain the FIFO before sustained full conditions occur.

**Target Design Behavior:**
This targets the FIFO's boundary condition handling—specifically validating that overflow protection mechanisms work correctly (write pointer doesn't advance, data integrity is maintained, error flags assert if present, and the full flag remains stable during rejected write attempts).


### Suggested Test Scenario

## Test Scenario: Directed Write-When-Full Sequence

**Scenario Description:**
Fill the FIFO to exact capacity with known data patterns, then attempt multiple consecutive write operations while the FIFO remains full (no reads). Verify that the full flag stays asserted, write pointer doesn't advance, overflow error flags assert (if present), and previously written data remains intact.

**Implementation:**

```systemverilog
class fifo_write_when_full_test extends fifo_base_test;
  `uvm_component_utils(fifo_write_when_full_test)
  
  function new(string name = "fifo_write_when_full_test", uvm_component parent = null);
    super.new(name, parent);
  endfunction
  
  virtual task run_phase(uvm_phase phase);
    fifo_sequence fill_seq;
    fifo_write_transaction wr_txn;
    int fifo_depth;
    bit [DATA_WIDTH-1:0] expected_data[$];
    
    phase.raise_objection(this);
    
    // Get FIFO depth from config
    if (!uvm_config_db#(int)::get(this, "", "fifo_depth", fifo_depth))
      `uvm_fatal(get_type_name(), "FIFO depth not configured")
    
    `uvm_info(get_type_name(), $sformatf("Starting write_when_full test with depth=%0d", fifo_depth), UVM_LOW)
    
    // Step 1: Fill FIFO to exact capacity
    for (int i = 0; i < fifo_depth; i++) begin
      wr_txn = fifo_write_transaction::type_id::create($sformatf("fill_wr_%0d", i));
      assert(wr_txn.randomize());
      expected_data.push_back(wr_txn.data);
      sequencer.execute_item(wr_txn);
    end
    
    // Wait for full flag to stabilize
    #10ns;
    
    // Step 2: Verify FIFO is full
    if (!vif.full) begin
      `uvm_error(get_type_name(), "FIFO not full after writing depth items")
    end
    
    // Step 3: Attempt multiple writes while full (no reads)
    repeat (5) begin
      wr_txn = fifo_write_transaction::type_id::create("overflow_wr");
      wr_txn.data = $random();
      wr_txn.write_enable = 1'b1;
      
      // Capture state before write attempt
      bit [PTR_WIDTH-1:0] wr_ptr_before = vif.wr_ptr;
      
      sequencer.execute_item(wr_txn);
      
      // Verify full flag remains asserted
      assert_full_flag: assert (vif.full) else
        `uvm_error(get_type_name(), "Full flag deasserted during write_when_full")
      
      // Verify write pointer didn't advance
      assert_wr_ptr_stable: assert (vif.wr_ptr == wr_ptr_before) else
        `uvm_error(get_type_name(), $sformatf("Write pointer advanced from %0d to %0d when full", 
                   wr_ptr_before, vif.wr_ptr))
      
      // Check overflow error flag if design has one
      if (vif.has_overflow_flag && !vif.overflow_error) begin
        `uvm_error(get_type_name(), "Overflow error flag not asserted")
      end
      
      #10ns; // Small delay between attempts
    end
    
    // Step 4: Verify data integrity - read back and compare
    for (int i = 0; i < fifo_depth; i++) begin
      fifo_read_transaction rd_txn;
      rd_txn = fifo_read_transaction::type_id::create($sformatf("verify_rd_%0d", i));
      rd_txn.read_enable = 1'b1;
      sequencer.execute_item(rd_txn);
      
      if (rd_txn.data !== expected_data[i]) begin
        `uvm_error(get_type_name(), 
                   $sformatf("Data corruption at index %0d: expected=0x%0h, got=0x%0h",
                            i, expected_data[i], rd_txn.data))
      end
    end
    
    `uvm_info(get_type_name(), "Write_when_full test completed successfully", UVM_LOW)
    phase.drop_objection(this);
  endtask
  
endclass
```

**Key Configuration Details:**

```systemverilog
// In test configuration
class fifo_write_when_full_config extends fifo_base_config;
  
  // Disable random reads during fill phase
  constraint no_reads_during_fill {
    read_enable_weight == 0;
  }
  
  // Ensure writes are always enabled during fill
  constraint force_writes {
    write_enable_weight == 100;
  }
  
endclass
```

**Coverage Sampling Enhancement:**

```systemverilog
// Add to coverage collector
covergroup fifo_operations_cg @(posedge clk);
  
  write_when_full: coverpoint (write_enable && full) {
    bins write_attempt_when_full = {1'b1};
    option.at_least = 3; // Hit multiple times to ensure robustness
  }
  
  // Cross coverage for additional corner cases
  write_full_cross: cross write_enable, full, overflow_error {
    ignore_bins no_write = binsof(write_enable) intersect {0};
    ignore_bins not_full = binsof(full) intersect {0};
  }
  
endgroup
```

This directed test guarantees hitting the `write_when_full` coverage point by deterministically creating the full condition and attempting writes without any intervening reads, which random testing struggles to achieve.


---


## Gap 3: `write_after_reset`

**Coverage Group:** fifo_operations  
**Category:** write_scenarios


### Analysis

## Coverage Gap Analysis: write_after_reset

**Verification Perspective:**
This coverage point tracks whether a write operation occurs immediately following a FIFO reset condition, verifying the design's ability to accept data in the first clock cycle after reset deassertion. It validates that the FIFO's write pointer, full/empty flags, and control logic are properly initialized and functional post-reset.

**Why Random Testing Missed It:**
Random stimulus typically has low probability of generating a write transaction in the exact cycle following reset due to the temporal spacing of reset events and the randomization of write enable signals. Most testbenches apply reset infrequently, and random write generation doesn't naturally correlate with reset timing, creating a significant temporal gap between these events.

**Target Design Behavior:**
This targets the critical corner case of immediate post-reset write functionality, ensuring no initialization race conditions exist between reset logic and write path circuitry. It specifically validates that asynchronous reset release doesn't create metastability issues or timing violations that could corrupt the first write operation or leave the FIFO in an inconsistent state.


### Suggested Test Scenario

# Test Scenario: Write After Reset

## Scenario Description
Create a directed test that performs a write operation on the very first clock cycle after reset is deasserted, verifying that the FIFO correctly accepts data, updates its empty flag, and increments the write pointer without any initialization race conditions or metastability issues.

## SystemVerilog/UVM Implementation

```systemverilog
class write_after_reset_sequence extends base_fifo_sequence;
  `uvm_object_utils(write_after_reset_sequence)
  
  rand bit [DATA_WIDTH-1:0] first_write_data;
  
  function new(string name = "write_after_reset_sequence");
    super.new(name);
  endfunction
  
  task body();
    fifo_transaction txn;
    
    `uvm_info(get_type_name(), "Starting write_after_reset sequence", UVM_MEDIUM)
    
    // Step 1: Apply reset
    txn = fifo_transaction::type_id::create("reset_txn");
    txn.reset = 1'b1;
    txn.wr_en = 1'b0;
    txn.rd_en = 1'b0;
    start_item(txn);
    finish_item(txn);
    
    // Hold reset for a few cycles to ensure proper initialization
    repeat(3) begin
      txn = fifo_transaction::type_id::create("reset_hold_txn");
      txn.reset = 1'b1;
      txn.wr_en = 1'b0;
      txn.rd_en = 1'b0;
      start_item(txn);
      finish_item(txn);
    end
    
    // Step 2: Deassert reset and write on the SAME cycle
    // This is the critical timing - write enable asserted immediately
    txn = fifo_transaction::type_id::create("write_after_reset_txn");
    txn.reset = 1'b0;
    txn.wr_en = 1'b1;
    txn.rd_en = 1'b0;
    txn.wr_data = first_write_data;
    start_item(txn);
    finish_item(txn);
    
    `uvm_info(get_type_name(), 
              $sformatf("Write after reset: data=0x%0h", first_write_data), 
              UVM_MEDIUM)
    
    // Step 3: Perform additional writes to verify pointer progression
    repeat(2) begin
      txn = fifo_transaction::type_id::create("follow_up_write_txn");
      txn.reset = 1'b0;
      txn.wr_en = 1'b1;
      txn.rd_en = 1'b0;
      assert(txn.randomize());
      start_item(txn);
      finish_item(txn);
    end
    
    // Step 4: Read back and verify
    repeat(3) begin
      txn = fifo_transaction::type_id::create("readback_txn");
      txn.reset = 1'b0;
      txn.wr_en = 1'b0;
      txn.rd_en = 1'b1;
      start_item(txn);
      finish_item(txn);
    end
    
  endtask
  
endclass
```

## Scoreboard Checking Enhancement

```systemverilog
class fifo_scoreboard extends uvm_scoreboard;
  
  bit check_write_after_reset = 0;
  bit reset_just_deasserted = 0;
  int cycles_since_reset = 0;
  
  function void write_monitor(fifo_transaction txn);
    
    // Track reset deassertion
    if (txn.reset == 1'b0 && reset_just_deasserted) begin
      cycles_since_reset++;
      
      // Check for write on first cycle after reset
      if (cycles_since_reset == 1 && txn.wr_en == 1'b1) begin
        check_write_after_reset = 1;
        `uvm_info("SCOREBOARD", 
                  $sformatf("COVERAGE HIT: Write after reset detected, data=0x%0h", 
                            txn.wr_data), 
                  UVM_LOW)
        
        // Verify FIFO state expectations
        if (txn.empty !== 1'b0) begin
          `uvm_error("SCOREBOARD", 
                     "Empty flag should be deasserted after first write post-reset")
        end
        
        if (txn.full !== 1'b0) begin
          `uvm_error("SCOREBOARD", 
                     "Full flag should be deasserted after single write post-reset")
        end
      end
      
      if (cycles_since_reset > 5) begin
        reset_just_deasserted = 0;
        cycles_since_reset = 0;
      end
    end
    
    if (txn.reset == 1'b1) begin
      reset_just_deasserted = 1;
      cycles_since_reset = 0;
    end
    
  endfunction
  
endclass
```

## Test Configuration

```systemverilog
class write_after_reset_test extends base_fifo_test;
  `uvm_component_utils(write_after_reset_test)
  
  function new(string name = "write_after_reset_test", uvm_component parent = null);
    super.new(name, parent);
  endfunction
  
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    
    // Configure for precise timing control
    uvm_config_db#(int)::set(this, "env.agent.sequencer", 
                              "zero_delay_mode", 1);
  endfunction
  
  task run_phase(uvm_phase phase);
    write_after_reset_sequence seq;
    
    phase.raise_objection(this);
    
    seq = write_after_reset_sequence::type_id::create("seq");
    
    // Run multiple iterations with different data patterns
    repeat(10) begin
      assert(seq.randomize());
      seq.start(env.agent.sequencer);
      #100ns; // Gap between iterations
    end
    
    phase.drop_objection(this);
  endtask
  
endclass
```

## Key Configuration Details

1. **Timing Precision**: The sequence uses `start_item()`/`finish_item()` to ensure cycle-accurate control, with write enable asserted on the exact cycle reset is deasserted.

2. **Reset Duration**: Hold reset for 3+ cycles to ensure all flip-flops are properly initialized before the critical write operation.

3. **Verification Points**:
   - Empty flag should transition from 1→0 after first write
   - Write pointer should increment from 0→1
   - Data integrity of first write should be maintained
   - No X's or Z's in control signals

4. **Coverage Sampling**: Add a coverpoint in the monitor that specifically samples when `wr_en && !reset && $past(reset)` to confirm this scenario is hit.


---


## Gap 4: `read_consecutive_until_empty`

**Coverage Group:** fifo_operations  
**Category:** read_scenarios


### Analysis

## Coverage Analysis: read_consecutive_until_empty

**What it represents:**
This coverage point tracks the scenario where consecutive read operations are performed on the FIFO until it transitions from a non-empty state to completely empty, verifying the FIFO's ability to handle continuous drain operations and correctly assert the empty flag at the boundary condition.

**Why random testing missed it:**
Random stimulus typically interleaves reads and writes probabilistically, making it statistically unlikely to generate an uninterrupted sequence of reads that fully drains the FIFO. The probability decreases exponentially with FIFO depth (e.g., for depth-16 FIFO, requires 16+ consecutive read transactions without writes).

**Target behavior/corner case:**
This targets the critical empty flag generation logic and underflow protection mechanisms, ensuring the FIFO correctly handles back-to-back reads at the empty boundary, maintains data integrity for the final entry, and properly prevents underflow conditions when reads attempt to continue past empty state.


### Suggested Test Scenario

# Test Scenario for `read_consecutive_until_empty`

## Scenario Description
Fill the FIFO to a known depth (not necessarily full), then perform back-to-back read operations without any intervening writes until the FIFO becomes empty. Verify the empty flag assertion timing, the last valid data read, and that subsequent read attempts are properly handled (no underflow corruption).

## SystemVerilog/UVM Implementation

```systemverilog
class fifo_drain_to_empty_test extends fifo_base_test;
  `uvm_component_utils(fifo_drain_to_empty_test)
  
  function new(string name = "fifo_drain_to_empty_test", uvm_component parent = null);
    super.new(name, parent);
  endfunction
  
  virtual task run_phase(uvm_phase phase);
    fifo_sequence fill_seq;
    fifo_drain_sequence drain_seq;
    int fill_depth;
    
    phase.raise_objection(this);
    
    // Test multiple fill levels to ensure coverage across different depths
    for (int i = 0; i < 5; i++) begin
      // Randomize fill depth between 25% and 100% of FIFO depth
      fill_depth = $urandom_range(FIFO_DEPTH/4, FIFO_DEPTH);
      
      `uvm_info(get_type_name(), 
                $sformatf("Iteration %0d: Filling FIFO to depth %0d", i, fill_depth), 
                UVM_MEDIUM)
      
      // Step 1: Fill FIFO to target depth
      fill_seq = fifo_sequence::type_id::create("fill_seq");
      fill_seq.num_writes = fill_depth;
      fill_seq.num_reads = 0;
      fill_seq.start(m_env.m_agent.m_sequencer);
      
      // Step 2: Drain FIFO completely with consecutive reads
      drain_seq = fifo_drain_sequence::type_id::create("drain_seq");
      drain_seq.expected_items = fill_depth;
      drain_seq.start(m_env.m_agent.m_sequencer);
      
      // Small delay between iterations
      #100ns;
    end
    
    phase.drop_objection(this);
  endtask
endclass

// Specialized sequence for consecutive reads until empty
class fifo_drain_sequence extends uvm_sequence #(fifo_transaction);
  `uvm_object_utils(fifo_drain_sequence)
  
  rand int expected_items;  // Number of items expected in FIFO
  
  function new(string name = "fifo_drain_sequence");
    super.new(name);
  endfunction
  
  virtual task body();
    fifo_transaction req;
    int read_count = 0;
    bit empty_detected = 0;
    
    // Perform consecutive reads
    repeat (expected_items + 2) begin  // +2 to verify behavior past empty
      req = fifo_transaction::type_id::create("req");
      start_item(req);
      
      // Force read operation with no delay
      assert(req.randomize() with {
        operation == READ;
        delay == 0;  // Back-to-back reads
      });
      
      finish_item(req);
      
      read_count++;
      
      // Monitor empty flag transition
      if (req.empty && !empty_detected) begin
        empty_detected = 1;
        `uvm_info(get_type_name(), 
                  $sformatf("Empty flag asserted after %0d reads (expected %0d)", 
                            read_count, expected_items), 
                  UVM_LOW)
        
        // Verify empty asserted at correct boundary
        if (read_count != expected_items + 1) begin
          `uvm_error(get_type_name(), 
                     $sformatf("Empty flag timing error: asserted at read %0d, expected at %0d",
                               read_count, expected_items + 1))
        end
      end
      
      // After empty, verify underflow protection
      if (empty_detected && req.read_valid) begin
        `uvm_error(get_type_name(), 
                   "Read valid asserted when FIFO is empty - underflow protection failed")
      end
    end
    
    `uvm_info(get_type_name(), 
              $sformatf("Drain sequence completed: %0d reads, empty detected: %0b", 
                        read_count, empty_detected), 
              UVM_MEDIUM)
  endtask
endclass
```

## Alternative Direct RTL Testbench Approach

```systemverilog
// For non-UVM environments
task automatic test_drain_to_empty(int fill_level);
  int write_data[$];
  int read_data;
  
  // Step 1: Reset FIFO
  rst_n = 0;
  repeat(2) @(posedge clk);
  rst_n = 1;
  @(posedge clk);
  
  // Step 2: Fill FIFO to specified level
  wr_en = 1;
  rd_en = 0;
  
  for (int i = 0; i < fill_level; i++) begin
    wr_data = $random;
    write_data.push_back(wr_data);
    @(posedge clk);
    
    // Verify not full until capacity reached
    if (i < FIFO_DEPTH - 1) begin
      assert(!full) else $error("Full asserted prematurely at write %0d", i);
    end
  end
  
  wr_en = 0;
  @(posedge clk);
  
  // Step 3: Consecutive reads until empty
  rd_en = 1;
  
  for (int i = 0; i < fill_level; i++) begin
    @(posedge clk);
    
    // Verify data integrity
    if (rd_valid) begin
      read_data = rd_data;
      assert(read_data == write_data[i]) else 
        $error("Data mismatch at read %0d: expected %h, got %h", 
               i, write_data[i], read_data);
    end else begin
      $error("Read valid not asserted for valid read %0d", i);
    end
    
    // Check empty flag timing
    if (i == fill_level - 1) begin
      // Last valid read - empty should assert AFTER this read completes
      @(posedge clk);
      assert(empty) else $error("Empty not asserted after final read");
    end else begin
      assert(!empty) else $error("Empty asserted prematurely at read %0d", i);
    end
  end
  
  // Step 4: Verify underflow protection
  repeat(3) begin
    @(posedge clk);
    assert(empty) else $error("Empty deasserted unexpectedly");
    assert(!rd_valid) else $error("Read valid asserted when FIFO empty");
  end
  
  rd_en = 0;
  $display("PASS: Drain to empty test completed for fill_level=%0d", fill_level);
endtask

// Test execution
initial begin
  // Test various fill levels
  test_drain_to_empty(FIFO_DEPTH);      // Full drain
  test_drain_to_empty(FIFO_DEPTH/2);    // Half drain
  test_drain_to_empty(FIFO_DEPTH/4);    // Quarter drain
  test_drain_to_empty(1);                // Single entry drain
  $finish;
end
```

## Key Configuration Details

1. **Constraint Requirements:**
   - Disable write operations during drain phase
   - Set read delay to 0 for back-to-back operations
   - Ensure read enable stays asserted throughout sequence

2. **Scoreboard Checks:**
   - Track FIFO occupancy count
   - Verify empty flag asserts when count reaches 0
   - Confirm last read data matches last written data
   - Validate no data corruption on underflow attempts

3. **Coverage Sampling


---


## Gap 5: `read_when_empty`

**Coverage Group:** fifo_operations  
**Category:** read_scenarios


### Analysis

## Coverage Gap Analysis: read_when_empty

**What it represents:**
This coverage point captures the scenario where a read operation is attempted on an empty FIFO, which should trigger underflow protection logic (typically asserting an empty flag, blocking the read, or returning invalid/stale data depending on the design specification).

**Why it wasn't hit:**
Random testing likely has a low probability of generating back-to-back reads that drain the FIFO completely followed by additional read attempts, especially if the testbench has balanced read/write traffic or includes implicit constraints that prevent reads when empty flags are asserted.

**Design behavior targeted:**
This targets critical boundary condition handling—specifically the FIFO's underflow protection mechanism, empty flag assertion timing, and data output behavior during illegal read operations. This is a fundamental safety feature that prevents invalid data propagation in the system.


### Suggested Test Scenario

# Test Scenario for `read_when_empty` Coverage

## Scenario Description
Create a directed test that explicitly drains the FIFO through consecutive reads until empty, then attempts multiple additional read operations while monitoring the empty flag, read valid signal, and data output stability. This verifies underflow protection and ensures the FIFO correctly handles illegal read attempts.

## SystemVerilog/UVM Implementation

```systemverilog
class fifo_read_when_empty_test extends fifo_base_test;
  `uvm_component_utils(fifo_read_when_empty_test)
  
  function new(string name = "fifo_read_when_empty_test", uvm_component parent = null);
    super.new(name, parent);
  endfunction
  
  virtual task run_phase(uvm_phase phase);
    fifo_sequence seq;
    read_when_empty_sequence drain_seq;
    
    phase.raise_objection(this);
    
    // First, populate the FIFO with known data
    seq = fifo_sequence::type_id::create("seq");
    seq.num_writes = 10;  // Write 10 entries
    seq.num_reads = 0;    // No reads yet
    seq.start(m_env.m_agent.m_sequencer);
    
    // Now drain and over-read
    drain_seq = read_when_empty_sequence::type_id::create("drain_seq");
    drain_seq.start(m_env.m_agent.m_sequencer);
    
    #1000ns;  // Allow time for all transactions
    phase.drop_objection(this);
  endtask
endclass

// Specialized sequence to drain FIFO and attempt reads when empty
class read_when_empty_sequence extends uvm_sequence#(fifo_transaction);
  `uvm_object_utils(read_when_empty_sequence)
  
  function new(string name = "read_when_empty_sequence");
    super.new(name);
  endfunction
  
  virtual task body();
    fifo_transaction req;
    int read_count = 0;
    bit empty_flag;
    
    // Phase 1: Drain the FIFO completely
    // Assume FIFO depth is known (e.g., 16) or query from config
    for (int i = 0; i < 16; i++) begin  // Read more than written to ensure empty
      req = fifo_transaction::type_id::create("req");
      start_item(req);
      assert(req.randomize() with {
        operation == READ;
        read_enable == 1'b1;
      });
      finish_item(req);
      
      // Monitor empty flag from response
      get_response(rsp);
      empty_flag = rsp.empty;
      
      `uvm_info(get_type_name(), 
                $sformatf("Read #%0d: empty=%0b, data=0x%0h", 
                          i, empty_flag, rsp.read_data), 
                UVM_MEDIUM)
      
      if (empty_flag) begin
        `uvm_info(get_type_name(), 
                  $sformatf("FIFO became empty after %0d reads", i+1), 
                  UVM_HIGH)
        break;
      end
    end
    
    // Phase 2: Attempt multiple reads while FIFO is empty
    // This is the critical part that hits the coverage point
    repeat (5) begin
      req = fifo_transaction::type_id::create("req");
      start_item(req);
      assert(req.randomize() with {
        operation == READ;
        read_enable == 1'b1;
      });
      finish_item(req);
      get_response(rsp);
      
      read_count++;
      
      `uvm_info(get_type_name(), 
                $sformatf("Read-when-empty #%0d: empty=%0b, valid=%0b, data=0x%0h", 
                          read_count, rsp.empty, rsp.read_valid, rsp.read_data), 
                UVM_HIGH)
      
      // Assertions to verify correct behavior
      assert(rsp.empty == 1'b1) else
        `uvm_error(get_type_name(), "Empty flag not asserted during read-when-empty!")
      
      // Depending on design spec, read_valid should be low or data should be stable
      if (rsp.read_valid == 1'b1) begin
        `uvm_warning(get_type_name(), 
                     "Read valid asserted when FIFO is empty - verify design intent")
      end
    end
    
  endtask
endclass
```

## Alternative: Constrained Random Approach

```systemverilog
// Add constraint to existing sequence to force read-heavy traffic
class read_biased_sequence extends fifo_base_sequence;
  `uvm_object_utils(read_biased_sequence)
  
  constraint read_when_empty_c {
    // Create scenarios where reads significantly outnumber writes
    num_reads == num_writes + 10;  // Always read 10 more than written
    
    // Cluster read operations together
    foreach (operations[i]) {
      if (i > num_writes) {
        operations[i] == READ;
      }
    }
  }
  
  // Disable any constraints that prevent reads when empty
  constraint disable_empty_check {
    check_empty_before_read == 1'b0;
  }
endclass
```

## Scoreboard Enhancement

```systemverilog
// Add specific checking in the scoreboard for this scenario
function void fifo_scoreboard::check_read_when_empty(fifo_transaction txn);
  if (txn.operation == READ && fifo_model.is_empty()) begin
    // Hit the coverage point
    cov.fifo_operations.read_when_empty++;
    
    // Verify design behavior
    `uvm_info(get_type_name(), "Detected read-when-empty condition", UVM_HIGH)
    
    assert(txn.empty == 1'b1) else
      `uvm_error(get_type_name(), "Empty flag not asserted!")
    
    assert(txn.read_valid == 1'b0) else
      `uvm_error(get_type_name(), "Read valid incorrectly asserted on empty FIFO!")
    
    // Verify data output is stable (doesn't change from last valid read)
    if (last_valid_read_data != txn.read_data) begin
      `uvm_warning(get_type_name(), 
                   $sformatf("Data changed during read-when-empty: was 0x%0h, now 0x%0h",
                             last_valid_read_data, txn.read_data))
    end
  end
endfunction
```

## Key Configuration Details

1. **Disable automatic empty checking**: Ensure the driver doesn't have built-in logic that prevents reads when empty flag is asserted
2. **FIFO depth awareness**: The test should know or query the FIFO depth to ensure complete draining
3. **Timing considerations**: Add appropriate delays between transactions to allow empty flag propagation
4. **Reset handling**: Start with a known empty state or explicitly reset before the test
5. **Monitor both flags**: Track both `empty` and `read_valid` (or equivalent) signals to fully verify behavior

This directed approach guarantees hitting the `read_when_empty` coverage point while thoroughly verifying the underflow protection mechanism.


---


## Gap 6: `alternating_rd_wr_at_full`

**Coverage Group:** fifo_operations  
**Category:** mixed_operations


### Analysis

## Coverage Gap Analysis: alternating_rd_wr_at_full

**What it represents:**
This coverage point targets the specific scenario where read and write operations alternate while the FIFO is in a full state, verifying that the FIFO correctly maintains the full flag and handles simultaneous read/write transactions at maximum capacity without data corruption or pointer misalignment.

**Why random testing missed it:**
Random testing has low probability of hitting this pattern because it requires: (1) filling the FIFO to full capacity, (2) maintaining precise alternating read-write sequences, and (3) sustaining this pattern long enough to be sampled. Random stimulus typically causes the FIFO to transition away from the full state quickly or generates bursts rather than strict alternation.

**Design behavior targeted:**
This tests critical pointer arithmetic and flag logic at the boundary condition where write_pointer catches read_pointer while full. It specifically validates that the full flag correctly deasserts for one cycle during the read, reasserts when the subsequent write occurs, and that no overflow/underflow conditions are incorrectly triggered during these rapid full-state transitions.


### Suggested Test Scenario

## Test Scenario: Alternating Read/Write at Full Boundary

**Scenario Description:**
Fill the FIFO to full capacity, then execute a precise alternating pattern of single read followed by single write operations for at least 20-30 cycles. This maintains the FIFO at the full boundary while exercising the pointer wrap-around logic and full flag transitions.

**Implementation:**

```systemverilog
class alternating_rd_wr_at_full_test extends base_fifo_test;
  `uvm_component_utils(alternating_rd_wr_at_full_test)
  
  function new(string name = "alternating_rd_wr_at_full_test", uvm_component parent);
    super.new(name, parent);
  endfunction
  
  task run_phase(uvm_phase phase);
    fifo_sequence fill_seq;
    fifo_transaction txn;
    int alternation_cycles = 30;
    
    phase.raise_objection(this);
    
    // Step 1: Fill FIFO to full capacity
    fill_seq = fifo_sequence::type_id::create("fill_seq");
    fill_seq.num_writes = FIFO_DEPTH;
    fill_seq.num_reads = 0;
    fill_seq.start(m_env.m_agent.m_sequencer);
    
    // Wait for full flag to assert
    wait(m_env.m_scoreboard.fifo_full == 1'b1);
    `uvm_info(get_type_name(), "FIFO filled to capacity", UVM_MEDIUM)
    
    // Step 2: Execute alternating read-write pattern
    for(int i = 0; i < alternation_cycles; i++) begin
      // Read operation
      txn = fifo_transaction::type_id::create($sformatf("rd_txn_%0d", i));
      assert(txn.randomize() with {
        rd_en == 1'b1;
        wr_en == 1'b0;
      });
      m_env.m_agent.m_sequencer.send_request(txn);
      
      // Wait one clock cycle
      @(posedge m_env.m_agent.vif.clk);
      
      // Verify full flag deasserted momentarily
      if(i == 0) begin
        assert(m_env.m_agent.vif.full == 1'b0) else
          `uvm_error(get_type_name(), "Full flag should deassert after read")
      end
      
      // Write operation
      txn = fifo_transaction::type_id::create($sformatf("wr_txn_%0d", i));
      assert(txn.randomize() with {
        rd_en == 1'b0;
        wr_en == 1'b1;
        wr_data inside {[0:$]};  // Any valid data
      });
      m_env.m_agent.m_sequencer.send_request(txn);
      
      // Wait one clock cycle
      @(posedge m_env.m_agent.vif.clk);
      
      // Verify full flag reasserted
      assert(m_env.m_agent.vif.full == 1'b1) else
        `uvm_error(get_type_name(), $sformatf("Full flag should reassert after write at cycle %0d", i))
      
      `uvm_info(get_type_name(), $sformatf("Alternation cycle %0d completed", i), UVM_HIGH)
    end
    
    phase.drop_objection(this);
  endtask
  
endclass
```

**Alternative Sequence-Based Approach:**

```systemverilog
class alternating_at_full_sequence extends uvm_sequence#(fifo_transaction);
  `uvm_object_utils(alternating_at_full_sequence)
  
  rand int num_alternations;
  
  constraint reasonable_alternations {
    num_alternations inside {[20:50]};
  }
  
  function new(string name = "alternating_at_full_sequence");
    super.new(name);
  endfunction
  
  task body();
    fifo_transaction txn;
    
    // Phase 1: Fill to full
    for(int i = 0; i < FIFO_DEPTH; i++) begin
      `uvm_do_with(txn, {
        wr_en == 1'b1;
        rd_en == 1'b0;
      })
    end
    
    // Phase 2: Alternating pattern at full boundary
    for(int i = 0; i < num_alternations; i++) begin
      // Read
      `uvm_do_with(txn, {
        rd_en == 1'b1;
        wr_en == 1'b0;
      })
      
      // Write
      `uvm_do_with(txn, {
        wr_en == 1'b1;
        rd_en == 1'b0;
      })
    end
  endtask
  
endclass
```

**Key Configuration Details:**

1. **Timing Control**: Use `@(posedge clk)` to ensure precise single-cycle operations between reads and writes
2. **Assertion Checks**: Monitor full flag transitions - should toggle: `1 → 0 → 1` with each read-write pair
3. **Data Integrity**: Scoreboard should verify that data written during alternation matches data read in subsequent cycles
4. **Pointer Monitoring**: If design exposes pointers, verify `(wr_ptr == rd_ptr) && full` remains true throughout
5. **Coverage Sampling**: Ensure coverage is sampled at clock edges during the alternating phase to capture the pattern

**Expected Behavior:**
- Full flag: `1 → 0 (after read) → 1 (after write)` repeating
- Empty flag: remains `0` throughout
- Write pointer and read pointer maintain 1-entry separation
- No overflow or underflow errors triggered


---


## Gap 7: `simultaneous_rd_wr_transitions`

**Coverage Group:** fifo_operations  
**Category:** mixed_operations


### Analysis

## Coverage Gap Analysis: simultaneous_rd_wr_transitions

**Verification Perspective:**
This coverage point targets the concurrent assertion of read and write enable signals on the same clock cycle, which tests the FIFO's ability to handle simultaneous enqueue/dequeue operations. This is critical for verifying pointer update logic, data path arbitration, and ensuring no race conditions exist when both operations occur together, particularly at boundary conditions like empty, full, or near-full/near-empty states.

**Why Random Testing Missed It:**
Random stimulus typically generates independent read/write transactions with probabilistic timing, making true cycle-exact simultaneity statistically rare (probability = P(rd_en) × P(wr_en)). Additionally, protocol constraints or testbench sequencing may inadvertently serialize operations, and the valid window for simultaneous operations may be narrow (e.g., only meaningful when FIFO is neither completely empty nor full).

**Target Design Behavior:**
This targets the FIFO's dual-port access logic and pointer arithmetic when both operations execute atomically—specifically verifying that: (1) write pointer and read pointer increment correctly in the same cycle, (2) the occupancy counter updates properly (net zero change), (3) full/empty flag logic handles the simultaneous transition correctly, and (4) no data corruption occurs during concurrent access to adjacent or same memory locations.


### Suggested Test Scenario

# Test Scenario for simultaneous_rd_wr_transitions

## Scenario Description
Create a directed test that forces simultaneous read and write operations across multiple FIFO states (empty, partially filled, almost full, and full-1). The test will explicitly synchronize read and write transactions on the same clock cycle while sweeping through different occupancy levels to verify pointer arithmetic, flag updates, and data integrity during concurrent operations.

## Implementation

```systemverilog
class simultaneous_rd_wr_test extends base_test;
  `uvm_component_utils(simultaneous_rd_wr_test)
  
  function new(string name = "simultaneous_rd_wr_test", uvm_component parent);
    super.new(name, parent);
  endfunction
  
  virtual task run_phase(uvm_phase phase);
    fifo_sequence seq;
    simultaneous_rd_wr_sequence simul_seq;
    
    phase.raise_objection(this);
    
    // Test 1: Simultaneous ops starting from empty+1
    `uvm_info(get_type_name(), "Testing simultaneous RD/WR from near-empty state", UVM_LOW)
    simul_seq = simultaneous_rd_wr_sequence::type_id::create("simul_seq");
    simul_seq.start_occupancy = 1;
    simul_seq.num_simultaneous_ops = 50;
    simul_seq.start(env.agent.sequencer);
    
    // Test 2: Simultaneous ops at half-full
    `uvm_info(get_type_name(), "Testing simultaneous RD/WR from half-full state", UVM_LOW)
    simul_seq = simultaneous_rd_wr_sequence::type_id::create("simul_seq");
    simul_seq.start_occupancy = FIFO_DEPTH/2;
    simul_seq.num_simultaneous_ops = 100;
    simul_seq.start(env.agent.sequencer);
    
    // Test 3: Simultaneous ops at almost-full
    `uvm_info(get_type_name(), "Testing simultaneous RD/WR from almost-full state", UVM_LOW)
    simul_seq = simultaneous_rd_wr_sequence::type_id::create("simul_seq");
    simul_seq.start_occupancy = FIFO_DEPTH - 1;
    simul_seq.num_simultaneous_ops = 50;
    simul_seq.start(env.agent.sequencer);
    
    phase.drop_objection(this);
  endtask
  
endclass

class simultaneous_rd_wr_sequence extends uvm_sequence#(fifo_transaction);
  `uvm_object_utils(simultaneous_rd_wr_sequence)
  
  rand int start_occupancy;
  rand int num_simultaneous_ops;
  
  constraint valid_occupancy_c {
    start_occupancy > 0;
    start_occupancy < FIFO_DEPTH;
  }
  
  function new(string name = "simultaneous_rd_wr_sequence");
    super.new(name);
  endfunction
  
  virtual task body();
    fifo_transaction wr_txn, rd_txn;
    fifo_transaction simul_txn;
    int expected_data_queue[$];
    
    // Step 1: Pre-fill FIFO to desired occupancy
    `uvm_info(get_type_name(), $sformatf("Pre-filling FIFO to occupancy=%0d", start_occupancy), UVM_MEDIUM)
    for(int i = 0; i < start_occupancy; i++) begin
      wr_txn = fifo_transaction::type_id::create("wr_txn");
      start_item(wr_txn);
      assert(wr_txn.randomize() with {
        wr_en == 1'b1;
        rd_en == 1'b0;
        data == (i + 100); // Predictable data pattern
      });
      expected_data_queue.push_back(wr_txn.data);
      finish_item(wr_txn);
    end
    
    // Step 2: Execute simultaneous read/write operations
    `uvm_info(get_type_name(), $sformatf("Executing %0d simultaneous RD/WR operations", num_simultaneous_ops), UVM_MEDIUM)
    for(int i = 0; i < num_simultaneous_ops; i++) begin
      simul_txn = fifo_transaction::type_id::create("simul_txn");
      start_item(simul_txn);
      
      // Force both rd_en and wr_en high simultaneously
      assert(simul_txn.randomize() with {
        wr_en == 1'b1;
        rd_en == 1'b1;
        data == (1000 + i); // New data pattern for simultaneous writes
      });
      
      // Update expected queue: pop front, push back
      if(expected_data_queue.size() > 0) begin
        void'(expected_data_queue.pop_front());
      end
      expected_data_queue.push_back(simul_txn.data);
      
      finish_item(simul_txn);
      
      // Add periodic checks every 10 operations
      if(i % 10 == 0) begin
        `uvm_info(get_type_name(), $sformatf("Completed %0d simultaneous ops, queue_size=%0d", 
                  i, expected_data_queue.size()), UVM_HIGH)
      end
    end
    
    // Step 3: Drain FIFO and verify data integrity
    `uvm_info(get_type_name(), "Draining FIFO to verify data integrity", UVM_MEDIUM)
    while(expected_data_queue.size() > 0) begin
      rd_txn = fifo_transaction::type_id::create("rd_txn");
      start_item(rd_txn);
      assert(rd_txn.randomize() with {
        wr_en == 1'b0;
        rd_en == 1'b1;
      });
      finish_item(rd_txn);
      void'(expected_data_queue.pop_front());
    end
    
  endtask
  
endclass
```

## Key Configuration Details

```systemverilog
// In the testbench top or configuration class:

// 1. Disable any automatic spacing between transactions
initial begin
  uvm_config_db#(int)::set(null, "*", "min_transaction_gap", 0);
end

// 2. Configure driver to ensure true simultaneity
class fifo_driver extends uvm_driver#(fifo_transaction);
  
  virtual task drive_transaction(fifo_transaction txn);
    // Critical: Apply both signals on same clock edge
    @(posedge vif.clk);
    vif.wr_en <= txn.wr_en;
    vif.rd_en <= txn.rd_en;
    vif.data  <= txn.data;
    @(posedge vif.clk);
    // Hold for one cycle, then release
    vif.wr_en <= 1'b0;
    vif.rd_en <= 1'b0;
  endtask
  
endclass

// 3. Enhanced scoreboard checking for simultaneous operations
class fifo_scoreboard extends uvm_scoreboard;
  
  function void check_simultaneous_op(fifo_transaction txn);
    if(txn.wr_en && txn.rd_en) begin
      // Verify occupancy remains constant
      if(prev_occupancy != current_occupancy) begin
        `uvm_error(get_type_name(), 
          $sformatf("Occupancy changed during simultaneous RD/WR: prev=%0d, curr=%0d",
                    prev_occupancy, current_occupancy))
      end
      
      // Verify both pointers incremented
      if((current_wr_ptr != (prev_wr_ptr + 1) % FIFO_


---


## Gap 8: `FULL_WRITE`

**Coverage Group:** cross_fifo_state x operation_type  
**Category:** cross


*Write attempted when FIFO is full*


### Analysis

## Coverage Gap Analysis: FULL_WRITE

**What it represents:**
This cross-coverage point captures the specific scenario where a write operation is attempted while the FIFO is in a FULL state, verifying the design's overflow protection logic, error flag generation, and data integrity preservation when the write pointer cannot advance.

**Why random testing missed it:**
Random stimulus typically has low probability of maintaining the FIFO in a sustained FULL state while simultaneously generating write transactions, as reads naturally drain the FIFO. The temporal alignment of "FIFO reaches 100% capacity" AND "write transaction arrives" requires either consecutive writes without reads or precise synchronization that random patterns rarely achieve.

**Target behavior:**
This targets critical boundary condition handling: verifying that full-flag assertion correctly blocks writes, no data corruption occurs in existing FIFO entries, appropriate error/status signals are generated, and the write pointer remains stable without wrapping or corrupting the read pointer relationship.


### Suggested Test Scenario

# Test Scenario for FULL_WRITE Coverage

## Scenario Description
Create a directed test that fills the FIFO to capacity with back-to-back writes, then attempts multiple write operations while maintaining the FULL state by preventing any reads. Verify that overflow protection mechanisms activate, error flags assert correctly, and existing FIFO data remains uncorrupted.

## SystemVerilog/UVM Implementation

```systemverilog
class fifo_full_write_test extends fifo_base_test;
  `uvm_component_utils(fifo_full_write_test)
  
  function new(string name = "fifo_full_write_test", uvm_component parent = null);
    super.new(name, parent);
  endfunction
  
  virtual task run_phase(uvm_phase phase);
    fifo_sequence fill_seq;
    fifo_write_sequence overflow_write_seq;
    int fifo_depth;
    
    phase.raise_objection(this);
    
    // Get FIFO depth from configuration
    if (!uvm_config_db#(int)::get(this, "", "fifo_depth", fifo_depth))
      `uvm_fatal(get_type_name(), "FIFO depth not configured")
    
    `uvm_info(get_type_name(), $sformatf("Starting FULL_WRITE test with depth=%0d", fifo_depth), UVM_LOW)
    
    // Step 1: Fill FIFO to exactly FULL state
    fill_seq = fifo_sequence::type_id::create("fill_seq");
    fill_seq.num_writes = fifo_depth;
    fill_seq.num_reads = 0;
    fill_seq.write_delay_min = 0;
    fill_seq.write_delay_max = 2;
    fill_seq.start(m_env.m_agent.m_sequencer);
    
    // Wait for FULL flag to stabilize
    #100ns;
    
    // Step 2: Attempt multiple writes while FULL (no reads)
    overflow_write_seq = fifo_write_sequence::type_id::create("overflow_write_seq");
    overflow_write_seq.num_transactions = 10; // Attempt 10 writes to FULL FIFO
    overflow_write_seq.delay_min = 1;
    overflow_write_seq.delay_max = 5;
    overflow_write_seq.start(m_env.m_agent.m_sequencer);
    
    // Step 3: Allow time for scoreboard checking
    #500ns;
    
    phase.drop_objection(this);
  endtask
  
endclass

// Dedicated write-only sequence
class fifo_write_sequence extends uvm_sequence#(fifo_transaction);
  `uvm_object_utils(fifo_write_sequence)
  
  rand int num_transactions;
  rand int delay_min;
  rand int delay_max;
  
  constraint reasonable_c {
    num_transactions inside {[5:20]};
    delay_min >= 0;
    delay_max >= delay_min;
    delay_max <= 10;
  }
  
  function new(string name = "fifo_write_sequence");
    super.new(name);
  endfunction
  
  virtual task body();
    fifo_transaction txn;
    
    for (int i = 0; i < num_transactions; i++) begin
      txn = fifo_transaction::type_id::create($sformatf("write_txn_%0d", i));
      
      start_item(txn);
      assert(txn.randomize() with {
        operation == WRITE;
        data dist {[0:255] :/ 80, [256:$] :/ 20}; // Varied data patterns
      });
      finish_item(txn);
      
      // Random delay between writes
      #($urandom_range(delay_max, delay_min) * 1ns);
    end
  endtask
  
endclass
```

## Scoreboard Enhancement for FULL_WRITE Checking

```systemverilog
class fifo_scoreboard extends uvm_scoreboard;
  
  // Track FIFO state
  bit is_full;
  int current_count;
  int fifo_depth;
  logic [DATA_WIDTH-1:0] reference_queue[$];
  
  // Coverage for FULL_WRITE
  covergroup fifo_full_write_cg;
    cp_full_state: coverpoint is_full {
      bins full = {1};
    }
    cp_write_op: coverpoint current_transaction.operation {
      bins write = {WRITE};
    }
    cross_full_write: cross cp_full_state, cp_write_op {
      bins full_write_hit = binsof(cp_full_state.full) && binsof(cp_write_op.write);
    }
  endgroup
  
  function void write_analysis_port(fifo_transaction txn);
    fifo_full_write_cg.sample();
    
    // Check FULL_WRITE scenario
    if (is_full && txn.operation == WRITE) begin
      `uvm_info(get_type_name(), 
                $sformatf("FULL_WRITE coverage hit! Count=%0d, Depth=%0d", 
                          current_count, fifo_depth), 
                UVM_MEDIUM)
      
      // Verify overflow protection
      assert_overflow_protection(txn);
    endif
    
    // Update state tracking
    update_fifo_state(txn);
  endfunction
  
  function void assert_overflow_protection(fifo_transaction txn);
    // Check that:
    // 1. Write pointer didn't advance
    // 2. Error/overflow flag is set
    // 3. FIFO count remains at max
    // 4. Existing data is uncorrupted
    
    if (!txn.overflow_error) begin
      `uvm_error(get_type_name(), 
                 "OVERFLOW ERROR: Write to FULL FIFO didn't set error flag!")
    end
    
    if (current_count != fifo_depth) begin
      `uvm_error(get_type_name(), 
                 $sformatf("COUNT ERROR: FIFO count changed during FULL write: %0d", 
                           current_count))
    end
    
    // Verify data integrity (existing entries unchanged)
    verify_data_integrity();
  endfunction
  
endclass
```

## Key Configuration Details

```systemverilog
// In test configuration
initial begin
  uvm_config_db#(int)::set(null, "*", "fifo_depth", 16); // Or parameterized
  
  // Disable random reads during overflow test phase
  uvm_config_db#(bit)::set(null, "*.m_agent.m_sequencer", "enable_reads", 0);
  
  // Enable aggressive write generation
  uvm_config_db#(int)::set(null, "*.write_seq", "write_probability", 100);
end
```

## Alternative: Constrained Random Approach

```systemverilog
// Virtual sequence with phases
class fifo_full_write_vseq extends uvm_sequence;
  
  virtual task body();
    // Phase 1: Fill FIFO
    fork
      begin
        repeat(fifo_depth) generate_write();
      end
    join
    
    // Phase 2: Maintain FULL + attempt writes
    fork
      begin
        // Attempt writes (should fail gracefully)
        repeat(20) begin
          generate_write();
          #($urandom_range(10,1) * 1ns);
        end
      end
      begin
        // Optionally: occasional reads to test transitions
        #($urandom_range(500,200) * 1ns);
        repeat(2) generate_read(); // Partial drain
        #100ns;
        repeat(2) generate_write(); // Refill to FULL
      end
    join
  endtask
  
endclass
```

This implementation guarantees hitting the FULL_WRITE coverage point through:
1. **Deterministic filling** to reach FULL state
2. **Controlled write attempts**


---


## Gap 9: `EMPTY_READ`

**Coverage Group:** cross_fifo_state x operation_type  
**Category:** cross


*Read attempted when FIFO is empty*


### Analysis

## Coverage Gap Analysis: EMPTY_READ

**Verification Perspective:**
This coverage point captures the critical corner case where a read operation is attempted on an empty FIFO, which should trigger underflow protection mechanisms (error flags, data validity signals, or read blocking). It verifies the FIFO's defensive behavior and proper status signaling when consumers attempt invalid operations.

**Why Random Testing Missed It:**
Random testing likely maintains a balanced read/write ratio that naturally prevents FIFO depletion, or the testbench's randomization constraints may implicitly avoid reads when empty to prevent protocol violations. The probability of hitting this exact state requires consecutive reads without intervening writes, which has low likelihood in unconstrained random scenarios.

**Target Design Behavior:**
This targets the FIFO's empty-state protection logic: verifying that `empty` flag assertion correctly inhibits data output, `underflow` error signaling activates, read pointer remains stable, and output data either holds previous valid data or drives a known safe value (zeros/X's) to prevent downstream corruption.


### Suggested Test Scenario

# Test Scenario for EMPTY_READ Coverage

## Scenario Description
Perform a controlled FIFO drain sequence followed by multiple consecutive read attempts on the empty FIFO, verifying that the empty flag remains asserted, underflow error is signaled, read pointer doesn't advance, and output data remains stable/safe.

## SystemVerilog/UVM Test Implementation

```systemverilog
class fifo_empty_read_test extends fifo_base_test;
  `uvm_component_utils(fifo_empty_read_test)
  
  function new(string name = "fifo_empty_read_test", uvm_component parent = null);
    super.new(name, parent);
  endfunction
  
  virtual task run_phase(uvm_phase phase);
    fifo_sequence seq;
    fifo_empty_read_sequence empty_read_seq;
    
    phase.raise_objection(this);
    
    // Step 1: Fill FIFO partially (known depth)
    seq = fifo_sequence::type_id::create("seq");
    seq.num_writes = 5;
    seq.num_reads = 0;
    seq.start(m_env.m_agent.m_sequencer);
    
    // Step 2: Drain FIFO completely
    seq = fifo_sequence::type_id::create("drain_seq");
    seq.num_writes = 0;
    seq.num_reads = 5;
    seq.start(m_env.m_agent.m_sequencer);
    
    // Step 3: Execute empty read sequence
    empty_read_seq = fifo_empty_read_sequence::type_id::create("empty_read_seq");
    empty_read_seq.start(m_env.m_agent.m_sequencer);
    
    #100ns;
    phase.drop_objection(this);
  endtask
  
endclass

// Dedicated sequence for empty FIFO reads
class fifo_empty_read_sequence extends uvm_sequence #(fifo_transaction);
  `uvm_object_utils(fifo_empty_read_sequence)
  
  rand int num_empty_reads;
  
  constraint empty_read_c {
    num_empty_reads inside {[3:10]}; // Multiple reads to stress the condition
  }
  
  function new(string name = "fifo_empty_read_sequence");
    super.new(name);
  endfunction
  
  virtual task body();
    fifo_transaction req;
    
    for (int i = 0; i < num_empty_reads; i++) begin
      req = fifo_transaction::type_id::create($sformatf("empty_read_%0d", i));
      start_item(req);
      
      // Force read operation with no write
      assert(req.randomize() with {
        operation == READ;
        wr_en == 1'b0;
        rd_en == 1'b1;
      });
      
      finish_item(req);
      
      // Small delay between reads to observe state
      #(get_config_int("clk_period"));
    end
  endtask
  
endclass
```

## Scoreboard Checking Enhancement

```systemverilog
class fifo_scoreboard extends uvm_scoreboard;
  
  // Track FIFO state
  int fifo_count;
  bit last_empty_flag;
  logic [DATA_WIDTH-1:0] last_valid_data;
  
  virtual function void check_empty_read(fifo_transaction txn);
    if (fifo_count == 0 && txn.rd_en) begin
      
      // Check 1: Empty flag must be asserted
      `uvm_error_if(txn.empty !== 1'b1, "EMPTY_READ_FLAG",
        $sformatf("Empty flag not asserted during empty read. Expected: 1, Got: %0b", 
                  txn.empty))
      
      // Check 2: Underflow flag should be set (if design has it)
      `uvm_error_if(txn.underflow !== 1'b1, "UNDERFLOW_FLAG",
        $sformatf("Underflow not signaled on empty read"))
      
      // Check 3: Data output should remain stable or be safe value
      if (txn.rd_data !== last_valid_data && txn.rd_data !== '0) begin
        `uvm_warning("EMPTY_READ_DATA",
          $sformatf("Read data changed during empty read: %0h -> %0h",
                    last_valid_data, txn.rd_data))
      end
      
      // Check 4: Read pointer should not advance
      // (This would be checked via internal signal monitoring)
      
      // Coverage sampling
      cov_empty_read_hit = 1'b1;
      sample_coverage();
      
      `uvm_info("EMPTY_READ_HIT", 
        $sformatf("Successfully hit EMPTY_READ coverage point at time %0t", $time),
        UVM_MEDIUM)
    end
    
    // Update tracking
    if (txn.rd_en && !txn.empty && fifo_count > 0) begin
      last_valid_data = txn.rd_data;
    end
  endfunction
  
endclass
```

## Configuration Details

```systemverilog
// In test configuration
virtual function void build_phase(uvm_phase phase);
  super.build_phase(phase);
  
  // Disable write-heavy randomization for this test
  uvm_config_db#(int)::set(this, "*", "write_weight", 0);
  uvm_config_db#(int)::set(this, "*", "read_weight", 100);
  
  // Set assertion severity for empty reads
  uvm_config_db#(bit)::set(this, "*", "empty_read_fatal", 0); // Don't kill sim
  
  // Enable detailed logging for this corner case
  uvm_config_db#(int)::set(this, "*scoreboard*", "verbosity", UVM_HIGH);
endfunction
```

## Key Implementation Points

1. **Deterministic Setup**: Explicitly fill then drain FIFO to guarantee empty state
2. **Multiple Reads**: Perform 3-10 consecutive reads to ensure coverage hit and stress protection logic
3. **Comprehensive Checking**: Verify empty flag, underflow signal, data stability, and pointer behavior
4. **No Randomization Escape**: Hard constraints prevent writes during the critical read sequence
5. **Coverage Confirmation**: Explicit logging when coverage point is hit for debug visibility

This approach guarantees hitting the EMPTY_READ cross coverage by creating the exact precondition (empty FIFO) and then executing the specific operation (read) in a controlled, repeatable manner.


---


## Gap 10: `ALMOST_FULL_SIMULTANEOUS_RD_WR`

**Coverage Group:** cross_fifo_state x operation_type  
**Category:** cross


### Analysis

## Coverage Gap Analysis: ALMOST_FULL_SIMULTANEOUS_RD_WR

**What it represents:**
This cross-coverage point targets the specific scenario where the FIFO is in an "almost full" state (typically 1-2 entries away from full) while simultaneous read and write operations occur in the same clock cycle. This verifies the pointer management logic correctly handles concurrent access at a critical threshold state.

**Why it wasn't hit:**
Random testing has low probability of hitting this corner case because it requires precise alignment of three conditions: (1) FIFO filling to almost-full threshold, (2) write operation being valid/enabled, and (3) read operation occurring simultaneously—all within the same cycle. The timing window is narrow, especially if the testbench has independent read/write traffic generators.

**Design behavior targeted:**
This tests the FIFO's ability to correctly update both read and write pointers atomically when near capacity, ensuring no overflow/underflow conditions occur, flags (almost_full, full) transition correctly, and data integrity is maintained during this high-stress boundary condition where pointer arithmetic is most susceptible to off-by-one errors.


### Suggested Test Scenario

# Test Scenario for ALMOST_FULL_SIMULTANEOUS_RD_WR

## Scenario Description
Create a directed test that fills the FIFO to exactly (DEPTH - ALMOST_FULL_THRESHOLD - 1) entries, then performs a precisely timed simultaneous read and write operation to hit the almost_full state while both operations are active. Use a constrained random sequence to maintain simultaneous operations for several cycles while hovering around the almost_full boundary.

## Implementation

```systemverilog
class almost_full_simul_rw_test extends base_fifo_test;
  `uvm_component_utils(almost_full_simul_rw_test)
  
  virtual task run_phase(uvm_phase phase);
    fifo_write_seq wr_seq;
    fifo_read_seq rd_seq;
    fifo_simul_rw_seq simul_seq;
    int fill_count;
    
    phase.raise_objection(this);
    
    // Step 1: Calculate precise fill level to reach almost_full - 1
    // Assuming DEPTH=16, ALMOST_FULL_THRESHOLD=2 (triggers when 14+ entries)
    fill_count = `FIFO_DEPTH - `ALMOST_FULL_THRESHOLD - 1; // Fill to 13 entries
    
    `uvm_info(get_type_name(), 
              $sformatf("Filling FIFO to %0d entries (almost_full-1)", fill_count), 
              UVM_MEDIUM)
    
    // Step 2: Fill FIFO without any reads
    wr_seq = fifo_write_seq::type_id::create("wr_seq");
    wr_seq.num_writes = fill_count;
    wr_seq.no_backpressure = 1; // Ensure continuous writes
    wr_seq.start(m_env.m_wr_agent.m_sequencer);
    
    // Step 3: Execute simultaneous read/write sequence
    `uvm_info(get_type_name(), 
              "Starting simultaneous RW at almost_full boundary", 
              UVM_MEDIUM)
    
    simul_seq = fifo_simul_rw_seq::type_id::create("simul_seq");
    simul_seq.num_cycles = 20; // Maintain simul ops for 20 cycles
    simul_seq.start(m_env.m_sequencer); // Assumes virtual sequencer
    
    phase.drop_objection(this);
  endtask
endclass

// Specialized sequence for simultaneous operations
class fifo_simul_rw_seq extends uvm_sequence;
  `uvm_object_utils(fifo_simul_rw_seq)
  
  rand int num_cycles;
  
  constraint reasonable_cycles_c {
    num_cycles inside {[10:50]};
  }
  
  virtual task body();
    fifo_transaction wr_txn, rd_txn;
    
    for (int i = 0; i < num_cycles; i++) begin
      // Fork parallel read and write to ensure same-cycle execution
      fork
        begin
          wr_txn = fifo_transaction::type_id::create("wr_txn");
          assert(wr_txn.randomize() with {
            op_type == WRITE;
            valid == 1;
            // Add data pattern for checking
            data == (i + 'hA0);
          });
          start_item(wr_txn);
          finish_item(wr_txn);
        end
        
        begin
          rd_txn = fifo_transaction::type_id::create("rd_txn");
          assert(rd_txn.randomize() with {
            op_type == READ;
            valid == 1;
          });
          start_item(rd_txn);
          finish_item(rd_txn);
        end
      join
      
      // Small percentage of cycles: skip one operation to create variation
      // This helps test pointer updates when operations aren't perfectly balanced
      if ($urandom_range(0,99) < 10) begin // 10% chance
        @(posedge vif.clk);
      end
    end
  endtask
endclass
```

## Alternative: Reactive Approach with Callbacks

```systemverilog
// Monitor callback to trigger simultaneous RW when almost_full detected
class almost_full_trigger_callback extends uvm_callback;
  
  virtual task post_status_update(fifo_monitor mon, fifo_status_txn status);
    fifo_transaction wr_txn, rd_txn;
    
    // Detect when we're one entry away from almost_full
    if (status.count == (`FIFO_DEPTH - `ALMOST_FULL_THRESHOLD - 1)) begin
      `uvm_info("CALLBACK", "Triggering simultaneous RW at almost_full-1", UVM_HIGH)
      
      // Inject simultaneous operations via sequencer
      fork
        begin
          wr_txn = fifo_transaction::type_id::create("inject_wr");
          wr_txn.op_type = WRITE;
          wr_txn.valid = 1;
          wr_txn.data = $urandom();
          mon.m_sequencer.send_request(wr_txn);
        end
        begin
          rd_txn = fifo_transaction::type_id::create("inject_rd");
          rd_txn.op_type = READ;
          rd_txn.valid = 1;
          mon.m_sequencer.send_request(rd_txn);
        end
      join_none
    end
  endtask
endclass
```

## Key Configuration Details

```systemverilog
// In test configuration
initial begin
  // Ensure clock alignment for true simultaneous operations
  uvm_config_db#(int)::set(null, "*", "clock_phase_align", 1);
  
  // Set FIFO parameters
  uvm_config_db#(int)::set(null, "*", "fifo_depth", 16);
  uvm_config_db#(int)::set(null, "*", "almost_full_threshold", 2);
  
  // Enable specific coverage tracking
  uvm_config_db#(bit)::set(null, "*", "track_simultaneous_ops", 1);
end

// Assertion to verify we hit the coverage point
property almost_full_simul_rw_hit;
  @(posedge clk) disable iff (!rst_n)
  (fifo_count == (`FIFO_DEPTH - `ALMOST_FULL_THRESHOLD)) && 
  wr_en && rd_en |-> ##1 $rose(coverage_hit_flag);
endproperty
assert_coverage_hit: assert property(almost_full_simul_rw_hit);
```

This approach guarantees hitting the coverage point by precisely controlling FIFO fill level and using forked transactions to ensure true simultaneous operations.


---


## Gap 11: `ALMOST_EMPTY_SIMULTANEOUS_RD_WR`

**Coverage Group:** cross_fifo_state x operation_type  
**Category:** cross


### Analysis

## Coverage Gap Analysis: ALMOST_EMPTY_SIMULTANEOUS_RD_WR

**Verification Perspective:**
This coverage point targets the specific corner case where the FIFO is in an almost-empty state (typically 1-2 entries remaining) while simultaneous read and write operations occur in the same clock cycle. This tests the priority logic, pointer update mechanisms, and flag generation when the FIFO is near depletion with concurrent access.

**Why Not Hit by Random Testing:**
The almost-empty state represents a narrow window in the FIFO's occupancy range, and achieving simultaneous read/write operations requires precise temporal alignment. Random testing has low probability of hitting this combination because: (1) the FIFO typically spends minimal time in almost-empty states during normal operation, and (2) random stimulus generators must coincidentally schedule both operations in the exact same cycle while in this specific state.

**Target Design Behavior:**
This tests critical boundary condition handling including: correct flag assertion/deassertion when operations cancel out, proper pointer arithmetic at low occupancy, potential underflow prevention logic, and verification that the almost-empty threshold calculation remains accurate during simultaneous bidirectional access.


### Suggested Test Scenario

# Test Scenario for ALMOST_EMPTY_SIMULTANEOUS_RD_WR

## Scenario Description
Create a directed test that deliberately drains the FIFO to the almost-empty threshold (e.g., 1-2 entries), then forces simultaneous read and write operations for multiple consecutive cycles while monitoring flag transitions and data integrity. The test verifies pointer collision handling, flag stability, and that the FIFO maintains correct occupancy count.

## SystemVerilog/UVM Test Implementation

```systemverilog
class fifo_almost_empty_simul_rw_test extends fifo_base_test;
  `uvm_component_utils(fifo_almost_empty_simul_rw_test)
  
  function new(string name = "fifo_almost_empty_simul_rw_test", uvm_component parent);
    super.new(name, parent);
  endfunction
  
  virtual task run_phase(uvm_phase phase);
    fifo_sequence seq;
    int almost_empty_threshold;
    int fifo_depth;
    
    phase.raise_objection(this);
    
    // Get FIFO parameters from config
    if (!uvm_config_db#(int)::get(this, "", "almost_empty_threshold", almost_empty_threshold))
      almost_empty_threshold = 2; // Default
    if (!uvm_config_db#(int)::get(this, "", "fifo_depth", fifo_depth))
      fifo_depth = 16; // Default
    
    `uvm_info(get_type_name(), $sformatf(
      "Starting almost_empty simultaneous R/W test (threshold=%0d, depth=%0d)", 
      almost_empty_threshold, fifo_depth), UVM_LOW)
    
    // Step 1: Fill FIFO partially
    seq = fifo_sequence::type_id::create("fill_seq");
    seq.num_transactions = fifo_depth / 2;
    seq.operation = WRITE_ONLY;
    seq.start(m_env.m_agent.m_sequencer);
    
    // Step 2: Drain to almost-empty state (leave threshold+1 entries)
    seq = fifo_sequence::type_id::create("drain_seq");
    seq.num_transactions = (fifo_depth / 2) - (almost_empty_threshold + 1);
    seq.operation = READ_ONLY;
    seq.start(m_env.m_agent.m_sequencer);
    
    // Step 3: Execute simultaneous read/write operations
    fork
      begin
        fifo_simultaneous_rw_sequence simul_seq;
        simul_seq = fifo_simultaneous_rw_sequence::type_id::create("simul_seq");
        simul_seq.num_cycles = 20; // Test for 20 consecutive cycles
        simul_seq.target_state = ALMOST_EMPTY;
        simul_seq.start(m_env.m_agent.m_sequencer);
      end
      
      begin
        // Monitor for flag transitions during simultaneous operations
        monitor_almost_empty_flag();
      end
    join
    
    #1000ns; // Allow scoreboard to settle
    phase.drop_objection(this);
  endtask
  
  // Monitor task to verify flag behavior
  virtual task monitor_almost_empty_flag();
    bit prev_almost_empty;
    int stable_count = 0;
    
    forever begin
      @(posedge m_env.m_agent.vif.clk);
      
      // Check for unexpected flag transitions
      if (m_env.m_agent.vif.almost_empty !== prev_almost_empty) begin
        `uvm_info(get_type_name(), $sformatf(
          "Almost_empty flag transition: %b -> %b at time %0t",
          prev_almost_empty, m_env.m_agent.vif.almost_empty, $time), UVM_MEDIUM)
        stable_count = 0;
      end else begin
        stable_count++;
      end
      
      // Verify flag remains stable during balanced operations
      if (stable_count > 5 && m_env.m_agent.vif.wr_en && m_env.m_agent.vif.rd_en) begin
        `uvm_info(get_type_name(), 
          "Flag stable during simultaneous R/W - PASS", UVM_HIGH)
      end
      
      prev_almost_empty = m_env.m_agent.vif.almost_empty;
      
      if (stable_count > 25) break; // Exit after sufficient monitoring
    end
  endtask
  
endclass

// Specialized sequence for simultaneous read/write
class fifo_simultaneous_rw_sequence extends uvm_sequence#(fifo_transaction);
  `uvm_object_utils(fifo_simultaneous_rw_sequence)
  
  rand int num_cycles;
  fifo_state_e target_state;
  
  constraint reasonable_cycles_c {
    num_cycles inside {[10:50]};
  }
  
  function new(string name = "fifo_simultaneous_rw_sequence");
    super.new(name);
  endfunction
  
  virtual task body();
    fifo_transaction wr_txn, rd_txn;
    
    for (int i = 0; i < num_cycles; i++) begin
      // Create write transaction
      wr_txn = fifo_transaction::type_id::create("wr_txn");
      start_item(wr_txn);
      assert(wr_txn.randomize() with {
        operation == WRITE;
        wr_en == 1'b1;
        rd_en == 1'b0;
      });
      
      // Create read transaction (will be executed simultaneously)
      rd_txn = fifo_transaction::type_id::create("rd_txn");
      assert(rd_txn.randomize() with {
        operation == READ;
        wr_en == 1'b0;
        rd_en == 1'b1;
      });
      
      // Force simultaneous execution via driver
      fork
        begin
          finish_item(wr_txn);
        end
        begin
          start_item(rd_txn);
          finish_item(rd_txn);
        end
      join
      
      `uvm_info(get_type_name(), $sformatf(
        "Cycle %0d: Simultaneous WR(data=0x%0h) and RD", 
        i, wr_txn.wr_data), UVM_HIGH)
    end
  endtask
endclass
```

## Driver Modification for True Simultaneity

```systemverilog
// Add to fifo_driver to support simultaneous operations
virtual task drive_simultaneous_transaction(fifo_transaction wr_txn, fifo_transaction rd_txn);
  @(posedge vif.clk);
  
  // Drive both operations in same cycle
  vif.wr_en   <= 1'b1;
  vif.rd_en   <= 1'b1;
  vif.wr_data <= wr_txn.wr_data;
  
  `uvm_info(get_type_name(), $sformatf(
    "Driving simultaneous R/W: wr_data=0x%0h", wr_txn.wr_data), UVM_HIGH)
  
  @(posedge vif.clk);
  vif.wr_en <= 1'b0;
  vif.rd_en <= 1'b0;
endtask
```

## Scoreboard Enhancement

```systemverilog
// Add to scoreboard to track almost-empty state transitions
function void check_almost_empty_simultaneous(fifo_transaction txn);
  int expected_count;
  
  if (txn.wr_en && txn.rd_en) begin
    // Simultaneous operation - count should remain stable
    expected_count = current_fifo_count;
    
    if (current_fifo_count <= almost_empty_threshold) begin
      `uvm_info("SCOREBOARD", $


---


## Gap 12: `RESET_WRITE`

**Coverage Group:** cross_fifo_state x operation_type  
**Category:** cross


*Write immediately after reset*


### Analysis

## Coverage Gap Analysis: RESET_WRITE

**What it represents:**
This cross-coverage point verifies the FIFO's behavior when a write operation occurs in the first clock cycle(s) immediately following a reset deassertion. It validates that the FIFO correctly initializes its write pointer, empty flag, and internal state machines to accept data without corruption or protocol violations.

**Why random testing missed it:**
Random stimulus generators typically insert variable delays between reset deassertion and the first operation, making the precise timing of "immediate write after reset" statistically unlikely. The probability of randomly generating back-to-back reset-then-write without intervening idle cycles is very low, especially if the testbench has weighted delays or other operations in the stimulus pool.

**Design behavior targeted:**
This targets critical reset recovery logic and initialization sequencing—specifically whether write enable, address pointers, and full/empty flag generation are properly synchronized and functional on the very first active cycle post-reset. It catches potential race conditions, incomplete reset propagation, or single-cycle setup violations in the write path control logic.


### Suggested Test Scenario

## Test Scenario: Immediate Write After Reset

**Scenario Description:**
Create a directed test that deasserts reset and immediately asserts write enable with valid data on the very next clock cycle, repeating this sequence multiple times with varying data patterns to verify the FIFO's write path initialization is race-free and functionally correct from cycle-1 post-reset.

**SystemVerilog/UVM Implementation:**

```systemverilog
class reset_write_sequence extends uvm_sequence#(fifo_transaction);
  `uvm_object_utils(reset_write_sequence)
  
  rand int num_iterations;
  rand bit [7:0] write_data[];
  
  constraint iterations_c {
    num_iterations inside {[5:20]};
  }
  
  constraint data_c {
    write_data.size() == num_iterations;
    foreach(write_data[i]) {
      write_data[i] inside {[0:255]};
    }
  }
  
  function new(string name = "reset_write_sequence");
    super.new(name);
  endfunction
  
  task body();
    fifo_transaction txn;
    
    for(int i = 0; i < num_iterations; i++) begin
      // Apply reset
      `uvm_do_with(txn, {
        operation == RESET;
        reset_duration inside {[2:5]}; // Hold reset for few cycles
      })
      
      // Immediately write on next cycle after reset deasserts
      `uvm_do_with(txn, {
        operation == WRITE;
        write_enable == 1'b1;
        data == write_data[i];
        pre_delay == 0; // CRITICAL: Zero delay after reset
      })
      
      // Add a read to verify data integrity
      `uvm_do_with(txn, {
        operation == READ;
        read_enable == 1'b1;
        pre_delay == 1; // One cycle delay before read
      })
      
      `uvm_info(get_type_name(), 
                $sformatf("Iteration %0d: Wrote 0x%0h immediately after reset", 
                          i, write_data[i]), UVM_MEDIUM)
    end
  endtask
endclass

// Alternative: Direct RTL-level test for non-UVM environments
module reset_write_directed_test;
  logic clk, rst_n, wr_en, rd_en;
  logic [7:0] wr_data, rd_data;
  logic full, empty;
  
  // DUT instantiation
  fifo_dut dut(.*);
  
  // Clock generation
  initial begin
    clk = 0;
    forever #5 clk = ~clk;
  end
  
  // Test stimulus
  initial begin
    // Test case 1: Single immediate write
    rst_n = 0;
    wr_en = 0;
    rd_en = 0;
    wr_data = 8'h00;
    
    repeat(3) @(posedge clk); // Hold reset
    @(posedge clk);
    rst_n = 1;
    
    // IMMEDIATE write on first cycle after reset
    @(posedge clk);
    wr_en = 1;
    wr_data = 8'hAA;
    
    @(posedge clk);
    wr_en = 0;
    
    // Verify write succeeded
    assert(empty == 0) else $error("FIFO should not be empty after immediate write");
    
    // Test case 2: Multiple back-to-back resets with immediate writes
    for(int i = 0; i < 10; i++) begin
      @(posedge clk);
      rst_n = 0;
      wr_en = 0;
      
      repeat(2) @(posedge clk);
      rst_n = 1;
      
      @(posedge clk);
      wr_en = 1;
      wr_data = 8'h50 + i;
      
      @(posedge clk);
      wr_en = 0;
      rd_en = 1;
      
      @(posedge clk);
      rd_en = 0;
      assert(rd_data == (8'h50 + i)) 
        else $error("Data mismatch on iteration %0d: expected 0x%0h, got 0x%0h", 
                    i, 8'h50+i, rd_data);
    end
    
    $display("RESET_WRITE coverage test completed successfully");
    $finish;
  end
  
  // Coverage collection
  covergroup cg_reset_write @(posedge clk);
    reset_state: coverpoint rst_n {
      bins reset = {0};
      bins active = {1};
    }
    
    write_op: coverpoint wr_en {
      bins write = {1};
      bins no_write = {0};
    }
    
    // Cross coverage to hit RESET_WRITE
    reset_to_write: cross reset_state, write_op {
      bins immediate_write = binsof(reset_state.active) && 
                             binsof(write_op.write);
    }
  endgroup
  
  cg_reset_write cg_inst = new();
  
endmodule
```

**Key Configuration Details:**

1. **Zero Pre-Delay Constraint**: The critical aspect is `pre_delay == 0` in the UVM sequence to ensure write happens immediately after reset deassertion without any idle cycles.

2. **Reset Duration Variation**: Vary reset hold time (2-5 cycles) to test different reset propagation scenarios.

3. **Data Pattern Coverage**: Use different data patterns (sequential, random, corner values like 0x00, 0xFF) to verify data path integrity.

4. **Verification Checks**:
   - Monitor empty flag transitions (should go from 1→0 on first write)
   - Verify write pointer increments correctly from reset value
   - Read back written data to confirm no corruption
   - Check for any protocol violations (unexpected full flag, etc.)

5. **Scoreboard Integration**: Ensure your scoreboard tracks that the first transaction post-reset is properly handled and data integrity is maintained.

This test will deterministically hit the `RESET_WRITE` cross-coverage bin by eliminating the randomness that prevented it from being covered naturally.


---


## Gap 13: `RESET_READ`

**Coverage Group:** cross_fifo_state x operation_type  
**Category:** cross


*Read immediately after reset*


### Analysis

## Coverage Gap Analysis: RESET_READ

**What it represents:**
This cross-coverage point verifies the FIFO's behavior when a read operation is attempted immediately following a reset condition, ensuring the empty flag is properly asserted, read pointers are correctly initialized to zero, and no spurious data is output during this critical state transition.

**Why random testing missed it:**
Random stimulus generators typically include delays or write operations after reset to populate the FIFO before reading, making the immediate post-reset read scenario statistically unlikely. Additionally, most constrained-random testbenches prioritize valid operational sequences over boundary conditions like reading from an empty, just-reset FIFO.

**Design behavior targeted:**
This targets the reset recovery path and empty-state protection logic, specifically verifying that the FIFO correctly handles underflow protection, maintains read pointer integrity at address 0x0, and prevents invalid data propagation when accessed before any writes occur post-reset.


### Suggested Test Scenario

# Test Scenario for RESET_READ Coverage Gap

## Scenario Description
Create a directed test that performs an immediate read operation on the very first clock cycle after reset deassertion, verifying that the FIFO correctly asserts the empty flag, maintains read pointer at 0x0, outputs known safe data (zeros or X's depending on design), and prevents any state corruption from the premature read attempt.

## SystemVerilog/UVM Implementation

```systemverilog
class reset_read_sequence extends base_fifo_sequence;
  `uvm_object_utils(reset_read_sequence)
  
  function new(string name = "reset_read_sequence");
    super.new(name);
  endfunction
  
  virtual task body();
    fifo_transaction txn;
    
    // Apply reset
    `uvm_info(get_type_name(), "Applying FIFO reset", UVM_MEDIUM)
    apply_reset();
    
    // Wait for reset deassertion (single clock cycle)
    @(posedge vif.clk);
    
    // Immediately attempt read on first cycle after reset
    txn = fifo_transaction::type_id::create("immediate_read_txn");
    start_item(txn);
    assert(txn.randomize() with {
      operation == READ;
      read_enable == 1'b1;
      write_enable == 1'b0;
    });
    finish_item(txn);
    
    // Verify empty flag is asserted
    @(posedge vif.clk);
    `uvm_info(get_type_name(), 
              $sformatf("Post-reset read: empty=%0b, rptr=0x%0h, data=0x%0h",
                        vif.empty, vif.read_ptr, vif.read_data), 
              UVM_HIGH)
    
    // Additional back-to-back reads to stress empty condition
    repeat(3) begin
      txn = fifo_transaction::type_id::create("continued_read_txn");
      start_item(txn);
      assert(txn.randomize() with {
        operation == READ;
        read_enable == 1'b1;
        write_enable == 1'b0;
      });
      finish_item(txn);
    end
    
  endtask
  
  // Helper task to apply reset
  virtual task apply_reset();
    vif.rst_n <= 1'b0;
    repeat(2) @(posedge vif.clk);
    vif.rst_n <= 1'b1;
  endtask
  
endclass
```

## Scoreboard Checking Logic

```systemverilog
class reset_read_scoreboard extends uvm_scoreboard;
  `uvm_component_utils(reset_read_scoreboard)
  
  uvm_analysis_imp#(fifo_transaction, reset_read_scoreboard) analysis_export;
  
  bit reset_just_occurred = 0;
  int cycles_since_reset = 0;
  
  function void write(fifo_transaction txn);
    if (txn.rst_n == 0) begin
      reset_just_occurred = 1;
      cycles_since_reset = 0;
    end else begin
      cycles_since_reset++;
    end
    
    // Check immediate post-reset read behavior
    if (reset_just_occurred && cycles_since_reset == 1 && txn.read_enable) begin
      
      // Critical checks for RESET_READ coverage point
      if (!txn.empty) begin
        `uvm_error(get_type_name(), 
                   "EMPTY flag not asserted on immediate post-reset read!")
      end
      
      if (txn.read_ptr != 0) begin
        `uvm_error(get_type_name(), 
                   $sformatf("Read pointer not at 0x0 after reset (actual: 0x%0h)", 
                             txn.read_ptr))
      end
      
      if (txn.write_ptr != 0) begin
        `uvm_error(get_type_name(), 
                   $sformatf("Write pointer not at 0x0 after reset (actual: 0x%0h)", 
                             txn.write_ptr))
      end
      
      // Verify no underflow error if design has underflow protection
      if (txn.underflow_error) begin
        `uvm_warning(get_type_name(), 
                     "Underflow error asserted on post-reset read - verify if expected")
      end
      
      `uvm_info(get_type_name(), 
                "RESET_READ coverage point successfully hit and verified", 
                UVM_MEDIUM)
      
      reset_just_occurred = 0; // Clear flag after first check
    end
  endfunction
  
endclass
```

## Test Configuration

```systemverilog
class reset_read_test extends base_fifo_test;
  `uvm_component_utils(reset_read_test)
  
  function new(string name = "reset_read_test", uvm_component parent = null);
    super.new(name, parent);
  endfunction
  
  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    
    // Configure environment for immediate post-reset operations
    uvm_config_db#(int)::set(this, "env.agent.sequencer", 
                              "post_reset_delay", 0); // Zero delay
    
    // Disable any automatic FIFO initialization
    uvm_config_db#(bit)::set(this, "env", 
                              "auto_fifo_init", 0);
  endfunction
  
  virtual task run_phase(uvm_phase phase);
    reset_read_sequence seq;
    
    phase.raise_objection(this);
    
    seq = reset_read_sequence::type_id::create("seq");
    seq.start(env.agent.sequencer);
    
    // Small delay to capture coverage
    #100ns;
    
    phase.drop_objection(this);
  endtask
  
endclass
```

## Key Configuration Details

1. **Zero Post-Reset Delay**: Explicitly configure sequencer to issue transactions immediately after reset deassertion
2. **Disable Auto-Init**: Turn off any automatic FIFO population that might occur in base test classes
3. **Assertion Monitoring**: Ensure protocol checkers are active to catch any X-propagation or metastability issues
4. **Coverage Sampling**: Verify coverage is sampled on the exact clock edge where `empty=1` AND `read_enable=1` AND `cycles_since_reset=1`

This targeted approach guarantees hitting the RESET_READ cross-coverage point while thoroughly validating the design's reset recovery and empty-state protection mechanisms.


---


## Gap 14: `(FULL,_WRITE)`

**Coverage Group:** unknown  
**Category:** unknown


### Analysis

# Coverage Gap Analysis: (FULL, _WRITE)

## Verification Perspective
This coverage point tracks write operations attempted when a buffer, FIFO, or memory structure is in a FULL state. It verifies the design's handling of overflow conditions and back-pressure scenarios where producers attempt to write data despite lack of available space.

## Why Random Testing Missed It
Random testing likely failed to hit this because:
1. The probability of generating sustained write traffic without corresponding reads to fill the structure completely is low
2. Timing constraints may prevent random sequences from maintaining the FULL condition long enough while simultaneously issuing write requests
3. Default testbench behavior may include implicit flow control that prevents writes when full

## Target Design Behavior
This targets critical error handling and data integrity corner cases: verifying that writes to a full structure are properly rejected/blocked, error flags are asserted, write pointers don't corrupt, and no data loss or overflow occurs. Essential for validating producer-consumer synchronization and overflow protection mechanisms.


### Suggested Test Scenario

# Test Scenario for (FULL, _WRITE) Coverage

## Scenario Description
Create a directed test that fills the buffer/FIFO to capacity by issuing back-to-back writes without any reads, then continues to attempt additional write operations while monitoring that the FULL flag remains asserted, write operations are rejected, and no data corruption occurs.

## SystemVerilog/UVM Test Implementation

```systemverilog
class fifo_full_write_test extends base_test;
  `uvm_component_utils(fifo_full_write_test)
  
  function new(string name = "fifo_full_write_test", uvm_component parent = null);
    super.new(name, parent);
  endfunction
  
  virtual task run_phase(uvm_phase phase);
    fifo_write_seq write_seq;
    fifo_read_seq read_seq;
    int fifo_depth;
    
    phase.raise_objection(this);
    
    // Get FIFO depth from configuration
    if (!uvm_config_db#(int)::get(this, "", "fifo_depth", fifo_depth))
      `uvm_fatal("CFG", "FIFO depth not configured")
    
    `uvm_info("TEST", $sformatf("Starting FULL+WRITE test with depth=%0d", fifo_depth), UVM_LOW)
    
    // Step 1: Fill FIFO completely with back-to-back writes
    write_seq = fifo_write_seq::type_id::create("fill_seq");
    write_seq.num_writes = fifo_depth;
    write_seq.no_delays = 1;  // Back-to-back writes
    write_seq.start(env.agent.sequencer);
    
    // Step 2: Wait for FULL flag to stabilize
    #10ns;
    
    // Step 3: Attempt multiple writes while FULL
    write_seq = fifo_write_seq::type_id::create("overflow_seq");
    write_seq.num_writes = 10;  // Try 10 additional writes
    write_seq.no_delays = 1;
    write_seq.expect_full = 1;  // Constraint to expect rejection
    
    fork
      begin
        write_seq.start(env.agent.sequencer);
      end
      begin
        // Monitor that FULL stays asserted during overflow attempts
        repeat(10) begin
          @(posedge env.agent.monitor.vif.clk);
          if (!env.agent.monitor.vif.full) begin
            `uvm_error("FULL_CHECK", "FULL flag deasserted during overflow writes")
          end
        end
      end
    join
    
    // Step 4: Verify no data corruption by reading all valid entries
    read_seq = fifo_read_seq::type_id::create("drain_seq");
    read_seq.num_reads = fifo_depth;
    read_seq.start(env.agent.sequencer);
    
    #100ns;
    phase.drop_objection(this);
  endtask
  
endclass

// Specialized sequence for overflow write attempts
class fifo_write_seq extends uvm_sequence#(fifo_transaction);
  `uvm_object_utils(fifo_write_seq)
  
  rand int num_writes;
  bit no_delays = 0;
  bit expect_full = 0;
  
  function new(string name = "fifo_write_seq");
    super.new(name);
  endfunction
  
  virtual task body();
    fifo_transaction req;
    
    for (int i = 0; i < num_writes; i++) begin
      req = fifo_transaction::type_id::create($sformatf("write_req_%0d", i));
      
      start_item(req);
      assert(req.randomize() with {
        op_type == WRITE;
        if (expect_full) {
          // When expecting full, still try to write
          write_enable == 1'b1;
        }
      });
      finish_item(req);
      
      // Check response for proper rejection
      if (expect_full && req.write_accepted) begin
        `uvm_error("OVERFLOW", $sformatf("Write %0d accepted when FIFO was FULL!", i))
      end
      
      if (!no_delays) begin
        #($urandom_range(0, 5) * 1ns);
      end
    end
  endtask
  
endclass
```

## Scoreboard Enhancement for Coverage

```systemverilog
class fifo_scoreboard extends uvm_scoreboard;
  
  bit full_state;
  int write_attempts_when_full;
  
  covergroup fifo_overflow_cg;
    full_write_cp: coverpoint {full_state, write_attempt} {
      bins full_with_write = {2'b11};  // This is our target coverage bin
      bins not_full_write = {2'b01};
      bins full_no_write = {2'b10};
    }
  endgroup
  
  function void write_fifo_transaction(fifo_transaction txn);
    full_state = txn.full_flag;
    
    if (txn.op_type == WRITE && full_state) begin
      write_attempts_when_full++;
      
      // Verify proper rejection behavior
      assert_write_rejected: assert (!txn.write_accepted) else
        `uvm_error("OVERFLOW", "Write accepted when FIFO full")
      
      assert_full_maintained: assert (txn.full_flag) else
        `uvm_error("FULL_FLAG", "FULL flag dropped during overflow write")
        
      // Sample coverage
      fifo_overflow_cg.sample();
    end
  endfunction
  
endclass
```

## Key Configuration Details

```systemverilog
// In test configuration
initial begin
  uvm_config_db#(int)::set(null, "*", "fifo_depth", 16);
  
  // Disable any automatic flow control in the driver
  uvm_config_db#(bit)::set(null, "*.agent.driver", "ignore_full", 1);
  
  // Set aggressive write probability
  uvm_config_db#(int)::set(null, "*.agent.sequencer", "write_probability", 100);
end
```

## Critical Assertions to Add

```systemverilog
// In the interface or monitor
property no_write_when_full;
  @(posedge clk) (full && write_en) |=> (write_ptr == $past(write_ptr));
endproperty
assert_no_write_when_full: assert property(no_write_when_full);

property full_flag_stable_on_rejected_write;
  @(posedge clk) (full && write_en && !read_en) |=> full;
endproperty
assert_full_stable: assert property(full_flag_stable_on_rejected_write);
```

This test specifically targets the (FULL, _WRITE) coverage gap by deterministically creating the full condition and then forcing write attempts, while verifying all protection mechanisms work correctly.


---


## Gap 15: `(EMPTY,_READ)`

**Coverage Group:** unknown  
**Category:** unknown


### Analysis

# Coverage Gap Analysis: (EMPTY, _READ)

## Verification Perspective
This coverage point targets the specific scenario where a read operation is attempted on an empty data structure (likely a FIFO, queue, or buffer). It verifies the design's handling of underflow conditions and ensures proper error signaling, data validity flags, or protocol responses when reading from an empty state.

## Why Random Testing Missed It
Random testing typically generates read operations probabilistically without tracking the fill level of the structure. The gap exists because random stimulus rarely creates the precise sequence of: (1) emptying the structure completely through consecutive reads/flushes, then (2) immediately issuing another read before any writes occur—especially if the testbench has a bias toward balanced read/write traffic.

## Target Design Behavior
This targets critical corner-case behavior including underflow protection mechanisms, empty flag assertion timing, read pointer handling at boundary conditions, and verification that invalid/stale data isn't propagated on empty reads. It's essential for validating error handling and data integrity in resource-starved scenarios.


### Suggested Test Scenario

# Test Scenario for (EMPTY, _READ) Coverage Gap

## Scenario Description
Create a directed test that explicitly drains the data structure to empty state through consecutive reads, then immediately attempts one or more read operations while monitoring underflow flags, error signals, and data validity indicators.

## Test Implementation

```systemverilog
class empty_read_test extends base_test;
  `uvm_component_utils(empty_read_test)
  
  function new(string name = "empty_read_test", uvm_component parent = null);
    super.new(name, parent);
  endfunction
  
  virtual task run_phase(uvm_phase phase);
    empty_read_sequence seq;
    
    phase.raise_objection(this);
    
    seq = empty_read_sequence::type_id::create("seq");
    seq.start(m_env.m_agent.m_sequencer);
    
    phase.drop_objection(this);
  endtask
endclass

class empty_read_sequence extends uvm_sequence#(fifo_transaction);
  `uvm_object_utils(empty_read_sequence)
  
  function new(string name = "empty_read_sequence");
    super.new(name);
  endfunction
  
  virtual task body();
    fifo_transaction txn;
    int initial_depth;
    
    // Phase 1: Determine current fill level by reading status
    txn = fifo_transaction::type_id::create("status_read");
    start_item(txn);
    txn.operation = STATUS_READ;
    finish_item(txn);
    get_response(txn);
    initial_depth = txn.current_depth;
    
    `uvm_info(get_type_name(), 
              $sformatf("Initial FIFO depth: %0d", initial_depth), 
              UVM_MEDIUM)
    
    // Phase 2: Drain the FIFO completely
    repeat(initial_depth) begin
      txn = fifo_transaction::type_id::create("drain_read");
      start_item(txn);
      txn.operation = READ;
      finish_item(txn);
      get_response(txn);
      
      `uvm_info(get_type_name(), 
                $sformatf("Draining read %0d, empty_flag=%0b", 
                         initial_depth - $urandom_range(0,0), 
                         txn.empty_flag), 
                UVM_HIGH)
    end
    
    // Phase 3: Wait for empty flag to stabilize (critical timing check)
    #10ns;
    
    // Phase 4: Attempt multiple reads from EMPTY state
    repeat(5) begin
      txn = fifo_transaction::type_id::create("empty_read");
      start_item(txn);
      txn.operation = READ;
      finish_item(txn);
      get_response(txn);
      
      // Assertions to verify correct empty behavior
      `uvm_info(get_type_name(), 
                $sformatf("Empty read attempt: empty_flag=%0b, underflow=%0b, valid=%0b, data=0x%0h",
                         txn.empty_flag, txn.underflow_flag, 
                         txn.data_valid, txn.data), 
                UVM_MEDIUM)
      
      // Check expected behavior
      if (!txn.empty_flag) begin
        `uvm_error(get_type_name(), 
                   "Empty flag not asserted during empty read!")
      end
      
      if (!txn.underflow_flag && !txn.error_response) begin
        `uvm_warning(get_type_name(), 
                     "No underflow indication on empty read")
      end
      
      if (txn.data_valid) begin
        `uvm_error(get_type_name(), 
                   "Data valid asserted on empty read - data corruption risk!")
      end
      
      // Small delay between empty reads to check state persistence
      #(5ns + $urandom_range(0, 10));
    end
    
    // Phase 5: Verify recovery - write then read
    txn = fifo_transaction::type_id::create("recovery_write");
    start_item(txn);
    txn.operation = WRITE;
    txn.data = 32'hDEADBEEF;
    finish_item(txn);
    
    #5ns;
    
    txn = fifo_transaction::type_id::create("recovery_read");
    start_item(txn);
    txn.operation = READ;
    finish_item(txn);
    get_response(txn);
    
    if (txn.data !== 32'hDEADBEEF) begin
      `uvm_error(get_type_name(), 
                 $sformatf("Data mismatch after empty recovery: expected=0x%0h, got=0x%0h",
                          32'hDEADBEEF, txn.data))
    end
    
  endtask
endclass
```

## Scoreboard Coverage Collector

```systemverilog
covergroup empty_read_cg with function sample(bit empty, bit read_en, 
                                               bit underflow, bit valid);
  option.per_instance = 1;
  
  empty_state: coverpoint empty {
    bins empty_true = {1};
    bins empty_false = {0};
  }
  
  read_operation: coverpoint read_en {
    bins read_active = {1};
  }
  
  // The critical cross coverage
  empty_read_cross: cross empty_state, read_operation {
    bins hit_empty_read = binsof(empty_state.empty_true) && 
                          binsof(read_operation.read_active);
  }
  
  // Additional corner cases
  underflow_behavior: coverpoint underflow {
    bins underflow_asserted = {1};
    bins no_underflow = {0};
  }
  
  data_valid_on_empty: coverpoint valid iff (empty) {
    bins valid_low = {0};      // Expected
    bins valid_high = {1};     // Error condition
  }
  
endgroup
```

## Key Configuration Details

**Constraints:**
- Disable random write injection during the drain phase
- Set read-to-write ratio to 100:0 during empty state testing
- Configure minimum inter-transaction delay to 0 for back-to-back empty reads

**Assertions to Enable:**
```systemverilog
property empty_read_no_valid;
  @(posedge clk) (empty && read_en) |-> !data_valid;
endproperty

property empty_persistent;
  @(posedge clk) (empty && read_en && !write_en) |=> empty;
endproperty

assert_empty_read_no_valid: assert property(empty_read_no_valid)
  else `uvm_error("EMPTY_READ", "Valid asserted on empty read");
```

**Test Configuration:**
- Run with full FIFO initially, then drain completely
- Test with different initial depths (1, 2, half-full, full-1, full)
- Vary timing between drain completion and empty reads (0ns, 1 cycle, multiple cycles)


---


## Gap 16: `(ALMOST_FULL,_SIMULTANEOUS_RD_WR)`

**Coverage Group:** unknown  
**Category:** unknown


### Analysis

## Coverage Gap Analysis: (ALMOST_FULL, SIMULTANEOUS_RD_WR)

### What This Coverage Point Represents:
This coverage point targets the specific scenario where a FIFO or buffer is in an "almost full" state (typically 1-2 entries away from full) while simultaneous read and write operations occur in the same clock cycle. This tests the pointer management logic and flag generation when the buffer is near capacity with concurrent access.

### Why Random Testing Missed It:
The probability of hitting this corner case randomly is extremely low because it requires precise timing alignment: (1) the buffer must reach the almost-full threshold through a specific sequence of writes, and (2) a read operation must occur in the exact same cycle as a write. Random traffic patterns typically either fill the buffer completely or drain it before simultaneous operations occur at this critical threshold.

### Design Behavior Targeted:
This tests critical pointer arithmetic and status flag stability when read/write pointers are nearly colliding in the almost-full region. It verifies that the almost_full flag correctly updates, no data corruption occurs, and the design properly handles the edge case where one operation might prevent overflow while another attempts to add data—essential for preventing deadlock or data loss in high-throughput scenarios.


### Suggested Test Scenario

# Test Scenario for ALMOST_FULL with SIMULTANEOUS_RD_WR

## Scenario Description
Fill the FIFO to exactly (DEPTH - ALMOST_FULL_THRESHOLD - 1) entries, then perform simultaneous read and write operations for multiple cycles while monitoring the almost_full flag stability, pointer updates, and data integrity. This ensures the design correctly handles the boundary condition where operations keep the FIFO hovering at the almost_full threshold.

## SystemVerilog/UVM Test Implementation

```systemverilog
class fifo_almost_full_simul_rw_test extends fifo_base_test;
  `uvm_component_utils(fifo_almost_full_simul_rw_test)
  
  function new(string name = "fifo_almost_full_simul_rw_test", uvm_component parent = null);
    super.new(name, parent);
  endfunction
  
  virtual task run_phase(uvm_phase phase);
    fifo_sequence seq;
    int fifo_depth = 16; // Example depth
    int almost_full_threshold = 2; // Entries from full
    int target_fill_level;
    
    phase.raise_objection(this);
    
    // Calculate target: fill to exactly almost_full - 1
    target_fill_level = fifo_depth - almost_full_threshold - 1;
    
    `uvm_info(get_type_name(), 
              $sformatf("Filling FIFO to %0d entries (almost_full triggers at %0d)", 
                        target_fill_level, fifo_depth - almost_full_threshold), 
              UVM_MEDIUM)
    
    // Step 1: Fill FIFO to target level (write-only)
    seq = fifo_sequence::type_id::create("fill_seq");
    seq.num_transactions = target_fill_level;
    seq.operation_type = WRITE_ONLY;
    seq.start(m_env.m_agent.m_sequencer);
    
    // Step 2: Perform simultaneous read/write at almost_full boundary
    seq = fifo_almost_full_simul_sequence::type_id::create("simul_seq");
    seq.start(m_env.m_agent.m_sequencer);
    
    // Step 3: Drain and verify
    seq = fifo_sequence::type_id::create("drain_seq");
    seq.num_transactions = target_fill_level + 10; // Drain all
    seq.operation_type = READ_ONLY;
    seq.start(m_env.m_agent.m_sequencer);
    
    phase.drop_objection(this);
  endtask
endclass

// Specialized sequence for simultaneous operations at almost_full
class fifo_almost_full_simul_sequence extends uvm_sequence #(fifo_transaction);
  `uvm_object_utils(fifo_almost_full_simul_sequence)
  
  rand int num_simul_cycles;
  
  constraint simul_cycles_c {
    num_simul_cycles inside {[20:50]}; // Enough cycles to stress test
  }
  
  function new(string name = "fifo_almost_full_simul_sequence");
    super.new(name);
  endfunction
  
  virtual task body();
    fifo_transaction wr_txn, rd_txn;
    
    for (int i = 0; i < num_simul_cycles; i++) begin
      // Create simultaneous write and read transactions
      fork
        begin
          wr_txn = fifo_transaction::type_id::create("wr_txn");
          start_item(wr_txn);
          assert(wr_txn.randomize() with {
            operation == WRITE;
            data inside {[32'h0000_0000:32'hFFFF_FFFF]};
          });
          wr_txn.tag = $sformatf("SIMUL_WR_%0d", i);
          finish_item(wr_txn);
        end
        begin
          rd_txn = fifo_transaction::type_id::create("rd_txn");
          start_item(rd_txn);
          assert(rd_txn.randomize() with {
            operation == READ;
          });
          rd_txn.tag = $sformatf("SIMUL_RD_%0d", i);
          finish_item(rd_txn);
        end
      join
      
      `uvm_info(get_type_name(), 
                $sformatf("Cycle %0d: Simultaneous RD/WR completed", i), 
                UVM_HIGH)
    end
  endtask
endclass
```

## Enhanced Scoreboard Checking

```systemverilog
class fifo_scoreboard extends uvm_scoreboard;
  // ... existing scoreboard code ...
  
  bit almost_full_flag;
  int current_occupancy;
  int almost_full_threshold = 2;
  int fifo_depth = 16;
  
  // Monitor for simultaneous operations at almost_full
  function void check_almost_full_simul_rw(fifo_transaction wr_txn, 
                                            fifo_transaction rd_txn,
                                            bit almost_full_before,
                                            bit almost_full_after);
    int expected_occupancy;
    
    // When simultaneous RD/WR, occupancy should remain stable
    expected_occupancy = current_occupancy; // +1 write, -1 read = net 0
    
    // Check almost_full flag behavior
    if (current_occupancy >= (fifo_depth - almost_full_threshold)) begin
      if (!almost_full_before) begin
        `uvm_error(get_type_name(), 
                   $sformatf("almost_full should be HIGH at occupancy=%0d", 
                             current_occupancy))
      end
      
      // After simultaneous RD/WR, almost_full should remain stable
      if (almost_full_after != almost_full_before) begin
        `uvm_warning(get_type_name(), 
                     $sformatf("almost_full flag toggled during simul RD/WR: %b->%b at occupancy=%0d",
                               almost_full_before, almost_full_after, current_occupancy))
      end
    end
    
    // Verify data integrity - read data should match expected
    if (!compare_data(rd_txn.data, expected_data_queue.pop_front())) begin
      `uvm_error(get_type_name(), 
                 "Data mismatch during simultaneous RD/WR at almost_full")
    end
    
    // Store write data for future comparison
    expected_data_queue.push_back(wr_txn.data);
    
  endfunction
endclass
```

## Driver Implementation for Simultaneous Operations

```systemverilog
class fifo_driver extends uvm_driver #(fifo_transaction);
  
  virtual task drive_simultaneous_rw(fifo_transaction wr_txn, 
                                     fifo_transaction rd_txn);
    // Ensure both operations happen in the same clock cycle
    @(posedge vif.clk);
    
    // Assert both write and read enables simultaneously
    vif.wr_en <= 1'b1;
    vif.rd_en <= 1'b1;
    vif.wr_data <= wr_txn.data;
    
    // Sample flags before operation
    wr_txn.almost_full_before = vif.almost_full;
    rd_txn.almost_full_before = vif.almost_full;
    
    @(posedge vif.clk);
    
    // Sample flags and data after operation
    wr_txn.almost_full_after = vif.almost_full;
    rd_txn.almost_full_after = vif.almost_full;
    rd_txn.data = vif.rd_data;
    rd_txn.rd_valid = vif.rd_valid;
    
    // Deassert enables
    vif.wr_en <= 1'


---


## Gap 17: `(ALMOST_EMPTY,_SIMULTANEOUS_RD_WR)`

**Coverage Group:** unknown  
**Category:** unknown


### Analysis

## Coverage Gap Analysis: (ALMOST_EMPTY, SIMULTANEOUS_RD_WR)

### Verification Perspective
This coverage point targets the corner case where a FIFO/buffer is in an almost-empty state (typically 1-2 entries remaining) while simultaneous read and write operations occur in the same clock cycle. This tests the pointer management logic and flag generation circuitry when the buffer is near depletion with concurrent access, verifying that the almost-empty flag updates correctly and no underflow occurs.

### Why Random Testing Missed It
The probability of hitting this scenario randomly is extremely low because it requires precise temporal alignment: (1) the FIFO must be drained to almost-empty through a specific sequence of operations, AND (2) read and write requests must arrive simultaneously at exactly that moment. Random stimulus typically drains FIFOs completely or fills them, rarely maintaining the almost-empty threshold while generating concurrent operations.

### Target Design Behavior
This tests the priority logic and state machine behavior when almost-empty flag assertion/deassertion coincides with simultaneous transactions. It validates that the design correctly handles the race condition between pointer updates, prevents metastability in flag generation, and maintains data integrity when the read pointer nearly catches the write pointer during concurrent access.


### Suggested Test Scenario

# Test Scenario for (ALMOST_EMPTY, SIMULTANEOUS_RD_WR)

## Scenario Description
Create a directed test that drains the FIFO to exactly the almost-empty threshold (typically 1-2 entries), then performs simultaneous read and write operations for multiple consecutive cycles while maintaining the almost-empty state. This validates pointer arithmetic, flag stability, and data integrity at the critical almost-empty boundary.

## SystemVerilog/UVM Test Implementation

```systemverilog
class fifo_almost_empty_simul_rw_test extends fifo_base_test;
  `uvm_component_utils(fifo_almost_empty_simul_rw_test)
  
  function new(string name = "fifo_almost_empty_simul_rw_test", uvm_component parent);
    super.new(name, parent);
  endfunction
  
  virtual task run_phase(uvm_phase phase);
    fifo_sequence seq;
    int almost_empty_threshold;
    int num_simul_ops = 50; // Number of simultaneous rd/wr cycles
    
    phase.raise_objection(this);
    
    // Get FIFO parameters
    almost_empty_threshold = m_env.m_fifo_cfg.almost_empty_level; // e.g., 2
    
    `uvm_info(get_type_name(), $sformatf(
      "Starting almost_empty simultaneous rd/wr test with threshold=%0d", 
      almost_empty_threshold), UVM_LOW)
    
    // Step 1: Fill FIFO to a known state (half full)
    seq = fifo_sequence::type_id::create("fill_seq");
    seq.operation = WRITE_ONLY;
    seq.num_trans = m_env.m_fifo_cfg.depth / 2;
    seq.start(m_env.m_agent.m_sequencer);
    
    // Step 2: Drain to almost_empty threshold + 1
    // This ensures we're just above the threshold
    seq = fifo_sequence::type_id::create("drain_seq");
    seq.operation = READ_ONLY;
    seq.num_trans = (m_env.m_fifo_cfg.depth / 2) - (almost_empty_threshold + 1);
    seq.start(m_env.m_agent.m_sequencer);
    
    // Step 3: Perform simultaneous read/write operations
    // This maintains the FIFO at almost_empty threshold
    seq = fifo_sequence::type_id::create("simul_rw_seq");
    seq.operation = SIMULTANEOUS_RD_WR;
    seq.num_trans = num_simul_ops;
    seq.start(m_env.m_agent.m_sequencer);
    
    // Step 4: Verify almost_empty flag behavior during transitions
    #100ns; // Allow scoreboard to process
    
    phase.drop_objection(this);
  endtask
  
endclass
```

## Sequence Implementation with Precise Control

```systemverilog
class fifo_sequence extends uvm_sequence #(fifo_transaction);
  `uvm_object_utils(fifo_sequence)
  
  typedef enum {WRITE_ONLY, READ_ONLY, SIMULTANEOUS_RD_WR} operation_e;
  
  rand operation_e operation;
  rand int num_trans;
  rand bit [7:0] data_pattern[];
  
  function new(string name = "fifo_sequence");
    super.new(name);
  endfunction
  
  virtual task body();
    fifo_transaction req;
    
    case (operation)
      WRITE_ONLY: begin
        repeat(num_trans) begin
          req = fifo_transaction::type_id::create("req");
          start_item(req);
          assert(req.randomize() with {
            wr_en == 1'b1;
            rd_en == 1'b0;
          });
          finish_item(req);
        end
      end
      
      READ_ONLY: begin
        repeat(num_trans) begin
          req = fifo_transaction::type_id::create("req");
          start_item(req);
          assert(req.randomize() with {
            wr_en == 1'b0;
            rd_en == 1'b1;
          });
          finish_item(req);
        end
      end
      
      SIMULTANEOUS_RD_WR: begin
        repeat(num_trans) begin
          req = fifo_transaction::type_id::create("req");
          start_item(req);
          assert(req.randomize() with {
            wr_en == 1'b1;
            rd_en == 1'b1;
            // Ensure valid data for write
            wr_data inside {[8'h00:8'hFF]};
          });
          finish_item(req);
          `uvm_info(get_type_name(), $sformatf(
            "Simultaneous RD/WR: wr_data=0x%0h", req.wr_data), UVM_HIGH)
        end
      end
    endcase
  endtask
  
endclass
```

## Scoreboard Coverage Monitoring

```systemverilog
class fifo_scoreboard extends uvm_scoreboard;
  
  // Coverage for almost_empty with simultaneous operations
  covergroup cg_almost_empty_simul_ops @(posample_event);
    
    cp_almost_empty: coverpoint almost_empty_flag {
      bins almost_empty_asserted = {1};
      bins almost_empty_deasserted = {0};
    }
    
    cp_rd_en: coverpoint rd_en;
    cp_wr_en: coverpoint wr_en;
    
    cp_fifo_count: coverpoint fifo_count {
      bins at_threshold = {[1:2]}; // Typical almost_empty threshold
      bins above_threshold = {[3:$]};
      bins empty = {0};
    }
    
    // Cross coverage for the target scenario
    cross_almost_empty_simul: cross cp_almost_empty, cp_rd_en, cp_wr_en, cp_fifo_count {
      bins target_scenario = binsof(cp_almost_empty.almost_empty_asserted) &&
                             binsof(cp_rd_en) intersect {1} &&
                             binsof(cp_wr_en) intersect {1} &&
                             binsof(cp_fifo_count.at_threshold);
      
      // Also check transitions
      bins exit_almost_empty = binsof(cp_almost_empty.almost_empty_deasserted) &&
                               binsof(cp_rd_en) intersect {0} &&
                               binsof(cp_wr_en) intersect {1} &&
                               binsof(cp_fifo_count.above_threshold);
    }
    
  endgroup
  
  function new(string name, uvm_component parent);
    super.new(name, parent);
    cg_almost_empty_simul_ops = new();
  endfunction
  
  virtual function void write(fifo_transaction trans);
    // Update internal model
    update_fifo_model(trans);
    
    // Sample coverage
    almost_empty_flag = m_fifo_model.almost_empty;
    rd_en = trans.rd_en;
    wr_en = trans.wr_en;
    fifo_count = m_fifo_model.count;
    
    cg_almost_empty_simul_ops.sample();
    
    // Check for target coverage hit
    if (almost_empty_flag && rd_en && wr_en && (fifo_count inside {[1:2]})) begin
      `uvm_info(get_type_name(), 
        "*** HIT TARGET COVERAGE: ALMOST_EMPTY with SIMULTANEOUS_RD_WR ***", 
        UVM_LOW)
    end
  endfunction
  
endclass
```

## Key Configuration Details

```systemverilog
// In test configuration or base test
class fifo_config extends uvm_object;
  rand int depth


---


## Gap 18: `(RESET,_WRITE)`

**Coverage Group:** unknown  
**Category:** unknown


### Analysis

# Coverage Gap Analysis: (RESET, WRITE)

## Verification Perspective
This coverage point represents a critical state transition where a WRITE operation occurs simultaneously with or immediately following a RESET signal. This targets the design's ability to handle write requests during reset assertion or in the first clock cycle after reset deassertion, verifying proper initialization and write-enable gating logic.

## Why Random Testing Missed It
Random stimulus generators typically separate reset sequences from functional operations with stabilization periods. The temporal proximity required—asserting WRITE while RESET is active or within 1-2 cycles of reset release—has extremely low probability in unconstrained random testing (~0.1% depending on signal widths).

## Target Design Behavior
This tests reset priority logic and write-path protection mechanisms. The design must either: (1) ignore writes during reset, (2) properly queue/delay writes until post-reset, or (3) handle simultaneous reset-write as a defined corner case. Failure to cover this risks metastability, corrupted initial states, or FSM lockup conditions.


### Suggested Test Scenario

# Test Scenario for (RESET, WRITE) Coverage Gap

## Scenario Description
Create a directed test that asserts a WRITE transaction at precise timing points relative to RESET: (1) during active reset, (2) on the same cycle as reset deassertion, and (3) one cycle after reset release. This verifies write-gating logic, reset priority, and proper initialization sequencing.

## SystemVerilog/UVM Test Implementation

```systemverilog
class reset_write_collision_test extends base_test;
  `uvm_component_utils(reset_write_collision_test)
  
  function new(string name = "reset_write_collision_test", uvm_component parent);
    super.new(name, parent);
  endfunction
  
  virtual task run_phase(uvm_phase phase);
    reset_write_sequence seq;
    
    phase.raise_objection(this);
    
    seq = reset_write_sequence::type_id::create("seq");
    seq.start(m_env.m_agent.m_sequencer);
    
    phase.drop_objection(this);
  endtask
endclass

class reset_write_sequence extends uvm_sequence#(transaction);
  `uvm_object_utils(reset_write_sequence)
  
  function new(string name = "reset_write_sequence");
    super.new(name);
  endfunction
  
  virtual task body();
    transaction write_txn;
    
    // Test Case 1: Write during active reset
    `uvm_info(get_type_name(), "TC1: Write during active reset", UVM_LOW)
    fork
      begin
        // Assert reset
        assert_reset(10); // 10 cycle reset pulse
      end
      begin
        // Issue write at cycle 5 of reset (mid-reset)
        #(5 * `CLK_PERIOD);
        write_txn = transaction::type_id::create("write_during_reset");
        start_item(write_txn);
        assert(write_txn.randomize() with {
          cmd == WRITE;
          addr inside {[0:255]};
          data != 0; // Non-zero to detect corruption
        });
        finish_item(write_txn);
      end
    join
    
    // Verify write was ignored/blocked
    check_no_write_occurred();
    
    // Test Case 2: Write on same cycle as reset deassertion
    `uvm_info(get_type_name(), "TC2: Write coincident with reset release", UVM_LOW)
    fork
      begin
        assert_reset(5);
      end
      begin
        // Wait for exact reset deassertion edge
        @(posedge vif.clk iff vif.rst_n == 1'b0);
        @(posedge vif.clk); // This is the deassertion cycle
        
        write_txn = transaction::type_id::create("write_at_reset_release");
        start_item(write_txn);
        assert(write_txn.randomize() with {
          cmd == WRITE;
          addr == 8'hAA; // Specific address for tracking
          data == 32'hDEADBEEF;
        });
        finish_item(write_txn);
      end
    join
    
    // Check design behavior (should be blocked or queued)
    #(2 * `CLK_PERIOD);
    verify_reset_priority(8'hAA, 32'hDEADBEEF);
    
    // Test Case 3: Write one cycle after reset
    `uvm_info(get_type_name(), "TC3: Write T+1 after reset release", UVM_LOW)
    assert_reset(5);
    @(posedge vif.clk iff vif.rst_n == 1'b1);
    @(posedge vif.clk); // T+1 after reset release
    
    write_txn = transaction::type_id::create("write_post_reset");
    start_item(write_txn);
    assert(write_txn.randomize() with {
      cmd == WRITE;
      addr == 8'h55;
      data == 32'hCAFEBABE;
    });
    finish_item(write_txn);
    
    // This write should succeed
    #(2 * `CLK_PERIOD);
    verify_write_success(8'h55, 32'hCAFEBABE);
    
    // Test Case 4: Burst writes straddling reset boundary
    `uvm_info(get_type_name(), "TC4: Write burst across reset edge", UVM_LOW)
    fork
      begin
        #(3 * `CLK_PERIOD);
        assert_reset(4);
      end
      begin
        // Start burst before reset
        repeat(8) begin
          write_txn = transaction::type_id::create("burst_write");
          start_item(write_txn);
          assert(write_txn.randomize() with {
            cmd == WRITE;
          });
          finish_item(write_txn);
          @(posedge vif.clk);
        end
      end
    join
    
    verify_partial_burst_handling();
    
  endtask
  
  // Helper tasks
  task assert_reset(int cycles);
    vif.rst_n <= 1'b0;
    repeat(cycles) @(posedge vif.clk);
    vif.rst_n <= 1'b1;
  endtask
  
  task check_no_write_occurred();
    // Check scoreboard or memory model for no state change
    if (m_env.m_scoreboard.write_count_during_reset > 0) begin
      `uvm_error(get_type_name(), "Write executed during reset - reset priority violated!")
    end
  endtask
  
  task verify_reset_priority(bit [7:0] addr, bit [31:0] data);
    bit [31:0] readback;
    // Read the address to verify write was blocked
    read_memory(addr, readback);
    if (readback == data) begin
      `uvm_warning(get_type_name(), 
        $sformatf("Write at reset edge was accepted - verify if this is intended behavior"))
    end else begin
      `uvm_info(get_type_name(), "Reset correctly blocked write at deassertion edge", UVM_LOW)
    end
  endtask
  
  task verify_write_success(bit [7:0] addr, bit [31:0] expected_data);
    bit [31:0] readback;
    read_memory(addr, readback);
    assert(readback == expected_data) else
      `uvm_error(get_type_name(), 
        $sformatf("Post-reset write failed: expected 0x%0h, got 0x%0h", expected_data, readback))
  endtask
  
endclass
```

## Configuration Details

```systemverilog
// In test configuration or base test
class reset_write_config extends uvm_object;
  // Disable random reset injection during this test
  bit disable_random_reset = 1;
  
  // Configure precise timing control
  bit enable_cycle_accurate_mode = 1;
  
  // Reset assertion time (cycles)
  rand int reset_duration;
  constraint reset_duration_c {
    reset_duration inside {[3:10]};
  }
  
  // Write timing relative to reset (in clock cycles)
  typedef enum {
    DURING_RESET,      // -5 to -1 cycles before reset release
    AT_RESET_EDGE,     // Cycle 0 (same as reset deassertion)
    POST_RESET_T1,     // Cycle +1
    POST_RESET_T2      // Cycle +2
  } write_timing_e;
  
endclass
```

## Key Assertions to Add

```systemverilog
// In the DUT or testbench interface
property no_write_during_reset;
  @(posedge clk) (!rst_n) |-> (!write_enable);
endproperty

property write


---


## Gap 19: `(RESET,_READ)`

**Coverage Group:** unknown  
**Category:** unknown


### Analysis

# Coverage Gap Analysis: (RESET, READ)

## Verification Perspective
This coverage point represents the critical corner case of performing a READ operation immediately following or concurrent with a RESET condition. It verifies the design's behavior when read transactions occur during reset assertion, reset deassertion, or in the first clock cycle(s) after reset release.

## Why Random Testing Missed It
Random stimulus generators typically enforce protocol-compliant sequences where operations begin only after reset completes and stabilizes. The temporal proximity or overlap between RESET and READ violates normal operational assumptions, making this combination extremely rare (near-zero probability) in unconstrained random testing.

## Target Design Behavior
This targets reset-read race conditions, including: proper handling of read requests during reset (error responses, bus parking, or request dropping), correct initialization of read data paths, and verification that read operations don't corrupt or access uninitialized state immediately post-reset.

**Recommended Action**: Create a directed test forcing READ assertions during reset phases and within 1-5 cycles post-reset to verify graceful handling and data path integrity.


### Suggested Test Scenario

# Test Scenario for (RESET, READ) Coverage Gap

## Scenario Description
Create a directed test that issues READ transactions at various phases of the reset sequence: during reset assertion, during reset deassertion (same cycle), and within the first 5 cycles after reset release. Verify that the DUT handles these reads gracefully with proper error responses or valid default data, without hanging or corrupting internal state.

## SystemVerilog/UVM Test Implementation

```systemverilog
class reset_read_race_test extends base_test;
  `uvm_component_utils(reset_read_race_test)
  
  function new(string name = "reset_read_race_test", uvm_component parent = null);
    super.new(name, parent);
  endfunction
  
  virtual task run_phase(uvm_phase phase);
    reset_read_sequence seq;
    
    phase.raise_objection(this);
    
    seq = reset_read_sequence::type_id::create("seq");
    seq.start(m_env.m_agent.m_sequencer);
    
    phase.drop_objection(this);
  endtask
endclass

class reset_read_sequence extends uvm_sequence#(bus_transaction);
  `uvm_object_utils(reset_read_sequence)
  
  rand bit [31:0] read_addr;
  
  function new(string name = "reset_read_sequence");
    super.new(name);
  endfunction
  
  virtual task body();
    bus_transaction read_txn;
    
    // Test Case 1: READ during reset assertion
    `uvm_info(get_type_name(), "Test 1: READ during RESET assertion", UVM_LOW)
    fork
      begin
        // Assert reset
        p_sequencer.m_reset_agent.assert_reset(10); // 10 cycle reset
      end
      begin
        // Issue READ at cycle 3 of reset
        #(3 * get_clock_period());
        read_txn = bus_transaction::type_id::create("read_during_reset");
        start_item(read_txn);
        assert(read_txn.randomize() with {
          trans_type == READ;
          addr == read_addr;
        });
        finish_item(read_txn);
        
        // Check response - should be error or ignored
        `uvm_info(get_type_name(), 
                  $sformatf("READ during reset response: %s", 
                           read_txn.response.name()), UVM_MEDIUM)
        assert(read_txn.response inside {ERROR, NO_RESPONSE}) else
          `uvm_error(get_type_name(), "Unexpected response during reset")
      end
    join
    
    // Test Case 2: READ on same cycle as reset deassertion
    `uvm_info(get_type_name(), "Test 2: READ concurrent with reset deassertion", UVM_LOW)
    fork
      begin
        p_sequencer.m_reset_agent.assert_reset(5);
      end
      begin
        // Wait until reset deassertion edge
        @(posedge p_sequencer.m_reset_agent.reset_n);
        
        // Issue READ on same cycle
        read_txn = bus_transaction::type_id::create("read_at_reset_release");
        start_item(read_txn);
        assert(read_txn.randomize() with {
          trans_type == READ;
          addr == read_addr;
        });
        finish_item(read_txn);
        
        `uvm_info(get_type_name(), 
                  $sformatf("READ at reset release response: %s, data: 0x%0h", 
                           read_txn.response.name(), read_txn.data), UVM_MEDIUM)
      end
    join
    
    // Test Case 3: READ within 1-5 cycles after reset
    `uvm_info(get_type_name(), "Test 3: READ 1-5 cycles post-reset", UVM_LOW)
    p_sequencer.m_reset_agent.assert_reset(5);
    
    for (int cycle_delay = 1; cycle_delay <= 5; cycle_delay++) begin
      // Apply reset
      p_sequencer.m_reset_agent.assert_reset(5);
      
      // Wait specified cycles after reset release
      repeat(cycle_delay) @(posedge p_sequencer.m_vif.clk);
      
      // Issue READ
      read_txn = bus_transaction::type_id::create($sformatf("read_post_reset_cyc%0d", cycle_delay));
      start_item(read_txn);
      assert(read_txn.randomize() with {
        trans_type == READ;
        addr == read_addr;
      });
      finish_item(read_txn);
      
      `uvm_info(get_type_name(), 
                $sformatf("READ %0d cycles post-reset: response=%s, data=0x%0h", 
                         cycle_delay, read_txn.response.name(), read_txn.data), 
                UVM_MEDIUM)
      
      // Verify response is valid (not X or Z)
      assert(!$isunknown(read_txn.data)) else
        `uvm_error(get_type_name(), 
                   $sformatf("Unknown data at cycle %0d post-reset", cycle_delay))
    end
    
    // Test Case 4: Rapid reset-read cycles
    `uvm_info(get_type_name(), "Test 4: Rapid RESET-READ sequences", UVM_LOW)
    repeat(10) begin
      p_sequencer.m_reset_agent.assert_reset($urandom_range(2, 5));
      
      // Random delay 0-3 cycles
      repeat($urandom_range(0, 3)) @(posedge p_sequencer.m_vif.clk);
      
      read_txn = bus_transaction::type_id::create("rapid_read");
      start_item(read_txn);
      assert(read_txn.randomize() with {
        trans_type == READ;
      });
      finish_item(read_txn);
    end
    
  endtask
endclass
```

## Alternative: Direct RTL Testbench Approach

```systemverilog
module reset_read_directed_tb;
  logic clk, rst_n;
  logic read_en;
  logic [31:0] read_addr, read_data;
  logic read_valid, read_error;
  
  // DUT instantiation
  dut u_dut (.*);
  
  // Clock generation
  initial begin
    clk = 0;
    forever #5 clk = ~clk;
  end
  
  // Test stimulus
  initial begin
    // Initialize
    rst_n = 1;
    read_en = 0;
    read_addr = 0;
    
    // Test 1: READ during reset
    @(posedge clk);
    rst_n = 0;
    repeat(2) @(posedge clk);
    
    // Issue READ while reset asserted
    read_en = 1;
    read_addr = 32'hDEAD_BEEF;
    @(posedge clk);
    read_en = 0;
    
    // Check: should get error or no response
    assert(read_error || !read_valid) else
      $error("READ during reset should not succeed");
    
    repeat(3) @(posedge clk);
    
    // Test 2: READ on reset deassertion cycle
    rst_n = 0;
    repeat(5) @(posedge clk);
    
    // Deassert reset and read simultaneously
    @(posedge clk);
    rst_n = 1;
    read_en = 1;
    read_addr = 32'h0000_0100;
    @(posedge clk);
    read_en = 0;
    
    // Monitor response
    @(posedge clk);
    $


---


## Next Steps

1. Review each suggested test scenario

2. Implement the test sequences in your testbench

3. Run simulation and verify coverage improvement

4. Iterate on gaps that remain uncovered
