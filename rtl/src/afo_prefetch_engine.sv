`include "afo_defs.svh"

module afo_prefetch_engine (
  input  logic                 clk,
  input  logic                 rst_n,

  input  logic                 i_issue,
  input  logic [7:0]           i_layer_cur,
  input  logic [afo_defs::ADDR_W-1:0] i_weight_base,
  input  logic [afo_defs::ADDR_W-1:0] i_kv_base,

  output logic                 o_desc_valid,
  output afo_defs::dma_desc_t  o_desc,
  input  logic                 i_desc_ready
);
  import afo_defs::*;

  typedef enum logic [1:0] {S_IDLE, S_WEIGHT, S_KV} state_t;
  state_t state;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= S_IDLE;
    end else begin
      unique case (state)
        S_IDLE:   if (i_issue) state <= S_WEIGHT;
        S_WEIGHT: if (i_desc_ready) state <= S_KV;
        S_KV:     if (i_desc_ready) state <= S_IDLE;
        default:  state <= S_IDLE;
      endcase
    end
  end

  always_comb begin
    o_desc_valid = 1'b0;
    o_desc       = '0;

    unique case (state)
      S_WEIGHT: begin
        o_desc_valid       = 1'b1;
        o_desc.src_addr    = i_weight_base;
        o_desc.dst_bank    = 8'd0;
        o_desc.size_bytes  = 20'(192 * 1024); // 192KB tile
        o_desc.qos         = 2'b01;
        o_desc.layer_id    = i_layer_cur + 8'd1;
        o_desc.tensor_kind = 4'h1;
      end
      S_KV: begin
        o_desc_valid       = 1'b1;
        o_desc.src_addr    = i_kv_base;
        o_desc.dst_bank    = 8'd16;
        o_desc.size_bytes  = 20'(128 * 1024); // 128KB chunk
        o_desc.qos         = 2'b01;
        o_desc.layer_id    = i_layer_cur + 8'd1;
        o_desc.tensor_kind = 4'h2;
      end
      default: begin
      end
    endcase
  end
endmodule
