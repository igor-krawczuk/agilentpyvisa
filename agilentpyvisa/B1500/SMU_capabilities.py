from logging import getLogger
from .helpers import format_command
exception_logger = getLogger(__name__+":ERRORS")
from .enums import *

class SweepUnit(object):

    def set_sweep_auto_abort(self, auto_abort):
        exception_logger.info("Setting GLOBAL parameter SweepAbort")
        return self.parent.write("WM {}".format(auto_abort))

class PulseUnit(object):

    def set_pulse_timing(self, hold, width, period):
        self.parent.write(
            format_command("PT",
                           hold,
                           width,
                           period))


class StaircaseSweepUnit(SweepUnit):

    def set_staircase_sweep_timing(
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
        self.set_staircase_sweep_timing(staircase_setup.hold, staircase_setup.delay)
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


class SingleMeasure(object):

    def set_measure_mode(mode,):
        """ Defines which measurement to perform on the channel. Not used for all measurements,
        check enums.py  or MeasureModes for a full list of measurements"""
        self.parent.write(
            "MM {}".format(",".join(["{}".format(x) for x in [mode, channel]])))

    def set_measure_side(channel, side):
        """ Specify whether the sensor should read on the current, voltage,
        compliance or force side. See MeasureSides"""
        self.parent.write("CMM {},{}".format(channel, side))

    def set_measure_range(channel, target, range):
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
                channel = channels[0]
                self.set_measure_mode(config.mode, channel)
                if config.mode not in set(
                        [MeasureModes.sampling, MeasureModes.quasi_pulsed_spot]):
                    self.set_measure_side(channel, config.side)
                    if config.mode not in set(
                            [MeasureModes.sampling, MeasureModes.quasi_pulsed_spot]):
                        self.set_measure_range(
                            channel, config.target, config.range)


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


class SpotUnit(SingleMeasure):

    def setup_spot_measure(self, measure_setup, channel=None):
        self._setup_xe_measure(measure_setup, channel)
