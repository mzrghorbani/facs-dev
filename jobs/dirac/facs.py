# FLu And Coronavirus Simulator
# Covid-19 model, based on the general Flee paradigm.
import numpy as np
import sys
import random
import array
import csv
import pandas as pd
import os
#import fastrand
from datetime import datetime, timedelta

# TODO: store all this in a YaML file
lids = {"park":0,"hospital":1,"supermarket":2,"office":3,"school":4,"leisure":5,"shopping":6} # location ids and labels
lnames = list(lids.keys())
avg_visit_times = [90,60,60,360,360,60,60] #average time spent per visit
home_interaction_fraction = 0.2 # people are within 2m at home of a specific other person 20% of the time.


# Added commented code to shift from random.random if needed
#_rnd_i = 0
#_rnd_nums = np.random.random(10000)
def get_rnd():
    return random.random()
    #global _rnd_i, _rnd_nums
    #_rnd_i += 1
    #if _rnd_i > 9999:
    #  _rnd_i = 0
    #  _rnd_nums = np.random.random(10000)
    #return _rnd_nums[_rnd_i]

def get_rndint(high):
    #return random.randrange(0, high)
    #return fastrand.pcg32bounded(high)
    return np.random.randint(high)

class Needs():
  def __init__(self, csvfile):
    self.add_needs(csvfile)
    self.household_isolation_multiplier = 1.0
    print("Needs created. Household isolation multiplier set to {}.".format(self.household_isolation_multiplier))

  def i(self, name):
    for k,e in enumerate(self.labels):
      if e == name:
        return k

  def add_needs(self, csvfile=""):
    if csvfile == "":
      self.add_hardcoded_needs()
      return
    self.needs = np.zeros((len(lids),120))
    needs_cols = [0]*len(lids)
    with open(csvfile) as csvfile:
      needs_reader = csv.reader(csvfile)
      row_number = 0
      for row in needs_reader:
        if row_number == 0:
          for k,element in enumerate(row):
            if element in lids.keys():
              #Debug symbols in to debug custom sets of needs.
              #print(element,k)
              #print("NC:",needs_cols)
              
              needs_cols[lids[element]] = k
        else:
          for i in range(0,len(needs_cols)):
            self.needs[i,row_number-1] = int(row[needs_cols[i]])
          self.needs[i,lids["school"]] = int(0.75*int(row[needs_cols[i]])) # assuming 25% of school time is outside of the building (PE or breaks)
        row_number += 1

  def get_needs(self, person):
    if not person.hospitalised:
      n = self.needs[:,person.age].copy()
      if person.work_from_home:
        n[lids["office"]]=0
      if person.school_from_home:
        n[lids["school"]]=0
      return n
    else:
      return np.array([0,5040,0,0,0,0,0])

# Global storage for needs now, to keep it simple.
needs = Needs("needs.csv")
num_infections_today = 0
num_hospitalisations_today = 0
num_deaths_today = 0
num_recoveries_today = 0
log_prefix = "."


class OUTPUT_FILES():

    def __init__(self):
        self.files = {}

    def open(self, file_name):
        if not file_name in self.files:
            if os.path.exists(file_name):
                os.remove(file_name)            
            self.files[file_name] = open(file_name, "a")

        return self.files[file_name]

    def __del__(self) -> None:
        for out_file in self.files:
            self.files[out_file].close()


out_files = OUTPUT_FILES()


def log_infection(t, x, y, loc_type):
  global num_infections_today
  out_inf = out_files.open("{}/covid_out_infections.csv".format(log_prefix))
  print("{},{},{},{}".format(t, x, y, loc_type), file=out_inf, flush=True)
  num_infections_today += 1

def log_hospitalisation(t, x, y, age):
  global num_hospitalisations_today
  out_inf = out_files.open("{}/covid_out_hospitalisations.csv".format(log_prefix))
  print("{},{},{},{}".format(t, x, y, age), file=out_inf, flush=True)
  num_hospitalisations_today += 1

def log_death(t, x, y, age):
  global num_deaths_today
  out_inf = out_files.open("{}/covid_out_deaths.csv".format(log_prefix))
  print("{},{},{},{}".format(t, x, y, age), file=out_inf, flush=True)
  num_deaths_today += 1

def log_recovery(t, x, y, age):
  global num_recoveries_today
  out_inf = out_files.open("{}/covid_out_recoveries.csv".format(log_prefix))
  print("{},{},{},{}".format(t, x, y, age), file=out_inf, flush=True)
  num_recoveries_today += 1


