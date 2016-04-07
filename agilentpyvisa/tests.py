from collections import namedtuple
from .enums import *

def minCover_V(start,stop=None):
    # since after .format() the values for the limited ranging are the same for input,
    # output and measurement ranges we use the measurement Enum for all
    largest = None
    if stop is None:
        largest = abs(start)
    else:
        largest=max(abs(start),abs(stop))
    # TODO: might be nice to have binary tree here...just out of principle
    if largest <=0.2:
        return MeasureRanges_V.V0_2_limited
    elif largest <=0.5:
        return MeasureRanges_V.V0_5_limited
    elif largest <=2:
        return MeasureRanges_V.V2_limited
    elif largest <=5:
        return MeasureRanges_V.V5_limited
    elif largest <=20:
        return MeasureRanges_V.V20_limited
    elif largest <=40:
        return MeasureRanges_V.V40_limited
    elif largest <=100:
        return MeasureRanges_V.V100_limited
    elif largest <=200:
        return MeasureRanges_V.V200_limited
    elif largest <=500:
        return MeasureRanges_V.V500_limited
    elif largest <=1500:
        return MeasureRanges_V.V1500_limited
    elif largest <=3000:
        return MeasureRanges_V.V3000_limited
    else:
        return MeasureRanges_V.full_auto

def minCover_I(start,stop=None):
    # since after .format() the values for the limited ranging are the same for input,
    # output and measurement ranges we use the measurement Enum for all
    largest = None
    if stop is None:
        largest = abs(start)
    else:
        largest=max(abs(start),abs(stop))
    # TODO: might be nice to have binary tree here...just out of principle
    if largest <=1e-12:
        return MeasureRanges_I.pA1_limited
    elif largest <=1e-11:
        return MeasureRanges_I.pA10_limited
    elif largest <=1e-10:
        return MeasureRanges_I.pA100_limited
    elif largest <=1e-9:
        return MeasureRanges_I.nA1_limited
    elif largest <=1e-8:
        return MeasureRanges_I.nA10_limited
    elif largest <=1e-7:
        return MeasureRanges_I.nA100_limited
    elif largest <=1e-6:
        return MeasureRanges_I.uA1_limited
    elif largest <=1e-5:
        return MeasureRanges_I.uA10_limited
    elif largest <=1e-4:
        return MeasureRanges_I.uA100_limited
    elif largest <=1e-3:
        return MeasureRanges_I.mA1_limited
    elif largest <=1e-2:
        return MeasureRanges_I.mA10_limited
    elif largest <=1e-1:
        return MeasureRanges_I.mA100_limited
    elif largest <=1:
        return MeasureRanges_I.A1_limited
    elif largest <=2:
        return MeasureRanges_I.A2_limited
    elif largest <=2e2:
        return MeasureRanges_I.A20_limited
    elif largest <=4e2:
        return MeasureRanges_I.pA40_limited
    else:
        return MeasureRanges_I.full_auto


class TestSetup(namedtuple('__TestSetup',
                ["channels",    # list of channel setups
                 "highspeed_adc_number",  # AV, default 1, 1-1013 = number or numberx initial in auto
                 "highspeed_adc_mode",          # AV, default ADCMode.auto
                 "adc_modes",  # AIT, [(type,ADCMode.auto for type in ADCTypes as default
                 "multi_setup",
                "format",
                "output_mode",
                "filter"
                ])):
    def __new__(cls, channels, highspeed_adc_number=1, highspeed_adc_mode=ADCMode.auto,adc_modes=[], multi_setup=None, format=Formats.ascii12_with_header_crl,output_mode=OutputModes.dataonly,filter=Filter.disabled):
        # add default values
        return super(TestSetup, cls).__new__(cls, channels, highspeed_adc_number, highspeed_adc_mode, adc_modes, multi_setup, format,output_mode, filter)

