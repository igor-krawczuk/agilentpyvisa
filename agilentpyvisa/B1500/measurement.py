from collections import namedtuple
from .enums import *
from .enums import MeasureSides,MeasureRanges_I,MeasureRanges_V, MeasureModes

class MeasureStaircaseSweep(namedtuple("__MeasureStaircaseSweep",["target","range","side","mode"])):
    def __new__(cls,target,range=MeasureRanges_I.full_auto,side=MeasureSides.compliance_side):
        # full_auto the same in I and V (=0)
        """ Specifies a StaircaseSweep measurement, see page 2-8 of the manual"""
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

class MeasureLinearSearch(namedtuple("__MeasureLinearSearch",["mode",
                                                              "target",
                                                              "output_mode",
                                                              "auto_abort",
                                                              "post",
                                                              "hold",
                                                              "delay",
                                                              "searchmode",
                                                              "condition",
                                                              "measure_range",
                                                              "target_value",
                                                              ])):
    def __new__(cls,target,target_value,condition,post=SearchPost.start,output_mode=SearchOutput.sense_and_search, auto_abort=AutoAbort.enabled,hold=0,delay=0,searchmode=SearchModes.limit,measure_range=MeasureRanges_I.full_auto,):
        # full_auto the same in I and V (=0)
        mode=MeasureModes.binary_search
        if hold > 655.35 or hold <0:
            raise ValueError("hold must be between 0 and 655.35 s")
        if delay > 65.535 or delay <0:
            raise ValueError("delay must be between 0 and 65.535 s")
        return super(MeasureBinarySearch, cls).__new__(cls, mode,target,output_mode,auto_abort,post,hold,delay,searchmode,condition,measure_range,target_value)

class MeasureBinarySearch(namedtuple("__MeasureBinarySearch",["mode",
                                                              "target",
                                                              "output_mode",
                                                              "control_mode",
                                                              "auto_abort",
                                                              "post",
                                                              "hold",
                                                              "delay",
                                                              "searchmode",
                                                              "condition",
                                                              "measure_range",
                                                              "target_value",
                                                              ])):
    def __new__(cls,target,target_value,condition,post=SearchPost.start,output_mode=SearchOutput.sense_and_search, control_mode=SearchControlMode.normal,auto_abort=AutoAbort.enabled,hold=0,delay=0,searchmode=SearchModes.limit,measure_range=MeasureRanges_I.full_auto,):
        # full_auto the same in I and V (=0)
        mode=MeasureModes.binary_search
        if hold > 655.35 or hold <0:
            raise ValueError("hold must be between 0 and 655.35 s")
        if delay > 65.535 or delay <0:
            raise ValueError("delay must be between 0 and 65.535 s")
        return super(MeasureBinarySearch, cls).__new__(cls, mode,target,output_mode,control_mode,auto_abort,post,hold,delay,searchmode,condition,measure_range,target_value)

