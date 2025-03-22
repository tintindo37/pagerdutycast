import os
import argparse
import sys
import time
import urllib.parse
import requests
import pychromecast
from datetime import datetime, timezone, timedelta
from dateutil import parser as date_parser
from pydub import AudioSegment
from io import BytesIO
from common import add_log_arguments, configure_logging
import logging
import pytz

#env from docker 
env1 = os.getenv("IP")
env2 = os.getenv("NAME")
env3 = os.getenv("Pagerapi")
env4 = os.getenv("User")
env5 = os.getenv("Time")
env6 = os.getenv("Timezone")

if not env1 or not env2 or not env3 or not env4 or not env6:
    raise ValueError("Error: One or more required environment variables are missing!")
    sys.exit(0)
else: #conf for docker
    CAST_IP = env1 # IP of Google Home Mini or any Chromecast-enabled device
    CAST_NAME = env2  # Name of Google Home Mini or any Chromecast-enabled device
    PAGERDUTY_API_KEY = env3 # pg api
    USER_ID = env4 #pagerduty user
    CHECK_INTERVAL = int(env5)  # seconds between checks
    target_timezone = pytz.timezone(f"{env6}") # timezone
#Configuration
BASE_TTS_URL = "http://translate.google.com/translate_tts?ie=UTF-8&total=1&idx=0&textlen=32&client=tw-ob&q={}&tl=En-gb" #tts provider 
Ring_Url = "https://cdn.pixabay.com/download/audio/2025/01/13/audio_902fc3eeb8.mp3?filename=elevator-chimenotification-ding-recreation-287560.mp3"
parser = argparse.ArgumentParser(description="PagerDuty to TTS on Chromecast")
add_log_arguments(parser)
parser.add_argument("--cast", help='Name of cast device (default: "%s")' % CAST_NAME, default=CAST_NAME)
parser.add_argument("--test", help="Trigger test alarm", action="store_true")
args = parser.parse_args()

configure_logging(args)

#loging
def log_message(message):
    logging.info(message) #use logging.info to log information so docker will see

# Configure logging to output to stdout
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S %A')
# Find Chromecast
chromecasts, browser = pychromecast.get_listed_chromecasts(friendly_names=[args.cast], known_hosts=[CAST_IP])
if not chromecasts:
    log_message(f'No chromecast with name "{args.cast}" discovered')
    sys.exit(1)

cast = chromecasts[0]
cast.wait()

# Global variables for on-call time
startcall = None
finishcall = None

# Google translate tts cast
def speak_text(text):
    tts=limit_string_length(text) #limit charakter to google transalte tts 
    encoded_text = urllib.parse.quote(tts)
    media_url = BASE_TTS_URL.format(encoded_text)
    log_message(f'Speaking: "{tts}"')
    cast.media_controller.play_media(media_url, "audio/mp3")
    player_state = None
    t = 30.0
    has_played = False
    response = requests.get(media_url)
    audio = AudioSegment.from_file(BytesIO(response.content), format="mp3")
    length_in_seconds = len(audio) / 1000
    while True:
        try:
            if player_state != cast.media_controller.status.player_state:
                player_state = cast.media_controller.status.player_state
                log_message(f"Player state:, {player_state}")
            if player_state == "PLAYING":
                has_played = True
                time.sleep(length_in_seconds)
                break
            if cast.socket_client.is_connected and has_played and player_state != "PLAYING":
                has_played = False
                cast.media_controller.play_media(media_url, "audio/mp3")
            time.sleep(0.1)
            t = t - 0.1
        except KeyboardInterrupt:
            break
# Ring noise cast
def ring(URL_Media):
    log_message(f'Ringing: "{URL_Media}"')
    cast.media_controller.play_media(URL_Media, "audio/mp3")  
    player_state = None
    t = 30.0
    has_played = False
    response = requests.get(URL_Media)
    audio = AudioSegment.from_file(BytesIO(response.content), format="mp3")
    length_in_seconds = len(audio) / 1000
    while True:
        try:
            if player_state != cast.media_controller.status.player_state:
                player_state = cast.media_controller.status.player_state
                log_message(f"Player state:, {player_state}")
            if player_state == "PLAYING":
                has_played = True
                time.sleep(length_in_seconds)
                break
            if cast.socket_client.is_connected and has_played and player_state != "PLAYING":
                has_played = False
                cast.media_controller.play_media(URL_Media, "audio/mp3")  
            time.sleep(0.1)
            t = t - 0.1
        except KeyboardInterrupt:
            break

# google translate api limit
def limit_string_length(input_string, max_length=200):
  if len(input_string) > max_length:
    return input_string[:max_length]  # Truncate the string
  else:
    return input_string
# Get Pagerduty api incidents
def get_pagerduty_incidents():
    url = "https://api.pagerduty.com/incidents"
    headers = {
        "Authorization": f"Token token={PAGERDUTY_API_KEY}",
        "Accept": "application/json"
    }
    params = {"statuses[]": "triggered", "user_ids[]": USER_ID}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get("incidents", [])
    else:
        log_message(f"Error fetching incidents: {response.status_code} {response.text}")
        return []
