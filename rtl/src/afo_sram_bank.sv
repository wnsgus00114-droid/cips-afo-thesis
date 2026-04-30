module afo_sram_bank #(
  parameter int DATA_W = 256,
  parameter int DEPTH  = 4096
) (
  input  logic                        clk,
  input  logic                        i_we,
  input  logic [$clog2(DEPTH)-1:0]    i_addr,
  input  logic [DATA_W-1:0]           i_wdata,
  output logic [DATA_W-1:0]           o_rdata
);
  logic [DATA_W-1:0] mem [0:DEPTH-1];

  always_ff @(posedge clk) begin
    if (i_we) mem[i_addr] <= i_wdata;
    o_rdata <= mem[i_addr];
  end
endmodule