class Person():
  def __init__(self, location, household, ages):
    self.location = location # current location
    self.location.IncrementNumAgents()
    self.home_location = location
    self.household = household
    self.mild_version = True
    self.hospitalised = False
    self.dying = False
    self.work_from_home = False
    self.school_from_home = False
    self.phase_duration = 0.0 # duration to next phase.
    self.symptoms_suppressed = False # Symptoms suppressed, e.g. due to vaccination, but still infectious.
    self.antivax = False # Refuses vaccines if true.
    if np.random.rand() < 0.05: # 5% are antivaxxers.
      self.antivax = True

    self.status = "susceptible" # states: susceptible, exposed, infectious, recovered, dead, immune.
    self.symptomatic = False # may be symptomatic if infectious
    self.status_change_time = -1

    self.age = np.random.choice(91, p=ages) # age in years
    self.job = np.random.choice(4, 1, p=[0.865, 0.015, 0.08, 0.04])[0] # 0=default, 1=teacher (1.5%), 2=shop worker (8%), 3=health worker (4%)

  def assign_group(self, location_type, num_groups):
    """
    Used to assign a grouping to a person.
    For example, a campus may have 30 classes (num_groups = 30). Then you would use:
    assign_group("school", 30)
    The location type should match the corresponding personal needs category (e.g., school or supermarket).
    """
    if not hasattr(self, 'groups'):
      self.groups = {}
    self.groups[lids[location_type]] = get_rndint(num_groups)


  def location_has_grouping(self, lid):
    """
    Takes a location type ID: return True or False
    """
    if hasattr(self, 'groups'):
      if lid in list(self.groups.keys()):
        #print(lid, list(self.groups.keys()))
        return True
    return False


  def vaccinate(self, time, vac_no_symptoms, vac_no_transmission, vac_duration):
    self.status_change_time = time # necessary if vaccines give temporary immunity.
    if vac_duration > 0:
      if vac_duration > 100:
        self.phase_duration = np.random.gamma(10, vac_duration/10.0) # shape parameter is changed with variable, shape parameter is kept fixed at 15 (assumption).
      else:
        self.phase_duration = np.poisson(vac_duration)
    if self.status == "susceptible":
      if get_rnd() < vac_no_transmission:
        self.status = "immune"
      elif get_rnd() < vac_no_symptoms:
        self.symptoms_suppressed = True
    #print("vac", self.status, self.symptoms_suppressed, self.phase_duration)


  def plan_visits(self, e, deterministic=False):
    """
    Plan visits for the day.
    TODO: plan visits to classes not using nearest location (make an override).
    """

    if self.status in ["susceptible","exposed","infectious"]: # recovered people are assumed to be immune.
      personal_needs = needs.get_needs(self)
      for k,element in enumerate(personal_needs):
        nearest_locs = self.home_location.nearest_locations

        if element < 1:
          continue
        elif k == lids["hospital"] and self.hospitalised:
          location_to_visit = self.hospital

        elif k == lids["office"] and self.job > 0:
          if self.job == 1: # teacher
            location_to_visit = nearest_locs[lids["school"]]
          if self.job == 2: # shop employee
            location_to_visit = nearest_locs[lids["shopping"]]
          if self.job == 3: # health worker
            location_to_visit = nearest_locs[lids["hospital"]]

        elif self.location_has_grouping(k):
          location_to_visit = e.get_location_by_group(k, self.groups[k])

        elif nearest_locs[k]: 
          location_to_visit = nearest_locs[k]
        else: #no known nearby locations.
          continue
      
        location_to_visit.register_visit(e, self, element, deterministic)

  def print_needs(self):
    print(self.age, needs.get_needs(self))

  def get_needs(self):
    return needs.get_needs(self)

  def get_hospitalisation_chance(self, disease):
    age = int(min(self.age, len(disease.hospital)-1))
    return disease.hospital[age]

  def get_mortality_chance(self, disease):
    age = int(min(self.age, len(disease.hospital)-1))
    return disease.mortality[age]

  def infect(self, t, severity="exposed", location_type="house"):
    # severity can be overridden to infectious when rigidly inserting cases.
    # but by default, it should be exposed.
    self.status = severity
    self.status_change_time = t
    self.mild_version = True
    self.hospitalised = False
    log_infection(t,self.location.x,self.location.y,location_type)

  def recover(self, e, t, location):
    if e.immunity_duration > 0:
      self.phase_duration = np.random.gamma(e.immunity_duration/15, 15) # shape parameter is changed with variable, shape parameter is kept fixed at 15 (assumption).
    self.status = "recovered"
    self.status_change_time = t
    log_recovery(t, self.location.x, self.location.y, location)

  def progress_condition(self, e, t, disease):
    if self.status_change_time > t:
      return
    if self.status == "exposed" and t-self.status_change_time >= int(self.phase_duration):
      self.status = "infectious"
      self.status_change_time = t
      if get_rnd() < self.get_hospitalisation_chance(disease) and self.symptoms_suppressed==False: 
        self.mild_version = False
        #self.phase_duration = np.random.poisson(disease.period_to_hospitalisation - disease.incubation_period)
        self.phase_duration = max(1, np.random.poisson(disease.period_to_hospitalisation) - self.phase_duration)
      else:
        self.mild_version = True
        #self.phase_duration = np.random.poisson(disease.mild_recovery_period - disease.incubation_period)
        self.phase_duration = max(1, np.random.poisson(disease.mild_recovery_period) - self.phase_duration)

    elif self.status == "infectious":
      # mild version (may require hospital visits, but not ICU visits)
      if self.mild_version:
        if t-self.status_change_time >= self.phase_duration:
          self.recover(e, t, "house")
      # non-mild version (will involve ICU visit)
      else:
        if not self.hospitalised:
          if t-self.status_change_time >= self.phase_duration:
            self.hospitalised = True
            self.hospital = e.find_hospital()
            if self.hospital == None:
              print("Error: agent is hospitalised, but there are no hospitals in the location graph.")
              sys.exit()
            e.num_hospitalised += 1
            log_hospitalisation(t, self.location.x, self.location.y, self.age)
            self.status_change_time = t #hospitalisation is a status change, because recovery_period is from date of hospitalisation.
            if get_rnd() < self.get_mortality_chance(disease) / self.get_hospitalisation_chance(disease): # avg mortality rate (divided by the average hospitalization rate). TODO: read from YML.
              self.dying = True
              self.phase_duration = np.random.poisson(disease.mortality_period)
            else:
              self.dying = False
              self.phase_duration = np.random.poisson(disease.recovery_period)
        else:
          if t-self.status_change_time >= self.phase_duration: #from hosp. date
            self.hospitalised = False 
            e.num_hospitalised -= 1
            self.status_change_time = t
            # decease
            if self.dying:
              self.status = "dead"
              log_death(t,self.location.x,self.location.y,"hospital")
            # hospital discharge
            else:
              self.recover(e, t, "hospital")

    elif e.immunity_duration > 0 and (self.status == "recovered" or self.status == "immune"):
      if t-self.status_change_time >= self.phase_duration:
        #print("susc.", self.status, self.phase_duration)
        self.status = "susceptible"
        self.symptoms_suppressed=False


