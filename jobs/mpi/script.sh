#!/bin/bash

# Commands to enable modules, and then load an appropriate MP/MPI module
export PATH
. /etc/profile.d/modules.sh
module load mpi/mpich-x86_64

# Command to run your OpenMP/MPI program
# (This example uses mpirun, other programs
# may use mpiexec, or other commands)
mpirun -np 2 ./run $1 $2 $3 $4 $5 $6 $7 $8
