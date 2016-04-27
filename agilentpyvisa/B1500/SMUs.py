from logging import getLogger
from .loggers import exception_logger,write_logger, query_logger
from .enums import *
from .force import *
from .helpers import format_command
from .baseSMU import SMU
from .spgu import SPGUSMU
from .SMU_capabilities import *


# bundling up all the different Measuring Types possible with almost every SMU
class GeneralSMU(SMU,DCForceUnit,SpotUnit, PulsedSpotUnit, SingleMeasure, StaircaseSweepUnit,PulsedSweepUnit,BinarySearchUnit, LinearSearchUnit):
    pass

class HPSMU(GeneralSMU):

    def __init__(self, parent_device, slot):
        self.long_name = "High power source/monitor unit"
        self.models = ["B1510A"]
        self.input_ranges = tuple([InputRanges_V[x] for x in
                                   InputRanges_V.__members__
                                   if InputRanges_V[x].value
                                   in (0, 20, 200, 400, 1000, 2000)] +
                                  [InputRanges_I[x] for x in
                                   InputRanges_I.__members__
                                   if InputRanges_I[x].value
                                   in tuple([0] + list(range(11, 21)))])
        self.measure_ranges = tuple([0,20, 200, 400, 1000,
                                    2000, -20, -200,-400,-1000,-2000]+
                                   list(range(11,21))+list(range(-11,-21,-1))
                                    )
        self._search_max_voltage=100
        self._search_max_current=0.1
        self._search_min_voltage = 0
        self._search_min_current = 0
        self._search_compliance_current={20:1,
                                         40:500e-3,
                                         100:125-3,
                                         200:50-3,
                                         }
        self._search_compliance_voltage={50e-3:200,
                                         100-3:100,
                                         500e-3:40,
                                         1:20,
                                         }
        super().__init__(parent_device, slot)



class MPSMU(GeneralSMU):

    def __init__(self, parent_device, slot):
        self.long_name = "Medium power source/monitor unit"
        self.models = ("B1511A", "B1511B")
        self.input_ranges = [
            InputRanges_V[x] for x in InputRanges_V.__members__
            if InputRanges_V[x].value in (0, 5, 50, 200, 400, 1000)] + [
            InputRanges_I[x] for x in InputRanges_I.__members__
            if InputRanges_I[x].value in tuple([0] + list(range(8, 20)))]
        self.measure_ranges = tuple([0,5,20,50, 200, 400, 1000,
                                    -5, -20,-50, -200,-400,-1000,]+
                                   list(range(8,20))+list(range(-8,-20,-1))
                                     )
        self._search_max_voltage=100
        self._search_max_current=0.1
        self._search_min_voltage = 0
        self._search_min_current = 0
        self._search_compliance_current={20:0.1,
                                         40:50e-3,
                                         100:20e-3,
                                         }
        self._search_compliance_voltage={20e-3:100,
                                         50e-3:40,
                                        100e-3:20,
                                         }
        super().__init__(parent_device, slot)


class HCSMU(GeneralSMU):

    def __init__(self, parent_device, slot):
        self.long_name = "High current source/monitor unit"
        self.models = ("B1512A")
        self.input_ranges = [
            InputRanges_V[x] for x in InputRanges_V.__members__
            if InputRanges_V[x].value in (0, 20, 200, 400, 1000, 2000)] + [
            InputRanges_I[x] for x in InputRanges_I.__members__
            if InputRanges_I[x].value in tuple([0] + list(range(11, 21)))]
        self.measure_ranges = tuple([0,2,20, 200, 400,
                                    -5, -20,-200, -400,]+
                                    list(range(15,20))+list(range(-15,-20))+[22,-22]
                                    )
        super().__init__(parent_device, slot)
        self._search_max_voltage=40
        self._search_max_current=1
        self._search_min_voltage = 0
        self._search_min_current = 0


class HVSMU(GeneralSMU):

    def __init__(self, parent_device, slot):
        self.long_name = "High voltage source/Monitor unit"
        self.models = ("B1513A", "B1513B")
        self.input_ranges = [
            InputRanges_V[x] for x in InputRanges_V.__members__
            if InputRanges_V[x].value in (0, 2000, 5000, 15000, 30000)] + [
            InputRanges_I[x] for x in InputRanges_I.__members__
            if InputRanges_I[x].value in tuple([0] + list(range(11, 19)))]
        self.measure_ranges = tuple([0,2000,5000, 15000, 30000,
                                    -2000, -5000, -15000, -30000,]+
                                    list(range(11,19))+list(range(-11,-19,-1))
                                    )
        super().__init__(parent_device, slot)
        self._search_max_voltage=3000
        self._search_max_current=8e-3
        self._search_min_voltage = 0
        self._search_min_current = 0

class MCSMU(GeneralSMU):

    def __init__(self, parent_device, slot):
        self.long_name = "Medium current source/monitor unit"
        self.models = ("B1514A")
        self.input_ranges = [
            InputRanges_V[x] for x in InputRanges_V.__members__
            if InputRanges_V[x].value in (0, 2, 200, 400,)] + [
            InputRanges_I[x] for x in InputRanges_I.__members__
            if InputRanges_I[x].value in tuple([0] + list(range(15, 21)))]
        self.measure_ranges = tuple([0, 2,20,200,400,
                                    -2,-20,-200,-400]+
                                    list(range(15,20))+list(range(-15,-20))
                                    )

        super().__init__(parent_device, slot)
        self._search_max_voltage=30
        self._search_max_current=0.1
        self._search_min_voltage = 0
        self._search_min_current = 0

class HRSMU(GeneralSMU):

    def __init__(self, parent_device, slot):
        self.long_name = "High resolution source/monitor unit"
        self.models = ["B1517A"]
        self.input_ranges = tuple([InputRanges_V[x]
                                   for x in InputRanges_V.__members__
                                   if InputRanges_V[x].value
                                   in (0, 5, 50, 200, 400, 1000)] +
                                  [InputRanges_I[x]
                                   for x in InputRanges_I.__members__
                                   if InputRanges_I[x].value in tuple(
                                       [0] + list(range(8, 20)))])
        self.measure_ranges = tuple([0, 5,20, 50,200,400,1000,
                                    -5, -20, -50, -200, -400, -1000,]+
                                   list(range(8,20))+list(range(-8,-20,-1))
                                    )
        super().__init__(parent_device, slot)
        self._search_max_voltage=100
        self._search_max_current=0.1
        self._search_min_voltage = 0
        self._search_min_current = 0
        self._search_compliance_current={20:0.1,
                                         40:50e-3,
                                         100:20e-3,
                                         }
        self._search_compliance_voltage={20e-3:100,
                                         50e-3:40,
                                        100e-3:20,
                                         }


class HVSPGU(SMU,SPGUSMU):

    def __init__(self, parent_device, slot):
        self.long_name = "High Voltage SPGU (Semiconductor pulse generator unit)"
        self.models = ["B1525A"]
        self.load_impedance = {}
        self.busy = 0
        self.minV = -40
        self.maxV = 40
        super().__init__(parent_device, slot)



# STUP
class MFCFMU(SMU):

    def __init__(self, parent_device, slot):
        exception_logger.warn( NotImplementedError("This type of SMU has not been implemented yet"))
        self.long_name = "Multiple frequency capacitive frequency measuring unit"
        self.models = ["B1520A"]
        # TODO special treatment
        super().__init__(parent_device, slot)
        self._search_max_voltage=100
        self._search_max_current=0.1
        self._search_min_voltage = 0
        self._search_min_current = 0

