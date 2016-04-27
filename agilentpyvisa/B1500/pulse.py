from logging import getLogger
from .helpers import format_command
from .loggers import exception_logger,write_logger, query_logger
from .enums import *
class PulseUnit(object):
    """ Shared Functionality of PulsedSpot and PulsedSweep"""

    def set_pulse_timing(self, hold, width, period):
        """ Sets up the pulse timing parameters for SMU pulsed sweep and spot"""
        self.parent.write(
            format_command("PT",
                           hold,
                           width,
                           period))

class PulsedSpotUnit(PulseUnit):

    def set_pulse_spot_voltage(
        self,
        channel,
        input_range,
        base,
        peak,
     compliance):
        """ Voltage pulse configuration"""
        return self.parent.write(
            format_command(
                "PV",
                channel,
                input_range,
                base,
                peak,
                compliance))

    def set_pulse_spot_current(
        self,
        channel,
        input_range,
        base,
        pulse,
     compliance):
        """ Current pulse configuration"""
        return self.parent.write(
            format_command(
                "PI",
                channel,
                input_range,
                base,
                pulse,
                compliance))

    def setup_pulsed_spot(self, channel, pulse_setup):
        """Sets up timing and amplitude of the pulsed spot"""
        self.set_pulse_timing(pulse_setup.hold,pulse_setup.width,pulse_setup.period)
        if pulse_setup.input == Inputs.V:
            return self.set_pulse_spot_voltage(
                channel,
                pulse_setup.input_range,
                pulse_setup.base,
                pulse_setup.peak,
                pulse_setup.compliance)
        else:
            return self.set_pulse_spot_current(
                channel,
                pulse_setup.input_range,
                pulse_setup.base,
                pulse_setup.peak,
                pulse_setup.compliance)


