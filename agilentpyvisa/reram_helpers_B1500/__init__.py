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
rm = visa.ResourceManager()
print(rm.list_resources())
rm.close()

# import the actual library for the Tester
from ..B1500 import *

# hide all internal logging. Set this to logging.INFO to see the commands being sent 
import logging
exception_logger.setLevel(logging.INFO)
write_logger.setLevel(logging.INFO)
query_logger.setLevel(logging.WARN)

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


# define setup functions with sane defaults for Memristor testing.

def get_pulse(base, peak, width,count=1, lead_part=0.8, trail_part=0.8, loadZ=1e6,gate_voltage=1.85,
              ground=SMU2,channel=101,gate=SMU3):
    """
    Defines a SPGU setup based on the given parameters
    The setup assumes we use a transistor with
    smu3->gate, 
    bottom_electrode->drain, 
    source->ground(SMU2 by default.)
    """
    mspgu=SPGU(base, peak,width, loadZ=loadZ, pulse_leading=[lead_part*width], pulse_trailing=[trail_part*width],
               condition=count )
    inp_channel=Channel(number=channel,spgu=mspgu)
    ground_channel=Channel(number=ground,dcforce=DCForce(Inputs.V,0,.1))
    gate_channel = Channel(number=gate,dcforce=DCForce(Inputs.V,gate_voltage,.1))
    spgu_test=TestSetup(channels=[ground_channel, gate_channel, inp_channel,],
                        spgu_selector_setup=[(SMU_SPGU_port.Module_1_Output_2,SMU_SPGU_state.open_relay)])
    return (spgu_test,mspgu, inp_channel, ground_channel, gate_channel)

def get_Vsweep(start, stop, steps, compliance=300e-6,
               measure_range=MeasureRanges_I.full_auto,gate_voltage=1.85, ground=SMU2):
    """
    Defines a Sweep setup based on the given parameters
    The setup assumes we use a transistor with
    smu3->gate, 
    bottom_electrode->drain, 
    source->ground(SMU2 by default. We also measure here.SMU1 if you do not want to use the transistor for current limiting.)
    """
    swep_smu=b15.slots_installed[b15._B1500__channel_to_slot(3)]
    in_range=swep_smu.get_mincover_V(start,stop)
    
    sweep_measure=MeasureStaircaseSweep(Targets.I,range=measure_range, side=MeasureSides.current_side)
    
    sweep = StaircaseSweep(Inputs.V,InputRanges_V.full_auto,start,stop,steps,compliance, auto_abort=AutoAbort.disabled)
    
    inp_channel=Channel(number=SMU4,staircase_sweep=sweep, measurement=sweep_measure)
    
    ground_channel=Channel(number=ground,
                           dcforce=DCForce(Inputs.V,0,compliance),
                          )
    
    gate_channel = Channel(number=SMU3,dcforce=DCForce(Inputs.V,gate_voltage,.1),
                          )
    
    sweep_test=TestSetup(channels=[gate_channel,ground_channel,inp_channel],
                         spgu_selector_setup=[(SMU_SPGU_port.Module_1_Output_2,SMU_SPGU_state.open_relay)],
                        output_mode=OutputMode.with_primarysource,
                        format=Format.ascii13_with_header_crl, filter=Filter.enabled)
    return (sweep_test,sweep, inp_channel, ground_channel, gate_channel)


# some very basic analysis functions

def get_R(d, current_column='EI', voltage_column='EV'):
    """
    Takes in padnas.DataFrame and optional column labels, returns average Resistance
    """
    R = d[voltage_column]/d[current_column]
    # remove all infinite resistances
    R=R.replace([np.inf, -np.inf], np.nan).dropna()
    return R.abs().mean()



