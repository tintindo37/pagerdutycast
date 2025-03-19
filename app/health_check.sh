#!/bin/bash

# Health check function for wireguard vpn connection
if [ -z "$VPNIP" ]; then
  echo "You had to add IP address of the vpn"
  exit 1
fi
function check_container_health() {
    if ping -c 1 -W 1 $VPNIP &> /dev/null; then
        echo "$container_name is healthy."
        exit 0
    else
        echo "$container_name is unhealthy."
        exit 1
    fi
}

# Health check for container
check_container_health