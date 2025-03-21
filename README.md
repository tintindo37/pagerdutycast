# PagerDuty Alarm Notifier with Chromecast Support for armv6 like RPI Zero

This script checks for triggered alarms in PagerDuty. If an alarm is detected, it sends the information to a Chromecast-enabled device and reads it out.

## Quick Start

1. Use Docker Compose.
2. Set the required environment variables:
   - `NAME`: Name of the Chromecast-enabled device.
   - `IP`: IP address of the Chromecast-enabled device.
   - `Pagerapi`: PagerDuty API key linked to your account.
   - `User`: User ID found in the address bar of the PagerDuty website.
   - `Time`: Refresh interval (default: 15 seconds). It should not be set below 15-20 seconds.
```yaml
version: "3.7"
services:
  pagerdutycast:
    image: tintindohoang/pagerdutycast:armv6
    container_name: pagerdutycast
    environment:
      - NAME=  #Add the name of the Chromecast-enabled device
      - IP= #Add the IP address of the Chromecast-enabled device 
      - Pagerapi= #Add the PagerDuty API key linked to your account
      - User= #Add the User ID found in the address bar of the PagerDuty website
      - Timezone= #Add your timezone Asia/Ho_Chi_Minh or Europe/Warsaw
    restart: unless-stopped
```
---

