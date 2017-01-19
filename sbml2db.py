
#import sys
import os.path
import sqlite3
import libsbml
#from libsbml import *
import re
import validateSBML


def getThresholds(math_AST, sources_dict):

    if(math_AST.getType() == libsbml.AST_NAME):




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
    MA_is_set = True
    for i in range(1, qs_list.size()):
        qs = qs_list.get(i)
        Name = qs.getId()
        if qs.isSetMaxLevel():
            MaxActivity = qs.getMaxLevel()
        else:
            MaxActivity = -1
            MA_is_set = False
        c.execute('INSERT INTO Components VALUES (?,?)', (Name, MaxActivity))
    if not MA_is_set:
        print("[Warning] {0} : Maximum activity level not set in SBML file for at least one species. Calculating maximum activity from model logic.\n".format(sbml_input_path))

    # Table Regulations
    c.execute('CREATE TABLE Regulations (Target TEXT, Source TEXT, Threshold INTEGER)')

    input_transition_effect_is_OK = True
    output_transition_effect_is_OK = True
    for t in mplugin.getListOfTransitions():

        # sources and targets of this transition (2 lists of RefID strings == Qal. species names == component names)
        target_list = []
        source_list = []

        # get targets for table Regulations
        for output in t.getListOfOutputs():
            target_list.append(output.getQualitativeSpecies()) # returns RefID (Qual. species name)
            if output.getTransitionEffect() != 1: # logical/multivalued models should have "assignmentLevel" == 1
                output_transition_effect_is_OK = False

        # get sources for table Regulations
        for input in t.getListOfInputs():
            source_list.append(output.getQualitativeSpecies())
            if input.getTransitionEffect() != 0: # logical/multivalued models should have "none" == 0
                input_transition_effect_is_OK = False

        # dictionary for storage of thresholds for each source
        source_threshold_dict = {s:[] for s in source_list}

        # find thresholds of sources for the TREMPPI regulations which are encoded in this qualSBML transition (t)
        # get transition equalities/inequalities from function terms
        for f in t.getListOfFunctionTerms():
            # get the ASTNode tree of the SBML mathML definition of the function term
            # getMath() returns the top ASTNode of the tree
            mathTop_ASTNode = f.getMath()








writeSBMLToDBModel("inputdb.sqlite", "db2sbml_output.xml")