def plot_output(out, t='line',up='b',down='r', voltage_column='EV', current_column='EI',fig=None,ax1=None,ax2=None):
    """ Show bat plot of voltage sweep, with different colours for up and down sweep"""
    if not (fig and ax1 and ax2):
        fig, ax1=plt.subplots()
        ax2=ax1.twinx()
    lout = out[[voltage_column, current_column]]
    lout=lout[lout.applymap(lambda x: not np.isnan(x)).all(axis=1)] # remove NaN values
    y=lout[current_column].abs()*1e6 # scale up current from microns
    x=np.array(lout[voltage_column]) 
    half = lout[voltage_column].abs().idxmax() # find peak of sweep for up/down plot
    ax1.set_xlabel("Voltage in V")
    if t=='line':
        ax1.plot(x[:half],y[:half], color=up,marker='o')
        ax1.plot(x[half:],y[half:], color=down,marker='o')
    elif t=='scatter':
        ax1.scatter(x[:half],y[:half], color=up,marker='o')
        ax1.scatter(x[half:],y[half:], color=down,marker='o')
    if 'cumulative_energy' in out.columns:
        if t=='line':
            ax2.plot(x[:half],out['cumulative_energy'][:half]*1000,color='g',marker='x')
            ax2.plot(x[half:],out['cumulative_energy'][half:]*1000,color='g',marker='x')
        elif t=='scatter':
            ax2.scatter(x[:half],out['cumulative_energy'][:half]*1000,color='g',marker='x')
            ax2.scatter(x[half:],out['cumulative_energy'][half:]*1000,color='g',marker='x')
        ax2.set_ylabel("Total Energy consumed in mW")
        
    ax1.set_ylabel('Ground current in uA')
    plt.xlabel('Voltage forced in V')
    plt.autoscale()
    if "R" in out.columns and "cumulative_energy" in out.columns:
        e_r_fig,erax1 = plt.subplots()
        erax2= erax1.twinx()
        erax1.set_xlabel("Voltage in V")
        if t=='line':
            erax1.plot(x[:half],out['cumulative_energy'][:half]*1000,color='g',marker='x')
            erax1.plot(x[half:],out['cumulative_energy'][half:]*1000,color='g',marker='x')
            erax2.plot(x[:half],out['R'][:half]/1000,color='c',marker='x')
            erax2.plot(x[half:],out['R'][half:]/1000,color='m',marker='x')
        elif t=='scatter':
            erax1.scatter(x[:half],out['cumulative_energy'][:half]*1000,color='g',marker='x')
            erax1.scatter(x[half:],out['cumulative_energy'][half:]*1000,color='g',marker='x')
            erax2.scatter(x[:half],out['R'][:half]/1000,color='c',marker='x')
            erax2.scatter(x[half:],out['R'][half:]/1000,color='m',marker='x')
        erax1.set_ylabel("Total Energy consumed in mW")
        erax2.set_ylabel("Resistance in kOhm")


# test functions
assert(get_pulse(0,1,0.5))  # base 0, peak 1V, width 0.5 s
assert(get_Vsweep(0,1,50))  # start 0, stop 1, 50 steps

# pattern helpers

pulse_members=['voltage','width','slope','gate','gateVoltage','count']
class pattern_pulse(collections.namedtuple('_pulse_setup',pulse_members)):
    def __new__(cls,voltage,width,slope,gate,gateVoltage,count=1):
        return super().__new__(cls, voltage, width, slope, gate,gateVoltage,count)

checkr_members=['after']
class pattern_checkR(collections.namedtuple('_checkR', checkr_members)):
    def __new__(cls,after=None):
        return super().__new__(cls,after)

def handle_pattern(p,CURRENT_SAMPLE,print_check=False):
    global SPGU_SELECTOR
    if isinstance(p,pattern_pulse):
        if not SPGU_SELECTOR=='SPGU':
            SPGU_SELECTOR='SPGU'
            b15.set_SMUSPGU_selector(SMU_SPGU_port.Module_1_Output_1,SMU_SPGU_state.connect_relay_SPGU)
        pulse(p.voltage, p.width, slope=p.slope, gate=p.gate, gate_voltage=p.gateVoltage,loadZ=1e6,count=p.count )
        return p
    elif isinstance(p, pattern_checkR):
        R=checkR(CURRENT_SAMPLE)
        if print_check:
            print(R)
        return R

