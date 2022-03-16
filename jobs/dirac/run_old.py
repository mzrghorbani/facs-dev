#!/usr/bin/env python3

import facs as facs
import measures as measures
import read_age_csv
import numpy as np
import read_building_csv
import read_cases_csv
import read_disease_yml
import sys

from os import makedirs, path
import argparse
import csv
from pprint import pprint

from datetime import datetime, timedelta


if __name__ == "__main__":

    # halton 100 0.625 extend-lockdown 1 . . . False 19 23 01/12/2021 False

    #location = "greater_manchester"
    #house_ratio = int(100)
    #ci_multiplier = float(0.625)
    #transition_scenario = "extend-lockdown"
    #transition_mode = int(1)
    #output_dir = "."
    #data_dir = "."
    #measures_dir = "."
    #generic_outfile = False
    #simulation_period = int(19)
    #starting_infections = 23
    #start_date = "01/12/2021"
    #dbg = False
   
    location = sys.argv[1].lower()
    house_ratio = int(sys.argv[2])
    ci_multiplier = float(sys.argv[3])
    transition_scenario = sys.argv[4].lower()
    transition_mode = int(sys.argv[5])
    output_dir = sys.argv[6]
    data_dir = sys.argv[7]
    measures_dir = sys.argv[8]
    generic_outfile = sys.argv[9]
    simulation_period = int(sys.argv[10])
    starting_infections = sys.argv[11]
    start_date = sys.argv[12]
    dbg = sys.argv[13]
    print("The arguments are:" , str(sys.argv))


    # if simsetting.csv exists -> overwrite the simulation setting parameters
    if path.isfile('simsetting.csv'):
        with open('simsetting.csv', newline='') as csvfile:
            values = csv.reader(csvfile)
            for row in values:
                if len(row) > 0:  # skip empty lines in csv
                    if row[0][0] == "#":
                        pass
                    elif row[0].lower() == "transition_scenario":
                        transition_scenario = str(row[1]).lower()
                    elif row[0].lower() == "transition_mode":
                        transition_mode = int(row[1])

    transition_day = -1
    # if transition_mode == 1:
    #     transition_day = 77  # 15th of April
    # if transition_mode == 2:
    #     transition_day = 93  # 31st of May
    # if transition_mode == 3:
    #     transition_day = 108  # 15th of June
    # if transition_mode == 4:
    #     transition_day = 123  # 30th of June
    # if transition_mode > 10:
    #     transition_day = transition_mode

    # check the transition scenario argument
    AcceptableTransitionScenario = ['no-measures', 'extend-lockdown',
                                    'open-all', 'open-schools', 'open-shopping',
                                    'open-leisure', 'work50', 'work75',
                                    'work100', 'dynamic-lockdown', 'periodic-lockdown','uk-forecast']

    if transition_scenario not in AcceptableTransitionScenario:
        print("\nError !\n\tThe input transition scenario, %s , is not VALID" %
              (transition_scenario))
        print("\tThe acceptable inputs are : [%s]" %
              (",".join(AcceptableTransitionScenario)))
        sys.exit()

    # check if output_dir is exists
    if not path.exists(output_dir):
        makedirs(output_dir)

    outfile = "{}/{}-{}-{}.csv".format(output_dir,
                                       location,
                                       transition_scenario,
                                       transition_day)
    if generic_outfile == True:
      outfile = "{}/out.csv".format(output_dir)

    end_time = 1100
    if transition_scenario in ["extend-lockdown","dynamic-lockdown","periodic-lockdown","uk-forecast"]:
      end_time = 1100
    
    if simulation_period > 0:
      end_time = simulation_period
    
    print("Running basic Covid-19 simulation kernel.")
    print("scenario = %s" % (location))
    print("transition_scenario = %s" % (transition_scenario))
    print("transition_mode = %d" % (transition_mode))
    print("transition_day = %d" % (transition_day))
    print("end_time = %d" % (end_time))
    print("output_dir  = %s" % (output_dir))
    print("measures_dir = %s" % (measures_dir))
    print("outfile  = %s" % (outfile))
    print("data_dir  = %s" % (data_dir))


    e = facs.Ecosystem(end_time)

    e.ci_multiplier = ci_multiplier
    e.ages = read_age_csv.read_age_csv("{}/age-distr.csv".format(data_dir), location)

    print("age distribution in system:", e.ages, file=sys.stderr)

    e.disease = read_disease_yml.read_disease_yml(
        "{}/disease_covid19.yml".format(data_dir))

    building_file = "{}/{}_buildings.csv".format(data_dir, location)
    read_building_csv.read_building_csv(e,
                                        building_file,
                                        "{}/building_types_map.yml".format(data_dir),
                                        house_ratio=house_ratio, workspace=12, office_size=1600, household_size=2.6, work_participation_rate=0.5)
    # house ratio: number of households per house placed (higher number adds noise, but reduces runtime
    # And then 3 parameters that ONLY affect office placement.
    # workspace: m2 per employee on average. (10 in an office setting, but we use 12 as some people work in more spacious environments)
    # household size: average size of each household, specified separately here.
    # work participation rate: fraction of population in workforce, irrespective of age

    #print("{}/{}_cases.csv".format(data_dir, location))
    # Can only be done after houses are in.
    #read_cases_csv.read_cases_csv(e,
    #                              "{}/{}_cases.csv".format(data_dir, location),
    #                              start_date=args.start_date,
    #                              date_format="%m/%d/%Y")

    if starting_infections:
      starting_num_infections = int(starting_infections)
    if location == "test":
      starting_num_infections = 10

    for i in range(0,10):
      e.add_infections(int(starting_num_infections/10), i-19)

    print("THIS SIMULATIONS HAS {} AGENTS.".format(e.num_agents))

    e.time = -20
    e.date = datetime.strptime(start_date, "%d/%m/%Y")
    e.date = e.date - timedelta(days=20)
    e.print_header(outfile)
    for i in range(0, 20):
        e.evolve(reduce_stochasticity=False)
        print(e.time)
        if dbg == True:
            e.print_status(outfile)
        else:
            e.print_status(outfile, silent=True)


    track_trace_limit = 0.2 + transition_mode*0.1

    measures_file = "{}/measures_{}.yml".format(measures_dir, location.lower())

    for t in range(0, end_time):

        if t == transition_day:
            if transition_scenario == "extend-lockdown":
                pass
            elif transition_scenario == "open-all":
                e.remove_all_measures()
            elif transition_scenario == "open-schools":
                e.remove_closure("school")
            elif transition_scenario == "open-shopping":
                e.undo_partial_closure("shopping", 0.8)
            elif transition_scenario == "open-leisure":
                e.remove_closure("leisure")
            elif transition_scenario == "work50":
                measures.work50(e)
            elif transition_scenario == "work75":
                measures.work75(e)
            elif transition_scenario == "work100":
                measures.work100(e)

        if t>77 and transition_scenario == "dynamic-lockdown" and t%7 == 0:
            print("Dynamic lockdown test: {}/100".format(e.num_hospitalised), file=sys.stderr)
            measures.enact_dynamic_lockdown(e, measures.work50, e.num_hospitalised, 100)
        if t>77 and transition_scenario == "periodic-lockdown" and t%61 == 0:
            print("Periodic lockdown with 61 day interval.")
            measures.enact_periodic_lockdown(e, measures.work50)

        # Recording of existing measures
        if transition_scenario in ["uk-forecast"]:
          measures.uk_lockdown_forecast(e, t, transition_mode)
        elif transition_scenario not in ["no-measures"]:
          measures.uk_lockdown_existing(e, t, measures_file, track_trace_limit=track_trace_limit)

        # Propagate the model by one time step.
        e.evolve()

        print(t, e.get_date_string(),  e.vac_no_symptoms, e.vac_no_transmission)
        e.print_status(outfile)

    # calculate cumulative sums.
    e.add_cum_column(outfile, ["dead", "num hospitalisations today", "infectious", "num infections today"])

    print("Simulation complete.", file=sys.stderr)
