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


class SquareBasinStormJob(batch.HabaneroStormJob):
    r"""
    Modifications to the :class:'HabaneroStormJob' for 
    Long Island Habanero storm runs 
    """

    r"""Class used to describe a storm 
    job run 

    .. attribute:: type
 
        (string) - The top most directory that the storm 
        batch output will be located in. 

    .. attribute:: run_number::
 
        (int) storms named by number
    
    .. attribute:: storm_directory
       
        (string) specify the directory where jobs are saved 

    .. attribute:: storm_object 
        
        (geoclaw storm data object 
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
        Initialize a SquareBasinStormJob object.

        See :class:`SquareBasinStormJob` for full documentation

        """

        super(SquareBasinStormJob, self).__init__()
        
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
        output = super(SquareBasinStormJob, self).__str__()

        output += "{:<20}{:<1}{:<15}{:<1}".format("Region", ": ", "Long Island","\n")
        output += '{:<20}{:<1}{:<15}{:<1}'.format("Storm Format", ": ", "%s"
                                                %self.storm_ensemble_type, "\n")
        output += '{:<20}{:<1}{:<15}{:<1}'.format("Number", ": ", "%s" %self.prefix, "\n")
        
        return output


def run_squarebasin_job(first_storm     = 0,
                       last_storm      = 0,
                       wind_model      = 'holland80',
                       amr_level       = 2, 
                       cmip5_model     = None, 
                       chaz_storms     = None):  
    r"""
    Setup jobs to run at specific storm start and end.  
    """
    print('Initiated run_squarebasin_job') 
 
    # Path to file containing log of storms run
    path = os.path.join(os.environ.get('DATA_PATH', os.getcwd()), 
                        "new_york", "SquareBasin-storm-%i-%i" %(first_storm, last_storm),
                        "run_log.txt")
    #print(path) 

    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path))

 
    data_path = os.path.join(os.getcwd(), "../../../data")
    storms_path = os.path.join(data_path, "storms") 
    tracks = os.path.join(storms_path, "geoclaw-squarebasin-tracks")

    jobs = []  
    test = True 
    with open(path, 'w') as run_log_file: 
        jobs = []

        location = "SquareBasin" 
        for (i, storm) in enumerate(storms): 
            storm_name = "%s_%s" %(location, str(i))
            run_log_file.write("%s %s\n" % (i, '%s' %storm_name))
    
            # Create job and add to queue 
            jobs.append(SquareBasinStormJob(run_number = i, 
                                 storm_directory      = tracks, 
                                 storm_object         = storm, 
                                 wind_model           = wind_model, 
                                 amr_level            = amr_level, 
                                 storm_ensemble_type  = "Chaz", 
                                 region               = "SquareBasin", 
                                 cmip5_model          = cmip5_model))
        
        if test: 
            jobs = [jobs[0]] 
            controller = batch.HabaneroStormBatchController(jobs)
            controller.email = 'hq2152@columbia.edu'
            print(controller)
            controller.run()
            jobs = []
        else:     
            controller = batch.HabaneroStormBatchController(jobs)
            controller.email = 'hq2152@columbia.edu'
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
    # data_file = 'SquareBasin_obs_tracks_150.nc' 
    data_file = 'LongIsland_CHAZ_%s_wdir_TCGI_%s_PI_HIST.nc' %(climate_model, experiment)

    storms = load_chaz_storms(path=os.path.join('/rigel/home/hq2152',
                                        experiment, data_file), 
                                        mask_distance = md,  
                                        mask_coordinate = (-74.0060, 40.7128),
                                        mask_category = ms,  
                                        categorization="NHC")
    # Initial Run for Cmip5 model 
    # CCSM4 [0] 

    change_wind_model = False  
 
    i = 0
    j = 5

    run = True  

    # Number of storms 
    N = len(storms) 
    # N = 2  

    while i < N and run: 
        if (500 + i) > N:
            j = N
        else: 
            j = 500 + i 
        run_squarebasin_job(first_storm = i,
                           last_storm  = j,
                           wind_model  = model, 
                           amr_level   = amr_l,  
                           cmip5_model = climate_model, 
                           chaz_storms = storms) 
        i = j

    if not run: 
        run_squarebasin_job(first_storm = i,
                           last_storm  = j,
                           wind_model  = model, 
                           amr_level   = amr_l,  
                           cmip5_model = climate_model, 
                           chaz_storms = storms) 
         
            
