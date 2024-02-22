#!/bin/bash

# Function to scan for BLE devices and extract UUID of GROUP_37
scan_and_identify_uuid() {
    # Start BLE scan and capture the output
    scan_output=$(ble-scan)

    # Identify UUID of GROUP_37 device
    uuid=$(echo "$scan_output" | grep 'GROUP_37' | awk '{print $1}')

    # Print UUID to the user
    echo "UUID of GROUP_37 device: $uuid"
}

# Call the function to scan and identify UUID
scan_and_identify_uuid
