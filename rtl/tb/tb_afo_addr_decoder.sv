`timescale 1ns/1ps
`include "afo_defs.svh"

module tb_afo_addr_decoder;
  import afo_defs::*;

  logic [51:0] i_addr;
  mem_target_t o_target;
  logic o_fault;

  bit cov_hbf0, cov_hbf1, cov_hbf2, cov_hbf3;
  bit cov_hbm8, cov_hbm9, cov_hbmA, cov_hbmB;
  bit cov_sramF;
  bit cov_inv4, cov_invC, cov_invE;
  bit cov_lowbit_invariant;

  afo_addr_decoder dut (
    .i_addr(i_addr),
    .o_target(o_target),
    .o_fault(o_fault)
  );

  initial begin
    i_addr = '0;
    #1;

    i_addr = {4'h0, 48'h1234_5678_9abc}; #1;
    assert (o_target == MEM_HBF && !o_fault) else $fatal(1, "prefix 0 decode failed");
    cov_hbf0 = 1'b1;

    i_addr = {4'h1, 48'h0000_0000_0001}; #1;
    assert (o_target == MEM_HBF && !o_fault) else $fatal(1, "prefix 1 decode failed");
    cov_hbf1 = 1'b1;

    i_addr = {4'h2, 48'hffff_0000_abcd}; #1;
    assert (o_target == MEM_HBF && !o_fault) else $fatal(1, "prefix 2 decode failed");
    cov_hbf2 = 1'b1;

    i_addr = {4'h3, 48'h0000_ffff_abcd}; #1;
    assert (o_target == MEM_HBF && !o_fault) else $fatal(1, "prefix 3 decode failed");
    cov_hbf3 = 1'b1;

    i_addr = {4'h8, 48'h0123_4567_89ab}; #1;
    assert (o_target == MEM_HBM && !o_fault) else $fatal(1, "prefix 8 decode failed");
    cov_hbm8 = 1'b1;

    i_addr = {4'h9, 48'h1111_2222_3333}; #1;
    assert (o_target == MEM_HBM && !o_fault) else $fatal(1, "prefix 9 decode failed");
    cov_hbm9 = 1'b1;

    i_addr = {4'hA, 48'h2222_3333_4444}; #1;
    assert (o_target == MEM_HBM && !o_fault) else $fatal(1, "prefix A decode failed");
    cov_hbmA = 1'b1;

    i_addr = {4'hB, 48'h3333_4444_5555}; #1;
    assert (o_target == MEM_HBM && !o_fault) else $fatal(1, "prefix B decode failed");
    cov_hbmB = 1'b1;

    i_addr = {4'hF, 48'hdead_beef_cafe}; #1;
    assert (o_target == MEM_SRAM && !o_fault) else $fatal(1, "prefix F decode failed");
    cov_sramF = 1'b1;

    i_addr = {4'h4, 48'h0000_0000_0000}; #1;
    assert (o_target == MEM_NONE && o_fault) else $fatal(1, "prefix 4 fault decode failed");
    cov_inv4 = 1'b1;

    i_addr = {4'hC, 48'h1234_0000_5678}; #1;
    assert (o_target == MEM_NONE && o_fault) else $fatal(1, "prefix C fault decode failed");
    cov_invC = 1'b1;

    i_addr = {4'hE, 48'habcd_1234_5678}; #1;
    assert (o_target == MEM_NONE && o_fault) else $fatal(1, "prefix E fault decode failed");
    cov_invE = 1'b1;

    // Lower bits must not change region decode for a fixed prefix.
    i_addr = {4'h0, 48'h0000_0000_0000}; #1;
    assert (o_target == MEM_HBF && !o_fault) else $fatal(1, "lowbit test #1 failed");
    i_addr = {4'h0, 48'hffff_ffff_ffff}; #1;
    assert (o_target == MEM_HBF && !o_fault) else $fatal(1, "lowbit test #2 failed");
    cov_lowbit_invariant = 1'b1;

    assert (&{
      cov_hbf0, cov_hbf1, cov_hbf2, cov_hbf3,
      cov_hbm8, cov_hbm9, cov_hbmA, cov_hbmB,
      cov_sramF, cov_inv4, cov_invC, cov_invE,
      cov_lowbit_invariant
    }) else $fatal(1, "coverage bins incomplete");

    $display("[COV] tb_afo_addr_decoder covered=13 total=13");
    $display("[PASS] tb_afo_addr_decoder assertions passed.");
    $finish;
  end
endmodule
