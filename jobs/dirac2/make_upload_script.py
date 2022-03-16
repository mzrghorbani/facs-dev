#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os, glob

data_path = '/home/eepgmmg1/workspace/git/stamina/facs-dev/jobs/dirac'

lfn_dir = '/gridpp/user/m/maziar.ghorbani/mydata/facs/run_04032022'

se = 'UKI-LT2-QMUL2-disk'

s = "#!/bin/bash\n"

for my_file in sorted(glob.glob(data_path + "/*")):
    base_name  = os.path.basename(my_file)
    upload_lfn = os.path.join(lfn_dir, base_name)
    s += "dirac-dms-add-file %s %s %s\n" % (upload_lfn, my_file, se)

with open("upload_script.sh", "w") as sf:
    sf.write(s)
