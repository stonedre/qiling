#!/usr/bin/env python3
# 
# Cross Platform and Multi Architecture Advanced Binary Emulation Framework
#

from functools import cached_property

from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS32, UC_MODE_BIG_ENDIAN, UC_MODE_LITTLE_ENDIAN
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_BIG_ENDIAN, CS_MODE_LITTLE_ENDIAN
from keystone import Ks, KS_ARCH_MIPS, KS_MODE_MIPS32, KS_MODE_BIG_ENDIAN, KS_MODE_LITTLE_ENDIAN

from qiling import Qiling
from qiling.const import QL_ENDIAN
from qiling.arch.arch import QlArch
from qiling.arch.mips_const import *

class QlArchMIPS(QlArch):
    def __init__(self, ql: Qiling):
        super().__init__(ql)

        reg_maps = (
            reg_map,
            reg_map_afpr128
        )

        for reg_maper in reg_maps:
            self.ql.reg.expand_mapping(reg_maper)

        self.ql.reg.register_sp(reg_map["sp"])
        self.ql.reg.register_pc(reg_map["pc"])

    @cached_property
    def uc(self) -> Uc:
        endian = {
            QL_ENDIAN.EB: UC_MODE_BIG_ENDIAN,
            QL_ENDIAN.EL: UC_MODE_LITTLE_ENDIAN
        }[self.ql.archendian]

        return Uc(UC_ARCH_MIPS, UC_MODE_MIPS32 + endian)

    @cached_property
    def disassembler(self) -> Cs:
        endian = {
            QL_ENDIAN.EL : CS_MODE_LITTLE_ENDIAN,
            QL_ENDIAN.EB : CS_MODE_BIG_ENDIAN
        }[self.ql.archendian]

        return Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 + endian)

    @cached_property
    def assembler(self) -> Ks:
        endian = {
            QL_ENDIAN.EL : KS_MODE_LITTLE_ENDIAN,
            QL_ENDIAN.EB : KS_MODE_BIG_ENDIAN
        }[self.ql.archendian]

        return Ks(KS_ARCH_MIPS, KS_MODE_MIPS32 + endian)
