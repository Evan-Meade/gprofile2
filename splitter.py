'''
splitter.py (gprofile2)
Evan Meade, 2019
Research group of Dr. Lindsay King (UTD)

This script splits a galaxy list into n different galaxy lists.

Splitting a large galaxy list in this way allows for easy distributed
computing since each one can have its statistics computed in a separate
instance of gprofile2.py. Results can then be recombined and interpretted
together.

Dependencies:
- Python3

Execution format:
python splitter.py {galaxy list} {number of output files}

'''

# Built-in imports
import sys
import os
import math

# Calls down splitting parameters from execution line
list_name = sys.argv[1]
num_out = sys.argv[2]

# Initializes list to contain each galaxy argument
gals = []

# Reads each galaxy from given file into gals[]
with open(list_name, 'r') as orig:
    for line in orig:
        gals.append(line.strip(f"\n"))
    orig.close()

# Calculates how many galaxies to put into each file
num_gals = len(gals)
split_size = math.floor(num_gals / num_out)

# Creates and moves to folder named after master galaxy file and num_out
master_folder = f"GAL_SET___{list_name}---{num_out}"
if os.path.exists(master_folder):
    os.chdir(master_folder)
else:
    os.mkdir(master_folder)
    os.chdir(master_folder)

current_pos = 0   # Tracks current position of next unwritten line

# Loops over all new galaxy files except for last one
for i in range(0, num_out - 1):
    # Creates new file for each new galaxy file and reads in split_size gals
    with open(f"{list_name}---{i:03}", 'w') as clipped:
        for j in range(0, split_size):
            clipped.writelines(f"{gals[i + j]}\n")
        clipped.close()

    # Iterates current position of next unwritten line
    current_pos += split_size

# Writes remaining lines to last new galaxy file
with open(f"{list_name}---{(num_out - 1):03}", 'w') as clipped:
    for j in range(current_pos, len(gals)):
        clipped.writelines(f"{gals[j]}\n")
    clipped.close()
