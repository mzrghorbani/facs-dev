joblist = open("joblist.txt", "r")
lines = joblist.readlines()

for line in lines:
	j = Job()
	j.name = "%s" % (line.split()[0])
	j.application = Executable()
	j.application.exe = File('dist/run')
	j.application.args = line.split() 
	print(j.application.args)
	#j.inputfiles = [ LocalFile('../../covid_data/age-distr.csv'), LocalFile('../../covid_data/needs.csv'), LocalFile('../../offices.csv'), LocalFile('../../covid_data/greater_manchester_buildings.csv'), LocalFile('../../facs/base/facs.py'), LocalFile('../../facs/base/measures.py'), LocalFile('../../facs/base/disease.py'), LocalFile('../../covid_data/read_building_cvs.py'), LocalFile('../../facs/readers/read_disease_yml.py'), LocalFile('../../facs/readers/read_cases_csv.py'), LocalFile('../../facs/readers/read_age_csv.py'), LocalFile('../../covid_data/building_types_map.yml'), LocalFile('../../measures_regions/measures_greater_manchester.yml'), LocalFile('../../covid_data/disease_covid19.yml') ]
	#j.outputfiles = [ LocalFile('covid_out_infections.csv'), LocalFile('covid_out_recoveries.csv'), LocalFile('covid_out_deaths.csv'), LocalFile('covid_out_hospitalisations.csv'), LocalFile('greater_manchester-extend-lockdown--1.csv')]
	j.backend = Local()
	j.submit()


