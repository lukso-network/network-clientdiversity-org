import requests
import os
import math
import time
import json
import copy
import pprint
from datetime import datetime, timezone


current_time = round(time.time()) # seconds
date = datetime.now(timezone.utc).strftime('%Y-%m-%d') # yyyy-mm-dd
print(f"Epoch: {current_time}")
print(f"Date: {date}")

pp = pprint.PrettyPrinter(indent=4)
use_test_data = False
print_fetch_data = False
print_processed_data = True
pretty_print = True
exit_on_fetch_error = True
exit_on_save_error = True
exit_on_report_error = False

google_form_error_report_url = os.environ.get("")

# URLS
blockprint_api_addr = "http://34.140.62.68:8000"
node_crawler_api_addr = "http://34.140.62.68:10000"

# enter values for local testing
# rated_token = ""
# google_form_error_report_url = ""


def fetch_json(url, method="GET", payload={}, headers={}, retries=2):
  print(f"Fetch: {url}")
  response = {"status": 0, "attempts": 0, "data": None}
  try: 
    while response["attempts"] <= retries and (response["status"] != 200 or response["data"] == None):
      rate_limited_domains = ["rated.network"]
      rate_limited = any(domain in url for domain in rate_limited_domains)
      if (rate_limited or response["attempts"] > 0):
        time.sleep(1.05)
      response["attempts"] = response["attempts"] + 1
      r = requests.request(method, url, headers=headers, data=payload)
      response = {"status": r.status_code, "attempts": response["attempts"], "data": r.json()}
  except:
    error = f"Fetch failed: {url}"
    report_error(error)
    if exit_on_fetch_error:
      raise SystemExit(error)
    else:
      print(error)
  finally:
    print_data("fetch", response, label=None)
    return response

def save_to_file(rel_path, data):
  if not rel_path.startswith("/"):
    rel_path = "/" + rel_path
    abs_path = os.path.dirname(__file__) + rel_path
  # skip file save if using test data
  todays_data =  {
    "date":date,
    "timestamp":current_time,
    "data":data
  }
  # check if file exists yet
  if os.path.isfile(abs_path):
    try:
      with open(abs_path, 'r') as f:
        all_data = json.load(f)
        # check if there's already data for today
        if date != all_data[-1]['date'] and all_data[-1]['data'] != None:
          # append todays data to historical data and write to file
          all_data.append(todays_data)
          with open(abs_path, 'w') as f:
            json.dump(all_data, f, indent=None, separators=(',', ':'))
          f.close()
          print(f"{rel_path} data has been updated")
        # if the data was null then overwrite it
        elif date == all_data[-1]['date'] and all_data[-1]['data'] == None:
          del all_data[-1]
          # append todays data to historical data and write to file
          all_data.append(todays_data)
          with open(abs_path, 'w') as f:
            json.dump(all_data, f, indent=None, separators=(',', ':'))
          f.close()
          print(f"{rel_path} data has been updated")
        else:
          print(f"{rel_path} data for the current date was already recorded")
    except:
      # file is empty or malformed data
      error = f"ERROR: {rel_path} file read error"
      report_error(error)
      if exit_on_save_error:
        raise SystemExit(error)
      else:
        print(error)
  else:
    # create new file with today's data
    all_data = []
    all_data.append(todays_data)
    with open(abs_path, 'w') as f:
      json.dump(all_data, f, indent=None, separators=(',', ':'))
    f.close()
    print(f"{rel_path} data has been updated")

def report_error(error, context=""):
  data = {
    # "entry.2112281434": "name",    # text
    # "entry.1600556346": "option3", # dropdown
    # "entry.819260047": ["option2", "option3"], #checkbox multiple
    # "entry.1682233942": "option5"  # checkbox single
    "entry.76518486": error,
    "entry.943255668": context
  }
  try:
    requests.post(google_form_error_report_url, data)
    print("Error submitted")
  except:
    error = f"ERROR: {path} file read error"
    if exit_on_report_error:
      raise SystemExit(error)
    else:
      print(error)


def print_file(rel_path):
  # add leading / to relative path if not present
  if not rel_path.startswith("/"):
    rel_path = "/" + rel_path
  abs_path = os.path.dirname(__file__) + rel_path
  if os.path.isfile(abs_path):
    with open(abs_path, 'r') as f:
      contents = json.load(f)
      if pretty_print:
        pprint(contents)
      else:
        print(contents)
  else:
    print("not file")

def print_data(context, data, label=None):
  if context == "fetch" and print_fetch_data:
    if label:
      print(f"{label}:")
    if pretty_print:
      pp.pprint(data)
    else:
      print(data)
  if context == "processed" and print_processed_data:
    if label:
      print(f"{label}:")
    if pretty_print:
      pp.pprint(data)
    else:
      print(data)

def pprint(data):
  pp.pprint(data)


########################################



########################################


