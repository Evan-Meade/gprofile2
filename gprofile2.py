'''
gprofile2.py (gprofile2)
Evan Meade, 2019
Research group of Dr. Lindsay King (UTD)

This script samples lensing statistics over a given list of lenses.

Intended for use with glafic, developed by M. Oguri (2010). This script
procedurally generates .input files for glafic with varied lenses and
points to extrapolate statistical behavior over a given parameter space.
Could be modified to test other functions over a given parameter space.

Dependencies:
- Python3
- numpy
- progressbar2
- glafic (added to $PATH)

Execution format:
python gprofile2.py {template glafic input} {number of samples} {random seed}

Template format (for gprofile):
- Must be a .input file
- Set "prefix out"
    - If prefix set to something else, will have to modify calls here
- Ordinary .input glafic file except for three flagged lines to be iterated
    - **SIE**: this line will be systematically iterated over galaxy list
    - **SHEAR**: this line will be randomly sampled for external shear
    - **POINT**: this line will be randomly sampled over given sample space
    - **ZL**: this line will fill in the given redshift of the lens

Recommended parameter space:
- num_samp: 20
    - Higher sample number will more accurately characterize each lens
- xmin: -1.0
- ymin: -1.0
- xmax: 1.0
- ymax: 1.0
- zlens: 0.3
- zsrc: 3.0
- dat_file: "out_point.dat"
- config_file: "case.input"
This x,y box aims to completely contain caustics so as to characterize
all lensing regions. If far too big, will lead to low ratio of multiple to
single lensed systems, so requires parameter honing or a beefy system to
efficiently obtain good results.

NOTE: dat_file and config_file are deleted at end of execution; they are
merely temporary files to aid in collection of statistics. Continuously
overwritten by each run.

'''

# Built-in imports
import sys
import os
import subprocess
import random
import time
import math
from datetime import datetime

# Library imports
import numpy as np
import progressbar   # Actually imports progressbar2, not progressbar


num_samp = int(sys.argv[2])   # Total number of samples to be taken

seed = sys.argv[3]   # Random seed used in pseudorandom generation

'''
dat[]

List containing all time delay output data for all samples.

Frankly, this is a monster of a list. It is four dimensional.
dat[i][j][k][l]
- i: sample number
- k: line number for dat file of sample i
- l: element of line k of dat file of sample i

Special values:
- dat[i][j][0][0]: number of images for lens i, sample j
- dat[i][j][k > 0]: returns a line for each image if multiply imaged
    - dat[i][j][k > 0] = [ximg, yimg, mag, time_delay]
    - time_delay is relative to the first image's arrival; units of days
'''
dat = []


# Temporary file names
dat_file = "out_point.dat"
config_file = "case.input"

# Lens parameters
zlens = .3

# Point range parameters
xmin = -1.0
ymin = -1.0
xmax = 1.0
ymax = 1.0
zsrc = 3

# Derived point range parameters
xrng = xmax - xmin
yrng = ymax - ymin

# Initializes execution statistics to be defined later
trials = 0
start_time = 0
end_time = 0
succ_percent = 0

'''
Following are variables controlling generation of SIE galactic lenses.
'''

# Global variables that define the scope of the list
sigma_min = 75   # Minimum velocity dispersion
sigma_max = 375   # Maximum velocity dispersion
num_bins = 15   # Number of bins for velocity dispersion
bin_size = (sigma_max - sigma_min) / num_bins   # Simple bin width

# Global variables to aid in velocity dispersion distribution
left_bounds = []
freqs = []

# Constants for velocity dispersion distribution
phi_star = 2.099 * 10 ** -2   # units of (h/.7)^3Mpc^-3
sigma_star = 113.78   # units of km/s
alpha = 0.94
beta = 1.85

# Constants for all galaxies generated
xcoord = 0.0
ycoord = 0.0
theta = 0.0
rcore = 0.0


