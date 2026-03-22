import json
import os
import requests

API_BASE = "https://vatlog-api-production.up.railway.app"

FIRS = [
    "bird", "ebbu", "edgg", "edmm", "edww", "eett", "efin",
    "egpx", "egtt", "ehaa", "eisn", "ekdk", "enor", "epww",
    "esaa", "evrr", "eyvl", "laaa", "lbsr", "lccc", "ldzo",
    "lecb", "lecm", "lfbb", "lfee", "lfff", "lfmm", "lfrr",
    "lggg", "lhcc", "libb", "limm", "lirr", "ljla", "lkaa",
    "lmmm", "lovv", "lppc", "lqsb", "lrbb", "lsas", "ltbb",
    "luuu", "lwss", "lyba", "lzbb", "ukbv", "ukdv", "ukfv",
    "uklv", "ukov",
]

VALID_TIMES = [
    "0000", "0030", "0100", "0130", "0200", "0230",
    "0300", "0330", "0400", "0430", "0500", "0530",
    "0600", "0630", "0700", "0730", "0800", "0830",
    "0900", "0930", "1000", "1030", "1100", "1130",
    "1200", "1230", "1300", "1330", "1400", "1430",
    "1500", "1530", "1600", "1630", "1700", "1730",
    "1800", "1830", "1900", "1930", "2000", "2030",
    "2100", "2130", "2200", "2230", "2300", "2330",
]

SETTINGS_FILE = "localsettings.conf"
FIR_NAMES_FILE = os.path.join(os.path.dirname(__file__), "references", "firref.json")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_fir_names():
    with open(FIR_NAMES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

FIR_NAMES = load_fir_names()


def load_settings():
    """Return (show_names: bool, read_key: str, write_key: str)."""
    show_names = False
    read_key = ""
    write_key = ""
    with open(SETTINGS_FILE, "r") as f:
        for raw in f:
            line = raw.strip()
            if line == "names1":
                show_names = True
            elif line.startswith("apikey="):
                read_key = line.split("=", 1)[1]
            elif line.startswith("writekey="):
                write_key = line.split("=", 1)[1]
    return show_names, read_key, write_key


def save_names_setting(show_names: bool):
    """Toggle the names0/names1 flag in the settings file."""
    with open(SETTINGS_FILE, "r") as f:
        content = f.read()
    if show_names:
        content = content.replace("names0", "names1")
    else:
        content = content.replace("names1", "names0")
    with open(SETTINGS_FILE, "w") as f:
        f.write(content)


def fir_label(fir: str, show_names: bool) -> str:
    """Return 'EGTT' or 'EGTT (London)' depending on setting."""
    name = f" ({FIR_NAMES[fir]})" if show_names and fir in FIR_NAMES else ""
    return f"{fir.upper()}{name}"


def prompt_time() -> str:
    while True:
        t = input("\nEnter time (HHMM): ").strip()
        if t in VALID_TIMES:
            return t
        print("  Invalid time. Must be a 30-minute boundary, e.g. 0000, 0030 … 2330.")


def prompt_fir() -> str:
    while True:
        f = input("\nEnter FIR: ").strip().lower()
        if f in FIRS:
            return f
        print("  Unrecognised FIR.")


def fetch_all_logs(read_key: str) -> list:
    try:
        response = requests.get(
            f"{API_BASE}/logs",
            headers={"X-API-Key": read_key},
            timeout=15,
        )
        if response.status_code == 429:
            print("\nRate limit hit — please wait a moment and try again.")
            return []
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            print(f"\nUnexpected API response format: {data}")
            return []
        return data
    except requests.RequestException as e:
        print(f"\nNetwork error: {e}")
        return []


# ---------------------------------------------------------------------------
# Menu actions
# ---------------------------------------------------------------------------

def add_log(write_key: str, show_names: bool):
    time = prompt_time()
    print()
    batch = []
    for fir in FIRS:
        label = fir_label(fir, show_names)
        raw = input(f"{label}: ").strip()
        if raw.lower() == "x":
            continue
        value = int(raw) if raw.isdigit() and len(raw) <= 2 else 0
        batch.append({"fir": fir, "time": time, "value": value})

    print("\nSubmitting…")
    try:
        response = requests.post(
            f"{API_BASE}/logs",
            json=batch,
            headers={"X-API-Key": write_key},
            timeout=15,
        )
        response.raise_for_status()
        print("Successfully added!")
    except requests.RequestException as e:
        print(f"\nSubmission failed: {e}")


def summarise_by_fir(read_key: str):
    fir = prompt_fir()
    print("\nFetching from API…")
    entries = fetch_all_logs(read_key)
    if not entries:
        return

    label_width = max(len(f"At {t}:") for t in VALID_TIMES)
    print()
    for t in VALID_TIMES:
        match = next((e for e in entries if e["fir"] == fir and e["time"] == t), None)
        label = f"At {t}:".ljust(label_width)
        if match and match.get("count", 0) > 0:
            print(f"{label} {match['average']:.2f}      (n={match['count']})")
        else:
            print(f"{label} 0")
    print()


def summarise_by_time(read_key: str, show_names: bool):
    time = prompt_time()
    print("\nFetching from API…")
    entries = fetch_all_logs(read_key)
    if not entries:
        return

    labels = [fir_label(f, show_names) for f in FIRS]
    label_width = max(len(l) for l in labels) + 1   # +1 for the colon
    print()
    for fir, label in zip(FIRS, labels):
        match = next((e for e in entries if e["fir"] == fir and e["time"] == time), None)
        col = f"{label}:".ljust(label_width)
        if match and match.get("count", 0) > 0:
            print(f"{col} {match['average']:.2f}      (n={match['count']})")
        else:
            print(f"{col} 0")
    print()


def settings_menu(show_names: bool) -> bool:
    """Display/edit settings. Returns the (possibly updated) show_names value."""
    while True:
        print("\n" + "-" * 30)
        state = "TRUE" if show_names else "FALSE"
        print(f"\n  DISPLAY FIR NAMES : {state}\n")
        print("-" * 30)

        choice = None
        while choice not in ("1", "2"):
            choice = input("\n-1- : Toggle DISPLAY FIR NAMES\n-2- : Back\n\n").strip()

        if choice == "1":
            show_names = not show_names
            save_names_setting(show_names)
            state = "TRUE" if show_names else "FALSE"
            print(f"\nDISPLAY FIR NAMES is now {state}")
        elif choice == "2":
            return show_names


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    show_names, read_key, write_key = load_settings()

    while True:
        print("\n" + "-" * 30)
        choice = None
        while choice not in ("1", "2", "3", "9"):
            print("Welcome to the datacentre — how can I help?\n")
            print("-1- : View dataset by FIR")
            print("-2- : View dataset by Time")
            print("-3- : Settings")
            print("-9- : Add dataset (restricted)")
            choice = input("\n> ").strip()

        if choice == "1":
            summarise_by_fir(read_key)
        elif choice == "2":
            summarise_by_time(read_key, show_names)
        elif choice == "3":
            show_names = settings_menu(show_names)
        elif choice == "9":
            add_log(write_key, show_names)


if __name__ == "__main__":
    main()
