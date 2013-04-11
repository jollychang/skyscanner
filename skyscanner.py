#!/usr/bin/python

"""The script obtains prices and flight information for a given
   input (departure, arrival airports and date), outputs this
   data to the console and writes it to a csv file."""

__author__ = "Ingvaras Merkys"

import json
import urllib2
import re
import sys
import time

# Global vars:
AUTOSUGGEST_URL = "http://www.skyscanner.net/dataservices/geo/v1.0/autosuggest/uk/en/"
# e. g. http://www.skyscanner.net/dataservices/geo/v1.0/autosuggest/uk/en/edinb
SKYSCANNER_URL = "http://www.skyscanner.net/flights/"
# e. g. http://www.skyscanner.net/flights/vno/edi/130419
ROUTEDATA_URL = "http://www.skyscanner.net/dataservices/routedate/v2.0/"
# e. g. http://www.skyscanner.net/dataservices/routedate/v2.0/a00765d2-7a39-404b-86c0-e8d79cc5f7e3
SUGGESTIONS_URL = "http://www.skyscanner.net/db.ashx?ucy=UK&lid=en&ccy=GBP"
# e. g. http://www.skyscanner.net/db.ashx?ucy=UK&lid=en&ccy=GBP&fp=KAUN&tp=EDIN&dd=20130410

def main(argv):

   input_from = argv[0].replace(" ", "%20").replace("\"", "")
   input_to = argv[1].replace(" ", "%20").replace("\"", "")
   date = argv[2].replace("/", "")

   place_id_from, place_id_to, name_from, name_to = get_codes(input_from, input_to)

#  testjuly = map (lambda x: len(x) == 1 and '13070'+x or '1307'+x, [ str(i+1) for i in range(31) ])
#  for date in testjuly:
   session_key = get_session_key(place_id_from, place_id_to, date)

   for attempt in range(3):
      # if script is run repeatedly sometimes an empty html is returned
      try:
         response = urllib2.urlopen(ROUTEDATA_URL + session_key)
         html = response.read()
         data = json.loads(html)
      except ValueError:
         f = open("error.log", "a")
         f.write(ROUTEDATA_URL + session_key + "\n")
         f.write("Returned:\n" + html + "\n")
         time.sleep(1)
      else:
         break
   else:
      sys.exit(1)

   query = data['Query']

   if data['Stats']['OutboundLegStats']['TotalCount'] == 0:
      print "No flights found from", name_from, "to", name_to
      show_suggestions(query['OriginPlace'], query['DestinationPlace'], date)
      sys.exit(2)

   stations = data['Stations']
   quotes = data['Quotes']
   carriers = data['Carriers']
   cheapest_price = data['Stats']['ItineraryStats']['Total']['CheapestPrice']

   print "Results for flight from", name_from, "to", name_to
   print "Outbound date:", re.split('T', query['OutboundDate'])[0]
   print "Cheapest Journey:", cheapest_price, "RMB"

   # f = open(place_id_from + '-' + place_id_to + '-' + date + '.csv','w')

   # for leg in data['OutboundItineraryLegs']:
   #    leg_price = get_leg_price(leg['PricingOptions'], quotes)
   #    depart_time = leg['DepartureDateTime'].replace("T", " ")
   #    arrive_time = leg['ArrivalDateTime'].replace("T", " ")
   #    duration = leg['Duration']
   #    carrier_names = get_carrier_names(leg['MarketingCarrierIds'], carriers)[1]

   #    print "\n\tPrice:", leg_price, "GBP"
   #    print "\tDeparting:", depart_time
   #    print "\tArriving:", arrive_time
   #    print "\tDuration:", duration/60, "h", duration%60, "min"
   #    print "\tCarriers:", carrier_names
   #    print "\t# of stops: ", leg['StopsCount']

   #    stop_ids = leg.get('StopIds', [])
   #    stop_ids_string = ", ".join([ get_station_name(stop_id, stations) for stop_id in stop_ids ])
   #    print "\t\t", stop_ids_string

   #    row = str(leg_price) + "\t" + depart_time + "\t" + arrive_time + "\t" + str(duration) + "\t" + carrier_names + "\t" + stop_ids_string

   #    f.write(row + "\n")

