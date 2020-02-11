#!/usr/bin/env python

"""Run specificed storms from the synthetic storms provided."""

from __future__ import print_function
from __future__ import absolute_import

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

import glob
import subprocess

import time 
import pdb  

import batch.habanero as batch

import clawpack.geoclaw.dtopotools as dtopotools

from clawpack.geoclaw.surge.storm import Storm

# Time Conversions  
def days2seconds(days):
    return days * 60.0**2 * 24.0


class StormJob(batch.HabaneroJob):

    r"""
    Class used to describe a storm 
    job run 

    Attributes
    ----------
    type : str
        a formatted string to print out the type of job
    run_number : int
        the specificed number of the storm 
    storm_directory : str
        specify the directory where jobs are saved 
    storm_object : geoclaw storm data object 
        the number of legs the animal has (default 4)

    Methods
    -------
    
    """
    def __init__(self, run_number, 
                       storm_directory,
                       storm_object, 
                       wind_model, 
                       amr_level, 
                       storm_ensemble_type, 
                       region, 
                       gauges, 
                       regions):  
        r"""
        Initialize a StormJob object.

        See :class:`StormJob` for full documentation

        """

        super(StormJob, self).__init__()

        self.type = "storm-surge"
        self.storm_ensemble_type = storm_ensemble_type
        self.region = region 
 
        self.storm_directory = storm_directory
        self.storm_object = storm_object

        self.name = "%s-amr%s" %(wind_model, amr_level)  
        self.prefix = str(run_number).zfill(4) 
        self.executable = 'xgeoclaw'

        # Data objects
        import setrun
        self.rundata = setrun.setrun()

        # Set rundata friction, surge, and clawdata variables  
        # self.rundata = setrun.set_friction(self.rundata)
        
        # Set rundata friction, surge, and clawdata variables  
        self.rundata = setrun.setgeo(self.rundata)


        # Set surge data 
        # self.rundata = setrun.set_storm(self.rundata)  
        self.rundata.surge_data.storm_specification_type = wind_model 


        self.rundata.clawdata.t0 = days2seconds(0.0) 

        # clawdata.tfinal value is the entire length of the track in days
        tf = self.storm_object.t[-1] - self.storm_object.t[0]
        self.rundata.clawdata.tfinal = days2seconds(tf.days) + tf.seconds

        # Set refinement 
        self.rundata.amrdata.amr_levels_max = amr_level 

        # Set storm wind model 
        self.rundata.surge_data.storm_specification_type = wind_model

        # Include auxillary gauge data 
        self.rundata.gaugedata.aux_out_fields = [4, 5, 6] 
 
                                                  
        # Write storm data objects 
        storm_file = "%s_%s.storm" % (self.region, self.prefix) 
        self.rundata.surge_data.storm_file = os.path.join(self.storm_directory,
                                                          storm_file)
    
        self.storm_object.write(self.rundata.surge_data.storm_file, 
                             file_format = "geoclaw")

        # Set gauges
        if gauges is not None:  
            for i in range(0, len(gauges)):
                print(i+1, gauges[i][0], gauges[i][1]) 
                self.rundata.gaugedata.gauges.append([i+1, gauges[i][0], gauges[i][1],
                             self.rundata.clawdata.t0, 
                             self.rundata.clawdata.tfinal]) 
            print(self.rundata.gaugedata.gauges) 

        # Set region data
        if regions is not None:  
            for i in range(0, len(regions)): 
                self.rundata.regiondata.regions.append([regions[i][0],
                                                regions[i][1], 
                                                self.rundata.clawdata.t0, 
                                                self.rundata.clawdata.tfinal, 
                                                regions[i][2], regions[i][3], 
                                                regions[i][4], regions[i][5]])

    def __str__(self):
        output = super(StormJob, self).__str__()
        output += "\n  Region : Long Island \n"
        output += "\n  Storm Format : %s    \n" % self.storm_ensemble_type 
        output += "    Number : %s          \n" % self.prefix
        output += "\n"
        return output

