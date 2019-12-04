#!/usr/bin/env python

"""Run specificed storms from the synthetic storms provided."""

from __future__ import print_function
from __future__ import absolute_import

import os
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
