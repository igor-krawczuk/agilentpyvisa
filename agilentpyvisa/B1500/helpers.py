from .enums import MeasureRanges_I, InputRanges_I, InputRanges_V
from .enums import MeasureRanges_V, MeasureModes, Format
from logging import getLogger
exception_logger = getLogger(__name__+":ERRORS")


def availableInputRanges(model):
    """ Returns tuples of the available OutputRanging used for input_range settings, based on the model. Based on Pages 4-22 and 4-16 of B1500 manual"""
    if model =="B1510A":  # HPSMU High power source/monitor unit
        return tuple([InputRanges_V[x] for  x in InputRanges_V.__members__ if InputRanges_V[x].value in (0,20,200,400,1000,2000)]+
                     [InputRanges_I[x] for  x in InputRanges_I.__members__ if InputRanges_I[x].value in tuple([0]+list(range(11,21)))])
    if model in ("B1511A","B1511B"):  # MPSMU Medium power source/monitor unit
        return tuple([InputRanges_V[x] for  x in InputRanges_V.__members__ if InputRanges_V[x].value in (0,5,50,200,400,1000)]+
                     [InputRanges_I[x] for  x in InputRanges_I.__members__ if InputRanges_I[x].value in tuple([0]+list(range(8,20)))])
    if model =="B1512A":  # HCSMU High current source/monitor unit
        return tuple([InputRanges_V[x] for  x in InputRanges_V.__members__ if InputRanges_V[x].value in (0,2,200,400,)]+
                     [InputRanges_I[x] for  x in InputRanges_I.__members__ if InputRanges_I[x].value in tuple([0,22]+list(range(15,21)))])
    if model in ("B1513A", "B1513B"):  # HVSMU High voltage source/monitor unit
        return tuple([InputRanges_V[x] for  x in InputRanges_V.__members__ if InputRanges_V[x].value in (0,2000,5000,15000,30000)]+
                     [InputRanges_I[x] for  x in InputRanges_I.__members__ if InputRanges_I[x].value in tuple([0]+list(range(11,20)))])
    if model =="B1514A":  # MCSMU Medium current source/monitor unit
        return tuple([InputRanges_V[x] for  x in InputRanges_V.__members__ if InputRanges_V[x].value in (0,2,200,400,)]+
                     [InputRanges_I[x] for  x in InputRanges_I.__members__ if InputRanges_I[x].value in tuple([0]+list(range(15,21)))])
    if model =="B1517A":  # HRSMU High resolution source/monitor unit
        return tuple([InputRanges_V[x] for  x in InputRanges_V.__members__ if InputRanges_V[x].value in (0,5,50,200,400,1000)]+
                     [InputRanges_I[x] for  x in InputRanges_I.__members__ if InputRanges_I[x].value in tuple([0]+list(range(8,20)))])
    if model =="B1520A":  # MFCMU  CMU Multi frequency capacitance measurement unit
        exception_logger.warn("This device is not yet supported: {}".format(model))
        return ()
    elif model =="B1525A":  # HVSPGU SPGU High voltage semiconductor pulse generator unit
        return tuple([InputRanges_V[x] for  x in InputRanges_V.__members__ if InputRanges_V[x].value in ()]+
                     [InputRanges_I[x] for  x in InputRanges_I.__members__ if InputRanges_I[x].value in ()])
    else:
        raise NotImplementedError("We don't know this model {0}, thus we don't support it")

def format_command(cmd, *args):
    return "{} {}".format(cmd, ",".join(["{}".format(x) for x in args if x is not None]))



def availableMeasureRanges(model):
    raise NotImplementedError("This helper is not yet supported")


def isSweep(channels):
    return channels and any([c.measurement.mode in(
                    MeasureModes.staircase_sweep,
                    MeasureModes.multi_channel_sweep,
                    MeasureModes.CV_sweep_dc_bias,
                    MeasureModes.multichannel_pulsed_sweep,
                    MeasureModes.pulsed_sweep,
                    MeasureModes.staircase_sweep_pulsed_bias,
                ) for c in channels if c.measurement])
def isSpot(channels):
    return channels and any([c.measurement.mode in(
                    MeasureModes.spot,
                    MeasureModes.pulsed_spot,
                ) for c in channels if c.measurement])