class StormHabaneroBatchController(batch.HabaneroBatchController): 

    r"""
    Modifications to the habanero batch controller for Habanero 
    storm ensemble runs. 


    :Ignored Attributes:

    Due to the system setup, the following controller attributes are ignored:

        *plot*, *terminal_output*, *wait*, *poll_interval*, *plotclaw_cmd*
    """
    def __init__(self, jobs=[]):
        r"""
        Initialize Habanero batch controller

        See :class:`HabaneroBatchController` for full documentation
        """

        super(StormHabaneroBatchController, self).__init__(jobs)

        # Habanero specific execution controls
        self.email = None 

    def run(self):
        r"""Run Habanero jobs from controller's *jobs* list.

        This run function is modified to run jobs through the slurm queue 
        system and provides controls for running serial jobs (OpenMP only).

        Unless otherwise noted, the behavior of this function is identical to
        the base class :class:`BatchController`'s function.
        """

        # Run jobs
        paths = []
        for (i, job) in enumerate(self.jobs):
            # Create output directory
            data_dirname = ''.join((job.prefix, '_data'))
            output_dirname = ''.join((job.prefix, "_output"))
            plots_dirname = ''.join((job.prefix, "_plots"))
            run_script_name = ''.join((job.prefix, "_run.sh"))
            log_name = ''.join((job.prefix, "_log.txt"))

            if len(job.type) > 0:
                job_path = os.path.join(self.base_path, job.type, job.name)
            else:
                job_path = os.path.join(self.base_path, job.name)
            job_path = os.path.abspath(job_path)
            data_path = os.path.join(job_path, data_dirname)
            output_path = os.path.join(job_path, output_dirname)
            plots_path = os.path.join(job_path, plots_dirname)
            log_path = os.path.join(job_path, log_name)
            run_script_path = os.path.join(job_path, run_script_name)
            paths.append({'job': job_path, 'data': data_path,
                          'output': output_path, 'plots': plots_path,
                          'log': log_path})

            # Create job directory if not present
            if not os.path.exists(job_path):
                os.makedirs(job_path)

            # Clobber old data directory
            if os.path.exists(data_path):
                if not job.rundata.clawdata.restart:
                    data_files = glob.glob(os.path.join(data_path, '*.data'))
                    for data_file in data_files:
                        os.remove(data_file)
            else:
                os.mkdir(data_path)

            # Write out data
            temp_path = os.getcwd()
            os.chdir(data_path)
            job.write_data_objects()
            os.chdir(temp_path)

            # Handle restart requests
            if job.rundata.clawdata.restart:
                restart = "T"
                overwrite = "F"
            else:
                restart = "F"
                overwrite = "T"

            # Construct string commands
            run_cmd = "%s %s %s %s %s %s True\n" % (self.runclaw_cmd,
                                                    job.executable,
                                                    output_path,
                                                    overwrite,
                                                    restart,
                                                    data_path)

            gauge_max_program = os.path.join(self.base_path, "scripts", "get_gauge_max.py")  
            gauge_cmd = "python %s %s %s %s %s \n" %(gauge_max_program, output_path, self.base_path, job.name, job.prefix)  

            remove_cmd = "rm -rf %s_* \n" %job.prefix  

            # Write slurm run script
            run_script = open(run_script_path, 'w')

            run_script.write("#!/bin/sh\n")
            run_script.write("#SBATCH --account apam         # Job account\n")
            run_script.write("#SBATCH -J %s                  # Job name\n" % job.prefix)
            run_script.write("#SBATCH -o %s                  # Job log \n" % log_path)
            run_script.write("#SBATCH -n 1                   # Total number of MPI tasks requested\n")
            run_script.write("#SBATCH -N 1                   # Total number of MPI tasks requested\n")
            run_script.write("#SBATCH -p %s                  # queue\n" % job.queue)
            run_script.write("#SBATCH -t 10:30:00            # run time (hh:mm:ss)\n")
            if self.email is not None:
                run_script.write("#SBATCH --mail-user=%s \n" % self.email )
            run_script.write("\n")
            run_script.write("# OpenMP controls\n")
            run_script.write("export OMP_NUM_THREADS=%s\n" % job.omp_num_threads)
            run_script.write("\n")
            run_script.write("make .exe # Construct executable \n")
            run_script.write("\n") 
            run_script.write("# Run command\n")
            run_script.write(run_cmd)
            run_script.write("\n") 
            #run_script.write("# Extract Maximum Surge \n") 
            #run_script.write(gauge_cmd)
            #run_script.write("\n")
            #run_script.write("wait") 
            run_script.write("\n")
            #run_script.write("# Remove output files \n") 
            #run_script.write(remove_cmd)  
            run_script.write("\n")  

            run_script.close()
            
            
            # Submit job to queue
            subprocess.Popen("sbatch %s > %s" % (run_script_path, log_path),
                                                 shell=True).wait()

        # -- All jobs have been started --


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
    
    #storm_file = os.path.join(os.getcwd(), directory, "SquareBasing_%s" %str(i))
    #storm.write(storm_file, file_format='geoclaw')
    
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
    tracks = os.path.join(os.getcwd(), "data", "synthetic_storm_files") 

    num_storms=1000

    #storm_gauges = [(72.811790, 18.936508), (72.972316, 18.997762), 
    #                (72.819311, 18.818044)]
    #regions_data = []
 
    #regions_data.append([2, 5, 70, 75, 17, 22])
    ## Mumbai
    #regions_data.append([4, 7, 72.6, 73, 18.80, 19.15])

    storm_gauges = None
    regions_data = None

    num_storms = 1000
 
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
            storm_name = 'SquareBasin_%s.storm' % str(n)  
            run_log_file.write("%s %s\n" % (n, '%s' %storm_name))

            # Add job to queue  
            jobs.append(StormJob(run_number           = n, 
                                 storm_directory      = tracks, 
                                 storm_object         = storm,  
                                 wind_model           = wind_model, 
                                 amr_level            = amr_level, 
                                 storm_ensemble_type  = "Synthetic", 
                                 region               = "SquareBasin", 
                                 gauges               = storm_gauges, 
                                 regions              = regions_data))
            #num_storms = 1  

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
    
    # Batch 1 (0 - 1000)  
    run_storm_job(first_storm = 0,
                   last_storm  = 1000,
                   wind_model = model, 
                   amr_level = amr_l)  
 

 
