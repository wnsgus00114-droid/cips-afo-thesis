`timescale 1ns/1ps
`include "afo_defs.svh"

module tb_afo_top;
  import afo_defs::*;

  logic clk;
  logic rst_n;
  logic i_prefetch_issue;
  logic [7:0] i_layer_cur;
  logic [51:0] i_weight_base;
  logic [51:0] i_kv_base;
  logic [7:0] o_dma_qcount;
  logic o_dma_done;
  logic o_dma_busy;
  mem_target_t o_dec_weight_target;
  mem_target_t o_dec_kv_target;
  mem_target_t o_dec_desc_target;
  logic o_dec_weight_fault;
  logic o_dec_kv_fault;
  logic o_dec_desc_fault;

  integer done_count;
  integer desc_accept_count;
  integer wait_cycles;
  logic [3:0] first_kind, second_kind;
  logic [51:0] first_addr, second_addr;
  logic [7:0] first_layer, second_layer;

  afo_top dut (
    .clk(clk),
    .rst_n(rst_n),
    .i_prefetch_issue(i_prefetch_issue),
    .i_layer_cur(i_layer_cur),
    .i_weight_base(i_weight_base),
    .i_kv_base(i_kv_base),
    .o_dma_qcount(o_dma_qcount),
    .o_dma_done(o_dma_done),
    .o_dma_busy(o_dma_busy),
    .o_dec_weight_target(o_dec_weight_target),
    .o_dec_kv_target(o_dec_kv_target),
    .o_dec_desc_target(o_dec_desc_target),
    .o_dec_weight_fault(o_dec_weight_fault),
    .o_dec_kv_fault(o_dec_kv_fault),
    .o_dec_desc_fault(o_dec_desc_fault)
  );

  initial begin
    clk = 0;
    forever #5 clk = ~clk;
  end

  initial begin
    $dumpfile("../results/waves/tb_afo_top.vcd");
    $dumpvars(0, tb_afo_top);
  end

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      done_count <= 0;
      desc_accept_count <= 0;
      first_kind <= '0;
      second_kind <= '0;
      first_addr <= '0;
      second_addr <= '0;
      first_layer <= '0;
      second_layer <= '0;
    end else begin
      if (o_dma_done) begin
        done_count <= done_count + 1;
        $display("[%0t] DMA done pulse. done_count(next)=%0d", $time, done_count + 1);
      end

      if (dut.desc_valid && dut.desc_ready) begin
        desc_accept_count <= desc_accept_count + 1;
        $display("[%0t] DESC accepted kind=%0h addr=%h layer=%0d", $time, dut.desc.tensor_kind, dut.desc.src_addr, dut.desc.layer_id);
        if (desc_accept_count == 0) begin
          first_kind  <= dut.desc.tensor_kind;
          first_addr  <= dut.desc.src_addr;
          first_layer <= dut.desc.layer_id;
        end
        if (desc_accept_count == 1) begin
          second_kind  <= dut.desc.tensor_kind;
          second_addr  <= dut.desc.src_addr;
          second_layer <= dut.desc.layer_id;
        end
      end
    end
  end

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
    end else if (dut.desc_valid) begin
      assert (!o_dec_desc_fault)
        else $fatal(1, "Descriptor decode fault detected while desc_valid=1");
    end
  end

  initial begin
    done_count = 0;
    desc_accept_count = 0;
    wait_cycles = 0;
    first_kind = '0;
    second_kind = '0;
    first_addr = '0;
    second_addr = '0;
    first_layer = '0;
    second_layer = '0;

    rst_n = 0;
    i_prefetch_issue = 0;
    i_layer_cur = 8'd7;
    i_weight_base = 52'h1000_0000_0000;
    i_kv_base     = 52'h2000_0000_0000;

    #20;
    rst_n = 1;
    #20;

    assert (o_dec_weight_target == MEM_HBF && !o_dec_weight_fault)
      else $fatal(1, "Weight base should decode to HBF");
    assert (o_dec_kv_target == MEM_HBF && !o_dec_kv_fault)
      else $fatal(1, "KV base should decode to HBF");

    // Scenario 1: valid weight/KV bases -> expect 2 descriptors (weight then KV).
    i_prefetch_issue = 1;
    #10;
    i_prefetch_issue = 0;

    wait_cycles = 0;
    while ((done_count < 2 || desc_accept_count < 2) && (wait_cycles < 60)) begin
      #10;
      wait_cycles = wait_cycles + 1;
    end
    assert (wait_cycles < 60)
      else $fatal(1, "Timed out waiting for two descriptor completions");

    assert (desc_accept_count == 2)
      else $fatal(1, "Expected exactly 2 accepted descriptors, got %0d", desc_accept_count);
    assert (done_count == 2)
      else $fatal(1, "Expected exactly 2 DMA done pulses, got %0d", done_count);
    assert (first_kind == 4'h1 && second_kind == 4'h2)
      else $fatal(1, "Descriptor order mismatch: first=%0h second=%0h", first_kind, second_kind);
    assert (first_addr == i_weight_base && second_addr == i_kv_base)
      else $fatal(1, "Descriptor source addresses mismatch");
    assert (o_dec_desc_target == MEM_HBF)
      else $fatal(1, "Last descriptor target should decode to HBF");
    assert (first_layer == (i_layer_cur + 8'd1) && second_layer == (i_layer_cur + 8'd1))
      else $fatal(1, "Expected layer_id=(i_layer_cur+1) for both descriptors");
    assert (o_dma_qcount == 0)
      else $fatal(1, "DMA queue should drain to zero");
    assert (!o_dma_busy)
      else $fatal(1, "DMA should be idle after queue drain");

    // Scenario 2: invalid KV base -> prefetch issue should be blocked.
    i_kv_base = 52'h5_0000_0000_0000; // invalid region ([51:48]=5)
    #10;
    $display("[%0t] Scenario2 base=%h target=%0d fault=%0b", $time, i_kv_base, o_dec_kv_target, o_dec_kv_fault);
    assert (o_dec_kv_fault)
      else $fatal(1, "KV decode fault should assert for invalid region");

    i_prefetch_issue = 1;
    #10;
    i_prefetch_issue = 0;
    #100;

    assert (desc_accept_count == 2)
      else $fatal(1, "Invalid base should not enqueue descriptors");
    assert (done_count == 2)
      else $fatal(1, "Invalid base should not trigger DMA done");

    $display("[PASS] tb_afo_top assertions passed.");
    $finish;
  end
endmodule
