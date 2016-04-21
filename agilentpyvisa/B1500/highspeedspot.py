from logging import getLogger
exception_logger = getLogger(__name__+":ERRORS")
from .enums import *
from .force import *
from .helpers import format_command

class HighSpeedSpotUnit(object):

"""
DV gate
DV source
SSP
ACT
if phase compensation
ADJ
ADJ?
endif
FC
ACV
if open correction
DCORR
CORR?
CORRST x,1,1 open correciton on
CORRST x,2,0 short correction off
CORRST x,3,0 load correction off
IMP
LMN
DCV
TSR
TTC
TSQ

    def highspeed_spot_setup(self, channel_number, highspeed_setup):
        if highspeed_setup.target == Targets.C:
            pass  # IMP, FC?

    def highspeed_spot(self, channel_number, highspeed_setup):
        if highspeed_setup.target == Targets.I:
            self.write(
                "TTI {},{}".format(
                    channel_number,
                    highspeed_setup.irange))
        elif highspeed_setup.target == Targets.V:
            self.write(
                "TTV {},{}".format(
                    channel_number,
                    highspeed_setup.vrange))
        elif highspeed_setup.target == Targets.IV:
            self.write(
                "TTIV {},{}".format(
                    channel_number,
                    highspeed_setup.irange,
                    highspeed_setup.vrange))
        elif highspeed_setup.target == Targets.C:
            if highspeed_setup.mode == HighSpeedMode.fixed:
                self.write(
                    "TTC {},{},{}".format(
                        channel_number,
                        highspeed_setup.mode,
                        highspeed_setup.Rrange))
            else:
                self.write(
                    "TTC {},{}".format(
                        channel_number,
                        highspeed_setup.mode))
