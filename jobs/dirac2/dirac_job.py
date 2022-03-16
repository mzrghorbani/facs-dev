j = Job()
j.name = "facs_run_04032022"
j.application = Executable()
j.application.exe = File('run')
j.inputfiles = [ LocalFile('run'), LocalFile('age-distr.csv'), LocalFile('needs.csv'), LocalFile('offices.csv'), LocalFile('halton_buildings.csv'), LocalFile('facs.py'), LocalFile('measures.py'), LocalFile('disease.py'), LocalFile('read_building_cvs.py'), LocalFile('read_disease_yml.py'), LocalFile('read_cases_csv.py'), LocalFile('read_age_csv.py'), LocalFile('building_types_map.yml'), LocalFile('measures_halton.yml'), LocalFile('disease_covid19.yml') ]
j.outputfiles = [ LocalFile('covid_out_infections.csv'), LocalFile('covid_out_recoveries.csv'), LocalFile('covid_out_deaths.csv'), LocalFile('covid_out_hospitalisations.csv'), LocalFile('halton-extend-lockdown--1.csv')]
j.backend = Dirac()
j.submit()