class Channel(
              namedtuple(
                  '__Channel',
                  ["number",    # channel number
                    "measurement",  # measurement setup, if we measure from this channel
                     "series_resistance",  # connect series yes or no? default no
                     "channel_adc",  # AAD, default ADCTypes.highspeed
                   "dcforce",
                     "staircase_sweep",
                   "pulse_sweep",
                     "spot",
                     "pulse",
                      "quasipulse",
                   "SPGU",
                   "highspeed_spot", ])):
    def __new__(cls,number, measurement=None, series_resistance=SeriesResistance.disabled, channel_adc=ADCTypes.highspeed,
                   dcforce=None, staircase_sweep=None, pulse_sweep=None, spot=None, pulse=None, SPGU=None, quasipulse=None,
                   highspeed_spot=None ):
        # add default values
        # adc_type = AAD
        #
        if [x is not None for x in [dcforce, staircase_sweep, pulse_sweep, spot, quasipulse, pulse, SPGU, highspeed_spot]].count(True)>1:
            raise "At most one force setup can be use per channel"
        return super(Channel, cls).__new__(cls, number, measurement, series_resistance, channel_adc,
                   dcforce, staircase_sweep, pulse_sweep, spot, pulse, quasipulse, SPGU, highspeed_spot )




class DCForce(
              namedtuple(
                  "__DCForce",
                  ["input", # "I" or "V" for voltage and current respectively
                  "input_range",
                 "value",
                 "compliance",
                 "polarity",
                  "compliance_range"  # if not set, uses minimum range that will cover. If set, limited auto never goes below
                ])):
    def __new__(cls, input, value, compliance,input_range=None, polarity=Polarity.like_input,
                   compliance_range=None):
        if input_range is None:
            if input==Inputs.I:
                    input_range = minCover_I(value)
            else:
                    input_range = minCover_V(value)
        return super(DCForce, cls).__new__(cls,input,input_range, value, compliance, polarity,
                   compliance_range)


# TODO consolidate measurements (Highspeed spot etc) here
class Measurement(namedtuple("__Measurement",["target","mode","side","range"])):
    def __new__(cls,target,mode,side,range ):
        return super(Measurement, cls).__new__(cls,target,mode,side,range)




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



class Pulse(namedtuple("_Pulse", [
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

        return super(Pulse, cls).__new__(cls, input,input_range,base, pulse,compliance,width,hold,  period)

class QuasiPulse(namedtuple("__QuasiPulse", [
    "settling_detection_intervall", # BDM
    "measure_target", # BDM
    "input_range",  # BDV
    "start",  #BDV
    "stop", # BDV
    "compliance",# BDV
    "hold",     # BDT, 0 - 655.350 in s, 10 ms steps, wait before measuring starts
    "delay",   # BDT, 0 - 65.5350 in s,  0.1 ms steps, wait before measuring starts
])):  # BDM,BDT, BDV
    def __new__(cls, settling_detection_interval,measure_target,start,stop,compliance,hold=0, delay=0,input_range=None):
        if input_range is None:
            input_range = minCover_V(start,stop)
        return super(QuasiPulse, cls).__new__(cls, settling_detection_interval,measure_target,input_range,start,stop,compliance,hold, delay)
# EVERYTHING BELOW THIS TEXT IS STUBS ONLY AND NOT READY TO USE
class HighSpeedSpot(namedtuple("__HighSpeedSpot",[
    "target",
    "IMP",
    "FC",
    "vrange",
    "irange",
    "Rrange",
    "highspeed_mode"
                                                  ,])):
    pass



class Search(
    namedtuple(
        "__Search",
        [
            "type",
            "target",
            "auto_abort",
            "output_mode",
            "timing",
            "monitor",
            "search_source",
             "synchronous_source"])):  # binary/Linear, voltage/current, LSM,LSVM,LSTM,LGI,LSV,LSSV
    def __new__(cls, type,
            target,
            auto_abort,
            output_mode,
            timing,
            monitor,
            search_source,
             synchronous_source):
        return super(Search, cls).__new__(cls, type,
            target,
            auto_abort,
            output_mode,
            timing,
            monitor,
            search_source,
             synchronous_source)


class MultiChannelSetup(
    namedtuple(
        "__MultiChannelSetup", [
            "type", ])):  # pulsed, sweep,
    def __new__(cls, type):
        return super(MultiChannelSetup, cls).__new__(cls, type)


class QuasiStatic(namedtuple("__QuasiStatic", ["type", ])):  # pulsed, sweep,
    def __new__(cls, type):
        return super(QuasiStatic, cls).__new__(cls, type)


class SPGU(namedtuple("__SPGU",[])):
    def __new__(cls, type):
        return super(SPGU, cls).__new__(cls, )
    pass


class Sampling(namedtuple("__Sampling",[])):
    pass




class Pulsed(namedtuple("__Pulse",[])):
    pass


class Spot(namedtuple("__Spot",[])):
    pass
