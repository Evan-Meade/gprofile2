'''
gprofile2.py (gprofile2)
Evan Meade, 2020
Research group of Dr. Lindsay King (UTD)

To Do:
- add graphic update methods

'''

# Built-in imports
import sys
import os
import subprocess
import random
import time
import math
from datetime import datetime
import shutil

# Library imports
import numpy as np
import pandas as pd
import PySimpleGUI as sg


'''
Following are constants controlling generation of SIE galactic lenses.
'''

# Constants for velocity dispersion distribution
PHI_STAR = 2.099 * 10 ** -2   # units of (h/.7)^3Mpc^-3
SIGMA_STAR = 113.78   # units of km/s
ALPHA = 0.94
BETA = 1.85


def execute(values):
    # Passes trial values to the simulation function
    print('gprofile2 executed')
    simulate(values)


def simulate(values):
    # Trial parameters
    trial_name = values['trial_name']
    num_samp = int(values['num_samp'])
    seed = values['seed']

    # Columns of main dataframe
    cols = ['run_number', 'lens_sigma', 'lens_z', 'lens_x',
            'lens_y', 'lens_ellip', 'lens_theta',
            'lens_r_core', 'source_z', 'source_x',
            'source_y', 'shear_mag', 'shear_z', 'shear_x',
            'shear_y', 'shear_theta', 'shear_convergence',
            'num_images', 'image_dat_output'
            ]

    # Main dataframe containing run parameters and results
    data = pd.DataFrame(columns=cols)

    # Temporary file names
    dat_file = 'out_point.dat'
    template_file = 'config.input'
    config_file = 'case.input'

    # Lens redshift bounds
    lens_z_min = float(values['lens_z_min'])
    lens_z_max = float(values['lens_z_max'])
    lens_z_rng = lens_z_max - lens_z_min

    # Velocity dispersion parameters
    sigma_min = 75   # Minimum velocity dispersion
    sigma_max = 375   # Maximum velocity dispersion
    num_bins = 15   # Number of bins for velocity dispersion
    bin_size = (sigma_max - sigma_min) / num_bins   # Simple bin width

    # Source redshift bounds
    source_z_min = float(values['source_z_min'])
    source_z_max = float(values['source_z_max'])
    source_z_rng = source_z_max - source_z_min

    # Source position ranges
    samp_radius = float(values['samp_radius'])
    source_x_min = -1 * samp_radius
    source_y_min = -1 * samp_radius
    source_x_max = samp_radius
    source_y_max = samp_radius
    source_x_rng = source_x_max - source_x_min
    source_y_rng = source_y_max - source_y_min

    # Initializes execution statistics to be defined later
    trials = 0
    start_time = 0
    end_time = 0
    succ_percent = 0


    '''
    Main execution steps
    '''

    random.seed(seed)   # Pseudorandom function is seeded with given value

    # Creates representative distribution of SIE sigmas
    left_bounds, freqs = disp_bins(num_bins, sigma_min, bin_size)

    trials = 0   # Tracks total number of good and bad runs

    start_time = time.time()   # Used to time execution

    # Loop structure runs over all lenses for num_samp good trials each
    for i in range(0, num_samp):
        good_run = False   # Sets to true if system is multiply imaged
        while good_run == False:
            trials += 1   # Iterates trials since glafic is run

            v = pd.Series(index=cols, dtype='object')
            v['run_number'] = int(trials)
            v['lens_sigma'] = gen_lens_disp(left_bounds, freqs, bin_size)
            v['lens_z'] = lens_z_min + lens_z_rng * random.random()
            v['lens_x'] = 0.0
            v['lens_y'] = 0.0
            v['lens_ellip'] = gen_lens_ellip()
            v['lens_theta'] = 0.0
            v['lens_r_core'] = 0.0
            v['source_z'] = source_z_min + source_z_rng * random.random()
            v['source_x'] = source_x_min + source_x_rng * random.random()
            v['source_y'] = source_y_min + source_y_rng * random.random()
            v['shear_mag'] = gen_shear_mag()
            v['shear_z'] = v['source_z']
            v['shear_x'] = 0.0
            v['shear_y'] = 0.0
            v['shear_theta'] = gen_shear_angle()
            v['shear_convergence'] = gen_shear_convergence()

            # Creates temporary .input file for glafic system
            with open(config_file, 'w') as case:
                # Copies template file except for flagged lines
                with open(template_file, 'r') as template:
                    for line in template:
                        # Copies each line unless flagged
                        if "**ZL**" in line:
                            # Writes redshift of lens
                            zl = f"zl   {v['lens_z']}"
                            case.writelines(zl)
                        elif "**SIE**" in line:
                            # Writes randomly sampled SIE lens
                            lens = f"lens sie {v['lens_sigma']} {v['lens_x']} {v['lens_y']} {v['lens_ellip']} {v['lens_theta']} {v['lens_r_core']} 0.0\n"
                            case.writelines(lens)
                        elif "**SHEAR**" in line:
                            # Writes randomly sampled external shear
                            shear = f"\nlens pert {v['shear_z']} {v['shear_x']} {v['shear_y']} {v['shear_mag']} {v['shear_theta']} 0.0 {v['shear_convergence']}\n"
                            case.writelines(shear)
                        elif "**POINT**" in line:
                            # Writes randomly sampled point in range
                            point = f"\npoint {v['source_z']} {v['source_x']} {v['source_y']}\n"
                            case.writelines(point)
                        else:
                            case.writelines(line)
                    template.close()
                case.close()

            # Executes glafic with temporary .input file
            run = subprocess.check_output(f"glafic {config_file} > /dev/null 2>&1", shell=True)

            # Reads output of glafic to see if multiply imaged (good)
            output = np.loadtxt(dat_file)   # Loads dat file into numpy array
            if output.shape != (4,) and output[0,0] > 1:
                good_run = True

        # If good sample (multiply imaged), writes to data
        print(output)
        v['num_images'] = output[0,0]
        v['image_dat_output'] = output
        data = data.append(v, ignore_index=True)

    # Updates execution statistics
    end_time = time.time()
    total_time = end_time - start_time
    succ_percent = round(100 * num_samp / trials, 2)

    # Compiles execution statistics
    execution_stats = pd.Series({'num_samp': num_samp, 'samp_radius': samp_radius,
                                    'total_trials': trials, 'percent_good': succ_percent,
                                    'execution_time': total_time})

    # Deletes temporary files
    os.remove(config_file)
    os.remove(dat_file)

    # Prints entire data; more useful for debugging on small ranges
    print(data)

    # Writes data to Results
    save_data(data, trial_name, execution_stats)

    # Prints execution statistics
    print(f"\n\nTotal Samples: {num_samp}\nTotal Trials: {trials}")
    print(f"\nPercent Good: {succ_percent}%")
    print(f"\nTime Elapsed (sec): {end_time - start_time}\n")
    print("\nExecution complete")


