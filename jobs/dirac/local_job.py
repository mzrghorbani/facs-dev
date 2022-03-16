joblist = open("joblist.txt", "r")
lines = joblist.readlines()

for line in lines:
	j = Job()
	j.name = "%s" % (line.split()[0])
	j.application = Executable()
	j.application.exe = File('dist/run')
	j.applications.args = line.split() 
	#j.inputfiles = [ LocalFile('dist/run'), LocalFile('age-distr.csv'), LocalFile('needs.csv'), LocalFile('offices.csv'), LocalFile('greater_manchester_buildings.csv'), LocalFile('facs.py'), LocalFile('measures.py'), LocalFile('disease.py'), LocalFile('read_building_cvs.py'), LocalFile('read_disease_yml.py'), LocalFile('read_cases_csv.py'), LocalFile('read_age_csv.py'), LocalFile('building_types_map.yml'), LocalFile('measures_greater_manchester.yml'), LocalFile('disease_covid19.yml') ]
	#j.outputfiles = [ LocalFile('covid_out_infections.csv'), LocalFile('covid_out_recoveries.csv'), LocalFile('covid_out_deaths.csv'), LocalFile('covid_out_hospitalisations.csv'), LocalFile('greater_manchester-extend-lockdown--1.csv')]
	j.backend = Local()
	j.submit()


