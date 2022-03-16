#!/usr/bin/env python

# setup DIRAC
from DIRAC.Core.Base import Script
Script.parseCommandLine(ignoreErrors = True)

from DIRAC.Interfaces.API.Dirac import Dirac
from DIRAC.Interfaces.API.Job import Job
import sys
dirac = Dirac()
jobid = sys.argv[1]
print(dirac.getJobStatus(jobid))
