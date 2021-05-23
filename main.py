"""
Modify as you see fit.
"""

import cnw_scraper as cnw
import pandas
import bs4
import requests
import json
import re
import os

def update_guest_data(file_path:str,update_logs:bool=False,cnw_logs:bool=False):
    """
    Collect Joe Rogan guest data and write to file with newest data from podcast using data sites and my CNW_Scraper tool's scrape_names function. Data is written out as klsjd;klfjfa

    Data came from jrelibrary.com and DataWrapper. There is so much junk in here - unicode identifiers for non-ascii guest names, extra backslashes, inconsistent naming and multiple guest conventions used, missing names, hyperlinks sprinkled everywhere, extra quotes and other characters, junk html, ugh...

    The data is from the general podcasts ONLY - no MMA, fight companion, specials. Name and which episodes a guest appeared on are collected from jrelibrary, and the extra stuff (if avaliable) is from celebritynetworth. It's not perfect, but neither is the data that gets collected. So...Enjoy.

    :file_path: String to where you want to save the guest data (should be saved as JSON, but whatever floats yer boat.) Will be overwritten if file already exists.

    :update_logs: Print to terminal what this function is doing? False by default.

    :cnw_logs: Set CNW verbose, console printing, and log file writing to true. Log file is written next to the file you set at file_path. Name is 'cnw.log' with date/time logging active. False by default.

    :return: None.
    """

    # Got a valid path for that file?
    try:
        with open(file_path,"w") as f:
            pass
    except:
        raise ValueError("Ya dun goofed - file path invalid or inaccessible.")

    if update_logs: print("Updating guest data ...\n")

    # If Rogan has any more guests on with funny names that only unicode can handle, add those chars here.
    uni_chars = {r"\u2019":"'",r"\u00E9":"e",r"\u00F1":"n"}
    url = "https://datawrapper.dwcdn.net/eoqPA/"
    usr_agt = "Young Jamie" # LOL

    # Perform html request for data
    if update_logs: print("Getting raw data ...")
    with requests.get(url=url,headers={"user-agent":usr_agt},timeout=10) as response:
        response.raise_for_status()
        # Find latest data url link.
        url = re.search(r'(?<=url=).+?(?=")',response.text).group(0)
        with requests.get(url=url,headers={"user-agent":usr_agt},timeout=10) as response:
            response.raise_for_status()
            html = response.content

    # *cries in regex...and in unicode...and in bytes...and in backslashes*
    if update_logs: print("Parsing raw data ...")
    raw_script = bs4.BeautifulSoup(html,"html.parser").find_all("script")[1].contents[0]
    for k,v in uni_chars.items():
        raw_script = raw_script.replace(k,v)
    clean_script = raw_script.replace("\\","").replace("\"\"","\"")
    raw_entries = [l[0] for l in re.findall(r'((rn|">)#.+?\d{4}")',clean_script)]
    # Entries are three parts: episode number, name(s) of guests, date of episode.
    entries = list(map(lambda x: x[3:].replace("</a>\"",""),raw_entries))

    # Create basic guest data from jrelibrary.com/datawrapper.
    if update_logs: print("Setting up data objects ...")
    guest_data = {}
    fix_exceptions = ["Dr. Phil","Mr. T"] # Add more if needed.
    fix_removal = ["Dr. ","Mr. ","Mrs. ","Ms. ","Cmdr. "] # Ditto.
    fix = lambda x,r: x.replace(r, "") if x not in fix_exceptions else x
    for e in entries:
        ep_num = int(re.match(r'\d+',e).group(0))
        date = re.search(r'"\w+\s\d+,\s\d+"$',e).group(0)[1:-1]
        name_data = re.search(r'(?<=\d,)"?"?\w.+(?=,")',e)
        if not name_data: continue
        name_data = name_data.group(0)
        # Get rid of extra junk from name data.
        name_data = name_data[1:-1] if name_data[0] == "\"" else name_data
        if ": " in name_data:
            name_data = name_data[name_data.find(": ")+1:]
        if "- " in name_data:
            name_data = name_data[name_data.find("- ")+1:]
        name_data.strip()
        # Split up multiple guests if any.
        names = list(map(lambda x: x.strip(),re.split(r',|&',name_data)))
        for n in names:
            for f in fix_removal:
                n = fix(n,f).strip()
            if n in guest_data.keys():
                # This person already exists - add appearance.
                guest_data[n]["Appearances"].append((ep_num,date))
                continue
            guest_data.update({n:{"Name":n,"Appearances":[(ep_num,date)]}})

    # Get remaining data from celebritynetworth.com using my handy scraper.
    if update_logs: print("Collecting extra data from CNW (this may take a bit) ...")
    cnw.Options.custom_user_agent = usr_agt
    if cnw_logs:
        cnw.Logs.print_to_console = True
        cnw.Logs.verbose = True
        cnw.Logs.write_to_file(os.path.split(file_path)[0]+"/cnw")
    profiles = cnw.scrape_names([n for n in guest_data.keys()])

    # Add extra data to the guests.
    if update_logs: print("Parsing and adding extra data ...")
    valid_chars = lambda c: c.isalnum() or any([x in c for x in [" ","-","'"]])
    parse_name = lambda n: "".join(filter(valid_chars, n)).strip()
    for g in guest_data.keys():
        for field in cnw.Profile.fields:
            if field == "Name": continue
            guest_data[g][field] = "N/A"
        guest_name = parse_name(guest_data[g]["Name"])
        for p in profiles:
            t = p.description.lower()[:400]
            if all([x in t for x in guest_name.lower().split()]):
                for k in guest_data[g].keys():
                    if k not in p.stats:continue
                    if k == "Name": continue
                    guest_data[g][k] = p.stats[k]
                break

    # Write data and done.
    if update_logs: print("Writing data to file ...")
    with open(file_path,"w") as f:
        json.dump(guest_data,f,indent=4)
    if update_logs: print("\nGuest updates done.\n")

# df = pandas.read_json(".data/test/guest_data.json")

obj = """{
        "Name": "Reggie Watts",
        "Appearances": [
            {"Episode": 1648,"Date": "May 8, 2021"},
            {"Episode": 1484,"Date": "Jun 2, 2020"},
            {"Episode": 1322,"Date": "Jul 10, 2019"},
            {"Episode": 1015,"Date": "Sep 26, 2017"}
        ],
        "Net Worth": "2000000",
        "Salary": "$666 per episode",
        "Date of Birth": "Mar 23, 1972 (49 years old)",
        "Gender": "Male",
        "Height": "6 ft (1.83 m)",
        "Profession": "Comedian, Singer, Musician, Actor, Screenwriter, Film Score Composer",
        "Nationality": "United States of America",
        "Last Updated": "2020"
    }"""

# with open("test.json","w") as f:
df = pandas.json_normalize(json.loads(obj))
# print(df.dtypes)