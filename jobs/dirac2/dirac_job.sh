## The Ganga job.
j = Job()

# Name the job.
j.name = "facs-simulation-000"

# Tell Ganga it's running an executable: run.sh
j.application = Executable()
j.application.exe = File('run')

# run.sh takes one argument - the dataset directory.
#j.application.args = ['B06-W0212/2014-04-02-150255/']

# Specifiy which local files to upload with the job.
j.inputfiles = [ LocalFile('') ]

# Specify which files should be downloaded as output from the job.
j.outputfiles = [ LocalFile(''), LocalFile(''), LocalFile('') ]
j.submit()
