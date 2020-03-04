#!/usr/bin/env python

"""Run specificed storms from the synthetic storms provided."""

from __future__ import print_function

import sys
import os

import numpy
import matplotlib.pyplot as plt

import batch.habastorm as batch

import clawpack.geoclaw.dtopotools as dtopotools
import datetime
import time

from clawpack.geoclaw.surge.storm import Storm

from load_synthetic_storms import load_emanuel_storms  

 
import clawpack.clawutil as clawutil

# Time Conversions  
def days2seconds(days):
    return days * 60.0**2 * 24.0

#
class MumbaiStormJob(batch.HabaneroStormJob):

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

    .. attribute:: storm 
        
        (geoclaw storm data object 
        the number of legs the animal has (default 4)

    Methods"""
    
    def __init__(self, prefix, 
                       storm_directory,
                       storm, 
                       wind_model, 
                       amr_level, 
                       storm_ensemble_type, 
                       region):  
        r"""
        Initialize a MumbaiStormJob object.

        See :class:`MumbaiStormJob` for full documentation

        """

        super(MumbaiStormJob, self).__init__()

        self.type = "storm-surge"
        self.storm_ensemble_type = storm_ensemble_type
        self.region = region 
 
        self.storm_directory = storm_directory
        self.storm = storm

        self.name = "%s-amr%s" %(wind_model, amr_level)  
        self.prefix = str(prefix).zfill(4) 
        self.executable = 'xgeoclaw'

        # Data objects
        import setrun
        self.rundata = setrun.setrun()

        # Set rundata friction, surge, and clawdata variables  
        self.rundata = setrun.set_friction(self.rundata)

        # Set surge data 
        self.rundata = setrun.set_storm(self.rundata)  
        self.rundata.surge_data.storm_specification_type = wind_model 

        # Determine time offse
        x_domain = numpy.abs([self.rundata.clawdata.lower[0], self.rundata.clawdata.upper[0]])  
        y_domain = numpy.abs([self.rundata.clawdata.lower[1], self.rundata.clawdata.upper[1]])
        x = storm.eye_location[:, 0] 
        y = storm.eye_location[:, 1] 
        for b in range(0, len(x)): 
            if numpy.abs(x[b]) >= (x_domain[0]) and numpy.abs(x[b]) <= (x_domain[1]): 
                if numpy.abs(y[b]) >= (y_domain[0]) and numpy.abs(y[b]) <= (y_domain[1]): 
                    #storm.time_offset = (storm.t[b],b)
                    self.storm.time_offset = self.storm.t[b]
                    break 
        
       
        # Set initial time  
        #delta_t0 = self.storm.t[0] - self.storm.time_offset
        #self.rundata.clawdata.t0 = days2seconds(delta_t0.days)/2 
        self.rundata.clawdata.t0 = days2seconds(0.0)  

        # clawdata.tfinal value is the entire length of the track in days
        tf = self.storm.t[-1] - self.storm.t[0]
        self.rundata.clawdata.tfinal = days2seconds(tf.days) + tf.seconds

        # Set refinement 
        self.rundata.amrdata.amr_levels_max = amr_level 
         
        # == setregions.data values ==
        # Mumbai Region  
        self.rundata.regiondata.regions.append([2, 5, self.rundata.clawdata.t0, 
                                                      self.rundata.clawdata.tfinal,
                                                      70, 75, 17, 22])
        # Mumbai 
        self.rundata.regiondata.regions.append([4, 7, days2seconds(1.0),  
                                                      self.rundata.clawdata.tfinal,
                                                      72.6, 73, 18.80, 19.15])

        # Set Gauge Data 
        # for gauges append lines of the form  [gaugeno, x, y, t1, t2]
        self.rundata.gaugedata.gauges = [] 
        self.rundata.gaugedata.gauges.append([1, 72.811790, 18.936508,
                                            self.rundata.clawdata.t0, 
                                            self.rundata.clawdata.tfinal])  
        self.rundata.gaugedata.gauges.append([2, 72.972316, 18.997762,
                                            self.rundata.clawdata.t0, 
                                            self.rundata.clawdata.tfinal])  
        self.rundata.gaugedata.gauges.append([3, 72.819311, 18.818044,
                                            self.rundata.clawdata.t0, 
                                            self.rundata.clawdata.tfinal])  
        self.rundata.gaugedata.gauges.append([4, 72.50, 18.50,
                                            self.rundata.clawdata.t0, 
                                            self.rundata.clawdata.tfinal]) 

        # Include auxillary gauge data 
        self.rundata.gaugedata.aux_out_fields = [4, 5, 6] 
        
        # Write storm data objects 
        storm_file = "%s_%s.storm" % (self.region, self.prefix) 
        self.rundata.surge_data.storm_file = os.path.join(self.storm_directory,
                                                          storm_file)

        self.storm.write(self.rundata.surge_data.storm_file, 
                                 file_format = "geoclaw")
 

    def __str__(self):

        output = super(MumbaiStormJob, self).__str__()

        output += "{:<20}{:<1}{:<15}{:<1}".format("Region", ": ", "Mumbai","\n")
        output += '{:<20}{:<1}{:<15}{:<1}'.format("Storm Format", ": ", "%s"
                                                %self.storm_ensemble_type, "\n")
        output += '{:<20}{:<1}{:<15}{:<1}'.format("Number", ": ", "%s" %self.prefix, "\n")

        return output

def run_mumbai_job(wind_model  = 'holland80',
                   amr_level   = 2, 
                   storms     = None):  
    r"""
    Setup jobs to run at specific storm start and end.  
    """

    storm_tracker = storms[0].ID + len(storms)  
    # Path to file containing log of storms run

    path = os.path.join(os.getcwd(), "mumbai", 
                        "%s-%i-%i-%i" %(wind_model, amr_level, 
                                        storms[0].ID, storm_tracker), 
                        "run_log.txt") 
    #path = os.path.join(os.environ.get('DATA_PATH', os.getcwd()), 
    #               "mumbai", 
    #               "holland80-amr2-%i-%i" %(wind_model, amr_level, storms[0].ID, storm_tracker),
    #               "run_log.txt")
    print(path) 

    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path))

 
    data_path = os.path.join(os.getcwd(), "../../../data")
    storms_path = os.path.join(data_path, "storms") 
    tracks = os.path.join(storms_path, "geoclaw-mumbai-tracks")

    jobs = []  
    with open(path, 'w') as run_log_file: 
        jobs = []

        location = "Mumbai"
        
        # Run through list of storms and create 
        # Create storm name through storm ID and location
        # Write to log file and create job 
        for storm in storms:  
            storm_name = "%s_%s" %(location, str(storm.ID))
            run_log_file.write("%s %s\n" % (storm.ID, storm_name))
    
            # Create job and add to queue
            # with specified storm, directory path to storm
            # geoclaw data file, the specified wind model, 
            # and the max amr level 
            jobs.append(MumbaiStormJob(prefix = storm.ID, 
                                      storm_directory      = tracks, 
                                      storm                = storm, 
                                      wind_model           = wind_model, 
                                      amr_level            = amr_level, 
                                      storm_ensemble_type  = "Emanuel", 
                                      region               = "Mumbai"))
                
     
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
    
    # Default batch run 

    print(sys.argv)
    if len(sys.argv) == 1: 
        model = 'holland80'
        amr_l = 2
    else: 
        model = str(sys.argv[1])
        amr_l = int(sys.argv[2])


    # test = True 
    test = False  
    # Run all storms, but only adjust wind model 
    # wind_models = ['holland80', 'holland10', 'SLOSH', 'rankine', 'CLE',
    # 'modified-rankine', 'DeMaria'] 
    md = None  
    ms = None 

    data_file = "Mumbai3_io_ncep_reanalcal.mat"  

    storms = load_emanuel_storms(path=os.path.join('/rigel/home/hq2152', data_file), 
                                        mask_distance = md,  
                                        mask_coordinate = (72.8562, 19.0176),  
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


        # Wind Models 
        # holland80
        # holland10
        # SLOSH
        # rankine
        # CLE
        # modified-rankine
        # DeMaria
        num_storms = jobs_batch - jobs_counter
        print('Create %i jobs' %(num_storms))   
        run_mumbai_job(wind_model  = model,
                       amr_level   = amr_l,  
                       storms      = storms[jobs_counter : jobs_batch])

        # Update the jobs counter so we can do the next selection 
        jobs_counter = jobs_batch 
 
