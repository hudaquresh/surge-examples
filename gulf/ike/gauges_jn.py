#!/usr/bin/env

from clawpack.pyclaw.gauges import GaugeSolution
import datetime 
import numpy
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt 
import os 
import scipy.io as sio


geo_dir = 'gulf'
models = ['holland80', 'holland10', 'SLOSH', 'DeMaria', 'rankine',
'modified-rankine', 'CLE']
# models = ['H80']

title_font = {'fontname':'Arial', 'size':'10', 'color':'black',
'weight':'normal',
              'verticalalignment':'bottom'} # Bottom vertical alignment for more space
axis_font = {'fontname':'Arial', 'size':'10', 'weight':'normal'}

def seconds2days(seconds):
    r"""
    Convert seconds to days. 
    """
    days = seconds/(3600.0*24.0)
    return days 


def gather_file_paths(storm): 
    r"""
    Gather the paths needed to gather data.     
    """
    paths = [] 
    for w in models: 
        storm_run = '%s-%s' %(storm,w)
        dir_path = os.path.join(os.getcwd(), 'storm-surge', 'old-ike-amr2')
#         dir_path = '/Users/hudaqureshi/clawpack/geoclaw/examples/storm-surge'
        file_path = os.path.join(dir_path,'%s_output' %w)
        paths.append(file_path)

    return paths 

# print(gather_file_paths('ike'))

def gather_data(storm): 
    r"""
    Get data from file paths.
    """
    gauges = {} 
    
    paths = gather_file_paths(storm)
    for i in range(0,len(models)): 
        gauges[models[i]] = [] 
        for x in range(0,4): 
            gauges[models[i]].append(GaugeSolution(gauge_id=x+1, path = paths[i]))
            
    return gauges 
                                
                                
def plot_data(storm):
    r"""
    Plot the data for the specified storm. 
    """
    gauges = gather_data(storm)
#     storm = storm.upper()
    
    for x in range(0,4): 
        fig = plt.figure()
        fig.set_size_inches(8, 4)
        axes = fig.add_subplot(1, 1, 1)
        for w in models: 
            line_label = "%s" %w
            days = seconds2days(gauges[w][x].t)
            #days = days - days[0]
            axes.plot(days, gauges[w][x].q[3],'--',label=line_label)
        #axes.plot(days, numpy.zeros(gauges[w][x].q[3].shape[0]), '-k', label="MSL")
            
        #axes.set_title("%s Gauge %i" %(storm,x+1),**title_font)
        #axes.set_xlabel("Days from First Tracking",**axis_font)
        #axes.set_ylabel("Height from MSL (m)",**axis_font)
        axes.set_title("%s Gauge %i" %(storm,x+1))
        axes.set_xlabel("Days from First Tracking")
        axes.set_ylabel("Height from MSL (m)")
        
        
        figure_title = "%s_Gauge_%i_SurgeHeight.pdf" %(storm,x+1)
#         gauge_path = os.path.join(os.getcwd(), 'ike-amr2') %(figure_title)
        print()
        #plt.xticks(fontsize=12)
        #plt.yticks(fontsize=12)
        plt.xticks()
        plt.yticks()
        plt.xlim(days[0],days[-1])
        #plt.legend(prop={'size': 12})
        plt.legend()
    
        fig.savefig(os.path.join(os.getcwd(), 'pdf', figure_title), format='pdf')
        plt.show()
        
#plot_data('ike')

import sys
stations = 'WXYZ'

storm = 'old-ike'
depth = [-12.8, -9.3, -8.45, -9.2]
# line_style = ['--', '-.',':', (4,6)]
lstyle = ['-', '--', '-.', ':', '-', '--', '-.', ':']
# lstyle = ['-o','--', '-.',':', '-o', 's', 'p', '*']


gauges_time = {}
gauges_mean_water = {}
adjusted_gauges_time = {}
adjusted_gauges_mean_water = {}
gauge_days = {}
gauge_data = {} 

landfall = datetime.datetime(2008, 9, 13, 7) - \
                datetime.datetime(2008, 1, 1, 0)
landfall = landfall.days + seconds2days(landfall.seconds) 

N = len(stations)
for j in range(0,N): 

    mystr = os.path.join(os.getcwd(), 'observed-gauges', 'result_%s.mat'
%stations[j])
    mat = sio.loadmat(mystr)
    gauges_time[j] = mat['yd_processed']
    gauges_mean_water[j] = mat['mean_water'].transpose()
    adjusted_gauges_time[j] = [] 
    adjusted_gauges_mean_water[j] = [] 
    for m in range(0,len(gauges_mean_water[j][0])): 
        adjusted_gauges_time[j].append(gauges_time[j][0][m])
        adjusted_gauges_mean_water[j].append(gauges_mean_water[j][0][m])
    gauge_days[j] = numpy.array(adjusted_gauges_time[j])
    gauge_data[j] = numpy.array(adjusted_gauges_mean_water[j])
    gauge_days[j] = gauge_days[j] - landfall - 1
    gauge_data[j] = gauge_data[j] + depth[j] 


    
n_rows = 2 
n_cols = 2 
fig, ax = plt.subplots(n_rows, n_cols, figsize=(16,8))
#fig.set_size_inches(10, 6)


x = 0 
for i in range(n_rows):
    for j in range(n_cols):
        geoclaw_gauges = gather_data('old-ike')
        for w in models: 
            days = seconds2days(geoclaw_gauges[w][x].t)
            ax[i, j].plot(days, geoclaw_gauges[w][x].q[3], 
                                          linestyle = lstyle[models.index(w)],
                                          linewidth = 2.0, 
                                          label=w)
            
        ax[i,j].plot(gauge_days[x], gauge_data[x],'k-', linewidth=1.5, label='Obs')
    
        ax[i,j].set_title("Gauge %i" %(x+1),**title_font)
        ax[i,j].set_xlabel("Days from Landfall",**axis_font)
        ax[i,j].set_ylabel("Surface (m)",**axis_font)
        ax[i,j].grid(True, linestyle='-',color='0.75', linewidth=1.5)
        ax[i,j].tick_params(axis='x',labelsize=10)
        ax[i,j].tick_params(axis='y',labelsize=10)
        ax[i,j].tick_params(axis='x')
        ax[i,j].tick_params(axis='y')
        #ax[i,j].legend(prop={'size': 12})
        ax[i,j].legend(fontsize=8)
        ax[i,j].set_xlim(-2,1)
        ax[i,j].set_ylim(-1,5)
        x += 1 

        
figure_title = "%s_amr2_gauge_comparisons.pdf" %(storm)
save_path = os.path.join(os.getcwd(), 'pdf', figure_title)

plt.tight_layout()
plt.savefig(save_path)