def consume_patterns(CURRENT_SAMPLE,job_patterns,time_est_every=100,print_check=False):
    resp=[]
    est=None
    beginning=time.time()
    start=time.time()
    end=len(job_patterns)
    for i,p in enumerate(job_patterns):
        if i and i%time_est_every==0:
            time_per_run = (time.time()-start)/time_est_every
            print('estimated end',
                          time.strftime('%H:%M:%S',
                                        time.localtime(time.time()+time_per_run*(end-i))
                                        ),
                          " time per measurement:",
                          time_per_run,
                          "seconds"
                         )
            start=time.time()
        try:
            resp.append( (i,handle_pattern(p,CURRENT_SAMPLE,print_check)))
        except BaseException as e:
            print(e)
            resp.append((i,e))
        finally:
            pass
    return resp

def get_repeat_pattern(times,pulseVoltages=(-3.2,2.4), gateVoltages=(1.9,1.9),
                        widths=(1000e-6,1000e-6),
                        checkR_every=1,
                       slopes=(0.2,0.2)
                       ):
    patterns=[]
    i=0
    for i in range(times):
        #reset pattern
        patterns.append(pattern_pulse(voltage=pulseVoltages[0],
                                      width=widths[0],
                                      slope=slopes[0],
                                      gate=SMU3,
                                     gateVoltage=gateVoltages[0])
                       )
        # set pattern
        patterns.append(pattern_pulse(voltage=pulseVoltages[1],
                                      width=widths[1],
                                      slope=slopes[1],
                                      gate=SMU3,
                                     gateVoltage=gateVoltages[1])
                       )
    return insert_read_every(patterns,checkR_every)

def get_pyramid_pattern(baseVoltages=(-3.2,2.4), baseGateVoltages=(1.9,1.9),
                         voltagePercentages=[(1,1)],
                        gatePercentages=[(1,1)],widths=[(1000e-6,1000e-6)], checkR_every=1,
                       slopes=[(0.2,0.2)]):
    assert(len(voltagePercentages)==len(gatePercentages)==len(widths)==len(slopes))
    patterns=[]
    i=0
    while True:
        if i>=len(voltagePercentages):
            break
        #reset pattern
        patterns.append(pattern_pulse(voltage=baseVoltages[0]*voltagePercentages[i][0],
                                      width=widths[i][0],
                                      slope=slopes[i][0],
                                      gate=SMU3,
                                     gateVoltage=baseGateVoltages[0]*gatePercentages[i][0])
                       )
        # set pattern
        patterns.append(pattern_pulse(voltage=baseVoltages[1]*voltagePercentages[i][1],
                                      width=widths[i][1],
                                      slope=slopes[i][1],
                                      gate=SMU3,
                                     gateVoltage=baseGateVoltages[1]*gatePercentages[i][1])
                       )
        i+=1
    rev =[]
    i=len(patterns)
    while i>0:
        rev.append(patterns[i-2])
        rev.append(patterns[i-1])
        i-=2
    return insert_read_every(patterns+rev,checkR_every)

def insert_read_every(pattern,every=1):
    new_pattern=[]
    i=0
    while i<len(pattern):
        if (i%every)==0 or (i%every)==1:
            new_pattern.append(pattern_checkR())
        new_pattern.append(pattern[i])
        i+=1
    new_pattern.append(pattern_checkR())
    return new_pattern

