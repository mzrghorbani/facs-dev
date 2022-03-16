#!/usr/bin/env /cvmfs/dirac.egi.eu/dirac/v7r2p28/diracos/usr/bin/python

# Get DIRAC job output
import sys

# DIRAC does not work otherwise
from DIRAC.Core.Base import Script
Script.parseCommandLine(ignoreErrors = True)
# end of DIRAC setup

from DIRAC.Interfaces.API.Dirac import Dirac 
from DIRAC.Interfaces.API.Job import Job

dirac = Dirac() 
jobid = sys.argv[1] 
print(dirac.getOutputSandbox(jobid))
