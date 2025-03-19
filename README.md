# PagerDuty Alarm Notifier with Chromecast Support local

This python script checks for triggered alarms in PagerDuty. If an alarm is detected, it sends the information to a Chromecast-enabled device and reads it out. This is local version


## Installation
### Clone this branch to the device 
```sh
git clone this repo
```
### Python Dependencies
Install the required Python packages:
```sh
pip3 install -r /app/requirements.txt
```

### System Dependencies
Ensure necessary system packages are installed:
```sh
apt update 
apt install -y ffmpeg libsndfile1
```

---
## Quick Start
```sh
python3 main.py 
```

## Testing chromecast connection

For testing casting feature just add --test

```sh
python3 main.py --test
```