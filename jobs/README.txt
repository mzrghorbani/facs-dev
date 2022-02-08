# Instructions to sent jobs to condor

.
├── run.py
├── data
├── jobs
├── result
└── venv

Create <jobs/> directory for condor run
Create <jobs/job.submit> file

'''
executable = dist/run
arguments = $(option) 
log = log_$(ClusterId).log
output = out_$(ClusterId)_$(ProcId).out
error = err_$(ClusterId)_$(ProcId).err
queue option from job_list.txt
'''

Create <jobs/job_list.txt> file

'''
arg1
arg2
arg3
'''

Before creating the excecutable, make sure all paths in algorithm are relative to <jobs/> directory.

Create excecutable in <jobs/> directory from python file

	pyinstaller --onefile ../run.py

	Note: Excecutable creation may take a long time!

locate the excecutable in <jobs/dist> directory.

Submit jobs by:

	condor_submit job.submit

Check the jobs by:

	condor_q
