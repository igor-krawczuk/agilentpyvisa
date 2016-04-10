from collections import namedtuple
from .enums import *
from .helpers import (minCover_I, minCover_V)

class Channel(
              namedtuple(
                  '__Channel',
                  ["number",    # channel number
                     "series_resistance",  # connect series yes or no? default no
                     "channel_adc",  # AAD, default ADCTypes.highspeed
                   "dcforce",
                    "staircase_sweep",
                   "pulse_sweep",
                    "pulsed_spot",
                    "quasipulse",
                   "SPGU",
                   "highspeed_spot", ])):
    def __new__(cls,number,  series_resistance=SeriesResistance.disabled, channel_adc=ADCTypes.highspeed,
                   dcforce=None, staircase_sweep=None, pulse_sweep=None, pulsed_spot=None, SPGU=None, quasipulse=None,
                   highspeed_spot=None ):
        # add default values
        # adc_type = AAD
        #
        if [x is not None for x in [dcforce, staircase_sweep, pulse_sweep,  quasipulse, pulsed_spot, SPGU, highspeed_spot]].count(True)>1:
            raise "At most one force setup can be use per channel"
        return super(Channel, cls).__new__(cls, number, series_resistance, channel_adc,
                   dcforce, staircase_sweep, pulse_sweep,  pulsed_spot, quasipulse, SPGU, highspeed_spot )

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


# Everything below still needs review
class PulsedSpot(namedtuple("_PulsedSpot", [
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





### BELOW BE STUBS

