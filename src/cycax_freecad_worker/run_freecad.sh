#!/bin/bash

# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

set -e

if [ -z "${CYCAX_SERVER}" ]
then
  echo "CYCAX_SERVER has to be defined."
  echo "\tExample: export CYCAX_SERVER=http://localhost:8765"
  exit 5
fi

if [ -n "${1}" ]
then
  FREECADAPP=${1}
else
  echo "No AppImage path specified on the command line, search in ~/Applications."
  FREECADAPP=$(find ~/Applications -name "FreeCAD*.AppImage" | sort | tail -1)
fi

if [ ! -f "${FREECADAPP}" ]
then
  echo "Could not find FreeCAD AppImage."
else
  echo "Using FreeCAD ${FREECADAPP}"
fi

# Run FreeCAD
echo
echo "To stop run the command: touch ${WORKING_DIR}/.quit"
echo
echo "Starting FreeCAD and looking for jobs in ${WORKING_DIR}"
export CYCAX_JOBS_DIR=${WORKING_DIR}
${FREECADAPP} ./cycax_client_freecad.py
