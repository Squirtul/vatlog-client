import json
import os
import requests

API_BASE = "https://vatlog-api-production.up.railway.app"

def fetchAllLogs():
    response = requests.get(f"{API_BASE}/logs", headers=READ_HEADERS)
    response.raise_for_status()
    return response.json()

firs = ["bird", "ebbu", "edgg", "edmm", "edww", "eett", "efin",
        "egpx", "egtt", "ehaa", "eisn", "ekdk", "enor", "epww",
        "esaa", "evrr", "eyvl", "laaa", "lbsr", "lccc", "ldzo",
        "lecb", "lecm", "lfbb", "lfee", "lfff", "lfmm", "lfrr",
        "lggg", "lhcc", "libb", "limm", "lirr", "ljla", "lkaa",
        "lmmm", "lovv", "lppc", "lqsb", "lrbb", "lsas", "ltbb",
        "luuu", "lwss", "lyba", "lzbb", "ukbv", "ukdv", "ukfv",
        "uklv", "ukov"]

validTimes = ["0000", "0030", "0100", "0130", "0200", "0230",
              "0300", "0330", "0400", "0430", "0500", "0530",
              "0600", "0630", "0700", "0730", "0800", "0830",
              "0900", "0930", "1000", "1030", "1100", "1130",
              "1200", "1230", "1300", "1330", "1400", "1430",
              "1500", "1530", "1600", "1630", "1700", "1730",
              "1800", "1830", "1900", "1930", "2000", "2030",
              "2100", "2130", "2200", "2230", "2300", "2330"]

# Fetch FIR names
with open(os.path.join(os.path.dirname(__file__), 'references', 'firref.json'),'r',encoding='utf-8') as i:
    firNames = json.load(i)

def fetchSettings():
    with open("localsettings.conf", "r") as f:
        names = False
        apikey = None
        writekey = None
        for line in f.readlines():
            if "names" in line and line[-1] == "1":
                names = True
            if line.startswith("apikey"):
                apikey = line.split("=")[1].strip()
            if line.startswith("writekey"):
                writekey = line.split("=")[1].strip()
    return names, apikey, writekey

names, READ_KEY, WRITE_KEY = fetchSettings()
READ_HEADERS  = {"X-API-Key": READ_KEY}
WRITE_HEADERS = {"X-API-Key": WRITE_KEY}

def collectTime():
    time = ""
    while time not in validTimes:
        time = input("\nEnter time: ")
    return(time)
        
def addLog():
    time = collectTime()
    print()
    batch = []
    for i in firs:
        firName = f" ({firNames[i]})" if names else ""
        check = input(f"{i.upper()}{firName}: ")
        if check == "" or len(check) > 2:
            check = "0"
        batch.append({"fir": i, "time": time, "value": int(check)})
    print("\nSubmitting...")
    response = requests.post(f"{API_BASE}/logs", json=batch, headers=WRITE_HEADERS)
    response.raise_for_status()
    print("Successfully added!")

def summariseFIR():
    search = ""
    while search not in firs:
        search = input("\nEnter FIR: ").lower()
    print("Fetching from API...")
    entries = fetchAllLogs()
    labelWidth = max(len(f"At {i}:") for i in validTimes)
    print()
    for i in validTimes:
        match = next((e for e in entries if e["fir"] == search and e["time"] == i), None)
        label = f"At {i}:".ljust(labelWidth)
        if match and match["count"] > 0:
            print(f"{label} {match['average']:.2f}")
        else:
            print(f"{label} 0")
    print()

def summariseTime():
    search = collectTime()
    labelWidth = max(
        len(f"{i.upper()} ({firNames[i]}) at {search}:" if names else f"{i.upper()} at {search}:")
        for i in firs
    )
    print("Fetching from API...")
    entries = fetchAllLogs()
    print()
    for i in firs:
        firName = f" ({firNames[i]})" if names else ""
        match = next((e for e in entries if e["fir"] == i and e["time"] == search), None)
        label = f"{i.upper()}{firName}:".ljust(labelWidth)
        if match and match["count"] > 0:
            print(f"{label} {match['average']:.2f}")
        else:
            print(f"{label} 0")
    print()

def settings():
    print()
    print("-"*30)
    global names
    maintainSettings = True
    with open ("localsettings.conf","r") as f:
        lines = f.readlines()
        if names == True:
            print("\n  DISPLAY FIR NAMES : TRUE\n")
        else:
            print("\n  DISPLAY FIR NAMES : FALSE\n")
        print("-"*30)
        while maintainSettings:
            choiceS = 0
            while choiceS != 1 and choiceS != 2:
                choiceS = int(input("\n-1- : Edit DISPLAY FIR NAMES\n-2- : Exit\n\n"))
            if choiceS == 1:
                with open("localsettings.conf", "r") as f:
                    content = f.read()
                if names == False:
                    content = content.replace("names0", "names1")
                    print("\nDISPLAY FIR NAMES now TRUE")
                else:
                    content = content.replace("names1", "names0")
                    print("\nDISPLAY FIR NAMES now FALSE")
                with open("localsettings.conf", "w") as f:
                    f.write(content)
                names = fetchSettings()
            if choiceS == 2:
                maintainSettings = False

while True:
    choice = 0
    while choice != 1 and choice != 2 and choice != 3 and choice != 9:
        print("-"*30)
        try:
            choice = int(input("Welcome to the datacentre.. how can I help?\n\n-1- : View dataset by FIR\n-2- : View dataset by Time\n-3- : Settings\n-9- : Add dataset (restricted)\n\n"))
        except ValueError:
            continue
    if choice == 9:
        addLog()
    elif choice == 1:
        summariseFIR()
    elif choice == 2:
        summariseTime()
    elif choice == 3:
        settings()