'''
disp_bins()

Generates representative distribution of sigmas within given range.

First calculates the relative frequency of sigmas occurring in each
bin, then generates a list with the needed number of samples. The
number of samples for each bin is determined through relative frequency,
and each sample is given by a uniform distribution within the bin bounds.
'''
def disp_bins(num_bins, sigma_min, bin_size):
    # Initializes sampling parameter lists
    left_bounds = []
    freqs = []

    # Calculates relative frequencies and bin bounds
    total_freq = 0   # Used later to scale to num_gals
    for i in range(0, num_bins):
        sigma = sigma_min + i * bin_size
        left_bounds.append(sigma)   # List of bin bounds
        fr = phi_loc(sigma)
        freqs.append(fr)   # List of relative frequencies
        total_freq += fr

    # Scales each entry in freqs to make them sum up to 1
    correction = 1 / total_freq
    freqs[0] = freqs[0] * correction
    for i in range(1, len(freqs) - 1):
        freqs[i] = freqs[i] * correction + freqs[i-1]
    freqs[-1] = 1

    # Returns sampling parameter lists
    return left_bounds, freqs


'''
phi_loc(sigma)

Returns the value of the phi_loc distribution at a given sigma.

This function is given in M. Oguri (2018) to describe the observed
distribution of velocity dispersions for SIE galaxy generation.
'''
def phi_loc(sigma):
    return PHI_STAR * (sigma / SIGMA_STAR) ** ALPHA * math.exp(-1 *
        (sigma / SIGMA_STAR) ** BETA) * BETA / math.gamma(ALPHA / BETA) / sigma


