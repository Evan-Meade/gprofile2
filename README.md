# gprofile2
Statistically characterizes gravitational lensing of gravitational waves

By utilizing the computational methods of glafic, an executable developed by M. Oguri (2010), these scripts can rapidly generate, sample, and analyze a list of galactic lenses over a representative sampling distribution. Galactic lenses are randomly sampled over the SIE lens parameter space outlined in M. Oguri (2018).

The modular design of each step is intended to make it easy to divide tasks simply across multiple computing processes.

Dependencies:
* Python3
  * Developed with Python 3.6.8
* numpy
  * Developed with version 1.17.0 in a Python3 venv
* matplotlib
  * Developed with version 3.1.1 in a Python3 venv
* glafic (added to $PATH)
  * Can be downloaded at https://www.slac.stanford.edu/~oguri/glafic/
  * UNIX only (Mac OSX and Linux (64 bit))
  * Binary only; source code cannot be published due to copyright

NOTE: Developed in a UNIX environment (Ubuntu 18.04); untested elsewhere.

Usage instructions:
1. Clone repository or download and unzip source code for gprofile2
2. Install glafic
3. In bash shell, navigate to gprofile2 master directory
4. Create or activate appropriate venv (including Python3 and required packages)
5. Generate galaxy list with generator.py
  * Execute generator.py with appropriate parameters
  * "python generator.py {number of galaxies} {output file name} {random seed}"
  * Ex. "python generator.py 10 gals.dat 123456"
    * Will output list of 10 SIE galaxies to gals.dat in working directory
    * Same list will be generated if run with same parameters and seed
6. Run gprofile2.py on the galaxy list using a template glafic .input file
  * This bundle was designed to analyze time delays using config.input
  * "python gprofile2.py {template glafic input} {galaxy list} {random seed} {z lens} {z source}"
  * Ex. "python gprofile2.py config.input gals.dat 12345678"
  * Each successful run of this will create a new trial folder in Results/
7. Analyze .npy results with analyzer.py
  * Direct analyzer.py to the appropriate directory and it will compile .npy's
  * "python analyzer.py path/to/all/npy/files"
  * Ex. "python analyzer.py Results/gals.dat---Trial000"
8. Interpret given results or feed .npy files into further interpretation

Created by Evan Meade (https://github.com/Evan-Meade, aka. kracken9500), 2019

Research group of Dr. Lindsay King (UTD)
