# for more powerfull parameter construction
import itertools
import functools
import collections

# math library
import numpy as np

# data analysis librarz
import pandas as pd
#plotting library
import matplotlib.pyplot as plt

# for foldernames, timing etc
import sys
from datetime import datetime
import time

# show all resources available via VISA
import visa

if not "tester_id" in globals():
    tester_id='GPIB1::17::INSTR'
    print("Setting 'tester_id' to {} and creating test_object b15 to be used in tests.\
If you want to change this, set 'tester_id' globally and either reimport or recreate the b15 object".format(tester_id))
else:
    print("found tester_id {}, creating b15 object with it".format(tester_id))

# connect to tester
b15= B1500(tester_id)
# print all connected instruments with channel numbers
for c in b15.sub_channels:
    print(c,b15.slots_installed[int(str(c)[0])].name)
b15.default_check_err=False

# define channel numbers for use
if not "SMU2" in globals():
    SMU2=3 # C
    print("Setting SMU2 to {}".format(SMU2))
else:
    print("SMU2 found as value {}".format())

if not "SMU1" in globals():
    SMU1=2 # B
    print("Setting SMU1 to {}".format(SMU2))
else:
    print("SMU1 found as value {}".format())

if not "SMU3" in globals():
    SMU3=4 # D
    print("Setting SMU3 to {}".format(SMU2))
else:
    print("SMU3 found as value {}".format())

if not "SMU4" in globals():
    SMU4=5 # E
    print("Setting SMU4 to {}".format(SMU2))
else:
    print("SMU4 found as value {}".format())

SPGU_SELECTOR='SMU'

