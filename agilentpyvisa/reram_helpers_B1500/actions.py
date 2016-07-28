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
    out.to_csv("{}_read_{}.csv".format(mytimestamp(), CURRENT_SAMPLE))
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
t
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
                mytimestamp(),rgate, CURRENT_SAMPLE)
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
                mytimestamp(),sgate, CURRENT_SAMPLE)
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
    frames.to_csv('{}_annealing_{}.csv'.format(mytimestamp(), CURRENT_SAMPLE))
    return frames,annealing_data
