module afo_kv_sched (
  input  logic        clk,
  input  logic        rst_n,
  input  logic        i_new_token,
  input  logic [15:0] i_req_count,
  output logic [15:0] o_prefetch_budget,
  output logic        o_issue_prefetch
);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      o_prefetch_budget <= 16'd0;
      o_issue_prefetch  <= 1'b0;
    end else begin
      o_issue_prefetch <= i_new_token;
      if (i_new_token) o_prefetch_budget <= i_req_count << 2; // top-k=4 baseline
    end
  end
endmodule
