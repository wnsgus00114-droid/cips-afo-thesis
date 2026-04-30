`include "afo_defs.svh"

module afo_top (
  input  logic clk,
  input  logic rst_n,

  input  logic        i_prefetch_issue,
  input  logic [7:0]  i_layer_cur,
  input  logic [51:0] i_weight_base,
  input  logic [51:0] i_kv_base,
  input  logic        i_dma_ready,

  output logic [7:0]  o_dma_qcount,
  output logic [7:0]  o_dma_qmax,
  output logic        o_dma_done,
  output logic        o_dma_busy,
  output afo_defs::mem_target_t o_dec_weight_target,
  output afo_defs::mem_target_t o_dec_kv_target,
  output afo_defs::mem_target_t o_dec_desc_target,
  output logic        o_dec_weight_fault,
  output logic        o_dec_kv_fault,
  output logic        o_dec_desc_fault
);
  import afo_defs::*;

  logic desc_valid, desc_ready;
  logic dma_busy;
  logic prefetch_issue_qual;
  dma_desc_t desc;
  mem_target_t dec_weight_target, dec_kv_target, dec_desc_target;
  logic dec_weight_fault, dec_kv_fault, dec_desc_fault;

  assign prefetch_issue_qual = i_prefetch_issue & ~dec_weight_fault & ~dec_kv_fault;
  assign o_dec_weight_target = dec_weight_target;
  assign o_dec_kv_target     = dec_kv_target;
  assign o_dec_desc_target   = dec_desc_target;
  assign o_dec_weight_fault  = dec_weight_fault;
  assign o_dec_kv_fault      = dec_kv_fault;
  assign o_dec_desc_fault    = dec_desc_fault;

  afo_addr_decoder u_dec_weight (
    .i_addr(i_weight_base),
    .o_target(dec_weight_target),
    .o_fault(dec_weight_fault)
  );

  afo_addr_decoder u_dec_kv (
    .i_addr(i_kv_base),
    .o_target(dec_kv_target),
    .o_fault(dec_kv_fault)
  );

  afo_addr_decoder u_dec_desc (
    .i_addr(desc.src_addr),
    .o_target(dec_desc_target),
    .o_fault(dec_desc_fault)
  );

  afo_prefetch_engine u_prefetch (
    .clk(clk),
    .rst_n(rst_n),
    .i_issue(prefetch_issue_qual),
    .i_layer_cur(i_layer_cur),
    .i_weight_base(i_weight_base),
    .i_kv_base(i_kv_base),
    .o_desc_valid(desc_valid),
    .o_desc(desc),
    .i_desc_ready(desc_ready)
  );

  afo_dma_engine u_dma (
    .clk(clk),
    .rst_n(rst_n),
    .i_desc_valid(desc_valid),
    .i_desc(desc),
    .o_desc_ready(desc_ready),
    .i_dma_ready(i_dma_ready),
    .o_busy(dma_busy),
    .o_done_pulse(o_dma_done),
    .o_dbg_qcount(o_dma_qcount),
    .o_dbg_qmax(o_dma_qmax)
  );

  assign o_dma_busy = dma_busy;
endmodule
