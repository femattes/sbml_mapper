
#import sys
import os.path
import sqlite3
import libsbml
#from libsbml import *
import re
import validateSBML

class ParseASTError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


def getThresholds(math_AST, sources_dict):

    if math_AST.getType() in [libsbml.AST_LOGICAL_AND, libsbml.AST_LOGICAL_OR, libsbml.AST_LOGICAL_NOT, libsbml.AST_LOGICAL_XOR]:
        print("numchildren: {0}".format(math_AST.getNumChildren()))
        for i in range(0, math_AST.getNumChildren()):
            print("Logical {0}:".format(i))
            sources_dict = getThresholds(math_AST.getChild(i), sources_dict)

    elif math_AST.getType() in [libsbml.AST_RELATIONAL_EQ, libsbml.AST_RELATIONAL_GEQ, libsbml.AST_RELATIONAL_GT, libsbml.AST_RELATIONAL_LEQ, libsbml.AST_RELATIONAL_LT, libsbml.AST_RELATIONAL_NEQ]:
        left = math_AST.getLeftChild()
        right = math_AST.getRightChild()
        flipped = False

        if left.getType() == libsbml.AST_INTEGER and right.getType() == libsbml.AST_NAME:
            tmp = left
            left = right
            right = tmp
            flipped = True

        if left.getType() == libsbml.AST_NAME and right.getType() == libsbml.AST_INTEGER:
            source = left.getName()
            print("Source: ", source)
            int_value = right.getInteger()
            if math_AST.getType() == libsbml.AST_RELATIONAL_EQ or math_AST.getType() == libsbml.AST_RELATIONAL_NEQ:
                new_thresholds = [x for x in [int_value, int_value + 1] if x not in sources_dict[source]]
                sources_dict[source].extend(new_thresholds)
            elif (math_AST.getType() == libsbml.AST_RELATIONAL_GEQ and not flipped) or (math_AST.getType() == libsbml.AST_RELATIONAL_LEQ and flipped):
                if int_value not in sources_dict[source]:
                    sources_dict[source].append(int_value)
            elif (math_AST.getType() == libsbml.AST_RELATIONAL_LEQ and not flipped) or (math_AST.getType() == libsbml.AST_RELATIONAL_GEQ and flipped):
                if int_value + 1 not in sources_dict[source]:
                    sources_dict[source].append(int_value + 1)
            elif (math_AST.getType() == libsbml.AST_RELATIONAL_GT and not flipped) or (math_AST.getType() == libsbml.AST_RELATIONAL_LT and flipped):
                if int_value + 1 not in sources_dict[source]:
                    sources_dict[source].append(int_value + 1)
            elif (math_AST.getType() == libsbml.AST_RELATIONAL_LT and not flipped) or (math_AST.getType() == libsbml.AST_RELATIONAL_GT and flipped):
                if int_value not in sources_dict[source]:
                    sources_dict[source].append(int_value)

        else:
            print("AAAARGH!")
            raise ParseASTError("Unexpected mathML expression in FunctionTerm: Lowest level expressions must be species~integer comparisons.\nComponent species may only be compared to integer values, and only by the following relations: =, /=, >=, <=, >, < \n")

    else:
        print("AAAARGH!")
        raise ParseASTError("Unexpected mathML expression in FunctionTerm: Only logical and relational mathML operators are allowed.")

    print(sources_dict)
    return(sources_dict)

#end getThresholds




'''
Function writeSBMLToDBModel
Input parameters:
    1) database_path: url where the TREMPPI model database is to be created; existing files/databases at this url will be deleted
    2) sbml_input_path: url of the qualSBML input file
Output:
    0 for successfully parsed qualSBML file
    1 in case of errors
    If qualSBML file is successfully parsed, a model database is created at database_path
'''
def writeSBMLToDBModel(database_path, sbml_input_path):

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
    for qs in qs_list:
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
    c.execute('CREATE TABLE Regulations (Source TEXT, Target TEXT, Threshold INTEGER)')

    input_transition_effect_is_OK = True
    output_transition_effect_is_OK = True
    count = 0
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
            source_list.append(input.getQualitativeSpecies())
            if input.getTransitionEffect() != 0: # logical/multivalued models should have "none" == 0
                input_transition_effect_is_OK = False

        # dictionary for storage of thresholds for each source
        source_threshold_dict = {s:[] for s in source_list}
        print("\ndict {0}: {1}".format(count, source_threshold_dict))
        count = count+1

        # find thresholds of sources for the TREMPPI regulations which are encoded in this qualSBML transition (t)
        # get transition equalities/inequalities from function terms
        for f in t.getListOfFunctionTerms():
            # get the ASTNode tree of the SBML mathML definition of the function term
            # getMath() returns the top ASTNode of the tree
            math_AST = f.getMath()
            try:
                source_threshold_dict = getThresholds(math_AST, source_threshold_dict)
            except ParseASTError as e:
                print("[Error] {0} : Couldn't compute Thresholds for FunctionTerm of target {1}. \n{2}".format(sbml_input_path, target_list[0], e.value))
                return 1

        print("filling database, source_threshold_dict={0}, target_list={1}, source_list={2}".format(source_threshold_dict,target_list,source_list))
        for target in target_list:
            for source in source_list:
                #print(source_threshold_dict[source])
                for threshold in source_threshold_dict[source]:
                    #print("target: {0}, source: {1}, threshold: {2}".format(target, source, threshold))
                    c.execute('INSERT INTO Regulations VALUES (?,?,?)', (source, target, threshold))

    conn.commit()
    return(0)

#end writeSBMLToDBModel





writeSBMLToDBModel("inputdb.sqlite", "db2sbml_output.xml")



