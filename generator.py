'''
generator.py (gprofile2)
Evan Meade, 2019
Research group of Dr. Lindsay King (UTD)

This script generates lists of SIE galaxies under randomizing parameters.

These lists can then be fed into gprofile2.py to find statistical
behavior of lensing over given parameters. Generated lists are representative
of the range of inputs given as parameters. Modelling is based largely on
the parameter spaces described in M. Oguri (2018) for SIE galaxies.
Intended for use with glafic, written by M. Oguri (2010), but syntax may be
adjusted for other programs.

Dependencies:
- Python3
- numpy

Execution format:
python generator.py {number of galaxies} {output file name} {random seed}

Recommended parameter space:
- sigma: relative frequency based on phi_loc distribution
    - sigma_min: 75 (if < 75, multiple images unlikely to occur)
    - sigma_max: 375 (above this is unlikely to be seen in nature)
- xcoord: 0.0
- ycoord: 0.0
- ellip: normal distribution with mean of 0.3 and dispersion of 0.16
- theta: 0.0
- rcore: 0.0
This is all based on the assumption that trials are being run with only
1 galaxy at a time, and so positions/angles are all relative. Additionally,
this code was originally designed to not feature external shear, though
gprofile2 could be reasonably modified to include this feature as well.

'''

# Built-in imports
import sys
import math
import random

# Library imports
import numpy as np


# Global variables that define the scope of the list
num_gals = int(sys.argv[1])   # Number of galaxies in list
sigma_min = 75   # Minimum velocity dispersion
sigma_max = 375   # Maximum velocity dispersion
num_bins = 15   # Number of bins for velocity dispersion

# Global variables to aid in velocity dispersion distribution
left_bounds = []
freqs = []
disp_list = []
current_disp = 0

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

# Instance-specific variables
output_file = sys.argv[2]   # Name of output list
seed = sys.argv[3]   # Random seed used in pseudorandom generation


'''
main()

Main list generation and writing loop.

Sets seeds, finishes setting parameters, and calls line generation
method for desired number of galaxies, writing each one to the given
output file.
'''
def main():
    random.seed(seed)   # Pseudorandom function is seeded with given value
    disp_bins()   # Creates representative distribution of sigmas

    # Generates and writes each line to the output file
    with open(output_file, 'w') as output:
        for i in range(0, num_gals):
            gal = generate_gal()
            output.writelines(gal)
        output.close()


'''
generate_gal()

Calls random subroutines to return a galaxy as a string.
'''
def generate_gal():
    disp = gen_disp()   # Obtains velocity dispersion parameter
    ellip = gen_ellip()   # Obtains ellipticity parameter

    # Formats galaxy as a string and returns it
    gal = f"lens sie {disp} {xcoord} {ycoord} {ellip} {theta} {rcore} 0.0\n"
    return gal


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
disp_bins()

Generates representative distribution of sigmas within given range.

First calculates the relative frequency of sigmas occurring in each
bin, then generates a list with the needed number of samples. The
number of samples for each bin is determined through relative frequency,
and each sample is given by a uniform distribution within the bin bounds.
'''
def disp_bins():
    bin_size = (sigma_max - sigma_min) / num_bins   # Simple bin width

    # Calculates relative frequencies and bin bounds
    total_freq = 0   # Used later to scale to num_gals
    for i in range(0, num_bins):
        sigma = sigma_min + i * bin_size
        left_bounds.append(sigma)   # List of bin bounds
        fr = phi_loc(sigma)
        freqs.append(fr)   # List of relative frequencies
        total_freq += fr

    # Scales each entry in freqs to make them sum up to num_gals
    correction = num_gals / total_freq
    for i in range(0, len(freqs)):
        freqs[i] = round(freqs[i] * correction)

    # Addresses rounding errors leading to a non num_gals sum of samples
    run = True
    while run == True:
        sum_freq_samps = sum(freqs)
        if sum_freq_samps == num_gals:   # Exits if sum == num_gals
            run = False
        elif sum_freq_samps > num_gals:   # Random minus if sum > num_gals
            pos = random.randrange(0, len(freqs))
            if freqs[pos] > 0:
                freqs[pos] -= 1
        elif sum_freq_samps < num_gals:   # Random plus if sum < num_gals
            pos = random.randrange(0, len(freqs))
            freqs[pos] += 1

    # Generates list of representative samples using bin freqs
    for i in range(0, len(freqs)):
        for j in range(0, freqs[i]):
            # Pulls from uniform distribution on bin for each sample
            disp_list.append(random.uniform(left_bounds[i],
                left_bounds[i] + bin_size))


'''
gen_disp()

Returns next sigma from the representative list.

NOTE: disp_bins() MUST be called first to generate this list; this
merely iterates over that list and returns sequentially.
'''
def gen_disp():
    # Calls down latest value of sigma from list
    global current_disp
    disp = disp_list[current_disp]

    # Iterates position of latest value of sigma to prevent double sampling
    current_disp += 1

    # Returns sigma
    return disp


'''
gen_ellip()

Returns an ellipticity from [0,1] using normal distribution sampling.
'''
def gen_ellip():
    # Defining distribution parameters
    mean = 0.3
    disp = 0.16

    # Ensures generated ellipticity is in [0, 1]
    ellip = -1.0
    while ellip < 0 or ellip > .9:
        # Generates random sample from distribution
        ellip = np.random.normal(mean, disp, None)

    # When conditions satisfied, returns ellip
    return ellip


# Calls main subroutine after defining all functions
if __name__ == '__main__':
    main()
