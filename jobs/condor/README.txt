# Instructions to sent jobs to condor

Prerequisite:

	- binutils


Retrive git repository by:

	git clone https://github.com/mzrghorbani/facs-dev.git

Directory structure:
.
├── facs
│ ├── __pycache__
│ ├── covid_data
│ ├── docs
│ ├── facs
│ │ ├── base
│ │ │ └── __pycache__
│ │ └── readers
│ │     └── __pycache__
│ ├── jobs
│ │ ├── build
│ │ │ └── run2
│ │ │     └── localpycos
│ │ └── dist
│ ├── result
│ └── tests
└── venv


Optional:

Recreate <jobs/> directory for condor-run:

1- Create <jobs/job.submit> file with template below:

	'''
	executable = dist/run
	arguments = $(option) 
	log = log_$(ClusterId).log
	output = out_$(ClusterId)_$(ProcId).out
	error = err_$(ClusterId)_$(ProcId).err
	queue option from job_list.txt
	'''

2- Create <jobs/job_list.txt> file with template below:

	'''
	arg1
	arg2
	arg3
	'''

Note: Before creating the python excecutable, make sure all paths in algorithm are relative to the <jobs/> directory.

3- Create excecutable in <jobs/> directory from python file <run.py>

	pyinstaller --onefile ../run.py

	Note: Excecutable creation may take long time!

4- locate created python excecutable in <jobs/dist> directory.

5- Replace <executable> in job.submit with generated excecutable.

6- Submit jobs by condor commands:

	condor_submit job.submit

7- Displays information about jobs queued jobs in HTCondor by:

	condor_q

8- Check log, stderr, stdout by visiting:

	log_$(ClusterId).log
	err_$(ClusterId)_$(ProcId).err
	out_$(ClusterId)_$(ProcId).out

9- Modify <jobs/job_list.txt> for new jobs.
