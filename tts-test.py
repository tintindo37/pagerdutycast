import argparse
import sys
import time
import urllib.parse
import requests
import pychromecast
import json

from common import add_log_arguments, configure_logging

# Configuration
CAST_NAME = "XYZ"  # Name of Google Home Mini or any Chromecast-enabled device
CAST_IP = "192.168.1.1"  # IP of Google Home Mini or any Chromecast-enabled device
BASE_TTS_URL = "http://translate.google.com/translate_tts?ie=UTF-8&total=1&idx=0&textlen=32&client=tw-ob&q={}&tl=En-gb" #tts provider 
PAGERDUTY_API_KEY = "XYZ" # Pagerduty api key 
USER_ID = "XYZ" # Pagerduty user id
CHECK_INTERVAL = 30  # seconds between checks
Ring_Url = "https://cdn.pixabay.com/download/audio/2025/01/13/audio_902fc3eeb8.mp3?filename=elevator-chimenotification-ding-recreation-287560.mp3"
parser = argparse.ArgumentParser(description="PagerDuty to TTS on Chromecast")
add_log_arguments(parser)
parser.add_argument("--cast", help='Name of cast device (default: "%s")' % CAST_NAME, default=CAST_NAME)
parser.add_argument("--test", help="Trigger test alarm", action="store_true")
args = parser.parse_args()

configure_logging(args)

# Find Chromecast
chromecasts, browser = pychromecast.get_listed_chromecasts(friendly_names=[args.cast], known_hosts=[CAST_IP])
if not chromecasts:
    print(f'No chromecast with name "{args.cast}" discovered')
    sys.exit(1)

cast = chromecasts[0]
cast.wait()

#txt to speach
def speak_text(text):
    encoded_text = urllib.parse.quote(text)
    media_url = BASE_TTS_URL.format(encoded_text)
    print(f'Speaking: "{text}"')
    cast.media_controller.play_media(media_url, "audio/mp3")
    player_state = None
    t = 30.0
    has_played = False
    while True:
        try:
            if player_state != cast.media_controller.status.player_state:
                player_state = cast.media_controller.status.player_state
                print("Player state:", player_state)
            if player_state == "PLAYING":
                has_played = True
                break
            if cast.socket_client.is_connected and has_played and player_state != "PLAYING":
                has_played = False
                cast.media_controller.play_media(media_url, "audio/mp3")
            time.sleep(0.1)
            t = t - 0.1
        except KeyboardInterrupt:
            break
def ring(URL_Media):
    print(f'Ringing: "{URL_Media}"')
    cast.media_controller.play_media(URL_Media, "audio/mp3")  
    player_state = None
    t = 30.0
    has_played = False
    while True:
        try:
            if player_state != cast.media_controller.status.player_state:
                player_state = cast.media_controller.status.player_state
                print("Player state:", player_state)
            if player_state == "PLAYING":
                has_played = True
                break
            if cast.socket_client.is_connected and has_played and player_state != "PLAYING":
                has_played = False
                cast.media_controller.play_media(URL_Media, "audio/mp3")  
            time.sleep(0.1)
            t = t - 0.1
        except KeyboardInterrupt:
            break
#google translate api limit
def limit_string_length(input_string, max_length=200):
  if len(input_string) > max_length:
    return input_string[:max_length]  # Truncate the string
  else:
    return input_string
  
def get_pagerduty_incidents():
    url = "https://api.pagerduty.com/incidents"
    headers = {
        "Authorization": f"Token token={PAGERDUTY_API_KEY}",
        "Accept": "application/vnd.pagerduty+json;version=2"
    }
    params = {"statuses[]": "triggered", "user_ids[]": USER_ID}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get("incidents", [])
    else:
        print(f"Error fetching incidents: {response.status_code} {response.text}")
        return []

def main():
    if args.test:
        ring(Ring_Url)
        time.sleep(3.6)
        speak_text(limit_string_length("test tts")) #changed here for the tts max 200 character
        sys.exit(0)
    
    previous_incidents = set()
    while True:
        try:
            incidents = get_pagerduty_incidents()
            if incidents:
                new_incidents = {inc["id"]: inc["title"] for inc in incidents if inc["id"] not in previous_incidents}
                if new_incidents:
                    n=1
                    for incident_id, title in new_incidents.items():
                        ring(Ring_Url)
                        time.sleep(3.6)
                        speak_text(f"{n} New alarm: {limit_string_length(title)}")
                        previous_incidents.add(incident_id)
                        n=+1
                else:
                    print("No new incidents to announce.")
            else:
                print("No triggered incidents found.")
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print("Script terminated by user.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()