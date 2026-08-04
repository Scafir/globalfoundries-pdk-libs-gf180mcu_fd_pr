"""
pcells/resistor_pcell.py

ResistorPCell: KLayout PCell wrapper for the diffusion resistor device.
"""
import pya as kdb

from ..devices.guard_ring import GuardRingParams, GuardRing
from ..pcells.generic_pcell import GenericPCell


class GuardRingPCell(GenericPCell):
    param_class = GuardRingParams
    """KLayout PCell for the diffusion resistor with dynamic overrides."""
    
    def make(self, p: GuardRingParams):
        return GuardRing(p)

