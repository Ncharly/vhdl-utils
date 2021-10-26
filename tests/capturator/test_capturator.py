#!/usr/bin/env python
"""

Copyright (c) 2021 Carlos Megías

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""

import logging

import cocotb
from cocotbext_axis_transfer.axis_transfer import *
from cocotb.clock import Clock
from cocotb.regression import TestFactory
from cocotb.triggers import RisingEdge


class TB:
    def __init__(self, dut):
        self.dut = dut

        self.log = logging.getLogger("cocotb.tb")
        self.log.setLevel(logging.DEBUG)

        # Coroutine for design clock and corresponds it to the DUT
        cocotb.fork(Clock(dut.s_axis_aclk, 16, units="ns").start())

        # Instantiation of the data bus which serves as the main input for the DUT (maps the signals).
        # Instantiation of the AxiStreamTransferSource (for loading and sending transfers)
        self.source = AxiStreamTransferSource(
            AxiStreamBusUnconstrained.from_prefix(dut, "s_axis"), dut.s_axis_aclk, dut.s_axis_aresetn, reset_active_level=True, areset=True)

    async def areset(self):
        self.dut.s_axis_aresetn.setimmediatevalue(1)
        await RisingEdge(self.dut.s_axis_aclk)
        await RisingEdge(self.dut.s_axis_aclk)
        self.dut.s_axis_aresetn.value = 0
        await RisingEdge(self.dut.s_axis_aclk)
        await RisingEdge(self.dut.s_axis_aclk)
        self.dut.s_axis_aresetn.value = 1
        await RisingEdge(self.dut.s_axis_aclk)
        await RisingEdge(self.dut.s_axis_aclk)


async def run_test(dut):

    tb = TB(dut)
    test_duration = 20
    # Define transfers values
    init_transfer = AxiStreamTransfer(name="init", tdata=BinaryValue(n_bits=64), tkeep=BinaryValue("10101010", n_bits=8), tvalid=BinaryValue(
        1, n_bits=1), tready=BinaryValue(1, n_bits=1), tlast=BinaryValue(0, n_bits=1))

    empty_transfer = AxiStreamTransfer(name="empty", tdata=BinaryValue(n_bits=64), tkeep=BinaryValue(n_bits=8), tvalid=BinaryValue(
        0, n_bits=1), tready=BinaryValue(1, n_bits=1), tlast=BinaryValue(0, n_bits=1))

    end_transfer = AxiStreamTransfer(name="end", tdata=BinaryValue(n_bits=64), tkeep=BinaryValue(n_bits=8), tvalid=BinaryValue(
        1, n_bits=1), tready=BinaryValue(1, n_bits=1), tlast=BinaryValue(1, n_bits=1))

    transfer_generator = gen_data_transfer()

    # Initialize bus
    dut.s_axis_tready.value = 1
    # tb.source.bus.tready.value = 1
    await tb.source.send(empty_transfer)
    await tb.areset()

    # 1 Packet. In-Queue transfers. Prepare the inputs cycle by cycle
    await tb.source.send(init_transfer)
    for i in range(test_duration-4):
        await tb.source.send(next(transfer_generator))

    # End transfer with tlast='1'
    await tb.source.send(end_transfer)

    # Leave the bus with tvalid='0'
    await tb.source.send(empty_transfer)

    # Run time of simulation
    tb.log.info("\n Run time... \n")
    sof = []
    names = []
    for i in range(test_duration):
        names.append(tb.source.bus.current_transfer.name)
        sof.append(dut.sof_out.value)
        await RisingEdge(dut.s_axis_aclk)
        tb.log.info(sof)
        tb.log.info(names)

    # Assert that signal 'sof' only goes high when the transfer that inits the frame is in the axis bus
    assert(sof == [1 if x == "init" else 0 for x in names])


def gen_data_transfer():
    """Predefined independent data transfer generator"""
    while True:
        yield AxiStreamTransfer(name="data", tdata=BinaryValue(n_bits=64), tkeep=BinaryValue(n_bits=8), tvalid=BinaryValue(
            1, n_bits=1), tready=BinaryValue(1, n_bits=1), tlast=BinaryValue(0, n_bits=1))


if cocotb.SIM_NAME:
    print("Simulation starts...")
    print(cocotb.SIM_NAME)
    factory = TestFactory(run_test)

    factory.generate_tests()
