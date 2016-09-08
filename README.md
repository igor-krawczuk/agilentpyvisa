# WARNING: might contain bugs and while is very much intended to help you write code that generates nice configuration structs, a lot of refactoring still has to be done, so the API will break. Once I have finished my Masters Thesis I will do that major refactor, so you code WILL break.

If you are fine with that, feel free to read on and try the library:)

# agilentpyvisa
A WIP library to control B1500 and similar testers via the VISA protocol, built on pyvisa

First tests are working, but a lot is till to be done.

# Introduction
As I needed it for my research internship, I developed a python based library to make writing complex tests as convenient as possible.
 I am putting it on Github so others can use it if it helps them as well, critique it and maybe give me some advice on how to do things
 
It is very much a work in progress and not stable at all. It is also missing a lot of functions and was not tested yet.

# Design Goals

When I write one off scripts, I like the code to be self documenting. It also should scream at me if I do something wrong. This tries to do that.
The bulk of the work so far has been creating classes,Enums and namedtuples to make sure there are no magic numbers or cryptic commands, at the expense of more typing. But that is what ipython tabcompletion is for.

I went through a lot of trial and error with the documentation, as it is not quite what I would call an intuitive API. 
My lack of understanding of the system also shows in the commit history (as well as the fact that I use this repo to get it on the testing machine).
 But hey, now you don't have to go through all that pain! Just use the library :-)

I will continue working on this library as I go, ideally making it feature complete. If anyone from agilent reads this and wants to scream at me because I was to dumb to RTFM, feel free, I'd like to learn. 

If anybody wants to pay me to do a proper job quikcer, feel free to send me an offer:)
# Status
## What works right now

* StaircaseSweep, Spot Measurements, SPGU, DCForce
* Optional automatic error polling
* Controlling the 16440A SMU-SPGU Controller
* Parsing the ascii results into a pandas DataFrame

## What mostly works right now

