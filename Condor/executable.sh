#!/bin/bash

# input file
FILE=$1
DIR="/eos/experiment/fcc/ee/generation//stdhep//winter2023/wzp6_ee_HZZ_llnunu_ecm125/"
INPUT="${DIR}/${FILE}"

ILDCONFIG_DIR="/afs/cern.ch/user/m/mbabioel/tutorial_lcws/ILDConfig/StandardConfig/production"

# source
source /cvmfs/sw.hsf.org/key4hep/setup.sh
k4_local_repo
export ILDCONFIG_DIR=/afs/cern.ch/user/m/mbabioel/tutorial_lcws/ILDConfig/StandardConfig/production
export RESOURCE_DIR=/afs/cern.ch/user/m/mbabioel/tutorial_lcws/resources
source /afs/cern.ch/user/m/mbabioel/tutorial_lcws/setup_env.sh
export OUTPUT=/eos/user/m/mbabioel/outputs_reco
export LD_PRELOAD=/afs/cern.ch/user/m/mbabioel/LCIO/install/lib64/liblcio.so
export LD_LIBRARY_PATH=/afs/cern.ch/user/m/mbabioel/LCIO/install/lib64:$LD_LIBRARY_PATH


cp -r /afs/cern.ch/user/m/mbabioel/tutorial_lcws/ILDConfig/StandardConfig/production .

cd production

# prepare input
cp $INPUT $FILE
gunzip $FILE
UNZIP_FILE="${FILE%.gz}"
OUTPUT_FILE="${FILE%.stdhep.gz}"

# run simulation
ddsim --inputFiles $UNZIP_FILE --outputFile ${OUTPUT_FILE}_sim.root --compactFile $k4geo_DIR/ILD/compact/ILD_l5_v02/ILD_l5_v02.xml --steeringFile ddsim_steer.py -N 10000

# run reco
k4run ILDReconstruction.py --inputFiles=${OUTPUT_FILE}_sim.root --compactFile $k4geo_DIR/ILD/compact/ILD_l5_v02/ILD_l5_o1_v02.xml --outputFileBase=${OUTPUT_FILE} --num-events=-1



# copy output
cp ./${OUTPUT_FILE}_REC.edm4hep.root /eos/user/m/mbabioel/outputs_reco/

