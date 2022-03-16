import csv
import sys
import pprint
import yaml
import disease

pp = pprint.PrettyPrinter()

def read_disease_yml(ymlfile="disease-covid19.yml"):

  with open(ymlfile) as f:
    dp = yaml.safe_load(f)
  d = disease.Disease(dp["infection_rate"], dp["incubation_period"], dp["mild_recovery_period"], dp["recovery_period"], dp["mortality_period"], dp["period_to_hospitalisation"])
  d.addHospitalisationChances(dp["hospitalised"])
  d.addMortalityChances(dp["mortality"])
  d.print()
  return d


