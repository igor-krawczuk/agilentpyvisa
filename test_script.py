from agilentpyvisa.B1500 import *
import visa
import logging
logging.basicConfig(level=logging.INFO)

rm=visa.ResourceManager()

b=B1500(rm.list_resources()[0])