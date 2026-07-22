#!/usr/bin/env bash

set -euo pipefail

WORKSHOP_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
WORKSHOP_TARGET=workshop.target
WORKSHOP_SERVICES=(
    pigpiod.service
    workshop-control.service
    workshop-ustreamer.service
)

run_as_root() {
    if (( EUID == 0 )); then
        "$@"
    else
        sudo "$@"
    fi
}

require_installed_services() {
    if [[ ! -f /etc/systemd/system/workshop.target ]]; then
        echo "Workshop services are not installed. Run ./scripts/setup on the Raspberry Pi first." >&2
        exit 1
    fi
}
