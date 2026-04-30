TOP := afo_top
TB  := tb_afo_top
SRC := src/afo_addr_decoder.sv src/afo_dma_engine.sv src/afo_prefetch_engine.sv src/afo_top.sv
INC := include

.PHONY: lint sim wave clean

lint:
	verilator --lint-only -Wall -Wno-fatal --assert -I$(INC) $(SRC) tb/$(TB).sv

sim:
	mkdir -p ../results/waves
	verilator -Wall -Wno-fatal --assert --timing --binary --trace -I$(INC) tb/$(TB).sv $(SRC)
	./obj_dir/V$(TB)

wave: sim
	@echo "Generated VCD: ../results/waves/tb_afo_top.vcd"

clean:
	rm -rf obj_dir
