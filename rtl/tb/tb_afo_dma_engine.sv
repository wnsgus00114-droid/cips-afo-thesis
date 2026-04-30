`timescale 1ns/1ps
`include "afo_defs.svh"

module tb_afo_dma_engine;
  import afo_defs::*;

  logic clk;
  logic rst_n;
  logic i_desc_valid;
  dma_desc_t i_desc;
  logic o_desc_ready;
  logic i_dma_ready;
  logic o_busy;
  logic o_done_pulse;
  logic [7:0] o_dbg_qcount;
  logic [7:0] o_dbg_qmax;

  integer enq_count;
  integer done_count;

  bit cov_zero_size_dropped;
  bit cov_ready_deassert_when_full;
  bit cov_full_block_enq;
  bit cov_backpressure_queue_growth;
  bit cov_drain_complete;
  bit cov_qmax_depth;

  afo_dma_engine #(
    .DESC_DEPTH(4)
  ) dut (
    .clk(clk),
    .rst_n(rst_n),
    .i_desc_valid(i_desc_valid),
    .i_desc(i_desc),
    .o_desc_ready(o_desc_ready),
    .i_dma_ready(i_dma_ready),
    .o_busy(o_busy),
    .o_done_pulse(o_done_pulse),
    .o_dbg_qcount(o_dbg_qcount),
    .o_dbg_qmax(o_dbg_qmax)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  initial begin
    $dumpfile("../results/waves/tb_afo_dma_engine.vcd");
    $dumpvars(0, tb_afo_dma_engine);
  end

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      enq_count <= 0;
      done_count <= 0;
    end else begin
      if (i_desc_valid && o_desc_ready && (i_desc.size_bytes != 0)) begin
        enq_count <= enq_count + 1;
      end
      if (o_done_pulse) begin
        done_count <= done_count + 1;
      end
    end
  end

  task automatic drive_desc(input logic [19:0] sz, input logic [3:0] kind);
    begin
      i_desc.src_addr = 52'h1000_0000_0000;
      i_desc.dst_bank = 8'd3;
      i_desc.size_bytes = sz;
      i_desc.qos = 2'b01;
      i_desc.layer_id = 8'd9;
      i_desc.tensor_kind = kind;
      i_desc_valid = 1'b1;
      @(posedge clk);
      i_desc_valid = 1'b0;
      i_desc = '0;
    end
  endtask

  initial begin
    integer before_enq;
    integer before_done;
    integer w;
    integer i;

    rst_n = 1'b0;
    i_desc_valid = 1'b0;
    i_desc = '0;
    i_dma_ready = 1'b1;

    #20;
    rst_n = 1'b1;
    #1;

    assert (o_dbg_qcount == 0 && !o_busy) else $fatal(1, "reset state mismatch");

    // Scenario 1: zero-size descriptor must be dropped.
    before_enq = enq_count;
    drive_desc(20'd0, 4'hA);
    @(posedge clk);
    assert (enq_count == before_enq) else $fatal(1, "zero-size descriptor should not enqueue");
    assert (o_dbg_qcount == 0) else $fatal(1, "zero-size descriptor should keep qcount=0");
    cov_zero_size_dropped = 1'b1;

    // Scenario 2: backpressure queue buildup to full.
    i_dma_ready = 1'b0;
    for (i = 0; i < 4; i = i + 1) begin
      drive_desc(20'd64, 4'h1 + i[3:0]);
    end
    #1;
    assert (o_dbg_qcount == 4) else $fatal(1, "queue should be full at depth 4, got %0d", o_dbg_qcount);
    assert (!o_desc_ready) else $fatal(1, "o_desc_ready should deassert when full");
    cov_backpressure_queue_growth = 1'b1;
    cov_ready_deassert_when_full = 1'b1;

    // Attempt enqueue while full: must be blocked.
    before_enq = enq_count;
    drive_desc(20'd64, 4'hF);
    #1;
    assert (enq_count == before_enq) else $fatal(1, "enqueue while full should be blocked");
    assert (o_dbg_qcount == 4) else $fatal(1, "qcount should remain full after blocked enqueue");
    cov_full_block_enq = 1'b1;

    assert (int'(o_dbg_qmax) >= 4) else $fatal(1, "qmax should capture full depth");
    cov_qmax_depth = 1'b1;

    // Scenario 3: release ready and drain all.
    i_dma_ready = 1'b1;
    before_done = done_count;
    w = 0;
    while ((done_count - before_done) < 4 && w < 20) begin
      @(posedge clk);
      w = w + 1;
    end
    assert (w < 20) else $fatal(1, "drain timeout");
    assert ((done_count - before_done) == 4) else $fatal(1, "expected 4 done pulses after release");
    assert (o_dbg_qcount == 0) else $fatal(1, "queue should drain to zero");
    assert (!o_busy) else $fatal(1, "DMA busy should deassert after drain");
    cov_drain_complete = 1'b1;

    assert (&{
      cov_zero_size_dropped,
      cov_ready_deassert_when_full,
      cov_full_block_enq,
      cov_backpressure_queue_growth,
      cov_drain_complete,
      cov_qmax_depth
    }) else $fatal(1, "coverage bins incomplete");

    $display("[COV] tb_afo_dma_engine covered=6 total=6");
    $display("[PASS] tb_afo_dma_engine assertions passed.");
    $finish;
  end
endmodule
