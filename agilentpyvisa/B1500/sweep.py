from logging import getLogger
from .helpers import format_command
exception_logger = getLogger(__name__+":ERRORS")
from .enums import *

class SweepUnit(object):
    """ Common functionality of pulsed sweep and staircase weep"""

    def set_sweep_auto_abort(self, auto_abort):
        exception_logger.info("Setting GLOBAL parameter SweepAbort")
        return self.parent.write("WM {}".format(auto_abort))

    def set_sweep_timing(
        self,
        hold,
        delay,
        step_delay=None,
     output_trigger_delay=None):
        exception_logger.info("Setting GLOBAL parameter SweepTiming")
        return self.parent.write(
            format_command(
                "WT",
                hold,
                delay,
                step_delay,
                output_trigger_delay))

class StaircaseSweepUnit(SweepUnit):

    def set_staircase_sweep_current(
        self,
        channel,
        sweepmode,
        input_range,
        start,
        stop,
        step,
        Vcomp,
     power_comp):
        return self.parent.write(
            format_command(
                "WI",
                channel,
                sweepmode,
                input_range,
                start,
                stop,
                stop,
                Vcomp,
                power_comp))

    def set_staircase_sweep_voltage(
        self,
        channel,
        sweepmode,
        input_range,
        start,
        stop,
        step,
        Icomp,
     power_comp):
        return self.parent.write(
            format_command(
                "WV",
                channel,
                sweepmode,
                input_range,
                start,
                stop,
                stop,
                Icomp,
                power_comp))

    def setup_staircase_sweep(self, channel, staircase_setup):
        if channel not in self.channels:
            raise ValueError(
                "Trying to set nonexistent channel {} in SMU on slot {}".format(
                    channel, self.slot))
        self.measurements[channel] = staircase_setup
        self.set_sweep_timing(staircase_setup.hold, staircase_setup.delay)
        self.set_sweep_auto_abort(staircase_setup.auto_abort)
        if staircase_setup.input == Inputs.V:
            return self.set_staircase_sweep_voltage(
                channel,
                staircase_setup.sweepmode,
                staircase_setup.input_range,
                staircase_setup.start,
                staircase_setup.stop,
                staircase_setup.step,
                staircase_setup.compliance,
                staircase_setup.power_comp)
        else:
            return self.set_staircase_sweep_current(
                channel,
                staircase_setup.sweepmode,
                staircase_setup.input_range,
                staircase_setup.start,
                staircase_setup.stop,
                staircase_setup.step,
                staircase_setup.compliance,
                staircase_setup.power_comp)

    def setup_staircase_measure(self, channel, measure_setup):
        raise NotImplementedError()