class Household():
  def __init__(self, house, ages, size=-1):
    self.house = house
    if size>-1:
      self.size = size
    else:
      self.size = random.choice([1,2,3,4])

    self.agents = []
    for i in range(0,self.size):
      self.agents.append(Person(self.house, self, ages))


  def get_infectious_count(self):
    ic = 0
    for i in range(0,self.size):
      if self.agents[i].status == "infectious" and self.agents[i].hospitalised == False:
        ic += 1
    return ic


  def is_infected(self):
    return self.get_infectious_count() > 0


  def evolve(self, e, time, disease):
    ic = self.get_infectious_count()
    for i in range(0,self.size):
      if self.agents[i].status == "susceptible":
        if ic > 0:
          infection_chance = e.contact_rate_multiplier["house"] * disease.infection_rate * home_interaction_fraction * ic
          if needs.household_isolation_multiplier < 1.0:
            infection_chance *= 2.0 # interaction duration (and thereby infection chance) double when household isolation is incorporated (Imperial Report 9).
          if get_rnd() < infection_chance:
            self.agents[i].infect(time)

def calc_dist(x1, y1, x2, y2):
    return (np.abs(x1-x2)**2 + np.abs(y1-y2)**2)**0.5

def calc_dist_cheap(x1, y1, x2, y2):
    return np.abs(x1-x2) + np.abs(y1-y2)

class House:
  def __init__(self, e, x, y, num_households=1):
    self.x = x
    self.y = y
    self.households = []
    self.num_agents = 0
    for i in range(0, num_households):
        size = 1 + np.random.poisson(e.household_size-1)
        e.num_agents += size
        self.households.append(Household(self, e.ages, size))

  def IncrementNumAgents(self):
    self.num_agents += 1

  def DecrementNumAgents(self):
    self.num_agents -= 1

  def evolve(self, e, time, disease):
    for hh in self.households:
      hh.evolve(e, time, disease)

  def find_nearest_locations(self, e):
    """
    identify preferred locations for each particular purpose,
    and store in an array.

    Takes into account distance, and to a lesser degree size.
    """
    n = []
    ni = []
    for l in lnames:
      if l not in e.locations.keys():
        n.append(None)
        print("WARNING: location type missing")
      else:
        min_score = 99999.0
        nearest_loc_index = 0
        for k,element in enumerate(e.locations[l]): # using 'element' to avoid clash with Ecosystem e.
          #d = calc_dist_cheap(self.x, self.y, element.x, element.y)
          if element.sqm > 0:
            d = calc_dist(self.x, self.y, element.x, element.y) / np.sqrt(element.sqm)
            if d < min_score:
              min_score = d
              nearest_loc_index = k
          else:
            print("ERROR: location found with 0 sqm area.")
            print("name: {}, x: {}, y: {}, position in array: {}, type: {}".format(element.name, element.x, element.y, k, l))
            print("These errors are commonly caused by corruptions in the <building>.csv file.")
            print("To detect these, you can use the following command:")
            print("cat <buildings file name>.csv | grep -v house | grep \",0$\"")
            sys.exit()
        n.append(e.locations[l][nearest_loc_index])
        ni.append(nearest_loc_index)

    #for i in n:
    #  if i:  
    #    print(i.name, i.type)
    self.nearest_locations = n
    return ni


  def add_infection(self, time, severity="exposed"): # used to preseed infections (could target using age later on)
    infection_pending = True
    while infection_pending:
      hh = get_rndint(len(self.households))
      p = get_rndint(len(self.households[hh].agents))
      if self.households[hh].agents[p].status == "susceptible": 
        # because we do pre-seeding we need to ensure we add exactly 1 infection.
        self.households[hh].agents[p].infect(time, severity)
        infection_pending = False

  def has_age(self, age):
    for hh in self.households:
      for a in hh.agents:
        if a.age == age:
          if a.status == "susceptible":
            return True
    return False

  def add_infection_by_age(self, time, age):
    for hh in self.households:
      for a in hh.agents:
        if a.age == age:
          if a.status == "susceptible":
            a.infect(time, severity="exposed")

