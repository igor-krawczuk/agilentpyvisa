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

def splitHeader(lines ):
    separator =","
    return ([x.strip() for x in lines[0].split(separator) if x],lines[1:])

def hasHeader(format):
    if format in (Format.ascii12_with_header_comma, Format.ascii12_with_header_crl,
                  Format.ascii13_with_header_comma_flex, Format.ascii13_with_header_comma,
                  Format.ascii13_with_header_crl, Format.ascii13_with_header_crl_flex):
        return True
    else:
        return False