*  PulsedSweep, PulsedSpot, BinarySearch, LinearSearch
* Most of these have validations on creation of the configuration tuples which tell you what to do, give you the alllowable ranges should you exceed them etc
* Verbose namedtuples and IntEnums for self documenting code, but with the option to still hand code your tests (i.e., use "DV 0,{},{}".format(InputRange.full_auto, 5" to force 5 Volt with automatic input ranging, or write tester.set_highspeed_adc(0,0) == "AV 0,0" if you know which int means what)
* Recording setups as programs to speed up testing, keeping track of them in the tester object


## What does not yet work, but I might add soon, given time
* binary data format
* Multichannel synchronous sweep, pulsed sweep and pulsed spot, sampling and HighSpeedSpot measurements

## What I don't plan on adding unless I need for my work/get asked specifically
* MFCMU (all the capacitive measurements really)
* Triggers
* QuasiStatic and QuasiPulsed measurements


# Documentation and examples
In general, use the Tab completion a lot and peek in the source code. I have programmed VERY verbosely.
The API is not greatly composable, but I was not smart enough to do that in the limited time and given that I still basically wrap strings that get sent to the tester.

## Setup
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

# A more elaborate example, based on the test that I had to run personally. You can find a cleaner version in the [TestingToolbox.ipynb](TestingToolbox.ipynb)
The goal is to use a transistor to provide finer compliance current limiting.
First we do some initialization, which will reset the tester and make sure we know what is going on.

```python
import itertools
import functools
import collections
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import logging
import sys
from datetime import datetime
import visa
import logging
from agilentpyvisa.B1500 import *
# import the library, as well as additional helpers to analyze the data later

rm = visa.ResourceManager()
rm.list_resources()
# check for the device ID that we want

rm.close()


b15= B1500('GPIB1::17::INSTR')

for c in b15.sub_channels:
    print(c,b15.slots_installed[int(str(c)[0])].name)
b15.default_check_err=False
# verify that we found all of the devices, as well as getting a list of the channel numbers

SMU1=2 # B
SMU2=3 # C
SMU3=4 # D
SMU4=5 # E
```

With that done, we will define some helper functions

```python
# define the channel numbers, the letters in comments are the identifier returned in the ouput
def get_R(d):
    R = d['EV']/d['EI']
    R=R.replace([np.inf, -np.inf], np.nan).dropna()
    return R.abs().mean()
# we measure on SMU4 to estimate resistance, so we need to access the EV (voltage of SMU4) and EI (current of SMU4) of the returned dataframe
 
def plot_output(out, t='line',up='b',down='r'):
    """ A simple wrapper which will create the "bat plot" which we use to check our DC sweeps and how they changed our device"""
    lout = out[['EV','EI']]
    lout=lout[lout.applymap(lambda x: not np.isnan(x)).all(axis=1)]
    y=lout['EI'].abs()*1e6
    x=np.array(lout['EV'])
    half = lout['EV'].abs().idxmax()
    if t=='line':
        plt.plot(x[:half],y[:half], color=up,marker='o')
        plt.plot(x[half:],y[half:], color=down,marker='o')
    elif t=='scatter':
        plt.scatter(x[:half],y[:half], color=up,marker='o')
        plt.scatter(x[half:],y[half:], color=down,marker='o')
        
    plt.autoscale()

def unit(u):
    """ In order to make logging easier, I define my units in SI later on. This wrapper allows me to write 1 unit("mV") for 1e-3 Volts"""
    if u[0]=='m':
        return 1e-3
    elif u[0]=='u':
        return 1e-6
    elif u[0]=='n':
        return 1e-9
```
And now we get to actually use the library. We will need to do a couple of different sweeps and pulse measurements,
 so let's hack together two helper functions for easy parametrization.

```python
def get_pulse(base, peak, width,count=1, lead_part=0.8, trail_part=0.8, loadz=10,gate=1.85, ground=SMU2):
    """Defines a SPGU setup and a channel to go with it, based on the given parameters"""
    mspgu=SPGU(base, peak,width, loadZ=10, pulse_leading=[lead_part*width], pulse_trailing=[trail_part*width],condition=count )
    inp_channel=Channel(number=101,spgu=mspgu)
    ground_channel=Channel(number=ground,dcforce=DCForce(Inputs.V,0,.1))
    gate_channel = Channel(number=SMU3,dcforce=DCForce(Inputs.V,gate,.1))
    spgu_test=TestSetup(channels=[ground_channel, gate_channel, inp_channel,],spgu_selector_setup=[(SMU_SPGU_port.Module_1_Output_2,SMU_SPGU_state.connect_relay_SPGU)])
    return (spgu_test,mspgu, inp_channel, ground_channel, gate_channel)

def get_Vsweep(start, stop, steps, compliance=300e-6,
               measure_range=MeasureRanges_I.full_auto,gate_voltage=1.85, ground=SMU2):
    swep_smu=b15.slots_installed[b15._B1500__channel_to_slot(3)]
    in_range=swep_smu.get_mincover_V(start,stop)
    
    sweep_measure=MeasureStaircaseSweep(Targets.I,range=measure_range, side=MeasureSides.current_side)
    
    sweep = StaircaseSweep(Inputs.V,InputRanges_V.full_auto,start,stop,steps,compliance, auto_abort=AutoAbort.disabled)
    
    inp_channel=Channel(number=SMU4,staircase_sweep=sweep, measurement=sweep_measure)
    
    ground_channel=Channel(number=ground,
                           dcforce=DCForce(Inputs.V,0,compliance),
                           #measurement=sweep_measure
                          )
    
    gate_channel = Channel(number=SMU3,dcforce=DCForce(Inputs.V,gate_voltage,.1),
                          # measurement=MeasureStaircaseSweep(Targets.V,
                          #                                   range=measure_range,
                          #                                   side=MeasureSides.voltage_side)
                          )
    
    sweep_test=TestSetup(channels=[gate_channel,ground_channel,inp_channel],
                         spgu_selector_setup=[(SMU_SPGU_port.Module_1_Output_2,SMU_SPGU_state.connect_relay_SMU)],
                        output_mode=OutputMode.with_primarysource,
                        format=Format.ascii13_with_header_crl, filter=Filter.enabled)
    return (sweep_test,sweep, inp_channel, ground_channel, gate_channel)


```
You can easily inspect the returned setup If something seems off in your measurements with *print* or by lettting ipython show you the namedTuple.

Using these helper functions, we create the actual functions which will run the tests
```python
# read and calculate the resistance
def checkR(start=200e-6,stop=350e-6, steps=51,mrange=MeasureRanges_I.uA100_limited,  gate=1.85, pr=True):
    b15.set_SMUSPGU_selector(SMU_SPGU_port.Module_1_Output_1,SMU_SPGU_state.connect_relay_SMU)
    read_setup,read, _ ,ground_channel,gate_channel=get_Vsweep(start=start,stop=stop,steps=steps,
                                                                     measure_range=mrange,
                                                              gate_voltage=gate
                                                              )
    ret,out =b15.run_test(read_setup, force_wait=True, auto_read=True,force_new_setup=True)
    out,series_dict,raw =out
    R=get_R(out)
    if pr:
        print(R)
    return R

# perform a forming sweep
def form(forming_v, steps, compliance,mrange=MeasureRanges_I.full_auto, gate=1.85):
    b15.set_SMUSPGU_selector(SMU_SPGU_port.Module_1_Output_1,SMU_SPGU_state.connect_relay_SMU)
    forming_setup,forming, _ , ground_channel,gate_channel=get_Vsweep(start=0,stop=forming_v,
                                                                      steps=steps,compliance=compliance,
                                                                     measure_range=mrange,
                                                                     gate_voltage=gate)
    b15.set_SMUSPGU_selector(SMU_SPGU_port.Module_1_Output_1,SMU_SPGU_state.connect_relay_SMU)
    ret,out =b15.run_test(forming_setup, force_wait=True, auto_read=True,force_new_setup=True)
    out,series_dict,raw =out
    if plot:
        plot_output(out, up='c',down='m')
    print(out.describe())
    return out
# perform a set_sweep or reset sweep (note, this is functionally identical to the form, but we rename them so it is less generic)    
set = form
reset = form

# perform a SPGU pulse train with count=1
def pulse(p_v, width, slope, gate=1.85,ground=SMU2):
    reset_pulse_setup, reset_pulse,_,_,_= get_pulse(0,p_v,width,lead_part=slope,trail_part=slope,gate=gate,ground=ground)
    b15.set_SMUSPGU_selector(SMU_SPGU_port.Module_1_Output_1,SMU_SPGU_state.connect_relay_SPGU)
    b15.run_test(reset_pulse_setup,force_wait=True,force_new_setup=True)
    b15.set_SMUSPGU_selector(SMU_SPGU_port.Module_1_Output_1,SMU_SPGU_state.connect_relay_SMU)
```

With this, we can already start testing the DUT with different parameters easily.
I for example needed to know how different voltage combinations affect the states we end up in. So I defined some helper functions again perform the pulse-then-measure,
do a lot of these and gather the result and finally do a lot of the parametrized chains and again combine the results.
You can see the functions here:

```python
def pulse_cycle(rV=-0.5,sV=0.8,width=1e-3,slope=0.8,pr=True):
    # define a pulse cycle: 1 reset, 1 set, check both re/post set/reset 
    pre_reset =checkR(pr=pr)
    pulse(rV, width, slope,ground=SMU1)
    post_reset = checkR(pr=pr)
    pre_set = checkR(pr=False)
    pulse(sV, width,slope)
    post_set=checkR(pr=pr)
    return (pre_reset, post_reset,pre_set,post_set)

def pulse_iter(rV=-0.5,sV=0.8,width=1e-3,slope=0.8,max_iter=100,pr=True, abort_break=True):
    # an iterator which will iterate untl the postSet/postReset values are within an order of magnitude of each other, unless told otherwise
    i=0
    while True:
        if i%100 == 0:
            print('Iteration ',i)
        pR,poR,pS,poS = pulse_cycle(rV,sV,width,slope,pr=pr)
        yield (pR,poR,pS,poS)
        if (abort_break  and np.log10(poR/poS) < 1) or i>=max_iter:
            
            break
        else:
            i+=1
    raise StopIteration
    

def N_cycles(w,it,rV=-0.5,sV=0.8,slope=0.8,plot=True, abort_break=True):
    c3=pd.DataFrame(np.fromiter(pulse_iter(width=w,max_iter=it,rV=rV,sV=sV,slope=slope,pr=False, abort_break=abort_break),
                      dtype=[('preReset',np.float),('postReset',np.float),('preSet',np.float),('postSet',np.float)]))
    print(c3.describe())
    if plot:
        c3.plot()
    return c3

def pyramid_voltage(voltages=[],voltage_si='mV',w=50,time_si='us',slope=0.8,times=10, abort_break=True):
    datas=[]
    for rV,sV in voltages:
        width=w*unit(time_si)
        resetV=rV*unit(voltage_si)
        setV=sV*unit(voltage_si)
        d=N_cycles(width, times,rV=resetV,sV=setV,slope=slope,plot=False, abort_break=abort_break)
        d['rV']=    pd.Series((resetV for _ in range(len(d))),index=d.index)
        d['sV']=    pd.Series((setV for _ in range(len(d))),index=d.index)
        datas.append(d)
        # do a cycle with the base rV/sV in order to restore initial conditions
        d=N_cycles(width, times,rV=voltages[0][0]*unit(voltage_si),sV=voltages[0][1]*unit(voltage_si),slope=slope,plot=False, abort_break=abort_break)
        d['rV']=    pd.Series((voltages[0][0]*unit(voltage_si) for _ in range(len(d))),index=d.index)
        d['sV']=    pd.Series((voltages[0][1]*unit(voltage_si) for _ in range(len(d))),index=d.index)
        datas.append(d)
    # final base rV/sV cycle to check if the device degraded at all in the test
    d=N_cycles(width, times,rV=voltages[0][0]*unit(voltage_si),sV=voltages[0][1]*unit(voltage_si),slope=slope,plot=False, abort_break=abort_break)
    d['rV']=    pd.Series((voltages[0][0]*unit(voltage_si) for _ in range(len(d))),index=d.index)
    d['sV']=    pd.Series((voltages[0][1]*unit(voltage_si) for _ in range(len(d))),index=d.index)
    datas.append(d)
        
    data = pd.concat(datas)
    data.index=range(len(data))
    data.to_csv('{}pyramid_with{}{}_slope{}percent.csv'.format(datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),
                                                                            width/unit(time_si),time_si,
                                                                            slope/1e-2
                                                                           )
        )
    return data
```
## Everything put together (including the initial helper functions



```python 
# do the initial form
form_sweep= plt.figure(figsize=[20,10])
f=form(3,100,10e-3, mrange=MeasureRanges_I.uA10_limited)
f.to_csv("{}_form_3V.csv".format(datetime.now().strftime('%Y-%m-%d_%H-%M-%S')))
plt.autoscale()
checkR()

# cycle reset/set a couple of times to anneal
iters=5
for i in range(iters):
    plt.figure()
    plt.hold()
    rt=reset_sweep(-1.5,500,5e-3,gate=1.85, mrange=MeasureRanges_I.uA10_limited)
    rt.to_csv("{}_reset{}_-1_5V.csv".format(
            datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),i)
             )
    checkR()
    s=set_sweep(1,500,10e-3, mrange=MeasureRanges_I.uA10_limited)
    s.to_csv("{}_set{}_1V.csv".format(
            datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),i)
            )
    checkR()
    plt.hold()

# and finally, use the previously defined helper functions
baseV = (-500,800)
r,s=baseV
percentages=list(reversed(range(40,101,5)))
rL=[r*i/100 for i in percentages]
sL=[s*i/100 for i in percentages]
pyr=list(itertools.product(rL,sL)) # creates a cross product of all voltage combinations
vpyr=pyramid_voltage(pyr, voltage_si='mV', abort_break=False)


# To get some initial insight we plot the original data, sorted by sV /rV both as primary/secondary and the scatter_matrix.
# Like this we can see any degradation over the course of testing, see the influence of different voltages following each other
# as well as get a feeling for any possible correlations
vpyr.plot(logy=[True,True], secondary_y=['rV','sV'],figsize=[10,5], title="The original pulse run")

sortpyr=vpyr.sort_values(['sV','rV'],ascending=[False,True])
sortpyr.index=range(len(sortpyr))
sortpyr.plot(logy=[True,True], secondary_y=['rV','sV'],figsize=[10,5], title="Sorted by sV-desc then rV-asc")

sortpyr2=vpyr.sort_values(['rV','sV'],ascending=[True,False])
sortpyr2.index=range(len(sortpyr2))
sortpyr2.plot(logy=[True,True], secondary_y=['rV','sV'],figsize=[10,5], title="Sorted by rV-asc then sV-desc")


pd.tools.plotting.scatter_matrix(vpyr, diagonal='kde')
```
 # Notes

* when forcing 0V in ground, don't set compliance to 0. The tester will actively regulate current flow in that node to 0, NOT just keep current flowing from the tester into the node to 0
