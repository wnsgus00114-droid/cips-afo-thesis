`include "afo_defs.svh"

module afo_dma_engine #(
  parameter int DESC_DEPTH = 16
) (
  input  logic                 clk,
  input  logic                 rst_n,

  input  logic                 i_desc_valid,
  input  afo_defs::dma_desc_t  i_desc,
  output logic                 o_desc_ready,

  output logic                 o_busy,
  output logic                 o_done_pulse,

  output logic [7:0]           o_dbg_qcount
);
  import afo_defs::*;

  localparam int QCOUNT_W = $clog2(DESC_DEPTH) + 1;
  localparam logic [QCOUNT_W-1:0] DESC_DEPTH_L = QCOUNT_W'(DESC_DEPTH);
  logic [$clog2(DESC_DEPTH):0] wr_ptr, rd_ptr, qcount;
  logic                        do_enq, do_deq, desc_nonzero;
  logic                        unused_desc_fields;

  assign o_desc_ready = (qcount < DESC_DEPTH_L);
  assign o_busy       = (qcount != 0);
  assign o_dbg_qcount = 8'(qcount);
  assign desc_nonzero = (i_desc.size_bytes != 0);
  assign unused_desc_fields = ^{
    i_desc.src_addr,
    i_desc.dst_bank,
    i_desc.size_bytes,
    i_desc.qos,
    i_desc.layer_id,
    i_desc.tensor_kind
  };
  assign do_enq       = i_desc_valid && o_desc_ready && desc_nonzero;
  assign do_deq       = (qcount != 0);

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      wr_ptr      <= '0;
      rd_ptr      <= '0;
      qcount      <= '0;
      o_done_pulse <= 1'b0;
    end else begin
      o_done_pulse <= 1'b0;

      if (do_enq) begin
        // Payload content is abstracted in this model; queue timing is modeled.
        wr_ptr <= wr_ptr + 1'b1;
      end

      if (do_deq) begin
        rd_ptr       <= rd_ptr + 1'b1;
        o_done_pulse <= 1'b1;
      end

      unique case ({do_enq, do_deq})
        2'b10: qcount <= qcount + 1'b1;
        2'b01: qcount <= qcount - 1'b1;
        default: qcount <= qcount;
      endcase
    end
  end
endmodule
