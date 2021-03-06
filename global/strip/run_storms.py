#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

import os
import sys

import numpy

# from batch.habanero import HabaneroJob as Job
# from batch.habanero import HabaneroBatchController as BatchController
from batch import Job, BatchController

import clawpack.geoclaw.surge.storm


class StormJob(Job):
    r"""Run a number of jobs specific to storm surge"""

    def __init__(self, storm, storm_number):
        r"""
        Initialize Habanero storm surge job

        See :class:`StormJob` for full documentation
        """

        super(StormJob, self).__init__()

        self.storm_number = storm_number
        self.storm = storm

        # Habanero queue settings
        self.omp_num_threads = 24
        self.time = "1:00:00"
        self.queue = ""

        # General job info
        self.type = "surge"
        self.name = "global_1"
        self.prefix = "storm_%s" % self.storm_number
        self.executable = "xgeoclaw"

        # Modify run data
        import setrun
        self.rundata = setrun.setrun()

        # Modify output times
        self.rundata.clawdata.output_style = 2
        recurrence = 6.0
        tfinal = (storm.t[-1] - storm.t[0]).total_seconds()
        N = int(tfinal / (recurrence * 60**2))
        self.rundata.clawdata.output_times = [t for t in
                 numpy.arange(0.0, N * recurrence * 60**2, recurrence * 60**2)]
        self.rundata.clawdata.output_times.append(tfinal)

        # Modify storm data
        surge_data = self.rundata.surge_data
        base_path = os.path.expandvars(os.path.join("$DATA_PATH", "storms",
                                                    "global", "storms"))
        surge_data.storm_file = os.path.join(base_path,
                                             'storm_%s.storm'
                                             % (str(i).zfill(5)))
        self.storm.time_offset = storm.t[0]

        print("Writing out GeoClaw storms...")
        self.storm.write(self.rundata.surge_data.storm_file)

        # TODO: Set gauges based on track

    def __str__(self):
        output = super(StormJob, self).__str__()
        output += "\n\tStorm %s:\n" % self.storm_number
        output += "\n\t\t%s" % self.storm
        output += "\n"
        return output

    def write_data_objects(self):

        super(StormJob, self).write_data_objects()


if __name__ == '__main__':
    print("Loading Emmanuel tracks...")
    path = os.path.expandvars(os.path.join("$DATA_PATH", "storms", "global",
                                           "Trial1_GB_dkipsl_rcp60cal.mat"))
    storms = clawpack.geoclaw.surge.storm.load_emmanuel_storms(path)
    print("Done.")
    num_storms = len(storms)

    if len(sys.argv) > 1:
        # Take this to be the number of storms to run
        num_storms = int(sys.argv[1])

    # Convert Emmanuel data to GeoClaw format

    jobs = []
    for (i, storm) in enumerate(storms[:num_storms]):
        jobs.append(StormJob(storm, i))
    print("Done.")

    controller = BatchController(jobs)
    controller.wait = False
    controller.plot = False
    print(controller)
    # controller.run()
