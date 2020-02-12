#!/usr/bin/env python

"""Run specificed storms from the synthetic storms provided."""

from __future__ import print_function

import sys
import os

import numpy
#import matplotlib.pyplot as plt

import batch.habanero as batch

import clawpack.geoclaw.dtopotools as dtopotools
import datetime
import time

from clawpack.geoclaw.surge.storm import Storm

import clawpack.clawutil as clawutil

# Time Conversions  
def days2seconds(days):
    return days * 60.0**2 * 24.0


class StormJob(batch.HabaneroJob):

    r"""Class used to describe a storm 
    job run 

    ...

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
    def __init__(self, wind_model, 
                       amr_level, 
                       storm, 
                       region):  
        r"""
        Initialize a StormJob object.

        See :class:`StormJob` for full documentation

        """

        super(StormJob, self).__init__()

        self.type = "storm-surge"
        self.storm = storm 
        self.region = region 
 
        self.name = "%s-amr%s" %(storm, str(amr_level))  
        self.prefix = "%s" %(wind_model)  
        self.executable = 'xgeoclaw'

        # Data objects
        import setrun
        self.rundata = setrun.setrun()

        self.rundata.surge_data.storm_specification_type = wind_model
        self.rundata.amrdata.amr_levels_max = amr_level


    def __str__(self):
        output = super(StormJob, self).__str__()
        output += "\n  Region       : %s \n" % self.region
        output += "\n  Storm        : %s \n" % self.storm  
        output += "\n  Wind Model   : %s \n" % self.prefix
        output += "\n"
        return output


def run_storm(wind_models = None, amr_level = None, 
                    storm = None, region = None): 
            
    r"""
    Setup jobs to run the storm ike using all 
    the wind models we give it.  

    Input: 
    
    
    """

    if storm or region is None: 
        return "Please provide a storm and a region."  

    # Default if no parameters given 
    if wind_models is None: 
        wind_models = ["holland80"] 
    
    if amr_level is None: 
        amr_level = 2 

    print('Initiated run ike storm.')
    
    # Path to file containing log of storms run
    #path = os.path.join(os.environ.get('DATA_PATH', os.getcwd()), 
    #                    "ike",
    #                    "run_log.txt")

    #print('Path to log file created')
    #print('path: %s' %path)
    #print("") 
  
    #if not os.path.exists(path):
    #    os.makedirs(os.path.dirname(path))


    jobs = []  
    #with open(path, 'w') as run_log_file: 

    for model in wind_models:
        print('model: %s' %model)  
        #run_log_file.write("Ike Amr%s %s \n" % (str(amr_level), model))
        jobs.append(StormJob(model, amr_level, storm))  

    controller = batch.HabaneroBatchController(jobs)
    controller.email = 'hq2152@columbia.edu'
    print(controller)
    controller.run()
    jobs = []

    return len(jobs)  
         


if __name__ == '__main__':
    r"""
    Run Batch jobs.    
    """
    

    #models = ['holland80', 'holland10', 'SLOSH', 'rankine', 'CLE',
    #               'modified-rankine', 'DeMaria'] 
    models = ['CLE']

    #run_storm(wind_models = models, amr_level = 2, storm='katrina')  
    #run_storm(storm='katrina', region='gulf') 
    run_storm() 
