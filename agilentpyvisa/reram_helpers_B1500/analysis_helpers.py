# some very basic analysis functions
def get_R(d, current_column='EI', voltage_column='EV'):
    """
    Takes in padnas.DataFrame and optional column labels, returns average Resistance
    """
    R = d[voltage_column]/d[current_column]
    # remove all infinite resistances
    R=R.replace([np.inf, -np.inf], np.nan).dropna()
    return R.abs().mean()

def reset_pulse_energy_estimate(peak,width,slope,lrs_res=2e3,hrs_res=15e3):
    lrs_energy=(0.5*slope+(0.5-slope))*width*peak*peak/lrs_res
    hrs_energy=(0.5*slope+(0.5-slope))*width*peak*peak/hrs_res
    return lrs_energy+hrs_energy


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
