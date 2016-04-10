from collections import namedtuple
from .enums import *
from .enums import MeasureSides,MeasureRanges_I,MeasureRanges_V, MeasureModes

class Measurement(namedtuple("__Measurement",["channel","config",])):
    def __new__(cls,channel, config):
        return super(Measurement, cls).__new__(cls, channel, config)

class MeasureStaircaseSweep(namedtuple("__MeasureStaircaseSweep",["target","range","side","mode"])):
    def __new__(cls,target,range=MeasureRanges_I.full_auto,side=MeasureSides.compliance_side):
        # full_auto the same in I and V (=0)
        mode=MeasureModes.staircase_sweep
        return super(MeasureStaircaseSweep, cls).__new__(cls,target,range,side,mode)

class MeasureSpot(namedtuple("__MeasureSpot",["target","range","side","mode"])):
    def __new__(cls, target,  range=MeasureRanges_I.full_auto, side=MeasureSides.compliance_side):
        # full_auto the same in I and V (=0)
        mode=MeasureModes.spot
        return super(MeasureSpot, cls).__new__(cls, target, range, side, mode)

class MeasurePulsedSpot(namedtuple("__MeasurePulsedSpot",["target","range","side","mode"])):
    def __new__(cls, target,  range=MeasureRanges_I.full_auto, side=MeasureSides.compliance_side):
        # full_auto the same in I and V (=0)
        mode=MeasureModes.pulsed_spot
        return super(MeasurePulsedSpot, cls).__new__(cls, target, range, side, mode)


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


class QuasiStatic(namedtuple("__QuasiStatic", ["type", ])):  # pulsed, sweep,
    def __new__(cls, type):
        return super(QuasiStatic, cls).__new__(cls, type)


class SPGU(namedtuple("__SPGU",[])):
    def __new__(cls, type):
        return super(SPGU, cls).__new__(cls, )
    pass


class Sampling(namedtuple("__Sampling",["range","base","bias","compliance","hold_bias","interval","number","hold_base"])):
    pass







class MultiChannel(
    namedtuple(
        "__MultiChannel", [
            "mode", ])):  # pulsed, sweep,
    def __new__(cls, type):
        return super(MultiChannelSetup, cls).__new__(cls, type)

