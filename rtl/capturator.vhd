-- Copyright (c) 2021 Carlos Megías

-- Permission is hereby granted, free of charge, to any person obtaining a copy
-- of this software and associated documentation files (the "Software"), to deal
-- in the Software without restriction, including without limitation the rights
-- to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
-- copies of the Software, and to permit persons to whom the Software is
-- furnished to do so, subject to the following conditions:

-- The above copyright notice and this permission notice shall be included in
-- all copies or substantial portions of the Software.

-- THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
-- IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY
-- FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
-- AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
-- LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
-- OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
-- THE SOFTWARE.

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use work.vhdl_utils_lib_pkg.all;

entity capturator is
    Port ( 
        s_axis_aclk             : in std_logic;                                                                   -- Clock signal                                         
        s_axis_aresetn          : in std_logic;                                                                   -- Reset signal    
        s_axis_tready           : in std_logic;                                                                   -- AXIS BUS
        s_axis_tvalid           : in std_logic;                                                                   -- AXIS BUS
        s_axis_tlast            : in std_logic;                                                                   -- AXIS BUS
        sof_out                 : out std_logic                                                                   -- START OF FRAME 
    );
end capturator;

architecture Behavioral of capturator is
    signal state: capturator_fsm;
    signal sof: std_logic;
    signal valid_sof: std_logic;
    signal eof: std_logic;
begin
    -- Finite State Machine of the module: fron IDLE to PARSING and viceversa (sof -> eof -> sof ...)
    FSM: process(s_axis_aclk)
    begin
        if(rising_edge(s_axis_aclk)) then
            if(s_axis_aresetn = '0') then
                state <= IDLE;
            else
                case state is
                    when IDLE =>
                        if(sof = '1') then
                            state <= PARSING;
                        else
                            state <= IDLE;
                        end if;
                    when PARSING =>
                        if(eof = '1') then
                            state <= IDLE;
                        else
                            state <= PARSING;
                        end if;
                    when others =>
                        state <= PARSING;                        
                end case;
            end if;
        end if;
    end process;
    
    -- Process that helps in SOF detectection. valid_sof is '1' in the next cycle where tvalid, tready and not tlast are '1'. It is '0' 
    -- when whichever of the aforementioned is not '1'.
    detect_SOF: process(s_axis_aclk)
    begin
        if(rising_edge(s_axis_aclk)) then
            if(s_axis_aresetn = '0') then
                valid_sof <= '0';
            else
                valid_sof <= s_axis_tvalid and s_axis_tready and not(s_axis_tlast);
            end if;
        end if;
    end process;
    -- If s_axis_last was '1' in the previous cycle, valid_sof is '0' in the current one. There are two options: 1. If no packet is coming in, in the current cycle, tvalid is '0', what makes sof at '1'. 
    -- 2. If a packet is coming in just after the previous one, tvalid is '1' and with (not valid_sof) at '1', sof is '1', detecting correctly the start of the consecutive packet to the previous one.
    sof <= s_axis_tvalid and s_axis_tready and (not valid_sof) when state = IDLE else '0';
    
    -- To detected the end of the frame (packet): '1' if the frame corresponds to the last one of the packet and it is valid (and tready high).
    eof <= s_axis_tvalid and s_axis_tready and s_axis_tlast;                              
    sof_out <= sof;                            
end Behavioral;
