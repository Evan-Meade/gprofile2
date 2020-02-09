'''
analyzer.py (gprofile2)
Evan Meade, 2020
Research group of Dr. Lindsay King (UTD)

Conducts analysis on results of lensing simulations from gprofile2.


To-Do:
- Add graphic update methods
- Expand image number id capture in secondary dataframes

'''

# Built-in imports
import sys
import os
import math

# Library imports
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def analyze():
    analyze_images()

    print('Analysis complete')

def analyze_images():
    trial_data = pd.read_hdf('data.h5', key='trial_data')
    print(trial_data)
    raw_img = np.array(trial_data['image_dat_output'])

    # Initializes arrays for later writing
    single_run_id = np.array([])
    pair_run_id = np.array([])
    num_images = np.array([])   # Number of images for each sampled system
    total_mag = np.array([])   # Total magnification of each sampled system
    pair_mags = np.array([])   # Magnification ratio for each image pair (unsigned)
    pair_delays = np.array([])   # Delay between each image pair in days
    image_delays = np.array([])   # Delay of each image relative to first image
    image_mags = np.array([])   # Magnification of each image
    min_delays = np.array([])   # Minimum relative delay between a system's image pairs

    tot_samps = len(raw_img)   # Total number of trials

    # Loops through raw image data appending relevant statistics as needed
    for i in range(0, tot_samps):
        run = trial_data.loc[i, 'run_id']   # Records run id for each image set

        num_images = np.append(num_images, int(round(raw_img[i][0,0])))   # Number of imgs
        lens_mag = 0   # Used to sum up total magnification for a sample

        cmin_delay = -1.0   # Tracks current pairwise min_delay

        # Loops through all images; line 0 contains some global stats
        for k in range(1, len(raw_img[i])):
            single_run_id = np.append(single_run_id, run)   # Updates run id array

            lens_mag += abs(raw_img[i][k,2])   # Add to total mag

            # Statistics for each image
            ktime = raw_img[i][k,3]
            kmag = raw_img[i][k,2]
            image_delays = np.append(image_delays, ktime)
            image_mags = np.append(image_mags, kmag)

            # Loops through pairs of images, avoiding doubles
            for l in range(k + 1, len(raw_img[i])):
                pair_run_id = np.append(pair_run_id, run)   # Updates pair run id array

                # Statistics for paired image
                ltime = raw_img[i][l,3]
                lmag = raw_img[i][l,2]

                # Pair's mag ratio computed Leading / Trailing (unsigned)
                if ktime < ltime:
                    pair_mags = np.append(pair_mags, abs(kmag)/abs(lmag))
                else:
                    pair_mags = np.append(pair_mags, abs(lmag)/abs(kmag))

                # Pair's relative time delay in days
                pair_delays = np.append(pair_delays, abs(ktime - ltime))

                # Compares each pair's delay against current min
                if cmin_delay < 0 or abs(ktime - ltime) < cmin_delay:
                    cmin_delay = abs(ktime - ltime)

        total_mag = np.append(total_mag, lens_mag)   # Total magnification for sample
        min_delays = np.append(min_delays, cmin_delay)   # Min delay for sample

    '''
    For this next section, it is just procedurally writing different output
    files to the trial folder. Contents of each file are described in
    method header. Can easily add or adjust file outputs by adding another
    write with block or adjusting existing ones; all will go into the
    same trial folder.
    '''

    # Opens up the main data.h5 file
    hdf = pd.HDFStore('data.h5')

    # Enters global stats into the file
    global_stats = pd.Series({'total_samples': tot_samps,
                                'total_images': np.sum(num_images),
                                'total_image_pairs': pair_delays.shape[0]})
    hdf.put('global_stats', global_stats, format='table', data_columns=True)

    # Appends total_mag and min_delay columns to data
    trial_data['total_mag'] = total_mag
    trial_data['min_delay'] = min_delays
    hdf.remove('trial_data')
    hdf.put('trial_data', trial_data, data_columns=True)

    # Enters stats for each pair of images in the same trial
    image_pairs = pd.DataFrame({'pair_run_id': pair_run_id,
                                'pair_delays': pair_delays,
                                'pair_mags': pair_mags})
    hdf.put('image_pairs', image_pairs, format='table', data_columns=True)

    # Closes main data.h5 file
    hdf.close()


    '''
    This section utilizes the same decomposed data written to files to
    generate a series of useful visualizations. Plots, histograms, and
    fitted curves are all used to better examine the relationship between
    different variables.
    '''

    # Approximates a cumulative distribution function (CDF) for min delays
    sorted_min_delays = min_delays   # Copies of min_delays
    sorted_min_delays.sort()   # Sorts min_delays in ascending order
    percent_below = []   # Stores CDF approximation for each amount of days
    days = []   # Lists days for plotting against

    # Loops through sorted_min_delays approximating CDF
    for i in range(1, 31):
        days.append(i)   # Appends day to days

        # Loops through sorted_min_delays until element exceeds days
        for j in range(0, len(sorted_min_delays)):
            if sorted_min_delays[j] > i:
                num_below = j
                break

        # Appends percentage of min delays below days
        percent_below.append(num_below / len(sorted_min_delays) * 100)

    # Plots CDF for probability of interference in n-Day observation window
    plt.figure(1)   # Numbers plot for multiple figure display at end
    plt.plot(days, percent_below, 'r--')
    plt.xlabel("Days")
    plt.ylabel("% of Systems with Min TD Below Days")
    plt.title("Likelihood of Interference with n-Day Observation Windows")
    plt.savefig("interference_cdf.png", dpi=200)

    #plt.show()

    # Plots magnification ratio against time delay between each image pair
    plt.figure(2)
    plt.scatter(pair_delays, pair_mags)
    plt.xlabel("Time Delay (Days)")
    plt.ylabel("Mag(Leading) / Mag(Trailing)")
    plt.title("Image Pair Mag Ratios Vs. TD")
    plt.savefig("image_ratios.png")
    #plt.show()

    # Preps image_delays for use in log histogram
    chopped_image_delays = []
    for i in range(0, len(image_delays)):
        # Trims elements to be within given range
        if image_delays[i] > 0 and image_delays[i] <= 45:
            # Appends log of each element in given range
            chopped_image_delays.append(math.log(image_delays[i]))

    # Plots a log histogram of the image delays relative to first image
    plt.figure(3)   # Numbers plot for multiple figure display at end
    plt.hist(chopped_image_delays, bins=50)
    plt.xlabel("Log of Time Delay (Days)")
    plt.ylabel("Number of Systems")
    plt.title("Histogram of Time Delays")
    plt.savefig("log_td.png")



    # Prints completion statement
    print('Image analysis complete')
