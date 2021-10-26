# Copyright (c) 2021 Carlos Megías
# Licensed under the Revised MIT License, see LICENSE for details

TOPLEVEL_LANG = vhdl

SIM ?= ghdl
WAVES ?= 0
SIM_ARGS ?= --wave=signals.ghw

COCOTB_HDL_TIMEUNIT = 1ns									# Time unit for simulation
COCOTB_HDL_TIMEPRECISION = 8ns								# Time precsion for simulation

DUT      = capturator
TOPLEVEL = $(DUT)
MODULE   = test_$(DUT)
VHDL_SOURCES += ../../rtl/$(DUT).vhd 
VHDL_SOURCES += ../../rtl/vhdl_utils_lib_pkg.vhd

include $(shell cocotb-config --makefiles)/Makefile.sim		# Prepare make rules for cocotb setup