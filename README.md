# PagerDuty Alarm Notifier with Chromecast Support

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
    image: tintindohoang/pagerdutycast:latest
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

# PagerDuty Alarm Notifier with Chromecast & WireGuard (Cloud Deployment)

This version includes WireGuard for cloud deployment and remote access to your home network which is required.

## Quick Start for `pagerdutycast-wg`

1. Use Docker Compose.
2. Set the required environment variables:
   - `NAME`: Name of the Chromecast-enabled device.
   - `IP`: IP address of the Chromecast-enabled device.
   - `Pagerapi`: PagerDuty API key linked to your account.
   - `User`:  User ID found in the address bar of the PagerDuty website.
   - `Time`: Refresh interval (default: 15 seconds). It should not be set below 15-20 seconds.
   - `IPVPN`: VPN IP address of the wireguard node.
3. Define the path for the WireGuard configuration file. Example: `'/home/ubuntu/wg:/config'`. You only need to specify the directory containing the `wg0.conf` file, not the file itself.

## Docker Compose Configuration

```yaml
version: "3.7"

services:
  pagerdutycast:
    depends_on:
      - wireguard
    image: tintindohoang/pagerdutycast:latest
    container_name: pagerdutycast-wg
    environment:
      - NAME=  #Add the name of the Chromecast-enabled device
      - IP= #Add the IP address of the Chromecast-enabled device 
      - Pagerapi= #Add the PagerDuty API key linked to your account
      - User= #Add the User ID found in the address bar of the PagerDuty website
      - IPVPN= #Add  the VPN IP address of the wireguard node
      - Timezone= #Add your timezone Asia/Ho_Chi_Minh or Europe/Warsaw
    restart: unless-stopped
    network_mode: service:wireguard-my
    healthcheck:
      test: ["CMD", "/bin/bash", "/app/health_check.sh"]
      interval: 30s
      retries: 3
      timeout: 10s

  wireguard:
    image: linuxserver/wireguard
    container_name: wireguard
    restart: unless-stopped
    networks:
      - net01
    volumes:
      - '/home/ubuntu/wg:/config'  # add this to the path where `wg0.conf` is located
      - '/lib/modules:/lib/modules:ro'
    environment:
      - PUID=1000
      - PGID=1000
    cap_add:
      - NET_ADMIN
      - SYS_MODULE
    sysctls:
      - net.ipv4.conf.all.src_valid_mark=1

networks:
  net01:
    driver: bridge
```

This setup ensures that your PagerDuty alerts can be securely sent to a Chromecast device, even when deploying the service from the cloud using WireGuard for a secure tunnel.

