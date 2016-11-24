
#import sys
#import os.path
import sqlite3
import libsbml
#from libsbml import *
import re
import validateSBML

def writeSBMLToDBModel(database_path, sbml_input_path, modelRow=1):

    # read qualSBML file
    if not os.path.exists(sbml_input_path):
        print("[Error] %s : no such file." % (sbml_input_path))
        return 1
    fileValidator = validateSBML(True)
    fileValidator.validate(sbml_input_path)
    if fileValidator.numinvalid > 0:
        print("SBML file invalid or inconsistant, aborting model import.")
        return 1
    document = libsbml.readSBML(sbml_input_path)

    # database connection
    try:
        conn = sqlite3.connect(database_path)
        c = conn.cursor()
    except sqlite3.OperationalError:
        print("Could not create or open database at " + database_path + "\n")
        return 1




