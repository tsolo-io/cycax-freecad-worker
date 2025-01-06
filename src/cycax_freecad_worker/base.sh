if [ -z "${CYCAX_SERVER}" ]
then
  echo "CYCAX_SERVER has to be defined."
  echo "  Example: export CYCAX_SERVER=http://localhost:8765"
  exit 5
fi

if [ -n "${1}" ]
then
  FREECADAPP=${1}
else
  echo "No FreeCAD specified on the command line, search in ~/Applications."
  FREECADAPP=$(find ~/Applications -name "FreeCAD*.AppImage" | sort | tail -1)
fi

if [ ! -f "${FREECADAPP}" ]
then
  echo "Could not find FreeCAD AppImage."
  FREECADAPP=$(which freecad)
fi

if [ ! -f "${FREECADAPP}" ]
then
  echo "Could not find FreeCAD."
  exit 2
else
  echo "Using FreeCAD ${FREECADAPP}"
fi

TEMPFILE=$(mktemp -t cycax.XXXXXX.py)
cat $0 | sed -e '1,/^##CYCAX##PYTHON##CODE##$/d' | base64 -d | xz -d > ${TEMPFILE}

# Run FreeCAD
echo
echo "Starting FreeCAD and getting Tasks from ${CYCAX_SERVER}"
echo "  CyCAx FreeCAD worker version ${VERSION} (${TEMPFILE})"
${FREECADAPP} ${TEMPFILE}
exit $?
##CYCAX##PYTHON##CODE##
