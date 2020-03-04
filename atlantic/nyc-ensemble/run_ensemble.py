#!/usr/bin/env python

"""Run specificed storms from the synthetic storms provided."""

from __future__ import print_function

import sys
import os

import numpy
import matplotlib.pyplot as plt

import batch.habastorm as batch

import clawpack.geoclaw.dtopotools as dtopotools
import clawpack.clawutil as clawutil
import datetime
import time

from clawpack.geoclaw.surge.storm import Storm

from load_synthetic_storms import load_chaz_storms 
from load_synthetic_storms import load_obs1 

# Time Conversions  
def days2seconds(days):
    return days * 60.0**2 * 24.0


class LongIslandStormJob(batch.HabaneroStormJob):
    r"""
    Modifications to the :class:'HabaneroStormJob' for 
    Long Island Habanero storm runs 
    """

    r"""Class used to describe a storm 
    job run 

    .. attribute:: type
 
        (string) - The top most directory that the storm 
        batch output will be located in. 

    .. attribute:: prefix::
 
        (int) storms named by number
    
    .. attribute:: storm_directory
       
        (string) specify the directory where jobs are saved 

    .. attribute:: storm_object 
        
        (geoclaw storm data object 
        the number of legs the animal has (default 4)

    Methods
    -------
    
    """
     
    def __init__(self, prefix, 
                       storm_directory,
                       storm_object, 
                       wind_model, 
                       amr_level, 
                       storm_ensemble_type, 
                       region, 
                       cmip5_model):  
        r"""
        Initialize a LongIslandStormJob object.

        See :class:`LongIslandStormJob` for full documentation

        """

        super(LongIslandStormJob, self).__init__()

        self.email = None 

        self.type = "storm-surge"
        self.storm_ensemble_type = storm_ensemble_type
        self.region = region 
 
        self.storm_directory = storm_directory
        self.storm_object = storm_object

        #self.name = "%s-amr%s" %(wind_model, amr_level)  
        self.name = "%s-amr%s" %(cmip5_model, amr_level)
        self.prefix = str(prefix).zfill(4) 
        self.executable = 'xgeoclaw'

        # Data objects
        import setrun
        self.rundata = setrun.setrun()

        # Set rundata friction, surge, and clawdata variables  
        self.rundata = setrun.setgeo(self.rundata)


        # Set surge data 
        self.rundata.surge_data.storm_specification_type = wind_model 

        #delta_t0 = self.storm_object.t[0] - self.storm_object.time_offset
        #self.rundata.clawdata.t0 = days2seconds(delta_t0.days)/2 
        #self.rundata.clawdata.t0 = days2seconds(-0.5)  
        self.rundata.clawdata.t0 = days2seconds(0.0)  
        
        # clawdata.tfinal value is the entire length of the track in days
        print(self.storm_object.t[-1]) 
        print(self.storm_object.time_offset) 
        delta_tf = self.storm_object.t[-1] - self.storm_object.time_offset
        self.rundata.clawdata.tfinal = days2seconds(delta_tf.days)

        # Set refinement 
        self.rundata.amrdata.amr_levels_max = amr_level 


        # Set regions data =
        # Long Island Region 
        self.rundata.regiondata.regions = []  
        self.rundata.regiondata.regions.append([1, 7, self.rundata.clawdata.t0, 
                                                      self.rundata.clawdata.tfinal, 
                                                      -74.1, -73.7, 40.55, 48.5])

        # Set Gauge Data 
        # for gauges append lines of the form  [gaugeno, x, y, t1, t2]
        self.rundata.gaugedata.gauges = []
        # Gauge 1 
        #self.rundata.gaugedata.gauges.append([1, -73.84055, 40.44838,
        #                                    self.rundata.clawdata.t0, 
        #                                    self.rundata.clawdata.tfinal]) 
        ## Gauge 2  
        #self.rundata.gaugedata.gauges.append([2, -73.33605, 40.62581,
        #                                    self.rundata.clawdata.t0, 
        #                                    self.rundata.clawdata.tfinal])
        #
        #self.rundata.gaugedata.gauges.append([3, -73.76252, 40.56637,
        #                                    self.rundata.clawdata.t0, 
        #                                    self.rundata.clawdata.tfinal]) 
        #
        #self.rundata.gaugedata.gauges.append([4, -74.09573, 40.49226,
        #                                    self.rundata.clawdata.t0, 
        #                                    self.rundata.clawdata.tfinal])
        #
        #self.rundata.gaugedata.gauges.append([5, -73.93428, 40.51212, 
        #                                    self.rundata.clawdata.t0, 
        #                                    self.rundata.clawdata.tfinal]) 
        #
        self.rundata.gaugedata.gauges.append([1, -73.82716, 40.47975,
                                            self.rundata.clawdata.t0, 
                                            self.rundata.clawdata.tfinal]) 
        
        self.rundata.gaugedata.gauges.append([2, -73.91643, 40.40659,
                                            self.rundata.clawdata.t0, 
                                            self.rundata.clawdata.tfinal]) 
        # Sea Gauge 1 for coasrse refinements 
        self.rundata.gaugedata.gauges.append([3, -73.82854, 40.26235, 
                                            self.rundata.clawdata.t0, 
                                            self.rundata.clawdata.tfinal]) 
       
        # Sea Gauge 2 for coarse refinements  
        self.rundata.gaugedata.gauges.append([4, -73.49758, 40.46744, 
                                            self.rundata.clawdata.t0, 
                                            self.rundata.clawdata.tfinal]) 
        # Include auxillary gauge data 
        self.rundata.gaugedata.aux_out_fields = [4, 5, 6] 
 
                                                  
        # Set path to geoclaw storm file  
        self.rundata.surge_data.storm_file = os.path.join(self.storm_directory,
                                       "%s_%s.storm" %(self.region, self.prefix))
    
        # Write storm data in geoclaw storm file  
        self.storm_object.write(self.rundata.surge_data.storm_file, 
                                            file_format = "geoclaw")


    def __str__(self):
        output = super(LongIslandStormJob, self).__str__()

        output += "{:<20}{:<1}{:<15}{:<1}".format("Region", ": ", "Long Island","\n")
        output += '{:<20}{:<1}{:<15}{:<1}'.format("Storm Format", ": ", "%s"
                                                %self.storm_ensemble_type, "\n")
        output += '{:<20}{:<1}{:<15}{:<1}'.format("Number", ": ", "%s" %self.prefix, "\n")
        
        return output


