# FACS: Flu And Coronavirus Simulator

[![Build Status](https://travis-ci.com/djgroen/facs.svg?branch=master)](https://travis-ci.com/djgroen/facs)
[![GitHub Issues](https://img.shields.io/github/issues/djgroen/facs.svg)](https://github.com/djgroen/facs/issues)
[![GitHub last-commit](https://img.shields.io/github/last-commit/djgroen/facs.svg)](https://github.com/djgroen/facs/commits/master)


Full documentation can be found at: http://facs.readthedocs.io

## How to run the code
To run a simple simulation of a basic test dataset, type:
`python3 run.py --location=test --transition_scenario=extend-lockdown --transition_mode=1 --output_dir=.`

To run a simulation of the Borough of Brent, type:
`python3 run.py --location=brent --transition_scenario=extend-lockdown --transition_mode=1 --output_dir=.`

To run a simulation of Brunel University London, type:
`python3 run_campus.py --location=brunel --transition_scenario=extend-lockdown --transition_mode=1 --output_dir=.`

Outputs are written as CSV files in the output\_dir. E.g. for the test run you will get:
covid\_out\_infections.csv
test-extend-lockdown-62.csv

There is a hardcoded lockdown in run.py which is representative for the UK. This can be disabled by selecting the transition scenario "no-measures".

We also included a simple plotting script. This can be called e.g. as follows:
`python3 PlotSEIR.py test-extend-lockdown-62.csv test`

## Advanced usage

### Running with a specific data directory
Flacs can be run with a different input data directory as follows:
`python3 run.py --location=brent --transition_scenario=extend-lockdown --transition_mode=1 --output_dir=. --data_dir=/home/derek/covid19-postprocess/flacs_input_private`

### Performing quick tests
Quick tests can be triggered with the '-q' flag. This sets the house ratio to 100 (default is 2), which means that households will be less well distributed.
However, as a number of calculations are performed on the house level (not the household level), this setting speeds up the code by up to an order of magnitude.
`python3 run.py -q --location=brent --transition_scenario=extend-lockdown --transition_mode=1 --output_dir=.`

# facs-dev is a development branch by Maziar Ghorbani (Stamina) on https://github.com/djgroen/facs.git
