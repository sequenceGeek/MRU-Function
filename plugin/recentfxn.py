#!/usr/bin/env python

from __future__ import print_function
import os
import collections
import logging

from mruutility import groupby
from expandmenu import ExpandMenu
from tags import TagFile, Tag
from pythontag import py_get_nearest_tag

# get directory of this file @i @python
PLUGIN_HOME = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = PLUGIN_HOME + "/../data/locations.log"
WINDOW_TEXT = PLUGIN_HOME + "/../tmp/windowtext.txt"
MENU_STATE = PLUGIN_HOME + "/../tmp/menu_state.txt"

def log_tag_info(srcFile, lineNum, colNum, fileExtension, logFile):
    ''' Log nearest tag when vim sends log signal '''
    #get the nearest tag, will return None if no tag match
    cBufferFN = PLUGIN_HOME + "/../tmp/cBuffers/cBuffer." + fileExtension
    logging.info("cbuffer file: " + cBufferFN)
    
    logging.info("getting nearest tag... " + cBufferFN)
    nTag = get_nearby_tag(cBufferFN, lineNum, colNum, fileExtension)
 
    if nTag:
        logging.info("FOUND TAG: %s", nTag.name)

        #change the file name to not point to the temp file
        nTag.srcName = srcFile
        with open(logFile, 'a') as f:
            f.write(nTag.to_json() + "\n")
    else:
        logging.warning("NO TAGS")

def get_nearby_tag(srcFile, lineNum, colNum, fileExtension, tagTypes = "fm"):
    ''' f = function, m = method '''
    lineNum, colNum = int(lineNum), int(colNum)
    tFile = TagFile(srcFile)
    lineNum_tag = groupby(tFile.tags, "lineNumber")

    # custom nearest tag functions
    logging.info("src, fe, line: %s, %s, %d", srcFile, fileExtension, lineNum)
    if fileExtension == "py":
        logging.info("PYTHON tag... ")
        (nTag, tagLineNum) = py_nearest_tag(srcFile, lineNum, colNum,  lineNum_tag, tagTypes)
    else:
        logging.info("GENERAL tag... ")
        (nTag, tagLineNum) = general_nearest_tag(lineNum, lineNum_tag, tagTypes)

    if nTag:
        nTag.cursorOffsetLine = lineNum - tagLineNum
        nTag.cursorColumnNumber = colNum
        return nTag
    else:
        return None

def py_nearest_tag(srcFile, lineNum, colNum, lineNum_tag, tagTypes):

    '''check 1-based line'''
    with open(srcFile, 'r') as f:
        fileText = f.read()

    pyNearest = py_get_nearest_tag(fileText, lineNum, colNum) 
    if pyNearest:
        logging.info("pyNearest: %d %s", pyNearest[0], pyNearest[1])
        tLineNum, tName = pyNearest
        if tLineNum in lineNum_tag:
            nTag = lineNum_tag[tLineNum][0]
            if nTag.type in tagTypes:
                logging.info("FOUND TAG [%s %d]", nTag.name, tLineNum)
                return (nTag, tLineNum)

    # no tags found
    logging.info("NO TAG FOUND")
    return (None, None)

def general_nearest_tag(lineNum, lineNum_tag, tagTypes):
    
    for i in xrange(lineNum, 0, -1):
        if i in lineNum_tag:
            nearTag = lineNum_tag[i][0]
            if nearTag.type in tagTypes:
                return (nearTag, i)

    # no tags
    return (None, None)

def update_log(logFN, cBufferFN):
    '''remove non-existing tags (file changed/deleted or refactored)
    and remove duplicate functions'''
    
    # re-factor log to class @wtodo @frequent-function
    tags = get_unique_tags(load_tags_from_log(logFN))

    # does the file even exist anymore?
    tags = [tag for tag in tags if os.path.exists(tag.srcName)]

    # debug level @programming @wtodo

    # does the function exist anymore, has it been refactored?
    tags = [tag for tag in tags if tag.check_existence(cBufferFN)] 

    with open(logFN, 'w') as f:
        [f.write(tag.to_json() + "\n") for tag in tags]

def get_unique_tags(tags):
    '''tags are returned in order given
    [a,b,c] -> [a,b] (if c was not unique)'''

    uniqueProps = set()
    uniqueTags = []
    while True:
        if not tags:
            break

        currTag = tags.pop()
        tagUniqueProps = (currTag.name, currTag.srcName, currTag.prototype)
        if tagUniqueProps not in uniqueProps:
            uniqueTags.append(currTag)
            uniqueProps.add(tagUniqueProps)

    # popping and appending reversed the list order
    uniqueTags.reverse()

    return uniqueTags

def load_tags_from_log(logFN):

    tags = []
    with open(logFN, 'r') as f:
        for jsonline in f:
            tags.append(Tag(jsonLine = jsonline))

    return tags

def generate_mru_browser_text(cBufferName, browserMode):

    # remove dups and non-existing first
    update_log(LOG_FILE, cBufferName)

    if browserMode == "fxn":
        menu_functions_only()
    elif browserMode == "byfile":
        menu_by_file()
    else:
        raise ValueError("Need Menu Mode")

def menu_by_file():
    '''create an expandable menu
    save text in windowtext file
    save state'''

    menuLines = create_by_file_expand_lines()
    eMenu = ExpandMenu(menuLines = menuLines)
    eMenu.output_menu(WINDOW_TEXT)
    eMenu.save_to_file(MENU_STATE)

def menu_functions_only():
    
    # get resulting tags and display in reverse order (log has newest at end)
    logTags = load_tags_from_log(LOG_FILE)
    logTags.reverse()
    
    with open(WINDOW_TEXT, 'w') as f:
        for tag in logTags:
            f.write(tag.function_choice_output() + "\n")

def create_by_file_expand_lines():
    '''should give this an ordered dict and have it make it'''
    
    # get resulting tags and display in reverse order (log has newest at end)
    logTags = load_tags_from_log(LOG_FILE)
    logTags.reverse()

    # group by the file names, order by mru file
    srcName_tags = collections.OrderedDict()
    for tag in logTags:
        srcName_tags.setdefault(tag.srcName, []).append(tag)

    return srcName_tags

def handle_expand_choice(choice):

    eMenu = ExpandMenu()
    eMenu.load_from_file(MENU_STATE)
    eMenu.handle_expansion_change(choice)
    eMenu.output_menu(WINDOW_TEXT)
    eMenu.save_to_file(MENU_STATE)

if __name__ == "__main__":
    import sys

    # Set up logging
    logging.basicConfig(filename=PLUGIN_HOME + '/../debug.txt', level=logging.INFO)

    # Handle events
    event = sys.argv[1]
    logging.info("***     MAIN     ***")
    logging.info("***     %s     ***", event)
    logging.info("args: %s", sys.argv[1:])
    if event == "log":
        log_tag_info(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], LOG_FILE)
    elif event == "menu":
        cBuffer, mode = sys.argv[2:]
        generate_mru_browser_text(cBuffer, mode)
    elif event == "expand":
        expand_choice = sys.argv[2]
        handle_expand_choice(expand_choice)
    else:
        raise KeyError("Must Specify Event")     
