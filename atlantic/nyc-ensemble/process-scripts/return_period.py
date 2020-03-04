import numpy
import matplotlib.pyplot as plt
plt.switch_backend('agg')

import os

import clawpack.geoclaw.units as units
import clawpack.geoclaw.surge.storm as storm

import sys 

from netCDF4 import Dataset

gauges=[0, 1, 2, 3, 4, 5, 6, 7, 8] 
#gauges=[0, 1, 2, 3] 


def calculate_surge(path=None, plot_output=None, job_name=None, agg_data=None,
climate_model=None): 
     

    if agg_data is None: 
        storm_gauges_file = os.listdir(path)
        gauge_surge = numpy.ones((8, len(storm_gauges_file)), dtype = float)


        for (index, storm_gauges) in enumerate(storm_gauges_file): 
            with open(os.path.join(path,storm_gauges), 'r') as gauges_data: 
                data = numpy.loadtxt(gauges_data, delimiter = ',', skiprows=1)
                gauge_surge[:, index] = data[:, 1]

    else: 
        gauge_surge = agg_data[climate_model]

    colors = ['b', 'g', 'r', 'k', 'c', 'm', 'y'] 

    for i in range(0, len(gauges)):

        
        bar_width = 1.0 
        opacity = 1.0

        gauge_label = "Gauge %s" %(i+1) 
       
        events_surge = numpy.zeros((1, gauge_surge.shape[1])) 
        events_surge[0, :] = gauge_surge[i, :]


        bin_edges = (numpy.amin(events_surge), numpy.amax(events_surge))
        bins_surge = numpy.linspace(bin_edges[0], bin_edges[1]+1, 60)
        period = 460*23 
      
        index = gauge_surge.shape[1] - 1    
        hist, bin_edges = numpy.histogram(events_surge, bins_surge) 
        index_edges = numpy.ones(bin_edges.shape) * (index + bar_width)
        n = hist.sum() 
        
        # Complement of empirical distribution function
        ECDF_c = numpy.cumsum(hist[::-1])[::-1] * 1/n
        ECDF = numpy.ones(ECDF_c.shape, dtype = float) - ECDF_c

        return_period = period * 1/n * (1/ECDF_c)


        T_r = numpy.zeros(events_surge.shape, dtype=float)

        events_surge = numpy.sort(events_surge)

        counter = 0

        for j in range(events_surge.shape[1]):
            if events_surge[0,j] < bin_edges[counter]:
                T_r[0,j] = return_period[counter]
            else:
                counter += 1
                T_r[0,j] = return_period[counter]
        
        fig = plt.figure() 
        fig.set_figwidth(fig.get_figwidth() * 2)

        title_font = {'fontname':'Arial', 'size':'12', 'color':'black', 'weight':'normal',
                  'verticalalignment':'bottom'} # Bottom vertical alignment for more space
        axis_font = {'fontname':'Arial', 'size':'12'}

        # First Plot 
        axes = fig.add_subplot(2, 2, 1) 
        axes.bar(index_edges[:-1] + bin_edges[:-1], ECDF_c, bar_width,
                        label = gauge_label, color = colors[0],
                        alpha = opacity)
        axes.set_xlabel('Meters', **axis_font)
        axes.set_ylabel('CDF', **axis_font)
        axes.set_title('Long Island %s' %gauge_label, **title_font)
        axes.legend()
        

        # Second Plot 
        axes = fig.add_subplot(2, 2, 2)  
        axes.plot(T_r[0, :], events_surge[0, :],  
                label = gauge_label, color = colors[0])
        axes.set_xlabel('Return Period (Years)', **axis_font)
        axes.set_ylabel('Surge (meters)', **axis_font)
        axes.set_title('Long Island %s' %gauge_label, **title_font)
        #axes.set_xlim(0,5000) 
        #axes.set_ylim(20,150) 
        axes.legend()


        # Third plot 
        axes = fig.add_subplot(2, 2, 3)  
        axes.plot(range(events_surge.shape[1]), events_surge[0, :],
                label = gauge_label, color = colors[0]) 
        axes.set_xlabel('Surge Event Index', **axis_font)
        axes.set_ylabel('Surge (meters)', **axis_font)
        axes.set_title('Long Island %s' %gauge_label, **title_font)
        axes.legend()
    
    
        plt.yticks(fontsize=10)
        plt.xticks(fontsize=10)
        plt.tight_layout()
        plot_path = os.path.join(plot_output, 'Chaz-NYC-%s-Gauge-%s.pdf' %(job_name, i+1))
        plt.savefig(plot_path)
    
    return fig

def process_data(base_path, gauge_data_dir, job_name):
    r"""
    Transform all seperate text files 
    into one master file. 
    """ 
    
    # Collect all gauge files and put them into one array
    storm_gauges_files = os.listdir(gauge_data_dir) 
    g = numpy.zeros((len(gauges), len(storm_gauges_files))) 
     
    #for storm_gauges in storm_gauges_files: 
    #    data_path = os.join(gauage_data_dir, storm_gauges)
    #    for i in range(0, len(gauges)): 
            
    for (index, storm_gauges) in enumerate(storm_gauges_file): 
        with open(os.path.join(gauge_data_dir ,storm_gauges), 'r') as gauges_data: 
            data = numpy.loadtxt(gauges_data, delimiter = ',', skiprows=1) 
            g[:, index] = data[:, 1]

    return g 
        



if __name__ == '__main__':

    #base_path = sys.argv[1]
    #job_name = sys.argv[2]
    #plot_output = os.path.join(base_path, "MaxSurge", "Gauge-Plots")
    #path = os.path.join(base_path, "MaxSurge", job_name)


    base_path = "/rigel/apam/users/hq2152/test-surge-examples/atlantic/chaz-storms" 

    #cmip5_models = ['CCSM4', 'GFDL_CM3', 'HadGEM2_ES', 'MIROC5', 'MPI_ESM_MR',
    #                'MRI_CGCM3']
    cmip5_models = ['HadGEM2_ES']
    amr_level = 2
    agg_gauge_data = {} 

    for climate_model in cmip5_models: 
        job_name = "%s-amr%s" %(climate_model, str(amr_level)) 
        plot_output = os.path.join(base_path, "max-surge", "gauge-plots") 
        gauge_data_path = os.path.join(base_path, "max-surge", job_name)
        
        storm_gauges_file = os.listdir(gauge_data_path)
        #print(storm_gauges_file)
        #print(len(storm_gauges_file))
        m = process_data(base_path=base_path, gauge_data_dir = gauge_data_path, job_name
                                = job_name)
        agg_gauge_data[climate_model] = m 
    #print(agg_gauge_data) 
    #gauge_surge = numpy.ones((6, len(storm_gauges_file)), dtype = float) 

        #base_path = "/rigel/apam/users/hq2152/test-surge-examples/new-storm-module/atlantic/chaz-storms" 
        #job_name = "holland80-amr5" 
        #plot_output = ''.join((base_path, "MaxSurge", "Gauge-Plots")) 
        #base_path = sys.argv[1]
        #job_name = sys.argv[2]
        #plot_output = sys.argv[3] 
        #path = os.path.join(base_path, "MaxSurge", job_name)


    print(plot_output) 
    if not os.path.exists(plot_output): 
        os.mkdir(plot_output)

    calculate_surge(gauge_data_path, plot_output, job_name, agg_gauge_data, climate_model)  
