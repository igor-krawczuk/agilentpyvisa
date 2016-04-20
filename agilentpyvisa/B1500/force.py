from collections import namedtuple
from collections import Sequence
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
    def __new__(cls, input, value, compliance,input_range=InputRanges_I.full_auto,  polarity=Polarity.like_input, compliance_range=None):
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
    """ Specifies a Channel setup, in which we force  a staircase (start-stop or start-stop-start) of DC current or voltage.
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
    "levels",
    "pulse_base",
    "pulse_peak",
    "sources",
    "pulse_delay",
    "pulse_width",
    "pulse_leading",
    "pulse_trailing",
    ])):
    def __new__(cls,
                pulse_base,
                pulse_peak,
                pulse_width,
                levels=SPGULevels.Signal1_2_levels,
                sources=SPGUSignals.Signal1,
                pulse_period=None,
                pulse_delay=[0],
                pulse_leading=[2e-8],
                pulse_trailing=[2e-8],
                wavemode=SPGUModes.Pulse,  # Pulses or Arbitrary Linear Wavve
                output_mode=SPGUOutputModes.count, ## Free run, number of pulses or duration
                condition=1,  ## Number of seconds to run or pulses to send
                loadZ=SPGUOutputImpedance.full_auto,  # that to set it automatically with CORRSER, otherwise 0.1 to 1M
                switch_state=SPGUSwitch.enabled,
                switch_normal=SPGUSwitchNormal.open, # switch normally open or closed
                switch_delay=0,# time to delay pulse opening, independent of pulse_delay
                switch_width=None,  # time to keep switch state, independent of pulse width
                ):
        """ Returns a validated SPGU setup, with the following default settings unless specified otherwise:
            - uses pulse switch,normall open, without delay,switch_width 1e-7 s or
            pulse_width + pulse_delay, whichever is longer
            - setting the loadZ automatically with a CORRSERR measurement
            - output mode = count the pulses, number of pulses=1
            - 2 level pulse, no pulse delay, minimum (8 ns) pulse lead/trail,
            pulse period set to just barely contain delay+pulse width
            - use SPGU pulse signal source 1

            When using 3 level pulse you need to explicitly specify the voltage and timing setup for signal 1 and 2 as tuple or list.
            If you omit pulse_leading,pulse_trailing or pulse_delay the default (minmum) values are simply duplicated and your "3-level" pulse will become 2 level pulse with the compounded peak
            """
        if levels==SPGULevels.BothSignals_3_levels:
            if not len(pulse_delay)==2 :
                pulse_delay = pulse_delay * 2
            if not len(pulse_leading)==2:
                pulse_leading = pulse_leading * 2
            if not len(pulse_trailing)==2:
                pulse_trailing = pulse_trailing * 2
            sources=(SPGUSignals.Signal1,SPGUSignals.Signal2)
            if any([not (isinstance(x,Sequence) and len(x)==2) for x in (pulse_base,pulse_peak,pulse_width,sources,pulse_delay,pulse_leading,pulse_trailing)]):
                raise ValueError("When specifying 3 level pulses, need to give pulse_base,pulse_peak,pulse_width,pulse_delay,pulse_lead,pulse_trail and sources as len 2 list or tuple")

        else:
            pulse_peak=[pulse_peak,]
            pulse_base=[pulse_base,]
            pulse_width=[pulse_width,]
            sources=[sources,]
            if not isinstance(pulse_delay,Sequence):
                pulse_delay=[pulse_delay,]
            if not isinstance(pulse_leading,Sequence):
                pulse_leading=[pulse_leading,]
            if not isinstance(pulse_trailing,Sequence):
                pulse_trailing=[pulse_trailing,]
        if pulse_period is None:
            pulse_period = sum(pulse_width)+1e-8
        if pulse_period < 2e-8 or pulse_period > 10:
            raise ValueError("Pulse period should be between 2e-8 s and 10 s, is {}s".format(pulse_period))
        if any([x < -40 or x > 40 for x in pulse_base+ pulse_peak]):
            raise ValueError("Voltage must stay between -40 V and 40 V, base is {} and peak is {}".format( pulse_base, pulse_peak))
        if not switch_width:
            switch_width= max(1e-7,sum(pulse_width+pulse_delay))
        elif switch_width<1e-7 or switch_width>pulse_period-switch_delay:
            raise ValueError("switch width must be between 1e-7 and pulse_period-delay s")
        if switch_delay<0 or switch_delay>pulse_period-1e-7:
            raise ValueError("switch delay must be between 0 and pulse_period-1e-7 s")
        if min(pulse_width)<1e-8 or max(pulse_width)>pulse_period-1e-8:
            raise ValueError("pulse width must be between 1e-7 and pulse_period-1e-8({}-1e-8={}) s, is {}".format(pulse_period,  pulse_period-1e-8, pulse_width))
        if min(pulse_delay)<0 or max(pulse_delay)>pulse_period-2e-8:
            raise ValueError("pulse delay must be between 0 and pulse_period-2e-8 s")
        if any([x >0.4 or x <8e-9 for x in pulse_leading+ pulse_trailing]):
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
                                        levels,
                                        pulse_base,
                                        pulse_peak,
                                        sources,
                                        pulse_delay,
                                        pulse_width,
                                        pulse_leading,
                                        pulse_trailing,
                                        )

class PulsedSpot(namedtuple("__PulsedSpot", [
         "input",  # V, I
         "input_range", # PV range
         "base",  # PV
         "peak",  # PV
         "compliance",
         "hold",     # 0 - 655.350 in s, 10 ms steps, hold before starting peak
         "width",   # # peak in seconds , see PT doc for ranges
         "period",  # 5-5000 in ms or one of PulsePeriod.{minimum,conservative} default PulsePeriod.minimum NOTE: gets multiplited by 10 to get resolutio
        ])):
    """ Specifies a setup where the SMU forces a Pulse between 5 and 5000 ms length(for shorter peaks, use  the SPGU setup.
    Default value:
-       input_range: full_auto
        base =0,
        hold =0, time to wait until pulse starts
        period= PulsePeriod.minimum, meaing the smalled time to fit both width and hold
        """
    def __new__(cls, input, peak,width, compliance, hold=0, base=0,input_range=InputRanges_I.full_auto, period=PulsePeriod.minimum,):
        return super(PulsedSpot, cls).__new__(cls, input,input_range,base, peak,compliance,hold, width,  period)

class PulsedSweep(
    namedtuple(
        "__PulsedSweep",
        [
         "input",
         "sweepmode",
         "input_range", #
         "base",
         "start",
         "stop",
         "step",
         "compliance",
         "auto_abort", # WM, leaving post parameter aside because abort should reset imo
         "sweep_hold",
         "sweep_delay",
         "pulse_hold",     # 0 - 655.350 in s, 10 ms steps, wait before measuring starts
         "pulse_width",   # # pulse in seconds , see PT doc for ranges
         "pulse_period",  # 5-5000 in ms or one of PulsePeriod.{minimum,conservative} default PulsePeriod.minimum NOTE: gets multiplited by 10 to get resolution
         ])):  #  WT
    """ Specifies a series of steadly increasing(and decreasing with start-stop-start ) pulses. Combines concepts from StaircaseSweep and PulseSpot
    input -  Inputs.I or Inputs.V
    sweepmode - linear/log, start-stop or start-stop-start
    input_range - smallest InputRange_X covering the value, full_auto by default, needs to take into account module
    base =0- base voltage from which we pulse
    sweep_hold =0, time to wait before sweep starts
    sweep_delay =0, time to wait before measuring start on every pulse
    pulse_hold =0, time to wait before every pulse
    start - the start value of the sweep
    stop - the stop value of the sweep
    step - steps of the sweep 1-100001
    compliance - maximum response Voltage or Current. Relatively slow, so use external safeguards of testing delicate units
    auto_abort - whether or not we should abort the test on any irregularities
    """
    def __new__(cls,input,start,stop,step,compliance, pulse_width, sweep_hold=0,weep_delay=0,pulse_hold=0,input_range=InputRanges_I.full_auto,base=0, pulse_period=PulsePeriod.minimum, auto_abort=AutoAbort.enabled,sweepmode=SweepMode.linear_up_down):
        return super(PulsedSweep, cls).__new__(cls,input,sweepmode,input_range,base,start,stop,step,compliance, auto_abort, sweep_hold,weep_delay,pulse_hold, pulse_width, pulse_period)


class BinarySearchSetup(
    namedtuple(
        "__BinarySearchSetup",
        [
        "input",
        "input_range",
        "start",
        "stop",
        "compliance",
        "sync_polarity", # cannot be set together with start/stop values, needs to be set on different channels
        "sync_offset",   # when defined the synchronous source will force start/stop/latest+offset (as defined by the measurement-post parameter) and keep the last value after the search
        "sync_compliance",
         ])):  #  WT
    """ Specifies the setup for a binary search. Paremeters are
    - target: Targets.I or Targets.V
    - start/stop - search start and stop values, start must be !=stop
    - input_range: Input range which covers start and stop
    - compliance
    - searchmode, Limit(0) search untl within target+-condition. count(1) finish
        after condition tries(1-16)
    - condition see above
    - measure_range range that covers target value
    - hold: wait time between starting the measurement and the first measuring.
    max 655.35, resolution 0.01 s
    - delay: settling time at every step between forcing a value and starting
    the step measurement. max 65.535, resolution 0.0001 s

    """
    def __new__(cls,input,start,stop,compliance,sync_compliance=None,sync_offset=0,sync_polarity=None, input_range=InputRanges_I.full_auto):
        if start and sync_polarity:
            raise ValueError("Source channel and synchronouschannel have to be the different")
        if not sync_compliance and sync_polarity:
            sync_compliance = compliance
        if start==stop:
            raise ValueError("start must be != stop")
        if compliance == 0:
            raise ValueError("Compliance must be !=0")
        return super(BinarySearchSetup, cls).__new__(cls,input, input_range, start, stop, compliance, sync_polarity,sync_offset,sync_compliance )