'''
gen_lens_disp()

Returns velocity dispersion randomly sampled from phi_loc.
'''
def gen_lens_disp(left_bounds, freqs, bin_size):
    sigma = 0
    bin_selector = random.random()
    for i in range(0, len(freqs)):
        if bin_selector <= freqs[i]:
            sigma = random.uniform(left_bounds[i], left_bounds[i] + bin_size)
            break
    return sigma


'''
gen_lens_ellip()

Returns an ellipticity from [0,1] using normal distribution sampling.
'''
def gen_lens_ellip():
    # Defining distribution parameters
    mean = 0.3
    disp = 0.16

    # Ensures generated ellipticity is in (0, .9)
    ellip = -1.0
    while ellip <= 0 or ellip >= .9:
        # Generates random sample from distribution
        ellip = np.random.normal(mean, disp, None)

    # When conditions satisfied, returns ellip
    return ellip


'''
gen_shear_mag()

Generates external shear magnitude from a log-normal distribution.
'''
def gen_shear_mag():
    # Ensures generated magnitude is in (0, 1)
    mag = -1
    while mag <= 0 or mag >= 1:
        # Approximated function by looking at graph from Dalal and Watson
        mag = np.exp(np.random.normal(np.log10(.025), .5 * (np.log10(.06) - np.log10(.01))))
    return mag


'''
gen_shear_angle()

Generates external shear angle with uniform randomness.
'''
def gen_shear_angle():
    return 2 * math.pi * random.random()


'''
gen_shear_convergence()

Generates convergence for external shear from a log-normal distribution.
'''
def gen_shear_convergence():
    k = -1
    while k <= 0 or k >= 1:
        # Approximated function by looking at graph from Dalal and Watson
        k = np.exp(np.random.normal(np.log10(.015), .5 * (np.log10(.04) - np.log10(.007))))
    return k


'''
save_data()

Saves data to an HDF5 file for analysis later.

Saves data with pandas, and also compiles basic execution statistics not
readily contained by data in a new .dat file.

execution_stats.csv:
- Basic statistics relating to the script's execution
- Intended to be human-readable, so each line contains name followed by value
- Contents
    - Number of Samples
    - Sampling Radius
    - Total Trials
    - Percent Good
        - Samples / Trials
    - Execution Time (sec)
'''
def save_data(data, trial_name, execution_stats):
    # Moves to master folder for all results; creates if doesn't already exist
    master_folder = "Results"
    if os.path.exists(master_folder):
        os.chdir(master_folder)
    else:
        os.mkdir(master_folder)
        os.chdir(master_folder)

    # Creates and moves to new folder based on current time and num_samp
    current_time = time.time()
    test_time = str(datetime.fromtimestamp(current_time)).replace(' ', '_')
    folder = f"{trial_name}---{test_time}"
    os.mkdir(folder)
    os.chdir(folder)

    # Saves data to an HDF5 file
    hdf = pd.HDFStore('data.h5')
    hdf.put('data', data, data_columns=True)
    hdf.close()

    # Writes data for "execution_stats.csv"
    execution_stats.to_csv('execution_stats.csv')
