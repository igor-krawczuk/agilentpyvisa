from collections import namedtuple
from .enums import *


class DCForce(
              namedtuple(
                  "__DCForce",
                  ["input", # "I" or "V" for voltage and current respectively
                   "input_range",
                   "value",
                   "compliance",
                   "polarity",
                   "compliance_range",  # if not set, uses minimum range that will cover. If set, limited auto never goes below
                ])):
    """ Specifies a Channel setup, in which we force  a DC current or voltage.
    input -  Inputs.I or Inputs.V
    input_range - smallest InputRange_X covering the value, full_auto by default, needs to take into account module
    value - the value we force, in A or V
    compliance - maximum response Voltage or Current. Relatively slow, so use external safeguards of testing delicate units
    polarity - whether the compliance limit has the same polarity as the forced value or not
    compliance_range - smallest InputRange_X Covering the compliance"""
    def __new__(cls, input,value, compliance,input_range=InputRanges_I.full_auto,  polarity=Polarity.like_input, compliance_range=None):
        return super(DCForce, cls).__new__(cls,input,input_range, value, compliance, polarity,
                   compliance_range)


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
])):
    """ Specifies a Channel setup, in which we force  a DC current or voltage.
    input -  Inputs.I or Inputs.V
    sweepmode - linear/log, start-stop or start-stop-start
    input_range - smallest InputRange_X covering the value, full_auto by default, needs to take into account module
    start - the start value of the sweep
    stop - the stop value of the sweep
    step - steps of the sweep 1-100001
    compliance - maximum response Voltage or Current. Relatively slow, so use external safeguards of testing delicate units
    power_comp - ??? see 4-235 of manual
    auto_abort - whether or not we should abort the test on any irregularities
    """
    def __new__(cls, input, input_range, start, stop, step, compliance,  sweepmode=SweepMode.linear_up_down, auto_abort=AutoAbort.enabled, power_comp=None, hold=0, delay=0):
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
    def __new__(cls, input,input_range,  base, pulse,width,hold, compliance, period=PulsePeriod.minimum,):
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
    def __new__(cls,input,input_range,base,start,stop,step,compliance, hold, width, period=PulsePeriod.minimum, auto_abort=AutoAbort.enabled,sweepmode=SweepMode.linear_up_down):
        return super(PulseSweep, cls).__new__(cls,input,sweepmode,input_range,base,start,stop,step,compliance, auto_abort, hold, width, period)






