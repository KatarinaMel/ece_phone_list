# File to scrape entries from the Jacobs School Directory

from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
from collections import defaultdict
import re

# Attempts to get the content at the specified url
def simple_get(url):
  try:
    with closing(get(url, stream = True)) as resp:
      if is_good_response(resp):
        return resp.content
      else:
        return None

  except RequestException as e:
    log_error('Error during requests to {0} : {0}'.format(url, str(e)))
    return None

# Checks if the response seems to be HTML (returns true if so)
def is_good_response(resp):
  content_type = resp.headers['Content-Type'].lower()
  return (resp.status_code == 200
          and content_type is not None
          and content_type.find('html') > -1)

# Prints errors
def log_error(e):
  print(e)

# Map the header to an index
def process_header(header):
  header_enum = defaultdict(str)
  i = 0
  for column in header.select('th'):
    header_enum[i] = column.string
    i += 1
  return header_enum

# Parses the value from a column
def parse_column(column):
  val = ""
  if column.string != None:
    val = column.string
  elif column.next_element.strip() != "":
    val = column.next_element.strip()
  elif len(column.select('a')) > 0:
    val = column.select('a')[0].string
  return val


# Read the directory from JSOE
def read_jsoe_dir(create, check, prev, fileName):
  # Get response from jsoe directory url
  response = simple_get("https://www.jacobsschool.ucsd.edu/about/about_contacts/directory.sfe")
  if response is not None:
    html = BeautifulSoup(response, 'html.parser')
    # Extract the search table (second elt of the searchTbl class)
    i = 0
    tables = html.select('[class=searchTbl]')
    table = tables[1]

    # Go through all the rows
    row_idx = 0
    people_table= defaultdict(list)
    people_list = list()
    for row in table.select('tr'):
      # Process the header
      if row_idx == 0:
        header_map = process_header(row)

      else:
        # Process each person
        person = list()
        col_idx = 0
        is_ece = False
        for column in row.select('td'):
          val = parse_column(column)
          # Save the name for the dictionary key
          if header_map[col_idx] == "Name":
            name = val
          # Check if the person is ECE
          if header_map[col_idx] == "Department":
            if val == "Electrical and Computer Engineering":
              is_ece = True
          if header_map[col_idx] == "Title":
            if "Academic" in val or "Postdoc" in val or "Other" in val or "Scholar" in val:
              title_on_list = False
            else:
              title_on_list = True
          person.append([val, True])
          col_idx += 1

        # Only add the ECE people
        if is_ece and title_on_list:
          people_table[name] = person
          people_list.append(name)

      row_idx += 1
    print("done!")
    return [people_table, people_list, header_map]

# Double check the table with the blink directory
def check_blink(table, header_map):
  for name in table:
    # Make url
    split_name = [re.sub(r'[^\w\s]','',s) for s in name.split(' ')]
    formatted_name = split_name[1] + "+" + split_name[0]
    url = "https://act.ucsd.edu/directory/search?jlinkevent=Redirect&entry=" + formatted_name + "&site=blink2"
    # Get response from blink search
    response = simple_get(url)
    if response is not None:
      html = BeautifulSoup(response, 'html.parser')

      # Loop through the results
      found = False
      if len(html.select('[class=sorting_2]')) != 0:
        for result in html.select('[class=sorting_2]'):
          res_name = result.select('a')[0].string.strip()
          if res_name.split() == name.split():
            found = True
            break

      # Search went straight to the eCard
      else:
        if len(html.select('h1')) > 0:
          res_name = html.select('h1')[0].next_element.strip()
          if res_name.split() == name.split():
            found = True
            table_row = table[name]
            i = 1
            for category in html.findAll(True, {'class':['col-xs-2', 'dir-result']}):
              print(category.string)
              print(header_map[i])
              print("---------")
              i += 1

def create_header_enum(header_map):
  header_enum = defaultdict(int)
  for i in header_map:
    header_enum[header_map[i]] = i

  return header_enum

def title_symbol(title):
  if "Res" in title:
    return "R"
  elif "Emer" in title:
    return "PE"
  elif "Prof" in title:
    return "P"
  else:
    return "S"

def shorten_phone(num):
  if len(num) < 6:
    return ''
  short_num = num[-6:]
  return short_num.replace('-', '')

def split_location(loc):
  room_idx = re.search('\d', loc)
  last_idx = len(loc)
  room = ""
  if room_idx is not None:
    last_idx = room_idx.start()
    room = loc[last_idx:]
    if last_idx - 1 >= 0 and loc[last_idx - 1] is 'B':
      last_idx = last_idx - 1
      room = loc[last_idx - 1] + room
    last_idx = last_idx - 1 # to get rid of the trailing space
  building = loc[:last_idx]
  return [room, building] 

def format_table(table, names, header_map):
# Re-map headers to nums
  header_enum = create_header_enum(header_map)
  
# TODO figure out how to use error checking bools too
  people_list = list()
  for name in names:
    if name in table:
      person = list()
      person.append(name)
      person.append(table[name][header_enum['Email']][0])
      person.append(title_symbol(table[name][header_enum['Title']][0]))
      person.append(shorten_phone(table[name][header_enum['Phone']][0]))
      [room, building] = split_location(table[name][header_enum['Location']][0])
      person.append(room)
      person.append(building)
      people_list.append(person)
  return people_list
