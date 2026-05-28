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

from .pcells.contact_pcell import ContactPCell
from .pcells.mosfet_pcell import MOSFETPCell
from .pcells.resistor_pcell import ResistorPCell
from .pcells.diode_pcell import DiodePCell
from .pcells.capacitor_pcell import CapMOSPCell, CapMIMPCell


class gf180_pcells(pya.Library):
    """Native PCell library for GF180MCU.

    Registered as "gf180_pcells".  Use together with the
    gf180mcu (gdsfactory-based) and gf180mcu_klayoutapi libraries.
    """

    def __init__(self):
        self.description = "GF180MCU Native PCells"

        self.layout().register_pcell("MOSFET", MOSFETPCell())
        self.layout().register_pcell("Resistor", ResistorPCell())
        self.layout().register_pcell("Contact", ContactPCell())
        self.layout().register_pcell("Diode", DiodePCell())
        self.layout().register_pcell("CapMOS", CapMOSPCell())
        self.layout().register_pcell("CapMIM", CapMIMPCell())

        self.register("gf180_pcells")