def run_longisland_job(wind_model  = 'holland80',
                       amr_level   = 2, 
                       cmip5_model = None, 
                       storms     = None):  
    r"""
    Setup jobs to run at specific storm start and end.  
    """

    storm_tracker = storms[0].ID + len(storms)  
    # Path to file containing log of storms run
    path = os.path.join(os.environ.get('DATA_PATH', os.getcwd()), 
                   "new_york", 
                   "LongIsland-storm-%i-%i" %(storms[0].ID, storm_tracker),
                   "run_log.txt")
    #print(path) 

    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path))

 
    data_path = os.path.join(os.getcwd(), "../../../data")
    storms_path = os.path.join(data_path, "storms") 
    tracks = os.path.join(storms_path, "geoclaw-longisland-tracks")

    jobs = []  
    with open(path, 'w') as run_log_file: 
        jobs = []

        location = "LongIsland" 
    
        # Run through list of storms and create 
        # Create storm name through storm ID and location
        # Write to log file and create job 
        for storm in storms:  
            storm_name = "%s_%s" %(location, str(storm.ID))
            run_log_file.write("%s %s\n" % (storm.ID, storm_name))
    
            # Create job and add to queue 
            jobs.append(LongIslandStormJob(prefix = storm.ID, 
                                 storm_directory      = tracks, 
                                 storm_object         = storm, 
                                 wind_model           = wind_model, 
                                 amr_level            = amr_level, 
                                 storm_ensemble_type  = "Chaz", 
                                 region               = "LongIsland", 
                                 cmip5_model          = cmip5_model))
        
        print('Jobs created sent to controller')
        print("")   
        # Jobs are all created now we run 
        # the jobs using the batch 
        # controller  
        controller = batch.HabaneroStormBatchController(jobs)
        #controller.email = 'hq2152@columbia.edu'
        print(controller)
        controller.run()
        jobs = []

    return len(jobs)  
         


if __name__ == '__main__':
    r"""
    Run Batch jobs.    
    """
    

    if len(sys.argv) == 1: 
        model = 'holland80'
        amr_l = 2 
    else: 
        model = str(sys.argv[1])
        amr_l = int(sys.argv[2]) 

    

    #test = False 
    test = True  
    cmip5_models = ['CCSM4', 'GFDL_CM3', 'HadGEM2_ES', 'MIROC5', 'MPI_ESM_MR',
                    'MRI_CGCM3', 'OBS']
    climate_model = cmip5_models[0]
    wind_models = ['holland80', 'holland10', 'SLOSH', 'rankine', 'CLE',
'modified-rankine', 'DeMaria'] 

    # Adjust mask distance and mask speed
    md = 1.0 
    ms = None  

    experiment = "SD" 

    # SD HIST Storms 
    # Run set of storms with sd experiment
    # data_file = 'LongIsland_obs_tracks_150.nc' 
    data_file = 'LongIsland_CHAZ_%s_wdir_TCGI_%s_PI_HIST.nc' %(climate_model, experiment)

    storms = load_chaz_storms(path=os.path.join('/rigel/home/hq2152',
                                        experiment, data_file), 
                                        mask_distance = md,  
                                        mask_coordinate = (-74.0060, 40.7128),
                                        mask_category = ms,  
                                        categorization="NHC")

    # Counter to track number of jobs 
    # in one batch should not exceed
    # 500 storms
    # N determines the full number of
    # storms we might run.  
    jobs_counter = 0
    if test: 
        N = 1 
    else: 
        N = len(storms)  
   
    while jobs_counter < N: 
        if (500 + jobs_counter > N): 
            jobs_batch = N
        else:
            jobs_batch = 500 + jobs_counter

        num_storms = jobs_batch - jobs_counter 
        print('Create %i jobs' %(num_storms)) 
        run_longisland_job(wind_model  = model, 
                           amr_level   = amr_l,  
                           cmip5_model = climate_model, 
                           storms      = storms[jobs_counter : jobs_batch])

        jobs_counter = jobs_batch 
