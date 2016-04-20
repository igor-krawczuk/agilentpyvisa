from logging import getLogger
from .helpers import format_command
exception_logger = getLogger(__name__+":ERRORS")
from .enums import *

from .search import BinarySearchUnit,LinearSearchUnit
from .sweep import SweepUnit, StaircaseSweepUnit
from .pulse import PulseUnit,PulsedSpotUnit
from .dcforce import DCForceUnit
from .pulsedsweep import PulsedSweepUnit

class SingleMeasure(object):

    def set_measure_side(self,channel, side):
        """ Specify whether the sensor should read on the current, voltage,
        compliance or force side. See MeasureSides"""
        self.parent.write("CMM {},{}".format(channel, side))

    def set_measure_range(self,channel, target, range):
        """ Sets measure ranges out of available Ranges. The less range changes,
        the faster the measurement. Thus the spees increases from full_auto to
        limited to fixed. See MeasureRanges_X for availble values"""
        if target == Inputs.V:
            self.parent.write(
                "RV {},{}".format(
                    channel,
                    range))  # sets channel adc type
        else:
            self.parent.write(
                "RI {},{}".format(
                    channel,
                    range))  # sets channel adc type

    def _setup_xe_measure(self,config, channel=None):
        """ Configures most XE triggered measurements. """
        if not channel:
            if len(self.channels) > 1:
                raise ValueError(
                    "Multiple channels founds on Slot {}, please specifiy one of {}".format(
                        self.slot, self.channels))
            else:
                channel = self.channels[0]
        if config.mode not in tuple([MeasureModes.sampling, MeasureModes.quasi_pulsed_spot]):
            self.set_measure_side(channel, config.side)
        if config.mode not in tuple([MeasureModes.sampling, MeasureModes.quasi_pulsed_spot]):
            self.set_measure_range(channel, config.target, config.range)


class SpotUnit(SingleMeasure):

    def setup_spot_measure(self, measure_setup, channel=None):
        self._setup_xe_measure(measure_setup, channel)
