module afo_matrix_accel (
  input  logic        clk,
  input  logic        rst_n,
  input  logic        i_start,
  input  logic [31:0] i_m,
  input  logic [31:0] i_n,
  input  logic [31:0] i_k,
  output logic        o_done,
  output logic [31:0] o_cycle_count
);
  logic [31:0] remain;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      remain       <= 32'd0;
      o_done       <= 1'b0;
      o_cycle_count <= 32'd0;
    end else begin
      o_done <= 1'b0;
      if (i_start && remain == 0) begin
        // Simplified cycles estimate.
        remain <= (i_m * i_n * i_k) >> 10;
      end else if (remain != 0) begin
        remain <= remain - 1'b1;
        o_cycle_count <= o_cycle_count + 1'b1;
        if (remain == 1) o_done <= 1'b1;
      end
    end
  end
endmodule
