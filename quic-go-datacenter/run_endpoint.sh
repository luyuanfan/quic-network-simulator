#!/bin/bash
set -e

# set up routes / interfaces so this container can talk to ns-3
/setup.sh

echo "ROLE=$ROLE"
echo "SERVER_PARAMS=$SERVER_PARAMS"
echo "CLIENT_PARAMS=$CLIENT_PARAMS"

PORT=4242

if [ "$ROLE" = "server" ]; then
    echo "[server] starting datacenter_server on :$PORT"

    exec datacenter_server \
        -ip "0.0.0.0:${PORT}" \
        $SERVER_PARAMS

elif [ "$ROLE" = "client" ]; then
    # wait for the ns-3 sim container to be ready
    /wait-for-it.sh sim:57832 -s -t 30

    echo "[client] starting datacenter_client to server4:$PORT"

    exec datacenter_client \
        -ip "server4:${PORT}" \
        $CLIENT_PARAMS

else
    echo "Unknown ROLE: '$ROLE'" >&2
    exit 1
fi