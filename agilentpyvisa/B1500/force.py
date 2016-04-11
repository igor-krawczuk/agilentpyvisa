from collections import namedtuple
from .enums import *
from .helpers import (minCover_I, minCover_V)


class DCForce(
              namedtuple(
                  "__DCForce",
                  ["input", # "I" or "V" for voltage and current respectively
                   "input_range",
                   "value",
                   "compliance",
                   "polarity",
                   "compliance_range",  # if not set, uses minimum range that will cover. If set, limited auto never goes below
                   "power_comp",
                ])):
    def __new__(cls, input, value, compliance,input_range=None, polarity=Polarity.like_input, compliance_range=None, power_comp=None):
        if input_range is None:
            if input==Inputs.I:
                    input_range = minCover_I(value)
            else:
                    input_range = minCover_V(value)
        return super(DCForce, cls).__new__(cls,input,input_range, value, compliance, polarity,
                   compliance_range, power_comp)


class StaircaseSweep(
    namedtuple(
        "__StaircaseSweep",
        ["input",
         "sweepmode",  # WV
         "input_range", # WM, leaving post parameter aside because abort should reset imo
         "start",
         "stop",
         "step",
         "compliance",
         "power_comp",  # not set by default
         "auto_abort",  # aborting on compliance reached, overflow on AD,Oscilation on any channel, yes no?
         "hold",     # 0 - 655.350 in s, 10 ms steps, wait before measuring starts
         "delay",   # 0 - 65.5350 in s,  0.1 ms steps, wait before measuring starts
])):  #  WT
    def __new__(cls, input, start, stop, step, compliance, input_range=None, sweepmode=SweepMode.linear_up_down, auto_abort=AutoAbort.enabled, power_comp=None, hold=0, delay=0):
        if input_range is None:
            if input == Inputs.I:
                input_range = minCover_I(start, stop)
            elif input == Inputs.V:
                input_range = minCover_V(start, stop)
        return super(StaircaseSweep, cls).__new__(cls,input, sweepmode, input_range, start, stop, step, compliance, power_comp, auto_abort, hold, delay)

class SPGU(namedtuple("__SPGU",[
    "wavemode",
    "output_mode",
    "condition",
    "switch_state",
    "switch_normal",
    "switch_delay",
    "switch_width",
    "loadZ",
    "pulse_period",
    "pulse_level_sources",
    "pulse_base",
    "pulse_peak",
    "pulse_src",
    "timing_source",
    "pulse_delay",
    "pulse_width",
    "pulse_leading",
    "pulse_trailing",
    ])):
    def __new__(cls,
                pulse_base,
                pulse_peak,
                pulse_width,
                pulse_level_sources=SPGULevels.Signal1_2_levels,
                pulse_src=SPGUSignals.Signal1,
                timing_source=SPGUSignals.Signal1,
                pulse_period=None,
                pulse_delay=0,
                pulse_leading=2e-8,
                pulse_trailing=2e-8,
                wavemode=SPGUModes.Pulse,
                output_mode=SPGUOutputModes.count,
                condition=1,
                loadZ=SPGUOutputImpedance.full_auto,  # that to set it automatically with CORRSER, otherwise 0.1 to 1M
                switch_state=SPGUSwitch.enabled,
                switch_normal=SPGUSwitchNormal.open,
                switch_delay=0,
                switch_width=1e-7,
                ):
        if pulse_period is None:
            pulse_period = pulse_width + 2e-8
        if pulse_period < 2e-8 or pulse_period > 10:
            raise ValueError("Pulse period should be between 2e-8 s and 10 s, is {}s".format(pulse_period))
        if any([x < -40 or x > 40 for x in [pulse_base, pulse_peak]]):
            raise ValueError("Voltage must stay between -40 V and 40 V, base is {} and peak is {}".format( pulse_base, pulse_peak))
        if switch_width<1e-7 or switch_width>pulse_period-switch_delay:
            raise ValueError("switch width must be between 1e-7 and pulse_period-delay s")
        if switch_delay<0 or switch_delay>pulse_period-1e-7:
            raise ValueError("switch delay must be between 0 and pulse_period-1e-7 s")
        if pulse_width<1e-8 or pulse_width>pulse_period-1e-8:
            raise ValueError("pulse width must be between 1e-7 and pulse_period-1e-8({}-1e-8={}) s, is {}".format(pulse_period,  pulse_period-1e-8, pulse_width))
        if pulse_delay<0 or pulse_delay>pulse_period-2e-8:
            raise ValueError("pulse delay must be between 0 and pulse_period-2e-8 s")
        if any([x >0.4 or x <8e-9 for x in [pulse_leading, pulse_trailing]]):
            raise ValueError("Pulse lead/trail must be in the rango 8e-9 to 0.4")
        return super(SPGU, cls).__new__(cls,
                                        wavemode,
                                        output_mode,
                                        condition,
                                        switch_state,
                                        switch_normal,
                                        switch_delay,
                                        switch_width,
                                        loadZ,
                                        pulse_period,
                                        pulse_level_sources,
                                        pulse_base,
                                        pulse_peak,
                                        pulse_src,
                                        timing_source,
                                        pulse_delay,
                                        pulse_width,
                                        pulse_leading,
                                        pulse_trailing,
                                        )

# Everything below still needs review
class PulsedSpot(namedtuple("__PulsedSpot", [
         "input",  # V, I
         "input_range", # PV range
         "base",  # PV
         "pulse",  # PV
         "compliance",
         "hold",     # 0 - 655.350 in s, 10 ms steps, wait before measuring starts
         "width",   # # pulse in seconds , see PT doc for ranges
         "period",  # 5-5000 in ms or one of PulsePeriod.{minimum,conservative} default PulsePeriod.minimum NOTE: gets multiplited by 10 to get resolutio
        ])):
    def __new__(cls, input,  base, pulse,width,hold, compliance,input_range=None, period=PulsePeriod.minimum,):
        if input_range is None:
            if input == Inputs.I:
                input_range = minCover_I(base, pulse)
            elif input == Inputs.V:
                input_range = minCover_V(base, pulse)

        return super(PulsedSpot, cls).__new__(cls, input,input_range,base, pulse,compliance,hold, width,  period)

### BELOW BE STUBS

class PulseSweep(
    namedtuple(
        "__PulseSweep",
        [
         "input",
         "sweepmode",
         "input_range", #
         "base",
         "start",
         "stop",
         "step",
         "compliance",
         "power_comp",  # not set by default
         "auto_abort", # WM, leaving post parameter aside because abort should reset imo
         "hold",     # 0 - 655.350 in s, 10 ms steps, wait before measuring starts
         "width",   # # pulse in seconds , see PT doc for ranges
         "period",  # 5-5000 in ms or one of PulsePeriod.{minimum,conservative} default PulsePeriod.minimum NOTE: gets multiplited by 10 to get resolution
         ])):  #  WT
    def __new__(cls,input,base,start,stop,step,compliance, hold, width, period=PulsePeriod.minimum,input_range=None, auto_abort=AutoAbort.enabled,sweepmode=SweepMode.linear_up_down):
        if input_range is None:
            if input == Inputs.I:
                input_range = minCover_I(start, stop)
            elif input == Inputs.V:
                input_range = minCover_V(start, stop)

        return super(PulseSweep, cls).__new__(cls,input,sweepmode,input_range,base,start,stop,step,compliance, auto_abort, hold, width, period)