# Functions

def get_codes(input_from, input_to):
   """Returns place id codes and names, e. g. ("EDI", "KUN", "Edinburgh", "Kaunas")"""
   try:
      i = 0
      autosuggest_json_from = json.load(urllib2.urlopen(AUTOSUGGEST_URL + input_from))
      if len(autosuggest_json_from[0]['PlaceId']) == 4:
      # for cases where the first result is abstract (e. g. Glasgow (Any))
         i = 1
      place_id_from = autosuggest_json_from[i]['PlaceId']
      name_from = autosuggest_json_from[i]['PlaceName']

      j = 0
      autosuggest_json_to = json.load(urllib2.urlopen(AUTOSUGGEST_URL + input_to))
      if len(autosuggest_json_to[0]['PlaceId']) == 4:
         j = 1
      place_id_to = autosuggest_json_to[j]['PlaceId']
      name_to = autosuggest_json_to[j]['PlaceName']
   except IndexError:
      print "No code found for:"
      print input_from, "AND/OR", input_to
      sys.exit(3)
   return (place_id_from, place_id_to, name_from, name_to)

def get_session_key(place_id_from, place_id_to, date):
   """Returns a session key for a given query, on failure exits
      NB. distant or past dates cause failures"""
   response = urllib2.urlopen(SKYSCANNER_URL + place_id_from + "/" + place_id_to + "/" + date)
   html = response.read()
   regex = ur'"SessionKey":"(.+?)"'
   # e. g. "SessionKey":"a00765d2-7a39-404b-86c0-e8d79cc5f7e3"
   try:
      session_key = re.findall(regex, html)[0]
   except IndexError:
      print "No data found for this date"
      sys.exit(4)
   return session_key

def show_suggestions(from_id, to_id, date):
   """Prints alternative departure airports"""
   suggest_places_string = ""
   suggestions_json = json.load(urllib2.urlopen(SUGGESTIONS_URL + "&fp=" + from_id + "&tp=" + to_id + "&dd=20" + date))
   try:
      suggest_places = suggestions_json['rs']
      for place in suggest_places:
         if place['fpid'] != from_id:
            suggest_places_string += place['fan'] + ", "
      if suggest_places_string[:-2] != "":
         print "Try airports: ", suggest_places_string[:-2]
   except (KeyError, IndexError):
      print "Suggestions unavailable"

def get_station_name(station_id, stations):
   """Returns the name of the (intermediate) station,
      e. g. "London Heathrow" """
   for station in stations:
      if station['Id'] == station_id:
         return station['Name']
   return ""

def get_leg_price(pricing, quotes):
   """Returns lowest leg price"""
   prices = []
   for price in pricing:
      prices.append(get_quote_price(price['QuoteIds'], quotes))
   return min(prices)

def get_quote_price(quote_ids, quotes):
   """Finds quotes by quote id and returns their price sum"""
   price = 0;
   for quote_id in quote_ids:
      for quote in quotes:
         if quote['Id'] == quote_id:
            price += quote['Price']
   return price

def get_carrier_names(carrier_ids, carriers):
   """Returns a tuple (list, string) with carrier names
      e.g. (["airBaltic", "KLM"], "airBaltic, KLM")"""
   carrier_names = []
   carrier_names_string = ""
   for carrier_id in carrier_ids:
      carrierName = get_carrier_name(carrier_id, carriers)
      carrier_names.append(carrierName)
      carrier_names_string += carrierName + ", "
   return (carrier_names, carrier_names_string[:-2])

def get_carrier_name(carrier_id, carriers):
   """Returns carrier name by id"""
   for carrier in carriers:
      if carrier['Id'] == carrier_id:
         return carrier['Name']
   return ""
   
if __name__ == "__main__":
   if len(sys.argv) == 4:
      main(sys.argv[1:])
   else:
      print "Enter arguments in this way:\n"
      print "python skyscanner.py {departure airport} {arrival airport} {departure date (yy/mm/dd)}\n\n"
      print "e. g. python skyscanner.py \"glasgow prestwick\" kaunas 13/07/21\n"
      sys.exit()
