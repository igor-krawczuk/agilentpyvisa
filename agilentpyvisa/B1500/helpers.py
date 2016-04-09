from .enums import MeasureRanges_I
from .enums import MeasureRanges_V

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


