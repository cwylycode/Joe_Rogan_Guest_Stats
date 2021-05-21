"""
Modify as you see fit.
"""

import cnw_scraper as cnw
import pandas
import bs4
import requests
import json
import re

def update_guest_data():
    """
    Data came from jrelibrary.com and DataWrapper. There is so much junk in here - unicode identifiers for non-ascii guest names, extra backslashes, inconsistent naming and multiple guest conventions used, missing names, hyperlinks sprinkled everywhere, extra quotes and other characters, junk html, ugh...
    """

    print("Updating guest data ...\n")

    # If Rogan has any more guests on with funny names that only unicode can handle, add those chars here.
    uni_chars = {r"\u2019":"'",r"\u00E9":"e",r"\u00F1":"n"}
    url = "https://datawrapper.dwcdn.net/eoqPA/"
    h = {"user-agent":"Young Jamie"} # LOL

    # Perform html request for data
    print("Getting raw data ...")
    with requests.get(url=url,headers=h,timeout=10) as response:
        response.raise_for_status()
        # Find latest data url link.
        url = re.search(r'(?<=url=).+?(?=")',response.text).group(0)
        with requests.get(url=url,headers=h,timeout=10) as response:
            response.raise_for_status()
            html = response.content

    # *cries in regex...and in unicode...and in bytes...and in backslashes*
    print("Parsing raw data ...")
    raw_script = bs4.BeautifulSoup(html,"html.parser").find_all("script")[1].contents[0]
    for k,v in uni_chars.items():
        raw_script = raw_script.replace(k,v)
    clean_script = raw_script.replace("\\","").replace("\"\"","\"")
    raw_entries = [l[0] for l in re.findall(r'((rn|">)#.+?\d{4}")',clean_script)]
    entries = list(map(lambda x: x[3:].replace("</a>\"",""),raw_entries))

    # Create basic guest data from jrelibrary.com/datawrapper.
    print("Setting up data objects ...")
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
    print("Collecting extra data from CNW (this may take a bit) ...")
    cnw.Options.custom_user_agent = "Young Jamie"
    cnw.Logs.print_to_console = True
    cnw.Logs.verbose = True
    cnw.Logs.write_to_file(".data/test/testlog",False)
    profiles = cnw.scrape_names([n for n in guest_data.keys()])

    # Add extra data to the guests.
    print("Parsing and adding extra data ...")
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
    print("Writing data to JSON file ...")
    with open(".data/test/guest_data.json","w") as f:
        json.dump(guest_data,f,indent=4)
    
    print("\nGuest updates done.\n")

update_guest_data()

# def collect_wealth():
    # Setup, get names, etc
    # df:pandas.DataFrame = pandas.read_csv("data.csv")
    # names:list = df["Name"].to_list()
    # parser = {"thousand":1_000,"million":1_000_000,"billion":1_000_000_000}

    # Attempt to turn the net worth into a real number
    # try:
    #     worth = worth.group(0)[1:].split()
    #     worth = int(worth[0]) * parser[worth[1]]
    # except:
    #     print("ERROR: Couldn't parse the worth for some reason. Is the person a trillionaire, or something?!")