import pytest
from agilentpyvisa.B1500 import *
import agilentpyvisa
import visa
import ipdb
import types

#import logging
#logging.basicConfig(level=logging.INFO)

class DummyTester():

    def __init__(self, *args,**kwargs):
        pass

    def query(*args, **kwargs):
        print(*[x for x in args if isinstance(x, str)])
        if kwargs:
            print(kwargs)
        if any(("UNT" in x for x in args if type(x)is str)):
            return ";".join(["B1517A,0"]*5)
        elif any(("LRN" in x for x in args if type(x)is str)):
            return "CL1;"
        else:
            return "+0"

    def write(*args, **kwargs):
        print(*[x for x in args if isinstance(x, str)])
        if kwargs:
            print(kwargs)


@pytest.fixture(scope="function")
def tester(monkeypatch):
    b= B1500("test",auto_init=False)
    b.__chanels = [HRSMU(b, i) for i in range(5)]
    return b


def test_init(tester):
    print("DC_sweep_I")
    #tester.init()

@pytest.mark.timeout(5)
def test_DC_sweep_V(tester):
    print("DC_sweep_V")
    tester.DC_Sweep_V(1,2,0,5,0.5,1)

def test_DC_Sweep_I(tester):
    print("DC_sweep_I")
    tester.DC_Sweep_I(1,2,0,5,0.5,1)

def test_DC_spot_V(tester):
    print("DC_spot_V")
    tester.DC_Spot_V(1,2,5,1)

def test_DC_spot_I(tester):
    print("DC_spot_I")
    tester.DC_Spot_I(1,2,5,1)

def test_pulsed_spot_V(tester):
    print("PulsedSpotV")
    tester.Pulsed_Spot_V(input_channel=1,
                         ground_channel=2,
                         base=1,
                         pulse=2,
                         width=1e-3,
                         compliance=1)

def test_pulsed_spot_I(tester):
    print("PulsedSpotV")
    tester.Pulsed_Spot_I(input_channel=1,
                         ground_channel=2,
                         base=1,
                         pulse=2,
                         width=1e-3,
                         compliance=1)

def test_SPGU(tester):
    print("SPGU_V")
    tester.SPGU(5,0,1,1)

