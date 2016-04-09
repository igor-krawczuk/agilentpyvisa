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
    print("inmkp")
    def mock(self,*args):
        self._device = DummyTester()
    monkeypatch.setattr(B1500, "__init__", mock)
    b= B1500("test",)
    return b


def test_init(tester):
    tester.init()

def test_DC_V_sweep(tester):
    tester.DC_V_sweep()

def test_DC_I_sweep(tester):
    tester.DC_I_sweep()

def test_DC_V_spot(tester):
    tester.DC_V_spot()

def test_DC_I_spot(tester):
    tester.DC_I_spot()

def test_DC_V_pulsed_spot(tester):
    tester.DC_V_sweep()

def test_DC_I_pulsed_spot(tester):
    tester.DC_I_pulsed_spot()

def test_SPGU_V(tester):
    pass

def test_SPGU_I(tester):
    pass
