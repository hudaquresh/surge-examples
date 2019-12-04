#!/usr/bin/env python

"""Run specificed storms from the synthetic storms provided."""

from __future__ import print_function

import sys
import os

import numpy
import matplotlib.pyplot as plt

import batch.habanero as batch

import clawpack.geoclaw.dtopotools as dtopotools
import datetime
import time

from clawpack.geoclaw.surge.storm import Storm
import clawpack.clawutil as clawutil

from storm_habanero import StormJob
from storm_habanero import StormHabaneroBatchController

import os
import numpy 

from clawpack.geoclaw.surge.storm import Storm 
import copy


# Piecewise wind curve with a max
def piecewise_wind_curve(U0, T): 
    r"""
    Returns a piecewise 
    continuous wind curve. 
    """
    N = T.shape[0]
    max_index = int((N - 1)/2) 
    
    # Intialize the wind speed vector 
    U = numpy.zeros(N)
    
    # Set initial wind speed at first time
    U[0] = U0
    dU = 1 
    
    for i in range(1, N): 
        if T[i] <= T[max_index]: 
            U[i] = U[i-1] + dU
        elif T[i] > T[max_index]: 
            U[i] = U[i-1] - dU

    return U 


def perturb_wind(max_wind_speed): 
    r"""
    Perturb the wind and return the new array
    """
    for i in range(0, max_wind_speed.shape[0]): 
        error = numpy.random.normal(loc = 1)
        max_wind_speed[i] = max_wind_speed[i] + error 

    return max_wind_speed 





directory = "data/synthetic_storm_files"
if not os.path.exists(os.path.join(os.getcwd(), directory)):
    os.makedirs(directory)
    
# File to tracy synthetic storm in atcf format 
tracy_atcf_path = 'data/tracy_synthetic_atcf.storm'

# Establish a control form of tracy 
control = Storm(path = tracy_atcf_path, file_format = 'ATCF')
control.read_atcf(path = tracy_atcf_path)

# Change tracy to piece wise constant wind curve 
u0 = control.max_wind_speed[1]
control.max_wind_speed = piecewise_wind_curve(u0, control.max_wind_speed)
control.write("data/tracy_geoclaw.storm", file_format = "geoclaw")
    
perturbed_radii = []
perturbed_winds = []

# Create storm objects with perturbed wind data 
for i in range(0, 1000): 
    storm = copy.copy(control)
    mws = copy.copy(control.max_wind_speed)
    mws = perturb_wind(mws)
    C0 = 218.3784 * numpy.ones(len(mws))
    mwr = C0 - 1.2014 * mws + (mws / 10.9884)**2 - (mws/ 35.3052)**3 - 145.5090 * numpy.cos(control.eye_location[:, 1] * 0.0174533)
    storm.max_wind_speed = mws 
    storm.max_wind_radius = mwr 
    
    storm_file = os.path.join(os.getcwd(), directory, "synthetic_%s" %str(i))
    storm.write(storm_file, file_format='geoclaw')
    
#     perturbed_radii.append(mwr)
#     perturbed_winds.append(mws)
 

def run_storm_job(first_storm = 0,
                   last_storm = 0,
                   wind_model = 'holland80',
                   amr_level = 2):  
    r"""
    Setup jobs to run at specific storm start and end.  
    """
    
    # Path to file containing log of storms run
    path = os.path.join(os.environ.get('DATA_PATH', os.getcwd()), 
                        "square_basin", "square-basin-storm-%i-%i" %(first_storm, last_storm),
                        "run_log.txt")

    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path))

    # File to tracy synthetic storm in atcf format 
    tracy_atcf_path = 'data/tracy_synthetic_atcf.storm'
    
    # Establish a control form of tracy 
    control = Storm(path = tracy_atcf_path, file_format = 'ATCF')
    control.read_atcf(path = tracy_atcf_path)
    
    # Change tracy to piece wise constant wind curve 
    u0 = control.max_wind_speed[1]
    control.max_wind_speed = piecewise_wind_curve(u0, control.max_wind_speed)
    control.write("data/tracy_geoclaw.storm", file_format = "geoclaw")
    
    # Get a general storm path 
    #data_path = os.path.join(os.getcwd(), "../../../data")
    #storms_path = os.path.join(data_path, "storms")
    #tracks = os.path.join(storms_path, "geoclaw-mumbai-tracks") 
    tracks = os.path.join("data", "synthetic_storm_files") 

    num_storms=1000

    #storm_gauges = [(72.811790, 18.936508), (72.972316, 18.997762), 
    #                (72.819311, 18.818044)]
    #regions_data = []
 
    #regions_data.append([2, 5, 70, 75, 17, 22])
    ## Mumbai
    #regions_data.append([4, 7, 72.6, 73, 18.80, 19.15])

    storm_gauges = None
    regions_data = None

    num_storms = 10
 
    with open(path, 'w') as run_log_file: 
        jobs = []

        for n in range(0, num_storms): 
 
            storm = copy.copy(control)
            mws = copy.copy(control.max_wind_speed)
            mws = perturb_wind(mws)
            C0 = 218.3784 * numpy.ones(len(mws))
            mwr = C0 - 1.2014 * mws + (mws / 10.9884)**2 - (mws/ 35.3052)**3 - 145.5090 * numpy.cos(control.eye_location[:, 1] * 0.0174533)
            
            storm.max_wind_speed = mws 
            #storm.max_wind_radius = mwr
 
            # Name storm file and write to log  
            storm_name = 'synthetici_%s.storm' % str(n)  
            run_log_file.write("%s %s\n" % (n, '%s' %storm_name))

            # Add job to queue  
            jobs.append(StormJob(run_number           = n, 
                                 storm_directory      = tracks, 
                                 storm_object         = storm,  
                                 wind_model           = wind_model, 
                                 amr_level            = amr_level, 
                                 storm_ensemble_type  = "Synthetic", 
                                 region               = "Square Basin", 
                                 gauges               = storm_gauges, 
                                 regions              = regions_data))
            num_storms = 1  

            if n == num_storms-1:
               #controller = StormHabaneroBatchController(jobs)
               controller = batch.HabaneroBatchController(jobs)
               controller.email = 'hq2152@columbia.edu'
               print(controller)
               controller.run()
               jobs = []
               break 
    return jobs  
         


if __name__ == '__main__':
    r"""
    Run Batch jobs.    
    """
    
    # Default batch run 

    if len(sys.argv) == 1: 
        model = 'holland80'
        amr_l = 2 
    else: 
        model = str(sys.argv[1])
        amr_l = int(sys.argv[2]) 
    
    # Batch 1 (0-599) 
    run_storm_job(first_storm = 0,
                   last_storm  = 0,
                   wind_model = model, 
                   amr_level = amr_l)  
 
    ## Batch 2 (600-1199) 
    #run_storm_job(first_storm = 600,
    #               last_storm  = 679,
    #               wind_model = model, 
    #               amr_level = amr_l) 

    ### Batch 3 (1200-1849) 
    ##run_storm_job(first_storm = 1200,
    ##               last_storm  = 1300,
    ##               wind_model = model, 
    ##               amr_level = amr_l) 

 
