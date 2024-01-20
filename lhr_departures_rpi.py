import sys
sys.path.append('/root/python-spotled')

import os
import time
from pprint import pprint
from pyflightdata import FlightData

#import tkinter
#root =tkinter.Tk()
#root.configure(background="black")
#l=tkinter.Label()
#l.pack()
#l.configure(background="black",font=("Fixed",40),foreground="red")

import spotled
import re


REFRESH_PERIOD_SECONDS = 10
ARRIVAL_WARNING_TIME_SECONDS = 70
DISPLAY_PERIOD_SECONDS = 30
AIRPORT_ID = "LHR"
#AIRPORT_ID = "LAX"
#AIRPORT_ID = "LCY"


def display_flight_on_led_matrix(flight_id, arrdep, fromto, delay):
    global display_blanked
    os.system('rfkill block wifi')
    if display_blanked:
        os.system('uhubctl -l 2 -a 1 > /dev/null')
        time.sleep(1)
    try:
        retstr = display_flight_on_led_matrix_alt_6(flight_id, arrdep, fromto, delay)
        display_blanked = False
    except:
        retstr = "ERROR"
    os.system('rfkill unblock wifi')
    return retstr

# Display in single line format BA1212 VIE A+MMM using 6x12 font (Note: can only display delays up to 16.65 hours)"
def display_flight_on_led_matrix_alt_1(flight_id, arrdep, fromto, delay):
    textcolors = {'WHITE' : '%1', 'RED' : '%2', 'GREEN': '%3', 'BLUE' : '%4'}
    delay_minutes = abs((delay // 60))

    if(delay == 0):
        timestr = "000"
        timecolor = textcolors['GREEN']
    elif (delay > 0):
        timestr = "+{}".format(int(delay_minutes))
        timecolor = textcolors['RED']
    else:
        timestr = "-{}".format(int(delay_minutes))
        timecolor = textcolors['GREEN']

    # prevent the delay display from overflowing by limiting it to a max value
    if(delay_minutes > 999):
        timestr = '>16h'

    if(arrdep == 'ARR'):
        adstr = "A"
    else:
        adstr = "D"

    spotled_sender = spotled.LedConnection('28:BD:4E:5D:5A:A0')
    flightstr = "%4{} {} {}{}{}".format(flight_id, fromto, adstr,timecolor, timestr)
    spotled_sender.set_text_bd28(flightstr,font="6x12",line_height=16)
    spotled_sender.disconnect()
    return flightstr

# Display in single line format BA1212>VIE +H:MM using 6x12 font (Note: can only display delays up to 9 hours)"
def display_flight_on_led_matrix_alt_2(flight_id, arrdep, fromto, delay):
    textcolors = {'WHITE' : '%1', 'RED' : '%2', 'GREEN': '%3', 'BLUE' : '%4'}
    delay_minutes = abs((delay // 60))
    delayhr = abs(delay / 3600)

    if(delay == 0):
        timestr = " 0:00"
        timecolor = textcolors['GREEN']
    elif (delay > 0):
        timestr = "+{}:{}".format(int(delayhr),int(delay_minutes)%60)
        timecolor = textcolors['RED']
    else:
        timestr = "-{}:{}".format(int(delayhr),int(delay_minutes)%60)
        timecolor = textcolors['GREEN']

    # prevent the delay display from overflowing by limiting it to a max value
    # Note: display as a delay as assumed that a flight will never be > 1 hr early
    if(delayhr > 9):
        timestr = '>9h'

    if(arrdep == 'ARR'):
        adstr = "<"
    else:
        adstr = ">"

    spotled_sender = spotled.LedConnection('28:BD:4E:5D:5A:A0')
    flightstr = "%4{}{}{} {}{}".format(flight_id, adstr, fromto, timecolor, timestr)
    spotled_sender.set_text_bd28(flightstr,font="6x12",line_height=16)
    spotled_sender.disconnect()
    return flightstr

# Display in single line format BA1212 VIE D+XXy using 6x12 font, where XX is time and y is unit (h or m)"
def display_flight_on_led_matrix_alt_3(flight_id, arrdep, fromto, delay):
    textcolors = {'WHITE' : '%1', 'RED' : '%2', 'GREEN': '%3', 'BLUE' : '%4'}
    delay_minutes = abs((delay // 60))
    delayhr = abs(delay / 3600)

    if (delayhr >= 1):
        if (delay > 0):
            timestr = "+{}h".format(int(delayhr))
            timecolor = textcolors['RED']
        else:
            timecolor = textcolors['GREEN']
            timestr = "-{}h".format(int(delayhr))
    else:
        if (delay == 0):
            timestr = " 0m"
            timecolor = textcolors['GREEN']
        elif (delay > 0):
            timestr = "+{}m".format(int(delay_minutes))
            timecolor = textcolors['RED']
        else:
            timestr = "-{}m".format(int(delay_minutes)%60)
            timecolor = textcolors['GREEN']

    if(arrdep == 'ARR'):
        adstr = "<"
    else:
        adstr = ">"

    spotled_sender = spotled.LedConnection('28:BD:4E:5D:5A:A0')
    flightstr = "%4{}{}{} {}{}".format(flight_id, adstr, fromto, timecolor, timestr)
    spotled_sender.set_text_bd28(flightstr,font="6x12",line_height=16)
    spotled_sender.disconnect()
    return flightstr

# Display in two line format {BA1212 VIE} {DEP +HH:MM} using 5x7 font"
def display_flight_on_led_matrix_alt_4(flight_id, arrdep, fromto, delay):
    textcolors = {'WHITE' : '%1', 'RED' : '%2', 'GREEN': '%3', 'BLUE' : '%4'}
    if(delay == 0):
        timestr = "ONTIME"
        timecolor = textcolors['GREEN']
    elif (delay > 0):
        timestr = "+{}".format(time.strftime("%H:%M", time.gmtime(delay)))
        timecolor = textcolors['RED']
    else:
        timestr = "-{}".format(time.strftime("%H:%M", time.gmtime(-delay)))
        timecolor = textcolors['GREEN']

    if(arrdep == 'ARR'):
        adstr = "ARR"
    else:
        adstr = "DEP"

    flightstr="%4{} {}\n{}.      {}{}".format(flight_id, fromto, adstr, timecolor, timestr)
    try:
        spotled_sender = spotled.LedConnection('28:BD:4E:5D:5A:A0')
        spotled_sender.set_text_bd28(flightstr,font="5x7",line_height=8)
        spotled_sender.disconnect()
    except:
        pass

    return flightstr

# Display in single line format BA1212 VIE D+XXy using 6x12 font, where XX is time and y is unit (h or m)"
def display_flight_on_led_matrix_alt_5(flight_id, arrdep, fromto, delay):
    textcolors = {'WHITE' : '%1', 'RED' : '%2', 'GREEN': '%3', 'BLUE' : '%4'}
    delay_minutes = abs((delay // 60))
    delayhr = abs(delay / 3600)

    if (delayhr >= 1):
        if (delay > 0):
            timestr = "+{}h".format(int(delayhr))
            timecolor = textcolors['RED']
        else:
            timecolor = textcolors['GREEN']
            timestr = "-{}h".format(int(delayhr))
    else:
        if (delay == 0):
            timestr = " 0m"
            timecolor = textcolors['GREEN']
        elif (delay > 0):
            timestr = "+{}m".format(int(delay_minutes))
            timecolor = textcolors['RED']
        else:
            timestr = "-{}m".format(int(delay_minutes)%60)
            timecolor = textcolors['GREEN']

    if(arrdep == 'ARR'):
        adstr = "A"
    else:
        adstr = "D"

    spotled_sender = spotled.LedConnection('28:BD:4E:5D:5A:A0')
    flightstr = "%4{} {} {}{}{}".format(flight_id, fromto, adstr, timecolor, timestr)
    spotled_sender.set_text_bd28(flightstr,font="6x12",line_height=16)
    spotled_sender.disconnect()
    return flightstr

# Display in single line format BA1212 VIE D.+H:MM using modified 6x12 font (Note: can only display delays up to 9 hours)"
def display_flight_on_led_matrix_alt_6(flight_id, arrdep, fromto, delay):
    textcolors = {'WHITE' : '%1', 'RED' : '%2', 'GREEN': '%3', 'BLUE' : '%4'}
    delay_minutes = abs((delay // 60))
    delayhr = abs(delay / 3600)

    if(delay == 0):
        timestr = " 0:00"
        timecolor = textcolors['GREEN']
    elif (delay > 0):
        timestr = "+{}:{:02d}".format(int(delayhr),int(delay_minutes)%60)
        timecolor = textcolors['RED']
    else:
        timestr = "-{}:{:02d}".format(int(delayhr),int(delay_minutes)%60)
        timecolor = textcolors['GREEN']

    # prevent the delay display from overflowing by limiting it to a max value
    # Note: display as a delay as assumed that a flight will never be > 1 hr early
    if(delayhr > 9):
        timestr = '>9h'

    if(arrdep == 'ARR'):
        adstr = "A."
    else:
        adstr = "D."

    if(len(flight_id)<6):
        pad = ' '*(6-len(flight_id))
    else:
        pad = ''

    spotled_sender = spotled.LedConnection('28:BD:4E:5D:5A:A0')
    flightstr = "%4{} {} {}{}{}{}".format(flight_id, fromto, pad, adstr, timecolor, timestr)
    spotled_sender.set_text_bd28(flightstr,font="6x12mod",line_height=16)
    spotled_sender.disconnect()
    return flightstr


fd = FlightData()


departures_d1=fd.get_airport_departures(AIRPORT_ID, earlier_data=True)
arrivals_d1=fd.get_airport_arrivals(AIRPORT_ID, earlier_data=False)
announced_arrivals=[]
last_display_time = time.time()
display_blanked = False

logfnm = "log_{}_{}.dat".format(AIRPORT_ID, int(time.time()))
logfl = open(logfnm,'w')

while(True):
    # get current time
    t = time.time()

    #print("******************************************************************************************************")
    #print("New cycle t={}".format(t))
    #print("******************************************************************************************************")

    departures=fd.get_airport_departures(AIRPORT_ID, earlier_data=True)
    #arrivals=fd.get_airport_arrivals(AIRPORT_ID, earlier_data=False)
    arrivals=fd.get_airport_arrivals(AIRPORT_ID, earlier_data=True)

    # Departures detected by transition of departure time from 'None' to valid value
    for dep in departures:
        stime = dep['flight']['time']['scheduled']['departure']
        dtime = dep['flight']['time']['real']['departure']
        status_text = dep['flight']['status']['text']
        flight_id = dep['flight']['identification']['number']['default']

        # Ignore any flights not scheduled for today
        if (time.gmtime(float(stime)).tm_mday != time.gmtime(t).tm_mday):
            continue

        # Ignore any flights that departed more than 1 hour ago
        if (dtime != 'None' and (t-float(dtime)) >= 3600):
            continue

        # Ignore any flights scheduled for more than 1 hour in the future
        if(stime != 'None' and float(stime) > (t + 3600)):
            continue

        dep_d1 = [departures_d1[x] for x in range(len(departures_d1)) if departures_d1[x]['flight']['identification']['number']['default'] == flight_id and time.gmtime(float(departures_d1[x]['flight']['time']['scheduled']['departure'])).tm_mday == time.gmtime(t).tm_mday]

        sstr = 'None' if stime == 'None' else time.strftime("%D:%H:%M", time.gmtime(int(stime)))
        dstr = 'None' if dtime == 'None' else time.strftime("%D:%H:%M", time.gmtime(int(dtime)))
        #print ("Candidate departure {} Scheduled {} actual {}".format(flight_id,sstr,dstr))

        if len(dep_d1) > 0 and dep_d1[0]['flight']['time']['real']['departure'] == 'None' and dtime != 'None' and float(dtime) <= t:
            #print("{} departure time {}".format(flight_id, time.strftime("%H:%M", time.localtime(float(dtime)))))
            dest_id = dep['flight']['airport']['destination']['code']['iata']
            delay = int(dtime)-int(stime)
            flightstr=display_flight_on_led_matrix(flight_id=flight_id, arrdep='DEP', fromto=dest_id, delay=delay)
            #l.configure(text=re.sub('%[0-9]','',flightstr))
            print ("DEPARTURE {:6s} Scheduled {}, Status: {}".format(dep['flight']['identification']['number']['default'], time.strftime("%H:%M", time.localtime(float(stime))),status_text))
            last_display_time = t;
            #print("{}".format(t)+" "+re.sub('%[0-9]','',flightstr),file=logfl)
            print ("{}".format(int(t))+" DEPARTURE {:6s} Scheduled {}, Status: {}".format(dep['flight']['identification']['number']['default'], time.strftime("%H:%M", time.localtime(float(stime))),status_text),file=logfl)
            logfl.flush()
            break
        #else:
            ##some debug on why it was not displayed
            #print("not displayed")
            #if(dep_d1[0]['flight']['time']['real']['departure'] != 'None'):
                #print("previous departure was not None")
            #if(dtime=='None'):
                #print("no departure time")
            #else:
                #if(float(dtime)>t):
                    #print("reported actual departure time is in the future")
                #if(float(dtime) < (t-3600)):
                    #print("departure shown as > 1hour ago")

    departures_d1 = departures

    # Only display arrival if a departure has not been displayed this time around
    if last_display_time != t:
        # Arrivals detected by latest ETA within a warning time
        for arr in arrivals:
            stime = arr['flight']['time']['scheduled']['arrival']
            etime = arr['flight']['time']['other']['eta']
            atime = arr['flight']['time']['real']['arrival']
            status_text = arr['flight']['status']['text']
            flight_id = arr['flight']['identification']['number']['default']

            # Ignore any flights not scheduled for today
            if (time.gmtime(float(stime)).tm_mday != time.gmtime(t).tm_mday):
                continue

            # Ignore any flights that arrived more than 10min ago
            if (atime != 'None' and (t-float(atime)) >= 600):
                continue

            # Ignore any flights scheduled for more than 1 hour in the future
            if(stime != 'None' and float(stime) > (t + 3600)):
                continue

            sstr = 'None' if stime == 'None' else time.strftime("%H:%M", time.gmtime(int(stime)))
            estr = 'None' if etime == 'None' else time.strftime("%H:%M", time.gmtime(int(etime)))
            astr = 'None' if atime == 'None' else time.strftime("%H:%M", time.gmtime(int(atime)))
            #print ("Candidate arrival {} Scheduled {} est {} actual {}".format(flight_id,sstr,estr,astr))

            if etime != 'None' and float(etime) <= (t + ARRIVAL_WARNING_TIME_SECONDS) and flight_id not in announced_arrivals:
                announced_arrivals.append(flight_id)
                announced_arrivals=announced_arrivals[-1000:] # prevent unbounded growth
                from_id = arr['flight']['airport']['origin']['code']['iata']
                delay = int(etime)-int(stime)

                flightstr=display_flight_on_led_matrix(flight_id=flight_id, arrdep='ARR', fromto=from_id, delay=delay)

                #l.configure(text=re.sub('%[0-9]','',flightstr))
                print ("ARRIVAL   {:6s} Scheduled {} {}".format(arr['flight']['identification']['number']['default'], time.strftime("%H:%M", time.localtime(float(stime))),status_text))
                last_display_time = t;
                print ("{}".format(int(t))+" ARRIVAL {:6s} Scheduled {} {}".format(arr['flight']['identification']['number']['default'], time.strftime("%H:%M", time.localtime(float(stime))),status_text),file=logfl)
                #print("{}".format(int(t))+" "+re.sub('%[0-9]','',flightstr),file=logfl)
                logfl.flush()
                break
            #else:
                # some debug about why it was not displayed
                #print("arrival not displayed")
                #if(etime == 'None'):
                    #print("no estimated arrival time")
                #elif(float(etime) > (t + ARRIVAL_WARNING_TIME_SECONDS)):
                    #print("estimated arrival is > {} seconds in the future".format(ARRIVAL_WARNING_TIME_SECONDS))
                #elif(flight_id in announced_arrivals):
                    #print("already announced")

    # clear the display if displayed flight past a given age
    if(((t - last_display_time) > DISPLAY_PERIOD_SECONDS) and not display_blanked):
        spotled_sender = spotled.LedConnection('28:BD:4E:5D:5A:A0')
        spotled_sender.set_text_bd28("")
        spotled_sender.disconnect()
        display_blanked = True
        time.sleep(4)
        os.system('uhubctl -l 2 -a 0 > /dev/null')
        #time.sleep(1)
        #os.system('uhubctl -l 2 -a 1 > /dev/null')
        last_display_time = t

    # Update the TK window and sleep until the next refresh period
    #root.update()
    time.sleep(REFRESH_PERIOD_SECONDS)


