#!/usr/bin/env python3

try:
    from sonic_platform_base.sonic_pcie.pcie_common import PcieUtil
except ImportError as e:
    raise ImportError(str(e) + "- required module not found") from e


class Pcie(PcieUtil):
    """Platform-specific Pcie class"""

    def __init__(self, platform_path):
        PcieUtil.__init__(self, platform_path)
