"""
"""

import cnw_scraper as cnw
import pandas
import bs4
import requests
import json
import re
from unicodedata import normalize as uni_nrml

# data struct
# "Joe Rogan":{
#     "Name":"Joe Rogan",
#     "Appearances": [
#         [episode#,date],
#         [episode#,date],
#         [episode#,date],
#     ]
#     # cnw stuff
# }

# with open(".data/data.txt","w",encoding="utf-8") as f:
#     f.writelines([e+'\n' for e in entries])

def update_guest_data():
    """
    Data came from jrelibrary.com and DataWrapper
    """

    url = "https://datawrapper.dwcdn.net/eoqPA/"
    h = {"user-agent":"Young Jamie"}
    with requests.get(url=url,headers=h,timeout=10) as response:
        response.raise_for_status()
        # Find latest data link
        url = re.search(r'(?<=url=).+?(?=")',response.text).group(0)
        with requests.get(url=url,headers=h,timeout=10) as response:
            response.raise_for_status()
            html = response.content.decode("unicode_escape")

    # *cries in regex...and in unicode...and in bytes...and in backslashes*
    raw_script = bs4.BeautifulSoup(uni_nrml("NFKD",html),"html.parser").find_all("script")[1].contents[0]
    clean_script = raw_script.replace("\\","").replace("\"\"","\"")
    raw_entries = [l[0] for l in re.findall(r'((rn|">)#.+?\d{4}")',clean_script)]
    entries = list(map(lambda x: x[3:].replace("</a>\"",""),raw_entries))

    # Create base guest data from jrelibrary.com/datawrapper.
    guest_data = {}
    for e in entries:
        ep_num = int(re.match(r'\d+',e).group(0))
        name_data = re.search(r'(?<=\d,)"?\w.+"?(?=,")',e).group(0)
        date = re.search(r'"\w+\s\d+,\s\d+"$',e).group(0)[1:-1]
        # Get rid of extra junk from name data.
        name_data = name_data[1:-1] if name_data[0] == "\"" else name_data
        if ": " in name_data:
            name_data = name_data[name_data.find(": ")+1:]
        if "- " in name_data:
            name_data = name_data[name_data.find("- ")+1:]
        name_data.strip()
        if "," in name_data:
            # Name has separators for multiple guests.
            guest_names = list(map(lambda x: x.strip(),name_data.split(",")))
        else:
            # Only one guest.
            guest_names = [name_data]
        for n in guest_names:
            if n in guest_data.keys():
                guest_data[n]["Appearances"].append((ep_num,date))
                continue
            guest_data.update({n:{"Name":n,"Appearances":[(ep_num,date)]}})
    
    # Get remaining data from celebritynetworth.com using my handy scraper.

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