# -*- coding: utf-8 -*-
#! /usr/bin/python
import os
import time
from pync import Notifier
import sys 
reload(sys) 
sys.setdefaultencoding('utf8') 
import skyscanner

def get_come_flights():
    city_from = ['CAN', 'PEK', 'HKG']
    city_to = ['BUD', 'VIE', 'ZAG']
    arrive_date = ['13/09/17', '13/09/18']
    flights = []
    for f in city_from:
        for t in city_to:
            for d in arrive_date:
                if d =='13/09/17' and f =='HKG':
                    continue
                flights.append([f,t,d])
    return flights

def get_back_flight():
    city_from = ['BUD', 'VIE', 'ZAG']
    city_to =['PEK']
    arrive_date = ['13/10/05', '13/10/06', '13/09/07']    
    flights = []
    for f in city_from:
        for t in city_to:
            for d in arrive_date:
                flights.append([f,t,d])
    return flights

def notify_cheapset_price(come_flights, back_flights, less_than_price=7000):
    back_flights_dict = {}
    for come_flight in come_flights:
        come_cheapest_price = skyscanner.main(come_flight)
        if come_cheapest_price > 0:
            for back_flight in back_flights:
                back_flight_string = "-".join(back_flight)
                #don't need request two times for the same results
                if back_flight_string not in back_flights_dict.keys():
                    back_cheapest_price = skyscanner.main(back_flight)
                    back_flights_dict[back_flight_string] = back_cheapest_price
                else:
                    back_cheapest_price = back_flights_dict[back_flight_string]

                totol_price  = come_cheapest_price + back_cheapest_price
                if back_cheapest_price > 0 and totol_price < less_than_price:
                    come_flight_string = "-".join(come_flight)
                    Notifier.notify("COME: %s \n BACK: %s" % (come_flight_string, back_flight_string), title="%s" % totol_price)


if __name__=='__main__':

    come_flights = get_come_flights()
    back_flights = get_back_flight()
    notify_cheapset_price(come_flights, back_flights)

