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
- glafic (added to $PATH)

Execution format:
python gprofile2.py {template glafic input} {galaxy list} {random seed}

Template format (for gprofile):
- Must be a .input file
- Set "prefix out"
    - If prefix set to something else, will have to modify calls here
- Ordinary .input glafic file except for three flagged lines to be iterated
    - **SIE**: this line will be systematically iterated over galaxy list
    - **SHEAR**: this line will be randomly sampled for external shear
    - **POINT**: this line will be randomly sampled over given sample space

Recommended parameter space:
- num_samp: 20
    - Higher sample number will more accurately characterize each lens
- xmin: -1.0
- ymin: -1.0
- xmax: 1.0
- ymax: 1.0
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

# Library imports
import numpy as np


lenses = []   # Stores list of lens strings
num_samp = 20   # Number of samples to be taken for each lens

seed = sys.argv[3]   # Random seed used in pseudorandom generation

'''
dat[]

List containing all time delay output data for all samples.

Frankly, this is a monster of a list. It is four dimensional.
dat[i][j][k][l]
- i: lens number
- j: sample number for lens i
- k: line number for dat file of lens i, sample j
- l: element of line k of dat file of lens i, sample j

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

# Point range parameters
xmin = -1.0
ymin = -1.0
xmax = 1.0
ymax = 1.0
zsrc = 3.0

# Derived point range parameters
xrng = xmax - xmin
yrng = ymax - ymin

# Initializes execution statistics to be defined later
total_samp = 0
trials = 0
start_time = 0
end_time = 0
succ_percent = 0


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
    global total_samp, trials, start_time, end_time, succ_percent

    random.seed(seed)   # Pseudorandom function is seeded with given value

    # Reads in list of galaxies from file
    with open(sys.argv[2], 'r') as gals:
        for line in gals:
            lenses.append(line.strip(f"\n"))
        gals.close()

    trials = 0   # Tracks total number of good and bad runs

    total_samp = len(lenses) * num_samp   # Calculates total samples to run
    start_time = time.time()   # Used to time execution

    # Loop structure runs over all lenses for num_samp good trials each
    for i in range(0, len(lenses)):
        dat.append([])
        for j in range(0, num_samp):
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
                                # Writes galaxy line i
                                case.writelines(f"\n{lenses[i]}\n")
                            elif "**POINT**" in line:
                                # Writes randomly sampled point in range
                                point = gen_point()
                                case.writelines(point)
                            elif "**SHEAR**" in line:
                                shear = gen_shear()
                                case.writelines(shear)
                            else:
                                case.writelines(line)
                        template.close()
                    case.close()

                run_glafic()   # Executes glafic with temporary .input file

                # Reads output of glafic to see if multiply imaged (good)
                if check_mult():
                    good_run = True

            # If good sample (multiply imaged), writes to dat[]
            write_dat(i)

    # Updates execution statistics
    end_time = time.time()
    succ_percent = round(100 * total_samp / trials, 2)

    # Deletes temporary files
    os.remove(config_file)
    os.remove(dat_file)

    # Prints entire dat matrix; more useful for debugging on small ranges
    print(dat)

    # Compiles statistical lists for dat[] and writes to Trialxxx in Results
    #process_dat()
    save_dat()

    # Prints execution statistics
    print(f"\n\nTotal Samples: {total_samp}\nTotal Trials: {trials}")
    print(f"\nPercent Good: {succ_percent}%")
    print(f"\nTime Elapsed (sec): {end_time - start_time}\n")


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
    # Fix by regressing estimated points from graph
    return np.random.lognormal(0.05, 10 ** 0.2)


'''
gen_shear_angle()

Generates external shear angle with uniform randomness.
'''
def gen_shear_angle():
    return 2 * math.pi * random.random()


'''
gen_convergence()

Generates convergence for external shear as a constant.
'''
def gen_convergence():
    return 0.0


'''
run_glafic()

Executes glafic in bash shell using temporary .input file.
'''
def run_glafic():
    run = subprocess.check_output(f"glafic {config_file}", shell=True)


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
write_dat(i)

Appends current .dat output file to dat[] for lens i.
'''
def write_dat(i):
    output = np.loadtxt(dat_file)   # Loads .dat output file into numpy array
    dat[i].append(output)   # Appends numpy array to lens i of dat[]


'''
save_dat()

Saves dat[] to a .npy binary file for analysis later.

Saves dat[] with numpy, and also compiles basic execution statistics not
contained by dat[] in a new .dat file.

global_stats.dat:
- Broad statistics related to the sampling space and execution parameters
- Intended to be human-readable, so each line contains name followed by value
- Contents
    - Number of Lenses
    - Samples per Lens
    - Total Samples
    - Total Number of Images
    - Total Number of Image Pairs
    - X Range: [xmin, xmax]
    - Y Range: [ymin, ymax]
    - Redshift
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

    # Calculates next unused trial number; creates and moves to that folder
    searching = True
    index = 0
    while searching:
        folder = f"{sys.argv[2]}---Trial{index:03}"
        if os.path.exists(folder):
            index += 1
        else:
            os.mkdir(folder)
            os.chdir(folder)
            searching = False

    # Saves dat[] to a .npy binary file
    np.save('raw_data', dat)

    # Writes data for "global_stats.dat"
    with open("global_stats.dat", 'w') as stats:
        stats.writelines(f"Number of Lenses: {num_lenses}\n")
        stats.writelines(f"Samples per Lens: {num_samp}\n")
        stats.writelines(f"Total Samples: {num_lenses * num_samp}\n")
        stats.writelines(f"Total Number of Images: {sum(num_images)}\n")
        stats.writelines(f"Total Number of Image Pairs: {len(pair_delays)}\n")
        stats.writelines(f"X Range: [{xmin}, {xmax}]\n")
        stats.writelines(f"Y Range: [{ymin}, {ymax}]\n")
        stats.writelines(f"Redshift: {zsrc}\n")
        stats.writelines(f"Total Trials: {trials}\n")
        stats.writelines(f"Percent Good: {succ_percent}\n")
        stats.writelines(f"Execution Time (sec): {end_time - start_time}\n")
        stats.close()


# Calls main subroutine after defining all functions
if __name__ == '__main__':
    main()
