from collections import namedtuple
from enum import IntEnum, Enum
from .enumsB1500 import Polarity

def minCovRange(start,stop=None):
    if stop is None:
        return True
    else:
        return False
class Formats(IntEnum):
    ascii12_with_header_crl = 1 # compatible with 412B
    ascii12_no_header_crl = 2 # compatible with 412B
    binary4_crl = 3 # compatible with 412B
    binary4 = 4 # compatible with 412B
    ascii12_with_header_comma = 5 # compatible with 412B
    ascii13_with_header_crl = 11
    ascii13_no_header_crl_flex = 12
    binary8_crl = 13
    binary8 = 14
    ascii13_with_header_comma = 15
    ascii13_with_header_crl_flex = 21
    ascii13_no_header_crl_flex2 = 22
    ascii13_with_header_comma_flex = 25

class OutputModes(IntEnum):
    dataonly = 0
    default = 0
    with_primarysource = 1
    with_synchronoussource = 2  # comaptible with MM2, MM5
    # MM16, MM27, and MM28 1-10 select sweep source set by the WNX, MCPNX,
    # or MCPWNX command

class Filter(IntEnum):
    enabled = 0
    disabled = 1
class ADCTypes(IntEnum):
    highspeed = 0
    highresolution = 1
    highspeed_pulse =2

class ADCMode(IntEnum):
    auto = 0
    manual = 1

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
class SeriesResistance(IntEnum):
    disabled = 0
    enabled = 1
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



class Inputs(Enum):
    V = 0
    I = 1

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
                input_range = minCovRange(value)
        return super(DCForce, cls).__new__(cls,input,input_range, value, compliance, polarity,
                   compliance_range)

class MeasureModes(IntEnum):
    # MM
    spot = 1  # related source setup: DV,DI
    staircase_sweep = 2  # WI, WV, WT, WM, WSI, WSV
    pulsed_spot = 3  # PI, PV, PT
    pulsed_sweep = 4 # PWI, PWV, PT, WM, WSI, WSV
    staircase_sweep_pulsed_bias = 5 # WI, WV, WM, WSI,WSV, PI, PV, PT
    quasi_pulsed_spot = 9 # BDV, BDT, BDM
    sampling = 10 # MCC, MSC, ML, MT, MI, MV
    quasi_static_cv = 13 # QSV, QST, QSM
    linear_search = 14 # LSV, LSI, LGV, LGI, LSM, LSTM, LSSV, LSSI, LSVM
    binary_serach = 15 # BSV, BSI, BGV, BGI, BSM, BST, BSSV, BSSI, BSVM
    multi_channel_sweep = 16 # WI, WV, WT, WM, WNX
    spot_C = 17 # FC, ACV, DCV
    CV_sweep_dc_bias = 18 # FC, ACV, WDCV, WMDCV, WTDCV
    pulsed_spot_C = 19 # PDCV, PTDCV
    pulsed_sweep_CV = 20 # PWDCV, PTDCV
    sweep_Cf = 22 # WFC, ACV, DCV, WMFC, WTFC
    sweep_CV_ac_level = 23 # FC, WACV, DCV, WMACV, WTACV
    sampling_Ct = 26 # MSC, MDCV, MTDCV
    multichannel_pulsed_spot = 27 # MCPT, MCPNT, MCPNX
    multichannel_pulsed_sweep = 28 # MCPT, MCPNT, MCPNX, MCPWS, MCPWNX, WNX

class MeasureSides(IntEnum):
    # CMM
    compliance_side = 0 # returns reverse of force
    current_side = 1
    voltage_side = 2
    force_side = 3 # returns force
    current_and_voltage = 4  # returns as "compliance_side" and "force_side"

