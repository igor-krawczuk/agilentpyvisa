from logging import getLogger
from .helpers import format_command
exception_logger = getLogger(__name__+":ERRORS")
from .enums import *
from .pulse import PulseUnit
from .sweep import SweepUnit

class PulsedSweepUnit(PulseUnit, SweepUnit):

    def set_pulse_sweep_voltage(
        self,
        channel,
        input_range,
        base,
        start,
        stop,
        step,
        compliance,
        sweepmode=SweepMode.linear_up_down,
      power_comp=None):
        return self.parent.write(format_command("PWV",
                                                channel,
                                                sweepmode,
                                                input_range,
                                                base,
                                                start,
                                                stop,
                                                step,
                                                compliance,
                                                power_comp
                                                ))

        def set_pulse_sweep_current(
                self,
                channel,
                input_range,
                base,
                start,
                stop,
                step,
                compliance,
                sweepmode=SweepMode.linear_up_down,
                power_comp=None):
            return self.parent.write(format_command("PWI",
                                                    channel,
                                                    sweepmode,
                                                    input_range,
                                                    base,
                                                    start,
                                                    stop,
                                                    step,
                                                    compliance,
                                                    power_comp
                                                    )
                                     )

    def setup_pulsed_sweep(self, channel, sweep_setup):
        self.set_pulse_timing(
            sweep_setup.pulse_hold,
            sweep_setup.pulse_width,
            sweep_setup.pulse_period)
        self.set_sweep_auto_abort(sweep_setup.auto_abort)
        self.set_sweep_timing(sweep_setup.sweep_hold,sweep_setup.sweep_delay)
        if sweep_setup.input == Inputs.V:
            self.set_pulse_sweep_voltage(
                channel,
                sweep_setup.sweepmode,
                sweep_setup.input_range,
                sweep_setup.base,
                sweep_setup.start,
                sweep_setup.stop,
                sweep_setup.step,
                sweep_setup.compliance,
            )
        else:
            self.set_pulse_sweep_current(
                channel,
                sweep_setup.sweepmode,
                sweep_setup.input_range,
                sweep_setup.base,
                sweep_setup.start,
                sweep_setup.stop,
                sweep_setup.step,
                sweep_setup.compliance,
                sweep_setup.power_comp
            )
