#!/usr/bin/python3

import sys

# Checking for puremagic
try:
    import puremagic as pr
except:
    print("Error: >puremagic< module not found.")
    sys.exit(1)

# Checking for rich
try:
    from rich import print
    from rich.table import Table
except:
    print("Error: >rich< not found.")
    sys.exit(1)

# Checking for oletools
try:
    from oletools.olevba import VBA_Parser
    from oletools.crypto import is_encrypted
    from oletools.oleid import OleID
    from olefile import isOleFile
except:
    print("Error: >oletools< module not found.")
    print("Try 'sudo -H pip3 install -U oletools' command.")
    sys.exit(1)

# Legends
infoS = f"[bold cyan][[bold red]*[bold cyan]][white]"
errorS = f"[bold cyan][[bold red]![bold cyan]][white]"

# Target file
targetFile = str(sys.argv[1])

# Macro parser function
def MacroParser(macroList):
    answerTable = Table()
    answerTable.add_column("[bold green]Threat Levels", justify="center")
    answerTable.add_column("[bold green]Macros", justify="center")
    answerTable.add_column("[bold green]Descriptions", justify="center")

    for fi in range(0, len(macroList)):
        if macroList[fi][0] == 'Suspicious':
            if "(use option --deobf to deobfuscate)" in macroList[fi][2]:
                sanitized = f"{macroList[fi][2]}".replace("(use option --deobf to deobfuscate)", "")
                answerTable.add_row(f"[bold yellow]{macroList[fi][0]}", f"{macroList[fi][1]}", f"{sanitized}")
            elif "(option --decode to see all)" in macroList[fi][2]:
                sanitized = f"{macroList[fi][2]}".replace("(option --decode to see all)", "")
                answerTable.add_row(f"[bold yellow]{macroList[fi][0]}", f"{macroList[fi][1]}", f"{sanitized}")
            else:
                answerTable.add_row(f"[bold yellow]{macroList[fi][0]}", f"{macroList[fi][1]}", f"{macroList[fi][2]}")
        elif macroList[fi][0] == 'IOC':
            answerTable.add_row(f"[bold magenta]{macroList[fi][0]}", f"{macroList[fi][1]}", f"{macroList[fi][2]}")
        elif macroList[fi][0] == 'AutoExec':
            answerTable.add_row(f"[bold red]{macroList[fi][0]}", f"{macroList[fi][1]}", f"{macroList[fi][2]}")
        else:
            answerTable.add_row(f"{macroList[fi][0]}", f"{macroList[fi][1]}", f"{macroList[fi][2]}")
    print(answerTable)

# A function that finds VBA Macros
def MacroHunter(targetFile):
    print(f"\n{infoS} Looking for Macros...")
    try:
        fileData = open(targetFile, "rb").read()
        vbaparser = VBA_Parser(targetFile, fileData)
        macroList = list(vbaparser.analyze_macros())
        macro_state_vba = 0
        macro_state_xlm = 0
        # Checking vba macros
        if vbaparser.contains_vba_macros == True:
            print(f"[bold red]>>>[white] VBA MACRO: [bold green]Found.")
            if vbaparser.detect_vba_stomping() == True:
                print(f"[bold red]>>>[white] VBA Stomping: [bold green]Found.")

            else:
                print(f"[bold red]>>>[white] VBA Stomping: [bold red]Not found.")
            MacroParser(macroList)
            macro_state_vba += 1
        else:
            print(f"[bold red]>>>[white] VBA MACRO: [bold red]Not found.\n")

        # Checking for xlm macros
        if vbaparser.contains_xlm_macros == True:
            print(f"\n[bold red]>>>[white] XLM MACRO: [bold green]Found.")
            MacroParser(macroList)
            macro_state_xlm += 1
        else:
            print(f"\n[bold red]>>>[white] XLM MACRO: [bold red]Not found.")

        # If there is macro we can extract it!
        if macro_state_vba != 0 or macro_state_xlm != 0:
            choice = str(input("\n>>> Do you want to extract macros [Y/n]?: "))
            if choice == "Y" or choice == "y":
                print(f"{infoS} Attempting to extraction...\n")
                if macro_state_vba != 0:
                    for mac in vbaparser.extract_all_macros()[1]:
                        print(mac.strip("\r\n"))
                else:
                    for mac in vbaparser.xlm_macros:
                        print(mac)
                print(f"\n{infoS} Extraction completed.")

    except:
        print(f"{errorS} An error occured while parsing that file for macro scan.")

# Gathering basic informations
def BasicInfoGa(targetFile):
    # Check for ole structures
    if isOleFile(targetFile) == True:
        print(f"{infoS} Ole File: [bold green]True[white]")
    else:
        print(f"{infoS} Ole File: [bold red]False[white]")

    # Check for encryption
    if is_encrypted(targetFile) == True:
        print(f"{infoS} Encrypted: [bold green]True[white]")
    else:
        print(f"{infoS} Encrypted: [bold red]False[white]")
    
    # VBA_MACRO scanner
    vbascan = OleID(targetFile)
    vbascan.check()
    # Sanitizing the array
    vba_params = []
    for vb in vbascan.indicators:
        vba_params.append(vb.id)

    if "vba_macros" in vba_params:
        for vb in vbascan.indicators:
            if vb.id == "vba_macros":
                if vb.value == True:
                    print(f"{infoS} VBA Macros: [bold green]Found[white]")
                    MacroHunter(targetFile)
                else:
                    print(f"{infoS} VBA Macros: [bold red]Not Found[white]")
    else:
        MacroHunter(targetFile)

# Execution area
try:
    BasicInfoGa(targetFile)
except:
    print(f"{errorS} An error occured while analyzing that file.")
    sys.exit(1)