class MeasureRanges(IntEnum):
    # RI
    full_auto = 0
    pulse_compliance = 0 # 0, 8-23 with pulse is compliace range, minimum range that covers compliance value
    # limited ranges
    pA1_auto = 8
    pA10_auto = 9
    pA100_auto = 10
    nA1_auto = 11
    nA10_auto = 12
    nA100_auto = 13
    uA1_auto = 14
    uA10_auto = 15
    uA100_auto = 16
    mA1_auto = 17
    mA10_auto = 18
    mA100_auto = 19
    A1_auto = 20
    A2_auto = 21
    A20_auto = 22
    A40_auto = 23
    # fixed ranges
    pA1_fixed = -8
    pA10_fixed = -9
    pA100_fixed = -10
    nA1_fixed = -11
    nA10_fixed = -12
    nA100_fixed = -13
    uA1_fixed = -14
    uA10_fixed = -15
    uA100_fixed = -16
    mA1_fixed = -17
    mA10_fixed = -18
    mA100_fixed = -19
    A1_fixed = -20
    A2_fixed = -21
    A20_fixed = -22
    A40_fixed = -23

class Measurement(namedtuple("__Measurement",["target","mode","side","range"])):
    def __new__(cls,target,mode,side,range ):
        return super(Measurement, cls).__new__(cls,target,mode,side,range)



class SweepMode(IntEnum):
    #  up => sweeps from start to stop
    #  up_down => sweeps from start to stop to start
    linear_up = 1
    log_up = 2
    linear_up_down = 3
    log_up_down = 3

class AutoAbort(IntEnum):
    disabled = 1
    enabled = 2

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
    def __new__(cls, input, start, stop, step, compliance, input_range, sweepmode=SweepMode.linear_up_down, auto_abort=AutoAbort.enabled, power_comp=None, hold=0, delay=0):
        return super(StaircaseSweep, cls).__new__(cls,input, sweepmode, input_range, start, stop, step, compliance, power_comp, auto_abort, hold, delay)



class PulsePeriod(IntEnum):
    minimum = -1
    conservative = 0

class PulseSweep(
    namedtuple(
        "__PulseSweep",
        ["input",
         "sweepmode",
         "range", #
         "base",
         "start",
         "stop",
         "step",
         "compliance",
         "power_comp",  # not set by default
         "auto_abort", # WM, leaving post parameter aside because abort should reset imo
         "hold"     # 0 - 655.350 in s, 10 ms steps, wait before measuring starts
         "width",   # # pulse in seconds , see PT doc for ranges
         "period",  # 5-5000 in ms or one of PulsePeriod.{minimum,conservative} default PulsePeriod.minimum NOTE: gets multiplited by 10 to get resolution
         ])):  #  WT
    def __new__(cls,staircase_setup, pulse_setup, auto_abort, timing):
        return super(PulseSweep, cls).__new__(cls,staircase_setup, pulse_setup, auto_abort, timing)



class Pulse(namedtuple("_PulseSpot", [
         "input",  # V, I
         "input_range", # PV range
         "base",  # PV
         "pulse",  # PV
         "compliance",
         "auto_abort", # WM, leaving post parameter aside because abort should reset imo
         "hold"     # 0 - 655.350 in s, 10 ms steps, wait before measuring starts
         "width",   # # pulse in seconds , see PT doc for ranges
         "period",  # 5-5000 in ms or one of PulsePeriod.{minimum,conservative} default PulsePeriod.minimum NOTE: gets multiplited by 10 to get resolutio
        ])):
    def __new__(cls, input,base, pulse,width,hold, compliance, period=PulsePeriod.minimum,auto_abort=AutoAbort.enabled,):
        return super(Pulse, cls).__new__(cls, pulse_setup, pulse_timing)

# EVERYTHING BELOW THIS TEXT IS STUBS ONLY AND NOT READY TO USE

class QuasiPulse(namedtuple("__QuasiPulse", ["BDM","BDT","BDV"])):  # BDM,BDT, BDV
    def __new__(cls, pulse_setup, pulse_timing):
        return super(QuasiPulse, cls).__new__(cls, pulse_setup, pulse_timing)


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


class HighSpeedSpot(namedtuple("__HighSpeedSpot",[])):
    pass


class Pulsed(namedtuple("__Pulse",[])):
    pass


class Spot(namedtuple("__Spot",[])):
    pass
