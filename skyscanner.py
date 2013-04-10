#!/usr/bin/python
import json
import urllib2
import re
import sys

def main(argv):

   autosuggest_url = "http://www.skyscanner.net/dataservices/geo/v1.0/autosuggest/uk/en/"
   skyscanner_url = "http://www.skyscanner.net/flights/"
   # e. g. http://www.skyscanner.net/flights/vno/edi/130419/
   routedata_url = "http://www.skyscanner.net/dataservices/routedate/v2.0/"
   input_from = argv[0]
   input_to = argv[1]
   date = argv[2].replace("/", "")

   # getting codes using AutoSuggest
   code_from = json.load(urllib2.urlopen(autosuggest_url + input_from))[0]['PlaceId']
   code_to = json.load(urllib2.urlopen(autosuggest_url + input_to))[0]['PlaceId']
   response = urllib2.urlopen(skyscanner_url + code_from + "/" + code_to + "/" + date)
   html = response.read()
   
   regex = ur'"SessionKey":"(.+?)"'
   # e. g. "SessionKey":"a00765d2-7a39-404b-86c0-e8d79cc5f7e3"
   sessionkey = re.findall(regex, html)[0]

   response = urllib2.urlopen(routedata_url + sessionkey)
   html = response.read()
   data = json.loads(html)
   query = data['Query']
   stations = data['Stations']
   quotes = data['Quotes']
   carriers = data['Carriers']
   cheapest_price = data['Stats']['ItineraryStats']['Total']['CheapestPrice']

   print "Results for flight from", query['OriginPlace'], "to", query['DestinationPlace']
   print "Outbound date:", re.split('T', query['OutboundDate'])[0]
   print "Cheapest Journey:", cheapest_price, "GBP"

   for leg in data['OutboundItineraryLegs']:
      lowest_price = get_lowest_price(leg['PricingOptions'], quotes)
      depart_time = leg['DepartureDateTime'].replace("T", " ")
      arrive_time = leg['ArrivalDateTime'].replace("T", " ")
      duration = leg['Duration']
      carrier_names = get_carrier_names(leg['MarketingCarrierIds'], carriers)[1]
   
      print "\n\tPrice:", lowest_price, "GBP"
      print "\tDeparting:", depart_time
      print "\tArriving:", arrive_time
      print "\tDuration:", duration/60, "h", duration%60, "min"
      print "\tCarriers:", carrier_names

      print "\t# of stops: ", leg['StopsCount']
      stop_ids = leg.get('StopIds', [])
      for stop_id in stop_ids:
         print "\t\t", get_station_name(stop_id, stations)
      
def get_station_name(station_id, stations):
   for station in stations:
      if station['Id'] == station_id:
         return station['Name']
   return ""

def get_lowest_price(pricing, quotes):
   prices = []
   for price in pricing:
      prices.append(get_quote_price(price['QuoteIds'], quotes))
   return min(prices)

def get_quote_price(quote_ids, quotes):
   price = 0;
   for quote_id in quote_ids:
      for quote in quotes:
         if quote['Id'] == quote_id:
            price += quote['Price']
   return price

def get_carrier_names(carrier_ids, carriers):
   """returns tuple (list, string)"""
   carrier_names = []
   carrier_names_string = ""
   for carrier_id in carrier_ids:
      carrierName = get_carrier_name(carrier_id, carriers)
      carrier_names.append(carrierName)
      carrier_names_string += carrierName + ", "
   return (carrier_names, carrier_names_string[:-2])

def get_carrier_name(carrier_id, carriers):
   for carrier in carriers:
      if carrier['Id'] == carrier_id:
         return carrier['Name']
   return ""
   
if __name__ == "__main__":
   if len(sys.argv) == 4:
      main(sys.argv[1:])
   elif len(sys.argv) == 5:
      main(sys.argv[1:])
   else:
      print "Enter arguments in this way:"
      print "python skyscanner.py {from} {to} {departure date (yy/mm/dd)} [return date]"
      print "e. g. python skyscanner.py Edinburgh Paris 13/07/21"
      sys.exit()
