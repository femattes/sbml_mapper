
#import sys
import os.path
import sqlite3
import libsbml
#from libsbml import *
import re
import validateSBML

def writeSBMLToDBModel(database_path, sbml_input_path, modelRow=1):

    # read file
    if not os.path.exists(sbml_input_path):
        print("[Error] {0} : no such file.\n".format(sbml_input_path))
        return 1
    # try to parse SBML document
    try:
        document = libsbml.readSBML(sbml_input_path)
    except:
        print("[Error] {0} : File not readable by method libsbml.readSBML(), aborting model import.\n".format(sbml_input_path))
        return 1
    # check SBML level
    if not (document.getLevel() == 3 and document.getVersion() == 1):
        print("[Warning] {0} : SBML file has level {0}.{1}. This tool was written for SBML Level 3.1.\n".format(document.getLevel(), document.getVersion()))
    # check if qualitative model
    if not document.getPkgRequired("qual"):
        print("[Warning] {0} : \"qual\"-package is not set as required for this SBML file.\n".format(sbml_input_path))
    # check model consistency (document.checkConsistency() is called automatically by libsbml.readSBML)
    if document.getNumErrors() > 0:
        print("[Error] {0} : SBML file invalid or inconsistant, aborting model import.\n Error Log from libSBML:\n{1}".format(sbml_input_path, document.getErrorLog().toString()))
        return 1

    # create a model object
    model = document.getModel()
    # get a QualModelPlugin object plugged into the model object (enables qualSBML interface).
    mplugin = model.getPlugin("qual")

    print("SBML file read successfully!\n")

    # database connection
    try:
        if os.path.isfile(database_path):
            os.remove(database_path)
        conn = sqlite3.connect(database_path)
        c = conn.cursor()
    except sqlite3.OperationalError:
        print("Could not create database at " + database_path + "\n")
        return 1

    print("Database connection established!\n")

    # Table Components
    c.execute('CREATE TABLE Components (Name TEXT, MaxActivity INTEGER)')
    qs_list = mplugin.getListOfQualitativeSpecies()
    MA_set = False
    for i in range(1, qs_list.size()):
        qs = qs_list.get(i)
        Name = qs.getId()
        if qs.isSetMaxLevel():
            MaxActivity = qs.getMaxLevel()
            MA_set = True
        else:
            MaxActivity = -1
        c.execute('INSERT INTO Components VALUES (?,?)', (Name, MaxActivity))
    if not MA_set:
        print("[Warning] {0} : Maximum activity level not set in SBML file for at least one species. Calculating maximum activity from model logic.\n".format(sbml_input_path))



    # Table Regulations
    c.execute('CREATE TABLE Regulations (Target TEXT, Source TEXT, Threshold INTEGER)')








writeSBMLToDBModel("inputdb.sqlite", "db2sbmp_output.xml")