def get_blockprint_marketshare_data():  
  initial_timestamp = 1684856400
  initial_epoch = 0
  delta_timestamp = current_time - initial_timestamp # seconds
  current_epoch = math.floor(delta_timestamp / 384)

  # the Blockprint API caches results so fetching data based on an "epoch day" so 
  # everyone that loads the page on an "epoch day" will use the cached results and 
  # their backend doesn't get overloaded
  # Michael Sproul recommends using a 2-week period
  end_epoch = math.floor(current_epoch / 225) * 225
  start_epoch = end_epoch - 3150
  url = f"{blockprint_api_addr}/blocks_per_client/{start_epoch}/{end_epoch}"
  response = fetch_json(url)
  return response

def get_blockprint_accuracy_data():
  # accuracy of fingerprinting for each client
  url = f"{blockprint_api_addr}/confusion"
  response = fetch_json(url)
  return response


def process_blockprint_accuracy_data(raw_data):
  # example blockprint raw data:
  # raw_data = {'status': 200, 'attempts': 1, 'data': {
  #   'clients': {
  #     'Lighthouse': {
  #       'true_positives': 3644, 'true_negatives': 6921, 'false_positives': 377, 
  #       'false_negatives': 37, 'false_negatives_detail': {'Nimbus': 20, 'Prysm': 17}}, 
  #     'Nimbus': {
  #       'true_positives': 0, 'true_negatives': 10822, 'false_positives': 157, 
  #       'false_negatives': 0, 'false_negatives_detail': {}}, 
  #     'Prysm': {
  #       'true_positives': 5147, 'true_negatives': 5387, 'false_positives': 36, 
  #       'false_negatives': 409, 'false_negatives_detail': {'Lighthouse': 376, 'Nimbus': 30, 'Teku': 3}}, 
  #     'Teku': {
  #       'true_positives': 1615, 'true_negatives': 9234, 'false_positives': 3, 
  #       'false_negatives': 127, 'false_negatives_detail': {'Lighthouse': 1, 'Nimbus': 107, 'Prysm': 19}}
  #     }, 
  #     'nodes': [
  #       {'name': 'prysm-subscribe-all', 'label': 'Prysm', 'true_positives': 3648, 
  #         'false_negatives': {'Lighthouse': 3, 'Nimbus': 28, 'Teku': 2}, 'latest_slot': 7102453}, 
  #       {'name': 'prysm-subscribe-none', 'label': 'Prysm', 'true_positives': 1499, 
  #         'false_negatives': {'Lighthouse': 373, 'Nimbus': 2, 'Teku': 1}, 'latest_slot': 7102453}, 
  #       {'name': 'teku-subscribe-all', 'label': 'Teku', 'true_positives': 1615, 
  #         'false_negatives': {'Lighthouse': 1, 'Nimbus': 107, 'Prysm': 19}, 'latest_slot': 7102453}, 
  #       {'name': 'lighthouse-subscribe-none', 'label': 'Lighthouse', 'true_positives': 3644, 
  #         'false_negatives': {'Nimbus': 20, 'Prysm': 17}, 'latest_slot': 7102453}
  #     ]}}

  # calculate the accuracy for each client
  accuracy_data = []
  for key, value in raw_data["data"]["clients"].items():
    if (value["true_positives"] == 0 and value["false_negatives"] == 0):
      accuracy = "no data";
    elif (value["true_positives"] == 0 and value["false_negatives"] != 0):
      accuracy = "0";
    else:
      accuracy = round(value["true_positives"] / (value["true_positives"] + value["false_negatives"]), 6)
    accuracy_data.append({"name": key.lower(), "value": accuracy})
  print_data("processed", accuracy_data, "blockprint_accuracy_data")
  return accuracy_data

def process_blockprint_marketshare_data(raw_marketshare_data, processed_accuracy_data):
  # example blockprint raw data:
  # raw_marketshare_data = {'status': 200, 'attempts': 1, 'data': {
  #   'Uncertain': 0, 
  #   'Grandine': 0, 
  #   'Lighthouse': 33411, 
  #   'Lodestar': 1145, 
  #   'Nimbus': 4862, 
  #   'Other': 0, 
  #   'Prysm': 45450, 
  #   'Teku': 15458
  #   }}

  main_clients = ["lighthouse", "nimbus", "teku", "prysm", "lodestar", "erigon", "grandine"]
  threshold_percentage = 0.5 # represented as a percent, not a decimal
  sample_size = 0
  reformatted_data = []
  filtered_data = [{"name": "other", "value": 0}]
  marketshare_data = []
  extra_data = {}
  final_data = {}

  # reformat data into a list of dicts
  for key, value in raw_marketshare_data["data"].items():
    reformatted_data.append({"name": key.lower(), "value": value})
    sample_size += value
  # pprint(["reformatted_data", reformatted_data])
  # pprint(["sample_size", sample_size])

  # filter out items either under the threshold and not in the main_clients list
  for item in reformatted_data:
    if item["name"] in main_clients:
      filtered_data.append({"name": item["name"], "value": item["value"]})
    elif (item["value"] / sample_size * 100) >= threshold_percentage:
      filtered_data.append({"name": item["name"], "value": item["value"]})
    else:
      filtered_data[0]["value"] += item["value"]
  # pprint(["filtered_data", filtered_data])

  # calculate the marketshare for each client
  for item in filtered_data:
    marketshare = item["value"] / sample_size
    accuracy = "no data"
    for x in processed_accuracy_data:
      if x["name"] == item["name"]:
        accuracy = x["value"]
    marketshare_data.append({"name": item["name"], "value": marketshare, "accuracy": accuracy})
  # pprint(["marketshare_data", marketshare_data])

  # sort the list by marketshare descending
  sorted_data = sorted(marketshare_data, key=lambda k : k['value'], reverse=True)
  # pprint(["sorted_data", sorted_data])

  # supplemental data
  extra_data["data_source"] = "blockprint"
  extra_data["has_majority"] = False
  extra_data["has_supermajority"] = False
  extra_data["danger_client"] = ""
  if sorted_data[0]["value"] >= .50:
    extra_data["has_majority"] = True
    extra_data["danger_client"] = sorted_data[0]["name"]
  if sorted_data[0]["value"] >= .66:
    extra_data["has_supermajority"] = True
  extra_data["top_client"] = sorted_data[0]["name"]
  # pprint(["extra_data", extra_data])

  # create final data dict
  final_data["distribution"] = sorted_data
  # final_data["accuracy"] = processed_accuracy_data
  final_data["other"] = extra_data
  print_data("processed", final_data, "final_data_blockprint")

  return final_data


