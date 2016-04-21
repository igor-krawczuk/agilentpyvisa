# agilentpyvisa
A WIP library to control B1500 and similar testers via the VISA protocol, built on pyvisa

First tests are working, but a lot is till to be done.


# Introduction
As I need it for my research internship, I will develop a python based library to make writing complex tests as convenient as possible. I am putting it on Github so others can use it if it helps them as well, critique it and maybe give me some advice on how to do things
 
It is very much a work in progress and not stable at all. It is also missing a lot of functions and was not tested yet.

# Design Goals

When I write one off scripts, I like the code to be self documenting. The bulk of the work so far has been creating classes,Enums and namedtuples to make sure there are no magic numbers or cryptic commands, at the expense of more typing. But that is what ipython tabcompletion is for.

I went through a lot of trial and error with the documentation, as it is not quite what I would call intuitive. My lack of understanding of the system also shows in the commit history (as well as the fact that I use this repo to get it on the testing machine). But hey, now you don't have to go through all that pain! Just use the library :-)

I will continue working on this library as I go, ideally making it feature complete and a bit faster. But since this all boils down to string wrangling, I won't invest too much time into performance. Most of the low level commands have been reworked in so they can be used manually in a more traditional script, which will probably be the fastest you can get with this. The rest will soon follow.
# Status
## What works 100% right now

Nothing. WIP = Work In Progress, feel free to file any issues should you encounter problems. I will try respond as much as I can given my time.

## What mostly works right now

* Spot,  StaircaseSweep, PulsedSweep, PulsedSpot, SPGU, DCForce, BinarySearch, LinearSearch
* Most of these have validations on creation of the configuration tuples which tell you what to do, give you the alllowable ranges should you exceed them etc
* Optional automatic error polling
* Optional automatic conversion of measurement data into numpy array
* Controlling the 16440A SMU-SPGU Controller
* Verbose namedtuples and IntEnums for self documenting code, but with the option to still handcode your tests (i.e., use "DV 0,{},{}".format(InputRange.full_auto, 5" to force 5 Volt with automatic input ranging, or write tester.set_highspeed_adc(0,0) == "AV 0,0" if you know which int means what)
* ASCII data format
* Recording setups as programs to speed up testing, keeping track of them in the tester object

## What does not yet work, but I might add soon, given time
* binary data format
* Multichannel synchronous sweep, pulsed sweep and pulsed spot, sampling and HighSpeedSpot measurements

## What I don't plan on adding unless I need for my work/get asked specifically
* MFCMU (all the capacitive measurements
* Triggers
* QuasiStatic and QuasiPulsed measurements

# Documentation and examples
In general, use the Tab completion a lot and peek in the source code. I have programmed VERY verbosely.

Initialize a tester object by giving it the VISA address. It will initialize, reset the device and explore a bit to figure out what SMUs are connected. Afterwards you can see the available channels in the .sub_channels tuple of your tester instance

```python
from agilentpyvisa.B1500 import *
# imports all of the tuples, classes and enums

b = B1500("here be your VISA address")
# if you do not want to reset your device or explore, pass the auto_init=False option
#... does some init, warns you if it finds something it does not understand
b.sub_channels
#=>[101,102,2,3,4,5]
b.slots_installed
#=> dict with all SMU classes, with their slot as keys
```

You can run some simple oneshot tests  by using the builtins

```python

b.DC_Spot_I(input_channel=2, ground_channel=3, value=0.5, compliance=0.5)
# DC_Spot_X, DC_Sweep_X and Pulsed_Sweep_X are implemented so far
```

To run a more complex test, create a *TestSetup* with at least one *Channel* and an optional *Measurement* in that channel. Given here for the same Spot Measurement of a 2 port
```python

measure_channel = Channel(number=2,
                         dc_force=DCForce(input=Inputs.I, value=0.5, compliance=0.5,input_range=InputRanges_I.A1_limited),
			 measurement=SpotMeasurement(target=Targets.I,measure_range=MeasureRanges_i.A1_fixed, side=MeasureSides.compliance_side)
			 )
ground_channel = Channel(number=3,
                         dc_force=DCForce(input=Inputs.V, value=0, compliance=0.5,input_range=InputRanges_I.A1_limited),
			 )

setup = Testsetup(channels=[measure_channel, ground_channel])
b.run_test(setup, auto_read=True, force_wait=True)
# with this, the tester will send the OPC? command and wait until the operations are done, and then read out and parse the measurement into a numpy array
# the array will be an array of arrays, so for convenience either flatten it or read it into a pandas.DataFrame
```
There can only ever be one type of measurement at the same time, and one force per channel, but here the library already keep track for you.
It will also error out if you try to set input or measuring ranges outside the SMUs parameters. To avoid this, you can check your value before like so

```python
b.slots_installed[2].get_mincover_I(0.5)
#=> returns the Enum value for the minimum covering range on this unit, fullauto if it doesn't find anything
```
