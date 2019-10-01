'''
analyzer.py (gprofile2)
Evan Meade, 2019
Research group of Dr. Lindsay King (UTD)

This script compiles .npy binaries to analyze the entire lensing sample.

When called on a directory, it will create a master numpy array loading in
results from all .npy binaries. Then, it computes a variety of statistics
over the set, including visualizations.

Dependencies:
- Python3
- numpy
- matplotlib

Execution format:
python analyzer.py path/to/all/npy/files

'''

# Built-in imports
import sys
import os
import math

# Library imports
import numpy as np
import matplotlib.pyplot as plt

# Reads in execution arguments
folder = sys.argv[1]

# Initializes full dat array
dat = []


'''
main()

Main dat loading and processing loop.

Loads .npy data into dat using numpy. Then it processes that data into
statistics and visualizations.
'''
def main():
    load_dat()
    process_dat()


'''
load_dat()

Compiles all .npy binaries into singular dat[] array.
'''
def load_dat():
    # Inherits global variables
    global dat

    # Moves to directory given as an argument
    os.chdir(folder)

    # Searches through directory for .npy files and appends to dat[]
    for file in os.listdir():
        if file.endswith(".npy"):
            temp_dat = np.load(file, allow_pickle=True)
            for i in range(0, len(temp_dat)):
                dat.append(temp_dat[i])


'''
process_dat()

Compiles basic statistics from dat[] into a few files in a new folder.

All output placed in "../Results/Trialxxx" where xxx iterates from 000. Thus,
multiple trials can have outputs organized in the same master folder.

image_pairs.dat:
- Statistics computed for each pair of images
- Line for each pair of images in the same sample
- Line format: (absolute time difference), ((mag leading) / (mag trailing))

image_stats.dat:
- Statistics computed for each sampled system
- Line for each sampled system
- Line format: (number of images), (total magnification)
    - Total magnification is the sum of absolute mags of each image

image_list.dat:
- List of statistics for each individual image
- Line for each image
- Line format: (time delay), (magnification)
    - Time delays are still relative to first image in units of days
    - Magnifications here are given with their sign
'''
def process_dat():
    global succ_percent   # Inherits global variables

    # Initializes lists for later writing
    num_images = []   # Number of images for each sampled system
    total_mag = []   # Total magnification of each sampled system
    pair_mags = []   # Magnification ratio for each image pair (unsigned)
    pair_delays = []   # Delay between each image pair in days
    image_delays = []   # Delay of each image relative to first image
    image_mags = []   # Magnification of each image
    min_delays = []   # Minimum relative delay between a system's image pairs

    # Loops through dat[] appending relevant statistics as needed
    for i in range(0, len(dat)):
        for j in range(0, len(dat[i])):
            num_images.append(int(round(dat[i][j][0][0])))   # Number of imgs
            lens_mag = 0   # Used to sum up total magnification for a sample

            cmin_delay = -1.0   # Tracks current pairwise min_delay

            # Loops through all images; line 0 contains some global stats
            for k in range(1, len(dat[i][j])):
                lens_mag += abs(dat[i][j][k][2])   # Add to total mag

                # Statistics for each image
                ktime = dat[i][j][k][3]
                kmag = dat[i][j][k][2]
                image_delays.append(ktime)
                image_mags.append(kmag)

                # Loops through pairs of images, avoiding doubles
                for l in range(k + 1, len(dat[i][j])):
                    # Statistics for paired image
                    ltime = dat[i][j][l][3]
                    lmag = dat[i][j][l][2]

                    # Pair's mag ratio computed Leading / Trailing (unsigned)
                    if ktime < ltime:
                        pair_mags.append(abs(kmag)/abs(lmag))
                    else:
                        pair_mags.append(abs(lmag)/abs(kmag))

                    # Pair's relative time delay in days
                    pair_delays.append(abs(ktime - ltime))

                    # Compares each pair's delay against current min
                    if cmin_delay < 0 or abs(ktime - ltime) < cmin_delay:
                        cmin_delay = abs(ktime - ltime)

            total_mag.append(lens_mag)   # Total magnification for sample
            min_delays.append(cmin_delay)   # Min delay for sample

    '''
    From here on out, it is just procedurally writing different output
    files to the trial folder. Contents of each file are described in
    method header. Can easily add or adjust file outputs by adding another
    write with block or adjusting existing ones; all will go into the
    same trial folder.
    '''

    # Writes data for "image_pairs.dat"
    with open("image_pairs.dat", 'w') as pairs:
        for i in range(0, len(pair_delays)):
            pairs.writelines(f"{pair_delays[i]},{pair_mags[i]}\n")
        pairs.close()

    # Writes data for "image_stats.dat"
    with open("image_stats.dat", 'w') as images:
        for i in range(0, len(num_images)):
            images.writelines(f"{num_images[i]},{total_mag[i]}\n")
        images.close()

    # Writes data for "image_list.dat"
    with open("image_list.dat", 'w') as imgs:
        for i in range(0, len(image_delays)):
            imgs.writelines(f"{image_delays[i]},{image_mags[i]}\n")

    sorted_min_delays = min_delays
    sorted_min_delays.sort()
    percent_below = []
    days = []
    for i in range(1, 31):
        days.append(i)
        for j in range(0, len(sorted_min_delays)):
            if sorted_min_delays[j] > i:
                num_below = j
                break
        percent_below.append(num_below / len(sorted_min_delays))

    plt.plot(days, percent_below, 'r--')
    plt.xlabel("Days")
    plt.ylabel("% of Systems with Min TD Below Days")
    plt.title("Likelihood of Interference with n-Day Observation Windows")
    plt.show()

    plt.scatter(pair_delays, pair_mags)
    plt.xlabel("Time Delay (Days)")
    plt.ylabel("Mag(Leading) / Mag(Trailing)")
    plt.title("Image Pair Mag Ratios Vs. TD")
    plt.show()

    chopped_image_delays = []
    for i in range(0, len(image_delays)):
        if image_delays[i] > 0 and image_delays[i] <= 45:
            chopped_image_delays.append(math.log(image_delays[i]))

    plt.hist(chopped_image_delays, bins=50)
    #plt.xscale('log')
    plt.xlabel("Log of Time Delay (Days)")
    plt.ylabel("Number of Systems")
    plt.title("Histogram of Time Delays")
    plt.show()


# Calls main subroutine after defining all functions
if __name__ == '__main__':
    main()
