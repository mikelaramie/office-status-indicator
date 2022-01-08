import json
import os
import time

import pytz

from datetime import datetime, timedelta, timezone

from calendar_setup import get_calendar_service
import rainbowhat as rh

# Global variables
OFFICE_STATUS_HOUR_START = int(os.getenv("OFFICE_STATUS_HOUR_START", 8))
OFFICE_STATUS_HOUR_END = int(os.getenv("OFFICE_STATUS_HOUR_END", 18))
OFFICE_STATUS_TZ = os.getenv("OFFICE_STATUS_TZ", "America/New_York")
OFFICE_STATUS_WARNING_MINUTES = int(os.getenv("OFFICE_STATUS_WARNING_MINUTES", 10))
OFFICE_STATUS_WEEK_START = int(os.getenv("OFFICE_STATUS_WEEK_START", 0))
OFFICE_STATUS_WEEK_END = int(os.getenv("OFFICE_STATUS_WEEK_END", 4))

def get_events():

    # Get the calendar service
    service = get_calendar_service()

    # Call the Calendar API
    now = datetime.utcnow().isoformat() + 'Z'

    print('Getting list of calendar events...')

    events_result = service.events().list(calendarId='primary',
                                          timeMin=now,
                                          maxResults=10,
                                          singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])
    return events

def display_message(message):
    rh.display.print_str(message)
    rh.display.show()

def set_busy():
    set_color(255, 0, 0)
    display_message("BUSY")

def set_warn():
    set_color(255, 144, 0)
    display_message("SOON")

def set_open():
    set_color(0, 255, 0)
    display_message("OPEN")

def set_off():
    #Show Time/Temp?
    #set_color(0, 0, 0)
    #display_message("    ")
    set_clear()

def set_error():
    set_color(0,0,255)
    display_message(" err")

def set_clear():
    rh.display.clear()
    rh.display.show()
    rh.rainbow.clear()
    rh.rainbow.show()
    rh.lights.red.off()
    rh.lights.green.off()
    rh.lights.blue.off()

def set_color(r, g, b):
    rh.rainbow.set_all(r, g, b, brightness=0.1)
    rh.rainbow.show()

@rh.touch.A.press()
def press_a(channel):
    set_busy()

@rh.touch.B.press()
def press_b(channel):
    set_clear()

@rh.touch.C.press()
def press_c(channel):
    set_open()

def read_datetime(timestamp):
    return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S%z")


def main():
    
    current_time = datetime.now(timezone.utc)

    # Convert to the desired timezone
    pytz_timezone = pytz.timezone(OFFICE_STATUS_TZ)
    current_tz_time = current_time.astimezone(pytz_timezone)

    print(f"Current Time: {current_tz_time}")

    try:
        # Refresh calendar events
        events = get_events()
    except Exception:
        set_error()
        print("Failed to fetch calendar events from Google.")
        return

    # For each event
    for event in events:

        if event.get("transparency", "") == "transparent":
            continue

        # Get the datetime for the start/end of the event
        start_time = read_datetime(event["start"]["dateTime"])
        end_time = read_datetime(event["end"]["dateTime"])

        print(f"Next Calendar Event: {start_time}")

        if start_time < current_time < end_time:
            # In a Meeting
            set_busy()
            return
        elif start_time < current_time + timedelta(minutes=OFFICE_STATUS_WARNING_MINUTES):
            # Meeting Soon
            set_warn()
            return
        else:
            break

    # If it's a weekday
    if OFFICE_STATUS_WEEK_START <= current_tz_time.weekday() <= OFFICE_STATUS_WEEK_END:

        # If we're during working hours
        if OFFICE_STATUS_HOUR_START <= current_tz_time.hour < OFFICE_STATUS_HOUR_END:

            # No current/upcoming meetings
            set_open()
            return

    print(f"Not working hours...")
    set_off()
    return


if __name__ == '__main__':

    try:
        while True:
            main()
            time.sleep(60)
    
    except:
        set_clear()
