


import sys
import os.path
import sqlite3
from libsbml import *
import re

def writeDBModelsToSBML(database_path, sbml_output_path, parametrizationRow=1):

    # Create the connection to the SQLite model database
    conn = sqlite3.connect(database_path) # TO DO: exception for failed connection
    c = conn.cursor()

    # Create an SBMLNamespaces object with the given SBML level, version
    # package name, package version.
    sbmlns = SBMLNamespaces(3, 1, "qual", 1)
    # Creates an SBMLDocument object
    document = SBMLDocument(sbmlns)
    # mark qual as required
    document.setPackageRequired("qual", True)
    # create the Model
    model = document.createModel()

    # Get a QualModelPlugin object plugged in the model object.
    mplugin = model.getPlugin("qual")

    # Extract regulatory context descriptions from table Parametrizations
    column_name_list = [tuple[0] for tuple in c.execute("SELECT * FROM Parametrizations").description] # TO DO: exception for invalid/missing model

    context_name_list = [column_name for column_name in column_name_list if column_name[0:1] == 'K_'] # TO DO: index dependent = bad

    parameter_list = list(c.execute('SELECT ' + ', '.join(context_name_list) + ' FROM Parametrizations WHERE ID=' + str(parametrizationRow)).fetchall()) # TO DO: depends on single row/unique ID

    target_list = [target for target, in c.execute('SELECT DISTINCT Target FROM Regulations ORDER BY Target').fetchall()]
    context_list = []
    for context_name in context_name_list:
        target_match_list = [target for target in target_list if context_name[2:].find(target) != -1] # can find multiple e.g. context_name=RafB will match species Raf and RafB
        target = [match for match in target_match_list if len(match) == max(map(len, target_match_list))][0] # take longest match, TO DO: check if single match?
        thresholds_name = re.match(r'(?<=K_{0}_)\D+'.format(target), context_name).group(0) # TO DO: check if length >= 1 ?
        threshold_list = [int(d) for d in thresholds_name] # TO DO: what about double digit thresholds?
        context = [target, context_name].extend(threshold_list) # each context = list of format [Raf, K_Raf_031, 0, 3, 1]
        context_list.append(context)

    # write to qualSBML model

    for name, maxActivity in c.execute('SELECT Name, MaxActivity FROM Components ORDER BY Name').fetchall():
        # create a QualitativeSpecies
        qs = mplugin.createQualitativeSpecies()
        qs.setId(name)
        qs.setConstant(False)
        qs.setMaxLevel(maxActivity)
        #qs.setName(name)

    for target, in c.execute('SELECT DISTINCT Target FROM Regulations ORDER BY Target').fetchall():
        # create a transition
        t = mplugin.createTransition()
        # create transition output
        o = t.createOutput()
        o.setQualitativeSpecies(target)
        o.setTransitionEffect(1) # transitionEffect='assignmentLevel'

        source_list = []

        for source, in c.execute('SELECT DISTINCT Source FROM Regulations WHERE Target=' + target + ' ORDER BY Source').fetchall():
            # create transition input
            i = t.createInput()
            i.setQualitativeSpecies(source)
            i.setTransitionEffect(0) # transitionEffect='none'

            source_list.append(source)


        target_context_list = [context for context in context_list if context[0] == target]

        for context in target_context_list:
            f_sources = []
            source_state_list = context[2:]

            if sum(source_state_list) == 0:
                d = t.createDefaultTerm()
                param, = c.execute('SELECT ' + context[1] + ' FROM Parametrizations WHERE ID=' + str(parametrizationRow)).fetchall()
                d.setResultLevel()

            for source_index in range(0, len(source_state_list)-1):
                source = source_list[source_index]
                source_state = source_state_list[source_index]
                threshold_list, = c.execute('SELECT Threshold FROM Regulations WHERE Target=' + target + ' AND Source=' + source + ' ORDER BY Threshold').fetchall()
                f_thresholds = []
                for threshold in threshold_list:
                    if 0 <= source_state and source_state < threshold:
                       f_thresholds.append('')











