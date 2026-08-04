# Copyright 2022 GlobalFoundries PDK Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""GF180MCU native PCell library registration.

Provides a pya.Library subclass that registers all native PCells
under the library name "gf180_pcells".
"""

import pya

from .pcells.resistor_pcell import ResistorPCell
from .pcells.guard_ring_pcell import GuardRingPCell


class gf180_pcells(pya.Library):
    """Native PCell library for GF180MCU.

    Registered as "gf180_pcells".  Use together with the
    gf180mcu (gdsfactory-based) and gf180mcu_klayoutapi libraries.
    """

    def __init__(self):
        self.description = "GF180MCU Native PCells"

        self.layout().register_pcell("Resistor", ResistorPCell())
        self.layout().register_pcell("GuardRing", GuardRingPCell())

        self.register("gf180_pcells")
