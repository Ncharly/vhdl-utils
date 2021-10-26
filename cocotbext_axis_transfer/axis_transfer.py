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

from cocotb.binary import BinaryValue
from cocotb.triggers import RisingEdge
from cocotbext.axi.stream import (StreamBase, StreamBus, StreamPause,
                                  StreamSource, StreamTransaction)


class AxiStreamTransfer(StreamTransaction):
    """ Class for transfer instantiation for the Axi Stream Bus at bit level. Modified version of the StreamTransaction class from cocotbext-axi library """
    _signals = ["tdata", "tkeep", "tvalid", "tready",
                         "tlast", "tid", "tdest", "tuser"]

    def __init__(self, name=None, tdata=BinaryValue, tkeep=BinaryValue, tvalid=BinaryValue, tready=BinaryValue, tlast=BinaryValue, tid=BinaryValue, tdest=BinaryValue, tuser=BinaryValue):
        super().__init__(tdata=tdata, tkeep=tkeep, tvalid=tvalid,
                         tready=tready, tlast=tlast, tid=tid, tdest=tdest, tuser=tuser)

        self.name = name


class AxiStreamBusUnconstrained(StreamBus):
    """ Slightly modified version of the StreamBus class from cocotbext-axi library, not imposing any constrain in the present signals for the bus """
    _signals = []
    _optional_signals = ["tdata", "tkeep", "tvalid", "tready",
                         "tlast", "tid", "tdest", "tuser"]
    current_transfer = AxiStreamTransfer(name="X")

    def __init__(self, entity=None, prefix=None, **kwargs):
        super().__init__(entity, prefix, **kwargs)


class AxisStreamTransferBase(StreamBase):
    """ Base class for unconstrained transfers. Based on the StreamBase class from cocotbext-axi library. Added aresetn parameter """
    _signals = []
    _optional_signals = ["tdata", "tkeep", "tvalid", "tready",
                         "tlast", "tid", "tdest", "tuser"]
    _type = "base"
    current_transfer = None

    _transaction_obj = AxiStreamTransfer
    _bus_obj = AxiStreamBusUnconstrained

    def __init__(self, bus, clock, reset=None, reset_active_level=True, areset=True, *args, **kwargs):
        self.areset = areset

        super().__init__(bus, clock, reset,
                         reset_active_level, *args, **kwargs)

        self.log.info("AXI stream transfer %s signals:", self._type)

        for sig in sorted(list(set().union(self.bus._signals, self.bus._optional_signals))):
            if hasattr(self.bus, sig):
                self.log.info("  %s width: %d bits", sig,
                              len(getattr(self.bus, sig)))
            else:
                self.log.info("  %s: not present", sig)

    def _update_reset(self):
        new_state = self._local_reset or self._ext_reset
        if self._reset_state != new_state:
            self._reset_state = new_state
            if(self.areset):
                self._handle_reset(not new_state)
            else:
                self._handle_reset(new_state)

    def print_bus(self):
        self.log.info("Bus state signals:")
        for sig in self.bus._signals:
            self.log.info("\t" + sig + ": %s",
                          eval("self.bus." + sig + ".value"))


class AxiStreamTransferSource(AxisStreamTransferBase, StreamSource, StreamPause):
    """ Class which serves as transfers initiator. All the transfers are independent from the values of the signals """
    _type = "source"

    def __init__(self, bus, clock, reset=None, reset_active_level=True, areset=True, *args, **kwargs):
        super().__init__(bus, clock, reset, reset_active_level, areset, *args, **kwargs)

    def _handle_reset(self, state):
        super()._handle_reset(state)

        if state:
            for sig in self.bus._signals:
                exec("self.bus." + sig + ".value=0")

            if self.current_transfer:
                self.log.warning(
                    "Flushed transmit transfer during reset: %s", self.current_transfer)
                self.current_transfer = None

    async def _run(self):
        transfer = None
        self.active = False
        print("Run starts...")
        self.log.info("Run starts...")

        while True:
            await RisingEdge(self.clock)

            self.log.info("Run cycle...")
            self.print_bus()

            if transfer is None and not self.queue.empty():
                transfer = self.queue.get_nowait()
                self.dequeue_event.set()
                self.current_transfer = transfer
                self.log.info("Next transfer: %s",
                              transfer.name)
                self.active = True

            if transfer and not self.pause:
                self.bus.drive(transfer)
                self.bus.current_transfer = transfer
                transfer = None
                self.current_transfer = None

            else:
                if hasattr(self.bus, "tvalid"):
                    self.bus.tvalid.value = 0
                if hasattr(self.bus, "tlast"):
                    self.bus.tlast.value = 0
                self.active = bool(transfer)
                if not transfer and self.queue.empty():
                    self.idle_event.set()