def blockprint_marketshare():
  raw_marketshare_data = get_blockprint_marketshare_data()
  save_to_file("../_data/raw/blockprint_raw.json", raw_marketshare_data)
  raw_accuracy_data = get_blockprint_accuracy_data()
  save_to_file("../_data/raw/blockprint_accuracy_raw.json", raw_accuracy_data)
  processed_accuracy_data = process_blockprint_accuracy_data(raw_accuracy_data)
  processed_marketshare_data = process_blockprint_marketshare_data(raw_marketshare_data, processed_accuracy_data)
  save_to_file("../_data/blockprint.json", processed_marketshare_data)


########################################


def get_node_crawler_marketshare_data():
  url = f"{node_crawler_api_addr}/dashboard"
  response = fetch_json(url)
  return response

def process_node_crawler_marketshare_data(raw_data):
  # {
  #   "clients": [
  #     {
  #       "name": "geth",
  #       "count": 32
  #     },
  #     {
  #       "name": "erigon",
  #       "count": 2
  #     },
  #   ],
  # } 

  main_clients = ["geth", "erigon", "nethermind", "besu", "reth"]
  threshold_percentage = 0.5 # represented as a percent, not a decimal
  sample_size = 0
  reformatted_data = []
  filtered_data = [{"name": "other", "value": 0}]
  marketshare_data = []
  extra_data = {}
  final_data = {}

  # reformat data into a list of dicts
  for item in raw_data["clients"]:
    reformatted_data.append({"name": item["name"].lower(), "value": item["count"]})
    sample_size += item["value"]
  # pprint(["reformatted_data", reformatted_data])
  # pprint(["sample_size", sample_size])

  # filter out items either under the threshold and not in the main_clients list
  for item in reformatted_data:
    if item["name"] in main_clients:
      filtered_data.append({"name": item["name"], "value": item["value"]})
    elif (item["value"] / sample_size * 100) >= threshold_percentage:
      filtered_data.append({"name": item["name"], "value": item["value"]})
    else:
      filtered_data[0]["value"] += item["value"]
  # pprint(["filtered_data", filtered_data])

  # calculate the marketshare for each client
  for item in filtered_data:
    marketshare = item["value"] / sample_size
    marketshare_data.append({"name": item["name"], "value": marketshare, "accuracy": "no data"})
  # pprint(["marketshare_data", marketshare_data])

  # sort the list by marketshare descending
  sorted_data = sorted(marketshare_data, key=lambda k : k['value'], reverse=True)
  # pprint(["sorted_data", sorted_data])

  # supplemental data
  extra_data["data_source"] = "node_crawler"
  extra_data["has_majority"] = False
  extra_data["has_supermajority"] = False
  extra_data["danger_client"] = ""
  if sorted_data[0]["value"] >= .50:
    extra_data["has_majority"] = True
    extra_data["danger_client"] = sorted_data[0]["name"]
  if sorted_data[0]["value"] >= .66:
    extra_data["has_supermajority"] = True
  extra_data["top_client"] = sorted_data[0]["name"]
  # pprint(["extra_data", extra_data])

  # create final data dict
  final_data["distribution"] = sorted_data
  final_data["other"] = extra_data
  print_data("processed", final_data, "final_data_node_crawler")

  return final_data


def node_crawler_marketshare():
  raw_data = get_node_crawler_marketshare_data()
  save_to_file("../_data/raw/node_crawler_raw.json", raw_data)
  processed_data = process_node_crawler_marketshare_data(raw_data)
  save_to_file("../_data/node_crawler.json", processed_data)


def get_data():
  blockprint_marketshare()
  node_crawler_marketshare()


get_data()