# Get Pagerduty api oncall
def oncall():
    global startcall, finishcall  # Ensure we're modifying global variables
    URL = "https://api.pagerduty.com/oncalls"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00Z")
    tomorrow = datetime.now(timezone.utc).strftime("%Y-%m-%dT23:59:59Z")

    HEADERS = {
        "Accept": "application/json",
        "Authorization": f"Token token={PAGERDUTY_API_KEY}",
        "Content-Type": "application/json"
    }
    PARAMS = {
        "user_ids[]": USER_ID,
        "since": today,
        "until": tomorrow,
        "limit": 20
    }

    response = requests.get(URL, headers=HEADERS, params=PARAMS)
    if response.status_code == 200:
        data = response.json()
        shifts = [
            {
                "schedule": oncall["schedule"]["summary"],
                "start": oncall["start"],
                "end": oncall["end"]
            }
            for oncall in data.get("oncalls", [])
        ]
        if shifts:
            shifts.sort(key=lambda x: x["start"])
            earliest_shift = shifts[0]
            lasay_shift = shifts[-1]

            # Convert UTC timestamps to local time 
            startcall = date_parser.parse(earliest_shift["start"])
            startcall = startcall.astimezone(pytz.utc).astimezone(target_timezone)

            finishcall = date_parser.parse(lasay_shift["end"])
            finishcall = finishcall.astimezone(pytz.utc).astimezone(target_timezone)

           #log_message(f"Today's On-Call Schedule: {startcall.strftime("%H:%M")} to {finishcall.strftime("%H:%M")}")
        else:
            log_message("No on-call shifts found for today.")
            startcall = "None"
            finishcall = "None"
    else:
        log_message(f"Error: {response.status_code} - {response.text}")
# oncall cast
def oncallsay():
    global startcall, finishcall
    if startcall and finishcall:
        ring(Ring_Url)
        speak_text(f"You are on call from {startcall.strftime('%H:%M')} until {finishcall.strftime('%H:%M')}")
#saying
def say(text):
    ring(Ring_Url)
    speak_text(text)

def main():
    global startcall, finishcall
    if args.test:
        oncall()
        oncallsay()
        say("1 New alarm: say alarm")
        sys.exit(0)

    previous_incidents = set()
    log_message("testing first time boot")
    #oncall()
    #oncallsay()
    say("1 New alarm: test alarm")

    startcall_announced = False
    finishcall_announced = False
    about_to_start_announced = False
    post_finishcall_time = None

    while True:
        try:
            oncall()  # Fetch latest on-call schedule
            current_time = datetime.now(pytz.utc).astimezone(target_timezone) 

            if startcall != "null" and finishcall != "null":
                if current_time >= finishcall + timedelta(minutes=1) and current_time < finishcall + timedelta(minutes=2) and not finishcall_announced:
                    say(f"Finished duty at {finishcall.strftime('%H:%M')}")
                    finishcall_announced = True
                    post_finishcall_time = current_time
                elif current_time >= startcall - timedelta(minutes=5) and current_time < startcall - timedelta(minutes=4) and not about_to_start_announced:
                    say(f"About to start duty at {startcall.strftime('%H:%M')}")
                    about_to_start_announced = True
                elif startcall <= current_time <= finishcall:
                    log_message(f"On duty between {startcall} - {finishcall}")
                elif current_time == startcall and not startcall_announced:
                    oncallsay()
                    startcall_announced = True
                elif current_time < startcall:
                    startcall_announced = False
                    about_to_start_announced = False
                    log_message(f"Waiting... Current time: {current_time}, will run between {startcall} - {finishcall}")
                elif current_time > finishcall:
                    finishcall_announced = False
                    if post_finishcall_time is None or current_time >= post_finishcall_time + timedelta(hours=1):
                        log_message(f"Waiting after finishcall... Current time: {current_time}")
                        post_finishcall_time = current_time
                else:
                    log_message(f"Waiting... Current time: {current_time}, will run between {startcall} - {finishcall}")
            else:
                log_message("Start or finish call times are not set. Waiting for 1800 seconds")
    
            try:
                incidents = get_pagerduty_incidents()
                if incidents:
                    new_incidents = {inc["id"]: inc["title"] for inc in incidents if inc["id"] not in previous_incidents}
                    if new_incidents:
                        n = 1
                        for incident_id, title in new_incidents.items():
                            say(f"{n} New alarm: {title}")
                            previous_incidents.add(incident_id)
                            n += 1
                    else:
                        say(f"Old alarm triggered")
                else:
                    log_message("No triggered incidents found.")
                time.sleep(CHECK_INTERVAL)
            except Exception as e:
                log_message(f"An error occurred during pagerduty check: {e}")
                time.sleep(5)
        except KeyboardInterrupt:
            log_message("Script terminated by user.")
            break
        except Exception as e:
            log_message(f"An error occurred: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()