'''
main()

This is the main method which samples and compiles results.

First, it reads in the list of galaxies. Then, it runs a loop of trials
on the given sampling range until enough multiply imaged systems are found.
Results for each sample are recorded in dat[]. After all samples are
collected, results are compiled into input files and written out to Results
folder.
'''
def main():
    # Inherits shadowed global variables
    global trials, start_time, end_time, succ_percent

    random.seed(seed)   # Pseudorandom function is seeded with given value
    disp_bins()   # Creates representative distribution of SIE sigmas

    trials = 0   # Tracks total number of good and bad runs

    start_time = time.time()   # Used to time execution

    widgets = ['\x1b[33mTotal Progress: \x1b[39m',
               progressbar.Bar(marker='\x1b[32m#\x1b[39m'),
               progressbar.Percentage()]
    bar = progressbar.ProgressBar(widgets=widgets, max_value=num_samp).start()

    # Loop structure runs over all lenses for num_samp good trials each
    for i in range(0, num_samp):
        good_run = False   # Sets to true if system is multiply imaged
        while good_run == False:
            trials += 1   # iterates trials since glafic is run

            # Creates temporary .input file for glafic system
            with open(config_file, 'w') as case:
                # Copies template file except for flagged lines
                with open(sys.argv[1], 'r') as template:
                    for line in template:
                        # Copies each line unless flagged
                        if "**SIE**" in line:
                            # Writes randomly sampled SIE lens
                            lens = gen_lens()
                            case.writelines(lens)
                        elif "**POINT**" in line:
                            # Writes randomly sampled point in range
                            point = gen_point()
                            case.writelines(point)
                        elif "**SHEAR**" in line:
                            # Writes randomly sampled external shear
                            shear = gen_shear()
                            case.writelines(shear)
                        elif "**ZL**" in line:
                            # Writes redshift of lens
                            zl = gen_zl()
                            case.writelines(zl)
                        else:
                            case.writelines(line)
                    template.close()
                case.close()

            run_glafic()   # Executes glafic with temporary .input file

            # Reads output of glafic to see if multiply imaged (good)
            if check_mult():
                good_run = True

        # If good sample (multiply imaged), writes to dat[]
        write_dat()
        bar.update(i + 1)

    # Updates execution statistics
    end_time = time.time()
    succ_percent = round(100 * num_samp / trials, 2)

    # Deletes temporary files
    os.remove(config_file)
    os.remove(dat_file)

    # Prints entire dat matrix; more useful for debugging on small ranges
    #print(dat)

    # Compiles statistical lists for dat[] and writes to Trialxxx in Results
    #process_dat()
    save_dat()

    # Prints execution statistics
    print(f"\n\nTotal Samples: {num_samp}\nTotal Trials: {trials}")
    print(f"\nPercent Good: {succ_percent}%")
    print(f"\nTime Elapsed (sec): {end_time - start_time}\n")


'''
disp_bins()

Generates representative distribution of sigmas within given range.

First calculates the relative frequency of sigmas occurring in each
bin, then generates a list with the needed number of samples. The
number of samples for each bin is determined through relative frequency,
and each sample is given by a uniform distribution within the bin bounds.
'''
def disp_bins():
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


'''
phi_loc(sigma)

Returns the value of the phi_loc distribution at a given sigma.

This function is given in M. Oguri (2018) to describe the observed
distribution of velocity dispersions for SIE galaxy generation.
'''
def phi_loc(sigma):
    return phi_star * (sigma / sigma_star) ** alpha * math.exp(-1 *
        (sigma / sigma_star) ** beta) * beta / math.gamma(alpha / beta) / sigma


'''
gen_lens()

Generates string of random SIE galactic lens within script parameters.
'''
def gen_lens():
    disp = gen_disp()   # Obtains velocity dispersion parameter
    ellip = gen_ellip()   # Obtains ellipticity parameter

    # Formats galaxy as a string and returns it
    gal = f"lens sie {disp} {xcoord} {ycoord} {ellip} {theta} {rcore} 0.0\n"
    return gal


