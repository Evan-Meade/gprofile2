import numpy as np
import PySimpleGUI as sg

import gprofile2 as gp2


sg.ChangeLookAndFeel('Dark')

WIDTH = 80
ttl = {'font': ('Helvetica', 30)}
sec = {'font': ('Helvetica', 20)}
inp = {'size': (12,1)}

default_seed = f'{np.random.randint(0,100000000):08d}'

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

output_col = [
                [sg.Txt('Trial Output', **ttl)],
                [sg.Txt('_' * WIDTH)]
                ]

layout = [
            [sg.Column(input_col), sg.Column(output_col)]
            ]

window = sg.Window('gprofile2', layout)

while True:
    event, values = window.read()
    print(event, values)
    if event in (None, 'Exit'):
        break
    elif event in ('Run'):
        gp2.execute(values)

window.close()
