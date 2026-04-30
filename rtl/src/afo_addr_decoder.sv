`include "afo_defs.svh"

module afo_addr_decoder (
  input  logic [afo_defs::ADDR_W-1:0] i_addr,
  output afo_defs::mem_target_t        o_target,
  output logic                         o_fault
);
  import afo_defs::*;
  logic [3:0] prefix;
  logic unused_addr_low_bits;

  // Use lower bits to keep lint clean; decode intentionally uses only prefix.
  assign unused_addr_low_bits = ^i_addr[47:0];

  always_comb begin
    prefix  = i_addr[51:48];
    o_fault = 1'b0;
    unique case (prefix)
      4'h0, 4'h1, 4'h2, 4'h3: o_target = MEM_HBF;
      4'h8, 4'h9, 4'hA, 4'hB: o_target = MEM_HBM;
      4'hF:                   o_target = MEM_SRAM;
      default: begin
        o_target = MEM_NONE;
        o_fault  = 1'b1;
      end
    endcase
  end
endmodule
