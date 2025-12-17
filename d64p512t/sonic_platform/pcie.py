########################################################################
#
# D64P512T
#
# Module contains a platform specific implementation of SONiC Platform
# Base PCIe class
#
########################################################################

try:
    from sonic_platform.component import Component
    from sonic_platform_base.sonic_pcie.pcie_common import PcieUtil
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class Pcie(PcieUtil):
    """Platform-specific PCIe class"""

    def __init__(self, platform_path):
        PcieUtil.__init__(self, platform_path)
        self._conf_rev = "1"
