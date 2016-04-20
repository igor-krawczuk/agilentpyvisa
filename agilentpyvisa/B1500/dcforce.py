from logging import getLogger
from .helpers import format_command
exception_logger = getLogger(__name__+":ERRORS")
from .enums import *

class DCForceUnit(object):
    def force_voltage(self,
            channel,
            input_range,
            value,
            compliance,
            polarity=None,
            compliance_range=None):
        return self.parent.write(format_command("DV",
                                                channel,
                                                input_range,
                                                value,
                                                compliance,
                                                polarity,
                                                compliance_range,)
                                    )
    def setup_dc_force(self, channel, force_setup):
        """ Sets up the channel configuration for forcing a DC force or current."""
        if force_setup.input_range not in self.input_ranges:
            raise ValueError(
                "Input range {} of channel {} not available in installed module {}".format(
                    repr(
                        force_setup.input_range),
                    channel,
                    self))
        if force_setup.input == Inputs.V:
            return self.force_voltage(
                channel,
                force_setup.input_range,
                force_setup.value,
                force_setup.compliance,
                force_setup.polarity,
                force_setup.compliance_range,
            )
        elif force_setup.input == Inputs.I:
            return self.force_current(
                channel,
                force_setup.input_range,
                force_setup.value,
                force_setup.compliance,
                force_setup.polarity,
                force_setup.compliance_range,
            )
        else:
            raise ValueError("Unkown Input {}".format(force_setup.input))

    def force_current(
            self,
            channel,
            input_range,
            value,
            compliance,
            polarity=None,
            compliance_range=None):
        return self.parent.write(
            format_command(
                "DI",
                channel,
                input_range,
                value,
                compliance,
                polarity,
                compliance_range,
                ))
