'''
run.py (gprofile2)
Evan Meade, 2020
Research group of Dr. Lindsay King (UTD)

Generates GUI for assigning trial parameters and viewing preliminary results.

This script serves as a grahical front-end to gprofile2, a Python project
which statistically samples and characterizes strong lensing of gravitational
waves. It uses glafic, an executable developed by M. Oguri (2010), to
actually solve each lens equation, while gprofile2 randomly samples over a
physically accurate parameter space and compiles results. In order to simplify
use, this script adds a visual tool for assigning parameter bounds manually.


To-Do:
- Add graphic update methods

'''

# External package imports
import numpy as np
import PySimpleGUI as sg

# gprofile2 package imports
import gprofile2 as gp2


# Sets window theme
sg.ChangeLookAndFeel('Dark')

# Sets column width
WIDTH = 80

# Assigns style parameters for GUI items
ttl = {'font': ('Helvetica', 30)}
sec = {'font': ('Helvetica', 20)}
inp = {'size': (12,1)}

# Generates random seed
default_seed = f'{np.random.randint(0,100000000):08d}'

# Defines formatting of input parameters column
input_col = [
                [sg.Txt('Trial Configuration', **ttl)],
                [sg.Txt('_' * WIDTH)],
                [sg.Txt(' ' * WIDTH)],
                [sg.Txt('Simulation Parameters', **sec)],
                [sg.Txt('Trial name:'), sg.In('Untitled', size=(30,1), key='trial_name'), sg.Txt('Number of runs:'), sg.In('50', **inp, key='num_samp')],
                [sg.Txt('Random seed (string):'), sg.In(f'{default_seed}', **inp, key='seed')],
                [sg.Txt('_' * WIDTH)],
                [sg.Txt(' ' * WIDTH)],
                [sg.Txt('Lens Parameters', **sec)],
                [sg.Txt('Z-min:'), sg.In('0.3', **inp, key='lens_z_min'), sg.Txt('Z-max:'), sg.In('0.8', **inp, key='lens_z_max')],
                [sg.Txt('_' * WIDTH)],
                [sg.Txt(' ' * WIDTH)],
                [sg.Txt('Source Parameters', **sec)],
                [sg.Txt('Sampling radius (arcsecond):'), sg.In('1.0', **inp, key='samp_radius')],
                [sg.Txt('Z-min:'), sg.In('2.5', **inp, key='source_z_min'), sg.Txt('Z-max:'), sg.In('4.0', **inp, key='source_z_max')],
                [sg.Txt(' ' * WIDTH)],
                [sg.Button('Run'), sg.Button('Exit')],
                [sg.Txt(' ' * WIDTH)]
                ]

# Defines formatting of output results column
output_col = [
                [sg.Txt('Trial Output', **ttl, key='title_output')],
                [sg.Txt('_' * WIDTH)],
                [sg.Txt(' ' * WIDTH)],
                [sg.Image(filename='graph_placeholder.png', key='graph_output')],
                [sg.Txt(' ' * WIDTH)]
                ]

# Combines columns into final GUI layout
layout = [
            [sg.Column(input_col), sg.Column(output_col)]
            ]

# Creates window based on final GUI layout
window = sg.Window('gprofile2', layout)

values = {'trial_name': 'INIT', 'seed': 'INIT'}

# Scans for button input events
while True:
    # Prints event and values if button triggered
    event, values = window.read()
    print(event, values)

    # Exits scanning loop if 'Exit' buttons pressed
    if event in (None, 'Exit'):
        break

    # Executes gprofile2 simulation if 'Run' button pressed
    elif event in ('Run'):
        master_folder, trial_folder = gp2.execute(values)
        window['seed'].Update(value=f'{np.random.randint(0,100000000):08d}')
        interference = f'{master_folder}/{trial_folder}/interference_cdf.png'
        window['graph_output'].Update(filename=interference)
        window['title_output'].Update(value=trial_folder)

# Closes window
window.close()
