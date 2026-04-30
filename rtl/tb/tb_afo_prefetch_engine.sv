`timescale 1ns/1ps
`include "afo_defs.svh"

module tb_afo_prefetch_engine;
  import afo_defs::*;

  logic clk;
  logic rst_n;
  logic i_issue;
  logic [7:0] i_layer_cur;
  logic [51:0] i_weight_base;
  logic [51:0] i_kv_base;
  logic o_desc_valid;
  dma_desc_t o_desc;
  logic i_desc_ready;
  logic unused_prefetch_desc_fields;

  integer accept_count;
  logic [3:0] first_kind, second_kind;
  logic [7:0] first_layer, second_layer;

  bit cov_weight_seen;
  bit cov_kv_seen;
  bit cov_stall_weight_hold;
  bit cov_busy_issue_ignored;
  bit cov_order_weight_to_kv;
  bit cov_layer_inc;
  bit cov_two_issue_repeatable;

  afo_prefetch_engine dut (
    .clk(clk),
    .rst_n(rst_n),
    .i_issue(i_issue),
    .i_layer_cur(i_layer_cur),
    .i_weight_base(i_weight_base),
    .i_kv_base(i_kv_base),
    .o_desc_valid(o_desc_valid),
    .o_desc(o_desc),
    .i_desc_ready(i_desc_ready)
  );

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  initial begin
    $dumpfile("../results/waves/tb_afo_prefetch_engine.vcd");
    $dumpvars(0, tb_afo_prefetch_engine);
  end

  assign unused_prefetch_desc_fields = ^{
    o_desc.dst_bank,
    o_desc.size_bytes,
    o_desc.qos
  };

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      accept_count <= 0;
      first_kind <= '0;
      second_kind <= '0;
      first_layer <= '0;
      second_layer <= '0;
    end else begin
      if (o_desc_valid && i_desc_ready) begin
        accept_count <= accept_count + 1;
        if (accept_count == 0) begin
          first_kind <= o_desc.tensor_kind;
          first_layer <= o_desc.layer_id;
        end
        if (accept_count == 1) begin
          second_kind <= o_desc.tensor_kind;
          second_layer <= o_desc.layer_id;
        end
      end
    end
  end

  initial begin
    integer w;
    integer before_accept;
    integer iter;

    rst_n = 1'b0;
    i_issue = 1'b0;
    i_layer_cur = 8'd21;
    i_weight_base = 52'h1000_0000_0000;
    i_kv_base = 52'h2000_0000_0000;
    i_desc_ready = 1'b0;

    #20;
    rst_n = 1'b1;
    #10;

    assert (!o_desc_valid) else $fatal(1, "idle state should not assert desc_valid");

    // Scenario 1: stall on weight descriptor.
    @(negedge clk);
    i_issue = 1'b1;
    @(negedge clk);
    i_issue = 1'b0;

    // Wait until weight descriptor appears, then verify stall hold.
    w = 0;
    while (!(o_desc_valid && (o_desc.tensor_kind == 4'h1)) && w < 10) begin
      @(posedge clk);
      #1;
      w = w + 1;
    end
    assert (w < 10) else $fatal(1, "weight descriptor did not appear after issue");

    repeat (3) begin
      @(posedge clk);
      #1;
      assert (o_desc_valid) else $fatal(1, "weight descriptor should stay valid while stalled");
      assert (o_desc.tensor_kind == 4'h1) else $fatal(1, "expected weight kind while stalled");
      assert (o_desc.src_addr == i_weight_base) else $fatal(1, "weight address mismatch while stalled");
      cov_stall_weight_hold = 1'b1;
      cov_weight_seen = 1'b1;
    end

    // Busy issue should be ignored (still no handshake while ready=0).
    before_accept = accept_count;
    @(negedge clk);
    i_issue = 1'b1;
    @(negedge clk);
    i_issue = 1'b0;
    @(posedge clk);
    assert (accept_count == before_accept) else $fatal(1, "busy issue should not create extra handshake while stalled");
    cov_busy_issue_ignored = 1'b1;

    // Release ready: expect weight then KV then idle.
    @(negedge clk);
    i_desc_ready = 1'b1;

    w = 0;
    while (!(o_desc_valid && (o_desc.tensor_kind == 4'h2)) && w < 10) begin
      @(posedge clk);
      #1;
      w = w + 1;
    end
    assert (w < 10) else $fatal(1, "after weight handshake, KV descriptor did not appear");
    assert (o_desc.src_addr == i_kv_base) else $fatal(1, "KV address mismatch");
    cov_kv_seen = 1'b1;

    @(posedge clk);
    #1;
    assert (!o_desc_valid) else $fatal(1, "should return to idle after KV handshake");

    assert (accept_count == 2) else $fatal(1, "scenario1 should consume exactly 2 descriptors");
    assert (first_kind == 4'h1 && second_kind == 4'h2) else $fatal(1, "descriptor order should be weight->kv");
    cov_order_weight_to_kv = 1'b1;

    assert (first_layer == (i_layer_cur + 8'd1) && second_layer == (i_layer_cur + 8'd1))
      else $fatal(1, "layer increment mismatch");
    cov_layer_inc = 1'b1;

    // Scenario 2: repeatability for two more issues.
    for (iter = 0; iter < 2; iter = iter + 1) begin
      before_accept = accept_count;
      @(negedge clk);
      i_issue = 1'b1;
      @(negedge clk);
      i_issue = 1'b0;

      w = 0;
      while ((accept_count - before_accept) < 2 && w < 20) begin
        @(posedge clk);
        w = w + 1;
      end

      assert (w < 20) else $fatal(1, "timeout on repeated issue %0d", iter);
      assert ((accept_count - before_accept) == 2) else $fatal(1, "issue %0d should produce 2 descriptors", iter);
    end
    cov_two_issue_repeatable = 1'b1;

    assert (&{
      cov_weight_seen,
      cov_kv_seen,
      cov_stall_weight_hold,
      cov_busy_issue_ignored,
      cov_order_weight_to_kv,
      cov_layer_inc,
      cov_two_issue_repeatable
    }) else $fatal(1, "coverage bins incomplete");

    $display("[COV] tb_afo_prefetch_engine covered=7 total=7");
    $display("[PASS] tb_afo_prefetch_engine assertions passed.");
    $finish;
  end
endmodule
