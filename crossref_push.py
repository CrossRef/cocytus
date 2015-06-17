import requests
import urllib
try:
  from PUSH_TOKEN_SECRET import PUSH_TOKEN
except ImportError:
  print("Please create PUSH_TOKEN_SECRET.py file")

from config import *

def push_to_crossref(rcdict):
    for  addremove, doi_list in rcdict['doi'].items():
        for doi in doi_list:
            action = {'added':'add','deleted':'remove'}[addremove]
            server_url = rcdict['server_url']
            safe_title =  urllib.parse.quote(rcdict['title'].encode('utf-8'))
            article_url = url = "{server_url}/wiki/{safe_title}".format(server_url=server_url, safe_title=safe_title) 
            diff = rcdict['revision']['new']

            response = requests.post(PUSH_API_URL, json={"doi": doi,
                                              "source": PUSH_SOURCE,
                                              "type": PUSH_TYPE,
                                              "arg1":action,
                                              "arg2":article_url,
                                              "arg3":diff}, headers= {"Token": PUSH_TOKEN})
            return response

def heartbeat():
    return requests.post(PUSH_API_URL, json={"heartbeat-type": "input", "source": PUSH_SOURCE, "type": PUSH_TYPE},
                                       headers= {"Token": PUSH_TOKEN})

def output_heartbeat():
    return requests.post(PUSH_API_URL, json={"heartbeat-type": "output", "source": PUSH_SOURCE, "type": PUSH_TYPE},
                                       headers= {"Token": PUSH_TOKEN})

