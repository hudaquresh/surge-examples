import os
import pandas
import matplotlib.pyplot as plt
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
