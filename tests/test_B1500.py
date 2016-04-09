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
    tester.init()

def test_DC_V_sweep(tester):
    tester.DC_V_sweep(1,2,0,5,0.5,1)

def test_DC_I_sweep(tester):
    tester.DC_I_sweep(1,2,0,5,0.5,1)

def test_DC_V_spot(tester):
    tester.DC_V_spot(1,2,5,1)

def test_DC_I_spot(tester):
    tester.DC_I_spot(1,2,5,1)

def test_DC_V_pulsed_spot(tester):
    tester.DC_V_pulsed_spot()

def test_DC_I_pulsed_spot(tester):
    tester.DC_I_pulsed_spot()

def test_SPGU_V(tester):
    tester.SPGU_V()

def test_SPGU_I(tester):
    tester.SPGU_V()
