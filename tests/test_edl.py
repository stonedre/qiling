#!/usr/bin/env python3
#
# Cross Platform and Multi Architecture Advanced Binary Emulation Framework
#

import time
import unittest

from struct import pack
from typing import Callable

import sys
sys.path.append("..")

from qiling import Qiling
from qiling.const import QL_VERBOSE
from unicorn import *


def replace_function(ql: Qiling, addr: int, callback: Callable):
    def runcode(ql: Qiling):
        ret = callback(ql)
        ql.arch.regs.x0 = ret
        ql.arch.regs.pc = ql.arch.regs.x30  # lr

    ql.hook_address(runcode, addr)


def hook_mem_invalid(ql: Qiling, access: int, address: int, size: int, value: int, user_data):
    pc = ql.arch.regs.arch_pc

    info = {
        UC_MEM_WRITE:           f"invalid WRITE {address:#x} at {pc:#X}, data size = {size:d}, data value = {value:#x}",
        UC_MEM_READ:            f"invalid READ {address:#x} at {pc:#X}, data size = {size:d}",
        UC_MEM_FETCH:           f"UC_MEM_FETCH {address:#x} at {pc:#X}, data size = {size:d}",
        UC_MEM_READ_UNMAPPED:   f"UC_MEM_READ_UNMAPPED {address:#x} at {pc:#X}, data size = {size:d}",
        UC_MEM_WRITE_UNMAPPED:  f"UC_MEM_WRITE_UNMAPPED {address:#x} at {pc:#X}, data size = {size:d}",
        UC_MEM_FETCH_UNMAPPED:  f"UC_MEM_FETCH_UNMAPPED {address:#x} at {pc:#X}, data size = {size:d}",
        UC_MEM_WRITE_PROT:      f"UC_MEM_WRITE_PROT of {address:#x} at {pc:#X}, data size = {size:d}",
        UC_MEM_FETCH_PROT:      f"UC_MEM_FETCH_PROT of {address:#x} at {pc:#X}, data size = {size:d}",
        UC_MEM_FETCH_PROT:      f"UC_MEM_FETCH_PROT of {address:#x} at {pc:#X}, data size = {size:d}",
        UC_MEM_READ_AFTER:      f"UC_MEM_READ_AFTER of {address:#x} at {pc:#X}, data size = {size:d}"
    }

    print(info[access])

    return False


class TestAndroid(unittest.TestCase):
    def test_edl_arm64(self):
        test_binary = "../examples/rootfs/arm64_edl/bin/arm64_edl"
        rootfs = "../examples/rootfs/arm64_edl"

        ql = Qiling([test_binary], rootfs, verbose=QL_VERBOSE.DEBUG)

        ql.arch.enable_vfp()

        def devprg_time_usec(ql):
            current_milli_time = int(round(time.time() * 1000))
            ql.arch.regs.x0 = current_milli_time
            return current_milli_time

        def devprg_tx_blocking(ql):
            ptr = ql.arch.regs.x0
            plen = ql.arch.regs.x1
            data = ql.mem.read(ptr, plen)
            res=bytes(data)
            if b"response" in res:
                tmp=res.decode('utf-8').split("\n")
                if len(tmp)>2:
                    tmp=tmp[2].split("\"")
                    if len(tmp)>1:
                        ql.buf_out=tmp[1]
            return 0

        ql.hook_mem_invalid(hook_mem_invalid)
        replace_function(ql, 0x148595A0, devprg_time_usec)  # Register 0xC221000
        replace_function(ql, 0x1485C614, devprg_tx_blocking)  # Function being used by UART in DP_LOGI

        ql.arch.regs.sp = 0x146B2000  # SP from main
        xml_buffer_addr = 0x14684E80  # We extracted that from devprg_get_xml_buffer
        device_serial_addr = 0x148A8A8C
        device_serial = pack("<Q", 0x1337BABE)
        uart_data = b"<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n<data>\n<nop /></data>\x00"
        ql.arch.regs.x0 = xml_buffer_addr
        ql.arch.regs.x1 = len(uart_data)
        ql.mem.write(xml_buffer_addr, uart_data)
        ql.mem.write(device_serial_addr, device_serial)
        handle_xml_addr_start=0x14857C94
        handle_xml_addr_end=0x14857D4C
        ql.run(begin=handle_xml_addr_start, end=handle_xml_addr_end)

        self.assertEqual("ACK", ql.buf_out)

        del ql


if __name__ == "__main__":
    unittest.main()
