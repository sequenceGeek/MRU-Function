import os
import json

class ExpandMenu(object):

    def __init__(self, menuLines = None, options = None):
        self.menuLines = menuLines
        self.expanded = []
        self.menuText = ""

        if self.menuLines:
            self.create_menu_text(self.menuLines)

    def create_menu_text(self, menuLines):
        '''1D Menu Only
        menuLines is an ORDERED DICT'''

        prefixSep = "  "
        self.menuText = ""
        for i, fName in enumerate(menuLines):
            self.menuText += "+[" + str(i + 1) + "] " + os.path.basename(fName) + "\n"
            self.menuText +=  prefixSep + "...go to " + os.path.basename(fName) + "\t" + fName + "\n"
            for i, tag in enumerate(menuLines[fName]):
                self.menuText += prefixSep + tag.function_choice_output() + "\n"


    def menu_lines(self):
        return self.menuText.split("\n")

    def output_menu(self, fName):

        tPrint = False
        eCounter = 0
        with open(fName, 'w') as f:
            for mLine in self.menu_lines():
                if self.is_expandable(mLine):
                    eCounter += 1
                    if eCounter in self.expanded:
                        f.write(mLine.replace("+[", "-[") + "\n")
                        tPrint = True
                    else:
                        f.write(mLine + "\n")
                        tPrint = False
                else:
                    if tPrint: f.write(mLine + "\n")

    def handle_expansion_change(self, choice):

        # choice will be given as X of line in [X]
        choice = int(choice)
        print("choice " + str(choice))
        print(self.expanded)
        if choice in self.expanded:
            self.expanded.remove(choice)
        else:
            self.expanded.append(choice)

    def is_expandable(self, text):
        return text.startswith("+[") or text.startswith("-[")

    def load_from_file(self, fName):

        with open(fName, 'r') as f:
            self.from_json(f.readline())

    def save_to_file(self, fName): 

        with open(fName, 'w') as f:
            f.write(self.to_json())

    def to_json(self):
        # make a json dict maker @wtodo @python 
        jDict = {"menuText": self.menuText,
                 "expanded": self.expanded,
                 }

        return json.dumps(jDict)

    def from_json(self, jsonLine):
       objProperties = json.loads(jsonLine.strip()) 
       for attName, attProp in objProperties.items():
           setattr(self, attName, attProp)

def test_emenu():

    update_log(LOG_FILE, "None")

    #create menu
    mLines = create_by_file_expand_lines()
    eMenu = ExpandMenu(mLines)

    #output windowtext to file
    eMenu.output_menu(WINDOW_TEXT)

    #save state
    eMenu.save_to_file(MENU_STATE)


    #load state
    eMenu = ExpandMenu()
    eMenu.load_from_file(MENU_STATE)
    
    for cs in (1, 2, 2, 1):
        raw_input()

        #change expansion
        eMenu.handle_expansion_change(cs)
        eMenu.output_menu(WINDOW_TEXT)