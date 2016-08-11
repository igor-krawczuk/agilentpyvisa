import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

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