class Location:
  def __init__(self, name, loc_type="park", x=0.0, y=0.0, sqm=400):

    if loc_type not in lids.keys():
      print("Error: location type {} is not in the recognised lists of location ids (lids).".format(loc_type))
      sys.exit()

    self.name = name
    self.x = x
    self.y = y
    self.links = [] # paths connecting to other locations
    self.closed_links = [] #paths connecting to other locations that are closed.
    self.type = loc_type # supermarket, park, hospital, shopping, school, office, leisure? (home is a separate class, to conserve memory)
    self.sqm = sqm # size in square meters.
    self.loc_inf_minutes_id = -1 #id of minutes tracking in global array.

    if loc_type == "park":
      self.sqm *= 10 # https://www.medrxiv.org/content/10.1101/2020.02.28.20029272v2 (I took a factor of 10 instead of 19 due to the large error bars)

    self.visits = []
    #print(loc_type, len(lids), lids[loc_type], len(avg_visit_times))
    self.avg_visit_time = avg_visit_times[lids[loc_type]] # using averages for all visits for now. Can replace with a distribution later.
    #print(self.avg_visit_time)
    self.visit_probability_counter = 0.5 #counter used for deterministic calculations.

  def DecrementNumAgents(self):
    self.numAgents -= 1

  def IncrementNumAgents(self):
    self.numAgents += 1

  def clear_visits(self):
    self.visits = []
    self.visit_minutes = 0 # total number of minutes of all visits aggregated.

  def register_visit(self, e,  person, need, deterministic):
    visit_time = self.avg_visit_time
    if person.status == "dead":
      return
    elif person.status == "infectious":
      visit_time *= e.self_isolation_multiplier # implementing case isolation (CI)
      if self.type == "hospital":
        if person.hospitalised:
          e.loc_inf_minutes[self.loc_inf_minutes_id] += need/7 * e.hospital_protection_factor
          return

    elif person.household.is_infected(): # person is in household quarantine, but not subject to CI.
      visit_time *= needs.household_isolation_multiplier

    visit_probability = 0.0
    if visit_time > 0.0:
      visit_probability = need/(visit_time * 7) # = minutes per week / (average visit time * days in the week)
      #if ultraverbose:
      #  print("visit prob = ", visit_probability)
    else:
      return

    if deterministic:
      self.visit_probability_counter += min(visit_probability, 1)
      if self.visit_probability_counter > 1.0:
        self.visit_probability_counter -= 1.0
        self.visits.append([person, visit_time])
        if person.status == "infectious":
          e.loc_inf_minutes[self.loc_inf_minutes_id] += visit_time

    elif get_rnd() < visit_probability:
      self.visits.append([person, visit_time])
      if person.status == "infectious":
        e.loc_inf_minutes[self.loc_inf_minutes_id] += visit_time

  def evolve(self, e, deterministic=False):
    minutes_opened = 12*60

    base_rate = e.contact_rate_multiplier[self.type] * (e.disease.infection_rate/360.0) * (1.0 / minutes_opened) * (e.loc_inf_minutes[self.loc_inf_minutes_id] / self.sqm)
    # For Covid-19 this should be 0.07 (infection rate) for 1 infectious person, and 1 susceptible person within 2m for a full day.
    # I assume they can do this in a 4m^2 area.
    # So 0.07 = x * (24*60/24*60) * (24*60/4) -> 0.07 = x * 360 -> x = 0.07/360 = 0.0002
    # "1.0" is a place holder for v[1] (visited minutes).

    # Deterministic mode: only used for warmup.
    if deterministic:
      inf_counter = 0.5
      for v in self.visits:
        if v[0].status == "susceptible":
          infection_probability = v[1] * base_rate
          inf_counter += min(infection_probability, 1.0)
          if inf_counter > 1.0:
            inf_counter -= 1.0
            v[0].infect(e.time, location_type=self.type)

    # Used everywhere else
    else:
      for v in self.visits:
        if v[0].status == "susceptible":
          infection_probability = v[1] * base_rate
          #if ultraverbose:
          #  if infection_probability > 0.0:
          #    print("{} = {} * ({}/360.0) * ({}/{}) * ({}/{})".format(infection_probability, e.contact_rate_multiplier[self.type], e.disease.infection_rate, v[1], minutes_opened, self.inf_visit_minutes, self.sqm))
          if get_rnd() < infection_probability:
            v[0].infect(e.time, location_type=self.type)

