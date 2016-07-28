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

def insert_read_every(pattern,N=1):
    """
    """
    new_pattern=[]
    i=0
    while i<len(pattern):
        if (i%N)==0 or (i%N)==1:
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

def parse_job_results(results,CURRENT_SAMPLE, annealing_data=None, form_data=None):
    """
    Parses the job results and the previous annealing and forming data into a single dataframe to be used for feature building.
    form_data and annealing data are expected to be of a certain shape.
    annealing_data = {anneal_run(int):anneal_data}
    where anneal_data is has all of the keys in "child_dic_keys"
    form_data is expected to be a dict with all of "form_keys"
    """
    if form_data:
        form_keys=["FORM_V", "FORM_GATE"]
        assert all([k in form_data for k in form_keys]),"Ensure that form_data has keys {}".format(form_keys)
    if annealing_data:
        child_dic_keys=("RESET_HISTMAX", "SET_HISTMAX", "SET_V")
        assert all([isinstance(k,int) for k in annealing_data.keys()]),"Ensure annealing data is a dict with only int as keys"
        assert all([all([k in dic for k in child_dic_keys]) for dic in annealing_data.values()]),"Ensure all child-dicts of annealing data have the following keys {}".format(child_dic_keys)

    res=[]
    proto = {'Resistance':None,'Voltage':None,'gateVoltage':None,'Type':None,'width':None,'slope':None}

    if annealing_data:
        for k in annealing_data.keys():
            for k2,v in annealing_data[k].items():
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
    resulttable = pd.DataFrame(res)
    resulttable.to_csv("{}_pattern_run_{}.csv".format(mytimestamp(), CURRENT_SAMPLE))
    return resulttable

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
