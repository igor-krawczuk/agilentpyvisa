import pytest
from agilentpyvisa.B1500 import *
import agilentpyvisa
import visa
import ipdb

class DummyTester():

    def __init__(self, *args,**kwargs):
        pass

    def query(*args, **kwargs):
        print([x for x in args if isinstance(x, str)])
        if kwargs:
            print(kwargs)
        return False

    def write(*args, **kwargs):
        print([x for x in args if isinstance(x, str)])
        if kwargs:
            print(kwargs)


@pytest.fixture(scope="function")
def tester(monkeypatch):
    def mock(self,*args):
        self._device = DummyTester()
    monkeypatch.setattr(B1500, "__init__", mock)
    b= B1500("test",)
    return b


def test_init(tester):
    print("DC_sweep_I")
    tester.init()

def test_DC_sweep_V(tester):
    print("DC_sweep_V")
    tester.DC_sweep_V(1,2,0,5,0.5,1)

def test_DC_sweep_I(tester):
    print("DC_spot_I")
    tester.DC_sweep_I(1,2,0,5,0.5,1)

def test_DC_spot_V(tester):
    print("DC_spot_V")
    tester.DC_spot_V(1,2,5,1)

def test_DC_spot_I(tester):
    print("DC_spot_I")
    tester.DC_spot_I(1,2,5,1)

def test_pulsed_spot_V(tester):
    print("PulsedSpotV")
    tester.pulsed_spot_V(input_channel=1,
                         ground_channel=2,
                         base=1,
                         pulse=2,
                         width=1e-3,
                         compliance=1)

def test_pulsed_spot_I(tester):
    print("PulsedSpotV")
    tester.pulsed_spot_I(input_channel=1,
                         ground_channel=2,
                         base=1,
                         pulse=2,
                         width=1e-3,
                         compliance=1)

def test_SPGU_V(tester):
    tester.SPGU_V()

def test_SPGU_I(tester):
    tester.SPGU_V()