def getTerminator(format):
    if "comma" in repr(format):
        return ","
    elif "crl" in repr(format):
        return "\r\n"
    else:
        return "\n"

def splitHeader(lines):
    separator =","
    fields = []
    vals=[x.strip() for x in lines[0].split(separator) if x]
    for v in vals:
        if "+" in v:
            fields.append(v.split("+")[0])
        else:
            fields.append(v.split("-")[0])
    return fields


def hasHeader(format):
    if format in (Format.ascii12_with_header_comma, Format.ascii12_with_header_crl,
                  Format.ascii13_with_header_comma_flex, Format.ascii13_with_header_comma,
                  Format.ascii13_with_header_crl, Format.ascii13_with_header_crl_flex):
        return True
    else:
        return False

""" postpose binary parsing for now
def parse_binary4(self,byte_data):
    raise NotImplementedError
    bitstream = getBits(byte_data)
    for datum in group_bits(bitstream,8*4):
        a = datum[0]   # 1/0 measurement data/other data
        b = datum[1]   # parameter 1/0: SMU: current or capacitance/voltage,cmu:conductance or susceptance/resistance or reactance
        c = datum[2:7]  # range Value, see table page 1-42
        d = datum[7:24]  # data count. multiply with range_val from table import for data. for SMU: measurement_data = d*range_val/50e3, source-data=d*range_val/20e3
        e = datum[24:27] # status source data_001=> first or intermediate sweep 010 last sweep for measurement data:see table on 1-46
        f = datum[27:32] # channel number
        datum_type = parse4_getType(a)
        param = parse4_getParam(b)
        channel_num = int(d,base=2)
        unit = self.slots_installed.get(self.__channel_to_slot(channel)) # get the module using the channel number
        drange = parse4_getRange(c, unit)
        data = parse4_getData(d,drange,unit)
        status = parse4_getStatus(e, datum_type)

class Binary4DataType(Enum):
    MeasurementData =1
    OtherData = 0

def parse4_getType(bit):
    if bit==1:
        return Binary4DataType.MeasurementData
    elif bit==0:
        return Binary4DataType.MeasurementData
class Binary4Param(Enum):
    voltage = "SMU0"
    current = "SMU1"
    resistance_reactance ="CMU0"
    conductance_susceptance = "CMU1"
def parse4_getParam(b, spgu):
    if b == 1 and not "CM" in repr(spgu):
        return Binary4Param.current
    elif b == 0 and not "CM" in repr(spgu):
        return Binary4Param.voltage
    elif b == 1 and "CM" in repr(spgu):
        return Binary4Param.conductance_susceptance
    elif b == 0 and "CM" in repr(spgu):
        return Binary4Param.resistance_reactance


def parse_binary8(byte_data):
    raise NotImplementedError
    bitstream = getBits(byte_data)
    for datum in group_bits(bitstream,8*8):
        a = datum[0]  # 1/0 measurement data/other data
        b = datum[1:8] # parmeters, see table on page 1-49
        f = datum[59:64]  # channel number, see page 1-52
        datum_type = parse4_getType(a)
        param = parse4_getParam(b)
        channel_num = parse4_getChannel(d)
        if param == Binary8Param.TimeStamp:
            h = datum[8:56]   # timestaamp count, timestamp = count /1e6 => count in us, stamp in s if count[0] =1 count = count -140737488355328 (overflow) count[0]=1 and count[1:]==0 is invalid
            timestamp = parse8_getTimestamp(h)
        else:
            c = datum[8:16]  # range, see table on page 1-50
            d = datum[16:48] # data count, muplity with range_val from table import to get data. see page 1-51
            e = datum[48:56]  # status page 1-54
            g = datum[56:59]  # adc see page 1-52
        unit = None # get the module using the channel number
        drange = parse4_getRange(c, unit)
        data = parse4_getData(d,drange,unit)
        status = parse4_getStatus(e, datum_type)


def getBits(byte_data):
    i=it(byte_data.hex(),base=16)
    return bin(i).replace("0b","")

def group_bits(iterable, n ):
    it=iter(iterable)
    while True:
        accum=[]
        for i in range(n):
            try:
                accum.append(next(it))
            except StopIteration:
                raise StopIteration("".join(accum))
        yield "".join(accum)

"""
