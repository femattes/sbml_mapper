
#import sys
import os.path
import sqlite3
import libsbml
#from libsbml import *
import re
import validateSBML

def writeSBMLToDBModel(database_path, sbml_input_path, modelRow=1):

    # read SBML file
    if not os.path.exists(sbml_input_path):
        print("[Error] {0} : no such file.".format(sbml_input_path))
        return 1
    #fileValidator = validateSBML(True)
    #fileValidator.validate(sbml_input_path)
    document = libsbml.readSBML(sbml_input_path)
    if document.getNumErrors() > 0:
        print("[Error] {0} : SBML file invalid or inconsistant, aborting model import.\n Error Log from libSBML:\n{1}".format(sbml_input_path, document.getErrorLog().toString()))
        return 1
    model = document.getModel()



    print("SBML file read in successfully!\n")

    # database connection
    try:
        conn = sqlite3.connect(database_path)
        c = conn.cursor()
    except sqlite3.OperationalError:
        print("Could not create or open database at " + database_path + "\n")
        return 1

    print("Database connection established!\n")







writeSBMLToDBModel("inputdb.sqlite", "db2sbmp_output.xml")



