from clawpack.pyclaw.gauges import GaugeSolution

import os 
import sys

import numpy 


print("We are now collecting gauges.") 

data = sys.argv[1]
base_path = sys.argv[2]
job_name = sys.argv[3]
job_prefix = sys.argv[4] 

print("data successfully collected")   

#gauge_no = numpy.array([1, 2, 3, 4, 5, 6]) 
gauge_no = numpy.array([1, 2, 3, 4]) 
max_surge = numpy.zeros(gauge_no.shape, dtype=float)  

for i in range(0,4):
    gauge_data = os.path.join(data, "gauge0000%i.txt" %i) 
    gauge = GaugeSolution(gauge_id = i + 1, path = data) 
    max_surge[i] = numpy.max(gauge.q[3]) 
  
gauges_title = "%s_gaugeMaxSurge.txt" %job_prefix

max_surge_output_dir = os.path.join(base_path, "MaxSurge")
if not os.path.exists(max_surge_output_dir): 
    os.mkdir(max_surge_output_dir)  

output_dir = os.path.join(max_surge_output_dir, job_name) 
if not os.path.exists(output_dir): 
    os.mkdir(output_dir)

print("Made the Max Surge with job name file") 

output_path = os.path.join(output_dir, gauges_title) 

with open(output_path, "w") as gauge_surge: 
    gauge_surge.write("Gauge, Surge \n") 
    for i in range(0,6):  
        gauge_surge.write("%i, %f \n" %(gauge_no[i], max_surge[i])) 

gauge_surge.close() 
