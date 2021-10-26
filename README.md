# Cocotbext-axis-transfer

## Introduction

Collection of VHDL components. All these components have been designed to be parametrizable and have their corresponding tests running using the cocotb and cocotbext-axi libraries, together with the small library also included in this repository called: cocotbext-axis-transfer. This last one is a collection of simulation models for transfers/transactions of the AXI Streaming bus. 

## VHDL components: /rtl

### capturator module
AXIS module that detects the init of a frame and triggers a pulse for one cycle. It implements the interface AXIS as input (not all the signals are needed, but they me be added to completely acommodate the interface).

## Simulation

Two things are needed: the python environment and the simulator.

### Python environment

For the installation of all the python dependencies required to run the tests associated with each VHDL module the [poetry](https://python-poetry.org/) tool is recommended. Just run:
```
poetry shell
```
to create and activate a virtual environment. And run:
```
poetry install
```
to install all the dependencies of the project.

### Simulators

The simulator indicated in the test files (makefile) for the VHDL components is [GHDL](https://github.com/ghdl/ghd), but another can be installed. Similar for happens to simulate verilog components.


Once the Python environment is set and the simulator is installed, the testbenches are ready to run.