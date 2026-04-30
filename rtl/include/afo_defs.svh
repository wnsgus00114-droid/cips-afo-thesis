`ifndef AFO_DEFS_SVH
`define AFO_DEFS_SVH
`timescale 1ns/1ps

package afo_defs;
  parameter int ADDR_W = 52;
  parameter int LEN_W  = 20;

  typedef struct packed {
    logic [ADDR_W-1:0] src_addr;
    logic [7:0]        dst_bank;
    logic [LEN_W-1:0]  size_bytes;
    logic [1:0]        qos;
    logic [7:0]        layer_id;
    logic [3:0]        tensor_kind;
  } dma_desc_t;

  typedef enum logic [1:0] {
    MEM_NONE = 2'b00,
    MEM_HBM  = 2'b01,
    MEM_HBF  = 2'b10,
    MEM_SRAM = 2'b11
  } mem_target_t;
endpackage

`endif
