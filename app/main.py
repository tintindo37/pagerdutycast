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


#env from docker 
env1 = os.getenv("IP")
env2 = os.getenv("NAME")
env3 = os.getenv("Pagerapi")
env4 = os.getenv("User")
env5 = os.getenv("Time")

if env1 ==" none" or env2 == "none" or env3 == "none" or env4 == "none":
    raise ValueError("Error: One or more required environment variables are missing!")
    sys.exit(0)
else:
#conf for docker
    CAST_IP = env1 # IP of Google Home Mini or any Chromecast-enabled device
    CAST_NAME = env2  # Name of Google Home Mini or any Chromecast-enabled device
    PAGERDUTY_API_KEY = env3 # pg api
    USER_ID = env4 #pagerduty user
    CHECK_INTERVAL = int(env5)  # seconds between checks
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
    log_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S %A")  # Format time
    print(f"{log_time} - {message}")  # log_message log

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
    encoded_text = urllib.parse.quote(text)
    media_url = BASE_TTS_URL.format(encoded_text)
    log_message(f'Speaking: "{text}"')
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
            latest_shift = shifts[-1]

            # Convert UTC timestamps to local time in HH:MM format
            startcall = date_parser.parse(earliest_shift["start"]).astimezone()
            finishcall = date_parser.parse(latest_shift["end"]).astimezone()

            log_message(f"Today's On-Call Schedule: {startcall.strftime("%H:%M")} to {finishcall.strftime("%H:%M")}")
        else:
            log_message("No on-call shifts found for today.")
            startcall = None
            finishcall = None
    else:
        log_message(f"Error: {response.status_code} - {response.text}")
# oncall cast
def oncallsay():
    if startcall and finishcall:
        ring(Ring_Url)
        speak_text(limit_string_length(f"You are on call from {startcall.strftime("%H:%M")} until {finishcall.strftime("%H:%M")}"))
#testing
def test(text):
    ring(Ring_Url)
    speak_text(limit_string_length(text))

def main():
    global startcall, finishcall
    if args.test:
        oncall()
        oncallsay()
        test("1 New alarm: test alarm")
        sys.exit(0)

    previous_incidents = set()
    log_message("testing first time boot")
    oncall()
    oncallsay()
    test("1 New alarm: test alarm")
    while True:
        oncall()  # Fetch latest on-call schedule
        current_time = datetime.now().astimezone()

        if current_time <= finishcall  + timedelta(minutes=1):
            test(f"You just finished your duty at {finishcall.strftime("%H:%M")}")
        elif current_time <= startcall + timedelta(minutes=5):
            test(f"You are about to start your duty at {startcall.strftime("%H:%M")}")
        elif startcall and finishcall and startcall <= current_time <= finishcall:
            oncallsay()
            try:
                incidents = get_pagerduty_incidents()
                if incidents:
                    new_incidents = {inc["id"]: inc["title"] for inc in incidents if inc["id"] not in previous_incidents}
                    if new_incidents:
                        n = 1
                        for incident_id, title in new_incidents.items():
                            ring(Ring_Url)
                            speak_text(limit_string_length(f"{n} New alarm: {title}"))
                            previous_incidents.add(incident_id)
                            n += 1
                    else:
                        log_message("No new incidents to announce.")
                else:
                    log_message("No triggered incidents found.")
                time.sleep(CHECK_INTERVAL)
            except KeyboardInterrupt:
                log_message("Script terminated by user.")
                break
            except Exception as e:
                log_message(f"An error occurred: {e}")
                time.sleep(5)
        else:
            log_message(f"Waiting... Current time: {current_time.strftime("%H:%M")}, will run between {startcall.strftime("%H:%M")} - {finishcall.strftime("%H:%M")}")
            time.sleep(1800)

if __name__ == "__main__":
    main()