def get_random_pattern(pattern_length,
                       reset_pulse_range=(0,-3.2),
                       set_pulse_range=(0,2.4),
                       reset_gate_range=(1.9,1.9),
                       set_gate_range=(1.9,1.9),
                       width_range=(500e-6,1000e-6),
                       slope_range=(0.2,0.2)
                      ):
    dist=np.random.uniform
    
    if pattern_length%2!=0:
        print("Shortening to nearest multiple of 2, only do reset-set pairs")
    pattern=[]
    for i in range(pattern_length//2):
        pattern.append(pattern_pulse(voltage=dist(*reset_pulse_range),
                                      width=dist(*width_range),
                                      slope=dist(*slope_range),
                                      gate=SMU3,
                                     gateVoltage=dist(*reset_gate_range)
                                    )
                      )
        pattern.append(pattern_pulse(voltage=dist(*set_pulse_range),
                                      width=dist(*width_range),
                                      slope=dist(*slope_range),
                                      gate=SMU3,
                                     gateVoltage=dist(*set_gate_range)
                                    )
                      )
    return pattern

def get_series(numpulses,peak,width=1000e-6,slope=0.2,gateV=1.9,count=1):
    return [pattern_pulse(voltage=peak,width=width,slope=slope,gateVoltage=gateV,gate=SMU3,count=count) for _ in range(numpulses)]
get_series(5,-1.5)

def parse_job_results(results, annealing_data=None, form_data=None):
    """
    Parses the job results and the previous annealing and forming data into a single dataframe to be used for feature building.
    form_data and annealing data are expected to be of a certain shape.
    annealing_data = {anneal_run(int):anneal_data}
    where anneal_data is has all of the keys in "child_dic_keys"
    form_data is expected to be a dict with all of "form_keys"
    """
    if form_data:
        form_keys=["FORM_V", "FORM_GATE"]
        assert(all([k in form_data for k in form_keys]),"Ensure that form_data has keys {}".format(form_keys))
    if annealing_data:
        child_dic_keys=("RESET_HISTMAX", "SET_HISTMAX", "SET_V")
        assert(all([isinstance(k,int) for k in annealing_data.keys()]),"Ensure annealing data is a dict with only int as keys")
        assert(all(
            [all(
                [k in dic for k in child_dic_keys]
                ) for dic in annealing_data.values()])
            ,"Ensure all child-dicts of annealing data have the following keys {}".format(child_dic_keys))

    res=[]
    proto = {'Resistance':None,'Voltage':None,'gateVoltage':None,'Type':None,'width':None,'slope':None}

    if annealing_data:
        for k in annealing_data.keys():
            for k2,v in annealing_data.items():
                proto["{}_{}".format(k,k2)]=v
    if form_data:
        for k,v in form_data.items():
            proto[k]=v
    for i,r in results:
        p = proto.copy()
        if isinstance(r,float):
            post=''
            if len(res)>0 and res[-1].get('Type'):
                post=' after '+res[-1]['Type']
            p['Resistance']=r
            p['Type']='Check'+post
        elif isinstance(r,pattern_pulse):
            p['Voltage']=r.voltage
            p['gateVoltage']=r.gateVoltage
            p['width']=r.width
            p['slope']=r.slope
            if r.voltage > 0:
                p['Type']='Set'
            else:
                p['Type']='Reset'
        res.append(p)
    return pd.DataFrame(res)
def plot_pattern_results(rdf,figsize=[10,10],fill=False):
    fig, ax1 = plt.subplots(figsize=figsize)
    ax2=ax1.twinx()
    rsr=rdf[rdf['Type']=='Check after Reset']['Resistance']
    rss=rdf[rdf['Type']=='Check after Set']['Resistance']
    
    if fill:
        ax2.fill(rss.index,rss.values,'y')
        ax2.fill(rsr.index,rsr.values,'g')
    
    ax2.scatter(rsr.index,rsr.values,c='g',marker='o',label='Resistance after Reset', zorder=10)
    ax2.scatter(rss.index,rss.values,c='y',marker='o',label='Resistance after Set', zorder=10)
    rtdf = rdf[rdf['Type']=='Reset']
    sdf = rdf[rdf['Type']=='Set']
    for c,df,run in zip(['r','b'],[rtdf,sdf],['Reset','Set']):
        v=df['Voltage'].dropna()
        ax1.scatter(v.index,v.values,c=c,marker='+',label='Voltage '+run)
        gv=df['gateVoltage'].dropna()
        ax1.scatter(gv.index,gv.values,c=c,marker='x',label='gateVoltage '+run)
    ax1.legend(loc=2)
    ax2.legend(loc=1)

def reset_pulse_energy_estimate(peak,width,slope,lrs_res=2e3,hrs_res=15e3):
    lrs_energy=(0.5*slope+(0.5-slope))*width*peak*peak/lrs_res
    hrs_energy=(0.5*slope+(0.5-slope))*width*peak*peak/hrs_res
    return lrs_energy+hrs_energy
reset_pulse_energy_estimate(-1.5,1,0.2)


# base abstract procedures
def find_set_V(d):
    """
    Given a sweep datum, tries to find the voltage at which the jump occurs
    """
    jumpstep=d["EI"].diff().abs().idxmax()
    jumpV = d.get_value(jumpstep, "EV")
    return jumpV

def get_hist(d):
    """ 
    Given a Sweep datum with EI and EV, calculate the difference between the first and second pass through a EV value, return as a dataframe of index, EV and R
    """
    if not "R" in d.columns:
        d["R"]=d["EV"]/d["EI"]
    half=len(d)//2
    # get first half of EV; make sure we indice from 0 to half
    d1=d[:half]
    d1.index=range(half)

    # same for second half, but flip so that the EV align
    d2=d[half:]
    d2.index=range(half)
    d2=d2.iloc[::-1]
    d2.index=range(half)
    hist = d2-d1
    # dataframe now contains positive R where the second pass had a larger resistance than the first
    return pd.concat([d1["EV"],hist["R"]],axis=1)

def add_resistance(d):
    out = d
    out["R"]=d["EV"]/d["EI"]
    return out

def add_energy(datum):
    datum['cumulative_energy']=(datum['ET'].diff().fillna(0)*datum['EI']*datum['EV']).cumsum()
    return datum
def sweep(stop, steps, compliance=300e-6,start=0,mrange=MeasureRanges_I.full_auto,
          gate=1.85, plot=True, up='b',down='r', ground=SMU2, stats=True):
    """ Create and immediately perform a sweep, optionally plot the data and/or show statistics"""
    b15.set_SMUSPGU_selector(SMU_SPGU_port.Module_1_Output_1,SMU_SPGU_state.connect_relay_SMU)
    global SPGU_SELECTOR
    SPGU_SELECTOR='SMU'
    set_setup,set, _ ,ground_channel,gate_channel=get_Vsweep(start=start,stop=stop,steps=steps, compliance=compliance,
                                                                     measure_range=mrange,gate_voltage=gate, ground=ground)
    ret,out =b15.run_test(set_setup, force_wait=True, auto_read=True,force_new_setup=True)
    out,series_dict,raw =out
    out=add_energy(out)
    out=add_resistance(out)
    if plot:
        plot_output(out, up=up,down=down)
    if stats:
        print(out.describe())
    return out


def pulse(p_v, width, slope, gate=SMU3, gate_voltage=1.85,ground=SMU2,loadZ=1e6,count=1):
    reset_pulse_setup, reset_pulse,_,_,_= get_pulse(0,p_v,width,
                                                    lead_part=slope,trail_part=slope,gate=gate,gate_voltage=gate_voltage,
                                                    ground=ground,loadZ=loadZ,count=count
                                                   )
    global SPGU_SELECTOR
    SPGU_SELECTOR='SPGU'
    b15.set_SMUSPGU_selector(SMU_SPGU_port.Module_1_Output_1,SMU_SPGU_state.connect_relay_SPGU)
    b15.run_test(reset_pulse_setup,force_wait=True,force_new_setup=True)

    
    
# some more concrete cases, with the defaults we use initially
def read(CURRENT_SAMPLE,start=200e-6,stop=250e-6, steps=51,mrange=MeasureRanges_I.uA100_limited,
         gate=1.85, plot=True, print_R=True, stats=True):
    """
    A quick sweep to estimate the current Resistance of the DUT
    """
    out = sweep(start=start,stop=stop,steps=steps,mrange=mrange,gate=gate,plot=plot,stats=stats)
    out.to_csv("{}_read_{}.csv".format(datetime.now().strftime('%Y-%m-%d_%H-%M-%S'), CURRENT_SAMPLE))
    return out

def checkR(CURRENT_SAMPLE, start=200e-6,stop=350e-6, steps=51,mrange=MeasureRanges_I.uA100_limited,  gate=1.85):
    """
    Perform a read and calculate the mean, throw everything else away
    """
    out= read(CURRENT_SAMPLE,start=start,stop=stop, steps=steps,mrange=mrange,gate=gate, plot=False,stats=False)
    R= get_R(out)
    return R


def form(forming_v, steps, compliance,mrange=MeasureRanges_I.full_auto, gate=1.85):
    """
    Initial form sweep for the DUT
    """
    return sweep(forming_v, steps, compliance,mrange=mrange, gate=gate, plot=True, up='c', down='m')
    
    
def set_sweep(set_v, steps, compliance,mrange=MeasureRanges_I.full_auto, gate=1.85, plot=True):
    """
    DC Set, with SMU2 as ground -> transistor limits current in LRS after set
    """
    return sweep(set_v, steps, compliance,mrange=mrange, gate=gate, plot=plot, up='c', down='m')
    
def reset_sweep(reset_v, steps, compliance,mrange=MeasureRanges_I.full_auto, gate=1.85, plot=True):
    """
    DC reset, with SMU1 as ground -> no transistor limiting
    """
    return sweep(reset_v, steps, compliance,mrange=mrange, gate=gate, plot=plot, ground=SMU1)

# uncomment to test the functions, but beware, they do use the tester
#assert(read(stats=False,plot=False) is not None)
#assert(form(0,10,0.1) is not None)
#assert(set_sweep(0,10,0.1) is not None)
#assert(reset_sweep(0,10,0.1) is not None)

def anneal(CURRENT_SAMPLE,setV=1.0,resetV=-1.5,gateV=1.9,steps=100,times=3, plot=True,sleep_between=1):
    """
    Performs a number of reset/set cycles to anneal the sample and gather some data for characterisation
    TODO: refactor this, it comes straight from scripting
    """
    runs=[]
    annealing_data={}
    for i in range(times):
        anneal={}
        fig,ax1 = plt.subplots()
        ax2=ax1.twinx()
        #plt.suptitle("Reset gate 1.9V, Set gate {}V".format(perc[i]*1.9))
        plt.hold(True)
        rgate = gateV
        rpeak=resetV
        rsteps=steps
        print('Reset with Peak {}V, {} steps, gate {}V'.format(rpeak, rsteps, rgate))
        rt=reset_sweep(rpeak, rsteps,5e-3, mrange=MeasureRanges_I.uA10_limited,gate=rgate,plot=False)
        rt=add_energy(rt)
        rt.to_csv("{}_reset_gate{}_-1_5V_{}.csv".format(
                datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),rgate, CURRENT_SAMPLE)
                 )
        plot_output(rt,fig=fig,ax1=ax1,ax2=ax2)
        rh=get_hist(rt)
        anneal['RESET_HISTMAX']=rh['R'].abs().max()
        print('Histmax {}'.format(anneal['RESET_HISTMAX']))
        print('HRS',checkR(CURRENT_SAMPLE))
        time.sleep(sleep_between)
        speak= setV
        ssteps= steps
        sgate= gateV
        print('Set with Peak {}V, {} steps, gate {}V'.format(speak, ssteps, sgate))
        s=set_sweep(speak,ssteps,10e-3, mrange=MeasureRanges_I.uA10_limited,gate=SMU3,plot=False)
        s=add_energy(s)
        s.to_csv("{}_set_gate{}_1V_{}.csv".format(
                datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),sgate, CURRENT_SAMPLE)
                )
        plot_output(s,fig=fig,ax1=ax1,ax2=ax2)
        sh=get_hist(s)
        anneal['SET_HISTMAX']=sh['R'].abs().max()
        print('Histmax {}'.format(anneal['SET_HISTMAX']))
        anneal['SET_V']=find_set_V(s)
        print("Set V",anneal['SET_V'])
        print('LRS',checkR(CURRENT_SAMPLE))
        time.sleep(sleep_between)
        #plt.yscale("log")
        runs.append((rt,s,rgate,sgate))
        annealing_data[i]=anneal

    frames=[]
    for rt,s,rgate,sgate in runs:
        rt['gateV']=[rgate]*len(rt.index)
        rt['type']='reset'
        s['gateV']=[sgate]*len(s.index)
        s['type']='set'
        frames.append(rt)
        frames.append(s)
    frames = pd.concat(frames)
    frames.to_csv('{}_annealing_{}.csv'.format(datetime.now().strftime('%Y-%m-%d_%H-%M-%S'), CURRENT_SAMPLE))
    return frames,annealing_data