def check_vac_eligibility(a):
  if a.status == "susceptible" and a.symptoms_suppressed==False and a.antivax==False:
    return True
  return False


class Ecosystem:
  def __init__(self, duration, needsfile="needs.csv", mode="parallel"):
    self.locations = {}
    self.houses = []
    self.house_names = []
    self.time = 0
    self.date = None
    self.num_hospitalised = 0 # currently in hospital (ICU)
    self.disease = None
    self.closures = {}
    self.validation = np.zeros(duration+1)
    self.contact_rate_multiplier = {}
    self.initialise_social_distance() # default: no social distancing.
    self.self_isolation_multiplier = 1.0
    self.track_trace_multiplier = 1.0
    self.ci_multiplier = 0.625 # default multiplier for case isolation mode 
    self.num_agents = 0
    # value is 75% reduction in social contacts for 50% of the cases (known lower compliance).
    # 0.25*50% + 1.0*50% =0.625
    # source: https://www.gov.uk/government/publications/spi-b-key-behavioural-issues-relevant-to-test-trace-track-and-isolate-summary-6-may-2020
    # old default value is derived from Imp Report 9.
    # 75% reduction in social contacts for 70 percent of the cases.
    # (0.25*0.7)+0.3=0.475
    self.work_from_home = False
    self.ages = np.ones(91) # by default equal probability of all ages 0 to 90.
    self.hospital_protection_factor = 0.5 # 0 is perfect, 1 is no protection.
    self.vaccinations_available = 0 # vaccinations available per day
    self.vaccinations_today = 0
    self.vac_no_symptoms = 1.0 # Default: 100% of people receiving vaccine have no more symptons.
    self.vac_no_transmission = 1.0 # Default: 100% of people receiving vaccine transmit the disease as normal.
    self.vaccinations_age_limit = 70 # Age limit for priority group. Can be changed at runtime.
    self.vaccinations_legal_age_limit = 16 # Minimum age to be allowed vaccines.
    self.traffic_multiplier = 1.0
    self.status = {"susceptible":0,"exposed":0,"infectious":0,"recovered":0,"dead":0,"immune":0}
    self.enforce_masks_on_transport = False
    self.loc_groups = {}
    self.needsfile = needsfile 

    # Settings
    self.immunity_duration = -1 # value > 0 indicates non-permanent immunity.
    self.vac_duration = -1  # value > 0 indicates non-permanent vaccine efficacy.

    #Make header for infections file
    out_inf = open("covid_out_infections.csv",'w')
    print("#time,x,y,location_type", file=out_inf)


    # if mode == "parallel":
    #   from mpi4py import MPI

    #   self.comm = MPI.COMM_WORLD
    #   self.rank = self.comm.Get_rank()
    #   self.size = self.comm.Get_size()
    #   print('Hello from process {} out of {}'.format(self.rank, self.size))


  def init_loc_inf_minutes(self):
    #print('Hello from process {} out of {}'.format(self.rank, self.size))
    number_of_non_house_locations = 0
    offset = 0
    self.loc_offsets = {}
    for lt in self.locations:
      if lt != "house":
        for i in range(0, len(self.locations[lt])):
          self.locations[lt][i].loc_inf_minutes_id = offset + i

        print(lt, len(self.locations[lt]))
        number_of_non_house_locations += len(self.locations[lt])
        self.loc_offsets[lt] = offset
        offset += len(self.locations[lt])
    self.loc_inf_minutes = np.zeros(number_of_non_house_locations)
    print("# of non-house locations: ", number_of_non_house_locations)


  def get_date_string(self):
    """
    Return the simulation date as a short string.
    """
    return self.date.strftime('%-d/%-m/%Y')


  def make_group(self, loc_type, max_groups):
    """
    Creates a grouping for a location, and assigns agents randomly to groups.
    Agents need to have been read in *before* running this function.
    """
    print("make group:", self.locations.keys(), loc_type)
    num_locs = len(self.locations[loc_type])
    self.loc_groups[loc_type] = {}
    # Assign groups to specific locations of that type in round robin fashion.
    for i in range(0, max_groups):
      self.loc_groups[loc_type][i] = self.locations[loc_type][i % num_locs]

    # randomly assign agents to groups
    for k,e in enumerate(self.houses):
      for hh in e.households:
        for a in hh.agents:
          a.assign_group(loc_type, max_groups)


  def get_location_by_group(self, loc_type_id, group_num):
    loc_type = lnames[loc_type_id]
    return self.loc_groups[loc_type][group_num]


  def print_contact_rate(self, measure):
    print("Enacted measure:", measure)
    print("contact rate multipliers set to:")
    print(self.contact_rate_multiplier)

  def print_isolation_rate(self, measure):
    print("Enacted measure:", measure)
    print("isolation rate multipliers set to:")
    print(self.self_isolation_multiplier)

  def evolve_public_transport(self):
    num_agents = 0

    base_rate = self.traffic_multiplier * self.disease.infection_rate * (20 / 900)
    if self.enforce_masks_on_transport:
      base_rate *= 0.44 # 56% reduction when masks are widely used: https://www.medrxiv.org/content/10.1101/2020.04.17.20069567v4.full.pdf

    for k,e in enumerate(self.houses):
      num_agents += e.num_agents

    for k,e in enumerate(self.houses):
      for hh in e.households:
        for a in hh.agents:
          infection_probability = base_rate * ((self.status["infectious"] * 20 * self.self_isolation_multiplier) / num_agents * 1)
          # assume average of 40-50 minutes travel per day per travelling person (5 million people travel, so I reduced it to 20 minutes per person), transport open of 900 minutes/day (15h), self_isolation further reduces use of transport, and each agent has 1 m^2 of space in public transport.
          # traffic multiplier = relative reduction in travel minutes^2 / relative reduction service minutes
          # 1. if half the people use a service that has halved intervals, then the number of infection halves.
          # 2. if half the people use a service that has normal intervals, then the number of infections reduces by 75%.
          # infection_probability = e.contact_rate_multiplier[self.type] * (e.disease.infection_rate/360.0) * (v[1] / minutes_opened) * (self.inf_visit_minutes / self.sqm)
          if get_rnd() < infection_probability:
            a.infect(self.time, location_type="traffic")


  def load_nearest_from_file(self, fname):
      """
      Load nearest locations from CSV file.
      """
      try:
          f = open(fname, "r")
          near_reader = csv.reader(f)
          i = 0

          header_row = next(near_reader)
          #print(header_row)
          #print(lnames)
          #sys.exit()

          for row in near_reader:
              #print(row)
              self.houses[i].nearest_locations = row
              n = []
              for j in range(0,len(header_row)):
                  try:
                    n.append(self.locations[header_row[j]][int(row[j])])
                  except:
                    print("ERROR: nearest building lookup from file failed:")
                    print("row in CSV: ", i)
                    print("lnames index: ",j," len:", len(header_row))
                    print("self.locations [key][]: ", header_row[j], " [][index]", int(row[j]))
                    print("self.locations [keys][]", self.locations.keys(), " [][len]", len(self.locations[header_row[j]]))
                    sys.exit()
              self.houses[i].nearest_locations = n
              #print(self.houses[i].nearest_locations)
              i += 1
      except IOError:
          return False


  def update_nearest_locations(self, dump_and_exit=False):
    f = None
    read_from_file = False
    if dump_and_exit == True:
      f = open('nearest_locations.csv', "w")
    else:
      loaded = self.load_nearest_from_file('nearest_locations.csv')
      if loaded == True:
        return
      
    if dump_and_exit == True:
      # print header row
      print(",".join(f"{x}" for x in lnames), file=f)

    count = 0
    for h in self.houses:
      ni = h.find_nearest_locations(self)
      if dump_and_exit == True:
        print(",".join(f"{x}" for x in ni), file=f)
      count += 1
      if count % 1000 == 0:
        print(count, "houses scanned.", file=sys.stderr)
    print(count, "houses scanned.", file=sys.stderr)

    if dump_and_exit == True:
      sys.exit()

  def add_infections(self, num, day, severity="exposed"):
    """
    Randomly add an infection.
    """
    for i in range(0, num):
      house = get_rndint(len(self.houses))
      self.houses[house].add_infection(day, severity)
    print("add_infections:",num,day)

  def add_infection(self, x, y, age, day):
    """
    Add an infection to the nearest person of that age.
    """
    if age>90: # to match demographic data
      age=90

    selected_house = None
    min_dist = 99999
    print("add_infection:",x,y,age,len(self.houses),day)
    for h in self.houses:
      dist_h = calc_dist(h.x, h.y, x, y)
      if dist_h < min_dist:
        if h.has_age(age):
          selected_house = h
          min_dist = dist_h

    # Make sure that cases that are likely recovered 
    # already are not included.
    #if day < -self.disease.recovery_period:
    #  day = -int(self.disease.recovery_period)
      
    selected_house.add_infection_by_age(day, age)


  def evolve(self, reduce_stochasticity=False):
    global num_infections_today
    global num_hospitalisations_today
    num_infections_today = 0
    num_hospitalisations_today = 0 
    self.vaccinations_today = 0

    # remove visits from the previous day
    for lk in self.locations.keys():
      for l in self.locations[lk]:
        l.clear_visits()



    # collect visits for the current day
    for h in self.houses:
      for hh in h.households:
        for a in hh.agents:
          a.plan_visits(self, reduce_stochasticity)
          a.progress_condition(self, self.time, self.disease)

          if a.age > self.vaccinations_age_limit and self.vaccinations_available - self.vaccinations_today > 0:
            if check_vac_eligibility(a) == True:
              a.vaccinate(self.time, self.vac_no_symptoms, self.vac_no_transmission, self.vac_duration)
              self.vaccinations_today += 1


    if self.vaccinations_available - self.vaccinations_today > 0:
      for h in self.houses:
        for hh in h.households:
          for a in hh.agents:
            #print("VAC:",self.vaccinations_available, self.vaccinations_today, self.vac_no_symptoms, self.vac_no_transmission, file=sys.stderr)
            if self.vaccinations_available - self.vaccinations_today > 0:
              if a.age > self.vaccinations_legal_age_limit and check_vac_eligibility(a) == True:
                a.vaccinate(self.time, self.vac_no_symptoms, self.vac_no_transmission, self.vac_duration)
                self.vaccinations_today += 1

    self.evolve_public_transport()

    # process visits for the current day (spread infection).
    for lk in self.locations:
      if lk in self.closures:
        if self.closures[lk] < self.time:
          continue
      for l in self.locations[lk]:
        l.evolve(self, reduce_stochasticity)

    # process intra-household infection spread.
    for h in self.houses:
      h.evolve(self, self.time, self.disease)
    
    self.time += 1
    self.date = self.date + timedelta(days=1)

  def addHouse(self, name, x, y, num_households=1):
    h = House(self, x, y, num_households)
    self.houses.append(h)
    self.house_names.append(name)
    return h

  def addLocation(self, name, loc_type, x, y, sqm=400):
    l = Location(name, loc_type, x, y, sqm)
    if loc_type in self.locations.keys():
      self.locations[loc_type].append(l)
    else:
      self.locations[loc_type] = [l]
    return l

  def add_closure(self, loc_type, time):
    self.closures[loc_type] = time

  def remove_closure(self, loc_type):
    del self.closures[loc_type]

  def remove_closures(self):
    self.closures = {}

  def add_partial_closure(self, loc_type, fraction=0.8, exclude_people=False):
    if loc_type == "school" and exclude_people:
      for k,e in enumerate(self.houses):
        for hh in e.households:
          for a in hh.agents:
            if get_rnd() < fraction:
              a.school_from_home = True
    elif loc_type == "office" and exclude_people:
      for k,e in enumerate(self.houses):
        for hh in e.households:
          for a in hh.agents:
            if get_rnd() < fraction:
              a.work_from_home = True
    else:
      needs.needs[lids[loc_type],:] *= (1.0 - fraction)

  def undo_partial_closure(self, loc_type, fraction=0.8):
    if loc_type == "school":
      for k,e in enumerate(self.houses):
        for hh in e.households:
          for a in hh.agents:
            a.school_from_home = False
    elif loc_type == "office":
      for k,e in enumerate(self.houses):
        for hh in e.households:
          for a in hh.agents:
            a.work_from_home = False
    else:
      needs.needs[lids[loc_type],:] /= (1.0 - fraction)

  def initialise_social_distance(self, contact_ratio=1.0): 
    for l in lids:
      self.contact_rate_multiplier[l] = contact_ratio
    self.contact_rate_multiplier["house"] = 1.0
    self.print_contact_rate("Reset to no measures")

  def reset_case_isolation(self):
    self.self_isolation_multiplier=1.0
    self.print_isolation_rate("Removing CI, now multiplier is {}".format(self.self_isolation_multiplier))

  def remove_social_distance(self):
    self.initialise_social_distance()
    if self.work_from_home:
      self.add_work_from_home(self.work_from_home_compliance)
    self.print_contact_rate("Removal of SD")

  def remove_all_measures(self):
    global needs
    self.initialise_social_distance()
    self.remove_closures()
    needs = Needs(self.needsfile)
    for k,e in enumerate(self.houses):
      for hh in e.households:
        for a in hh.agents:
          a.school_from_home = False
          a.work_from_home = False

  def add_social_distance_imp9(self): # Add social distancing as defined in Imperial Report 0.
    # The default values are chosen to give a 75% reduction in social interactions,
    # as assumed by Ferguson et al., Imperial Summary Report 9, 2020.
    self.contact_rate_multiplier["hospital"] *= 0.25
    self.contact_rate_multiplier["leisure"] *= 0.25
    self.contact_rate_multiplier["shopping"] *= 0.25
    self.contact_rate_multiplier["park"] *= 0.25
    self.contact_rate_multiplier["supermarket"] *= 0.25
   
    # Values are different for three location types.
    # Setting values as described in Table 2, Imp Report 9. ("SD")
    self.contact_rate_multiplier["office"] *= 0.75
    self.contact_rate_multiplier["school"] *= 1.0
    self.contact_rate_multiplier["house"] *= 1.25
    self.print_contact_rate("SD (Imperial Report 9)")

  def add_work_from_home(self, compliance=0.75):
    self.add_partial_closure("office", compliance, exclude_people=True)
    self.print_contact_rate("Work from home with {} compliance".format(compliance))

  def add_social_distance(self, distance=2, compliance=0.8571, mask_uptake=0.0, mask_uptake_shopping=0.0):

    distance += mask_uptake*1.0 #if everyone wears a mask, we add 1.0 meter to the distancing, 
    tight_distance = 1.0 + mask_uptake_shopping*1.0
    # representing a ~75% reduction for a base distance of 1 m, and a ~55% reduction for a base distance of 2 m.
    # Source: https://www.medrxiv.org/content/10.1101/2020.04.17.20069567v4.full.pdf

    dist_factor = (0.5 / distance)**2
    dist_factor_tight = (0.5 / tight_distance)**2 # assuming people stay 1 meter apart in tight areas
    # 0.5 is seen as a rough border between intimate and interpersonal contact, 
    # based on proxemics (Edward T Hall).
    # The -2 exponent is based on the observation that particles move linearly in
    # one dimension, and diffuse in the two other dimensions.
    # gravitational effects are ignored, as particles on surfaces could still
    # lead to future contamination through surface contact.

    # dist_factor_tight excludes mask wearing, as this is incorporated explicitly for supermarkets and shopping.

    for k,e in enumerate(self.contact_rate_multiplier):
      if e in ["supermarket","shopping"]: # 2M not practical, so we use 1M+.
        m = dist_factor_tight * compliance + (1.0-compliance)
      if e in "house": # Intra-household interactions are boosted when there is SD outside (Imp Report 9)
        m = 1.25
      else: # Default is 2M social distancing.
        m = dist_factor * compliance + (1.0-compliance)
      
      self.contact_rate_multiplier[e] *= m

    self.print_contact_rate("SD (covid_flee method) with distance {} and compliance {}".format(distance, compliance))

  def add_case_isolation(self):
    self.self_isolation_multiplier=self.ci_multiplier * self.track_trace_multiplier
    self.print_isolation_rate("CI with multiplier {}".format(self.self_isolation_multiplier))


  def reset_household_isolation(self):
    needs.household_isolation_multiplier=1.0
    self.print_isolation_rate("Household isolation with multiplier {}".format(self.self_isolation_multiplier))


  def add_household_isolation(self, multiplier=0.625):
    # compulsory household isolation
    # assumption: 50% of household members complying
    # 25%*50% + 100%*50% = 0.625
    # source: https://www.gov.uk/government/publications/spi-b-key-behavioural-issues-relevant-to-test-trace-track-and-isolate-summary-6-may-2020
    # old assumption: a reduction in contacts by 75%, and 
    # 80% of household complying. (Imp Report 9)
    # 25%*80% + 100%*20% = 40% = 0.4
    needs.household_isolation_multiplier=multiplier
    self.print_isolation_rate("Household isolation with {} multiplier".format(multiplier))


  def add_cum_column(elf, csv_file, cum_columns):
    df = pd.read_csv(csv_file, index_col=None, header=0)

    for column in cum_columns:
      df['cum %s' % (column)] = df[column].cumsum()

    df.to_csv(csv_file)


  def find_hospital(self):
    n = []
    hospitals = []
    sqms= []
    total_sqms = 0
    if "hospital" not in self.locations.keys():
      print("Error: couldn't find hospitals with more than 4000 sqm.")
      sys.exit()
    else:
      for k,element in enumerate(self.locations["hospital"]): # using 'element' to avoid clash with Ecosystem e.
        if element.sqm > 4000:
          sqms += [element.sqm]
          hospitals += [self.locations["hospital"][k]]
      if len(hospitals) == 0:
        print("Error: couldn't find hospitals with more than 4000 sqm.")
        sys.exit()
    sqms = [float(i)/sum(sqms) for i in sqms]
    return np.random.choice(hospitals, p=sqms) 


  def print_needs(self):
    for k,e in enumerate(self.houses):
      for hh in e.households:
        for a in hh.agents:
          print(k, a.get_needs())

  def print_header(self, outfile):
    out = out_files.open(outfile)
    print("#time,susceptible,exposed,infectious,recovered,dead,immune,num infections today,num hospitalisations today,num hospitalisations today (data),hospital bed occupancy",file=out, flush=True)

  def print_status(self, outfile, silent=False):    
    status = {"susceptible":0,"exposed":0,"infectious":0,"recovered":0,"dead":0,"immune":0}
    for k,e in enumerate(self.houses):
      for hh in e.households:
        for a in hh.agents:
          status[a.status] += 1
    if not silent:
      out = out_files.open(outfile)
      print("{},{},{},{},{},{},{},{},{},{},{}".format(self.time,status["susceptible"],status["exposed"],status["infectious"],status["recovered"],status["dead"],status["immune"],num_infections_today,num_hospitalisations_today,self.validation[self.time],self.num_hospitalised), file=out, flush=True)
    self.status = status


  def add_validation_point(self, time):
    self.validation[max(time,0)] += 1


  def print_validation(self):
    print(self.validation)
    sys.exit()

if __name__ == "__main__":
  print("No testing functionality here yet.")