'''
gen_disp()

Returns velocity dispersion randomly sampled from phi_loc.
'''
def gen_disp():
    sigma = 0
    bin_selector = random.random()
    for i in range(0, len(freqs)):
        if bin_selector <= freqs[i]:
            sigma = random.uniform(left_bounds[i], left_bounds[i] + bin_size)
            break
    return sigma


'''
gen_ellip()

Returns an ellipticity from [0,1] using normal distribution sampling.
'''
def gen_ellip():
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
gen_point()

Generates string of point in given range and returns it.
'''
def gen_point():
    # Uniform sampling of xp and yp over sampling space
    xp = xmin + xrng * random.random()
    yp = ymin + yrng * random.random()

    # Formatting as string in glafic syntax and returning
    point = f"\npoint {zsrc} {xp} {yp}\n"
    return point


'''
gen_shear()

Generates string of external shear with random parameters and returns it.
'''
def gen_shear():
    mag = gen_shear_mag()
    angle = gen_shear_angle()
    convergence = gen_convergence()

    shear = f"\nlens pert {zsrc} 0.0 0.0 {mag} {angle} 0.0 {convergence}\n"
    return shear


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
gen_convergence()

Generates convergence for external shear from a log-normal distribution.
'''
def gen_convergence():
    k = -1
    while k <= 0 or k >= 1:
        # Approximated function by looking at graph from Dalal and Watson
        k = np.exp(np.random.normal(np.log10(.015), .5 * (np.log10(.04) - np.log10(.007))))
    return k


'''
gen_zl()

Generates line for the redshift (z) of the lens.
'''
def gen_zl():
    return f"zl   {zlens}"


'''
run_glafic()

Executes glafic in bash shell using temporary .input file.
'''
def run_glafic():
    run = subprocess.check_output(f"glafic {config_file} > /dev/null 2>&1", shell=True)


'''
check_mult()

Reads .dat output of glafic to determine if system is multiply imaged.
'''
def check_mult():
    output = np.loadtxt(dat_file)   # Loads dat file into numpy array

    # Reads element [0][0] to find number of images
    if output.shape != (4,) and output[0][0] > 1:
        return True   # If multiply imaged, returns True
    return False   # Otherwise, returns False


'''
write_dat()

Appends current .dat output file to dat[].
'''
def write_dat():
    output = np.loadtxt(dat_file)   # Loads .dat output file into numpy array
    dat.append(output)   # Appends numpy array to lens i of dat[]


'''
save_dat()

Saves dat[] to a .npy binary file for analysis later.

Saves dat[] with numpy, and also compiles basic execution statistics not
contained by dat[] in a new .dat file.

execution_stats.dat:
- Basic statistics relating to the script's execution
- Intended to be human-readable, so each line contains name followed by value
- Contents
    - Total Samples
    - X Range: [xmin, xmax]
    - Y Range: [ymin, ymax]
    - Total Trials
    - Percent Good
        - Samples / Trials
    - Execution Time (sec)
'''
def save_dat():
    # Moves to master folder for all results; creates if doesn't already exist
    master_folder = "Results"
    if os.path.exists(master_folder):
        os.chdir(master_folder)
    else:
        os.mkdir(master_folder)
        os.chdir(master_folder)

    # Creates and moves to new folder based on current time and num_samp
    test_time = str(datetime.fromtimestamp(start_time)).replace(' ', '_')
    folder = f"{test_time}---{num_samp}"
    os.mkdir(folder)
    os.chdir(folder)

    # Saves dat[] to a .npy binary file
    np.save('raw_data', dat)

    # Writes data for "global_stats.dat"
    with open("execution_stats.dat", 'w') as stats:
        stats.writelines(f"Total Samples: {num_samp}\n")
        stats.writelines(f"X Range: [{xmin}, {xmax}]\n")
        stats.writelines(f"Y Range: [{ymin}, {ymax}]\n")
        stats.writelines(f"Total Trials: {trials}\n")
        stats.writelines(f"Percent Good: {succ_percent}\n")
        stats.writelines(f"Execution Time (sec): {end_time - start_time}\n")
        stats.close()


# Calls main subroutine after defining all functions
if __name__ == '__main__':
    main()
