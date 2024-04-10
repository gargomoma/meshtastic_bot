# meshtastic_bot
Make your meshtastic device smart with the power of Python!

## Overview
Useful for router_clients connected via MQTT (or other fixed devices).

This simple script leverages the power of **[Meshtastic Python](https://meshtastic.org/docs/software/python/cli)** letting users add extra actions to their stations.

* /ping Answers users, helpful to see if the station is succesfully connected to the mesh.
* /rt   Shows users RSSI and SNR of the "/rt" message recieved by the station. Useful for RangeTests.
* Telegram messages forwarding.

## TODO:
* Avoid spamming & overlap of multiple bot-stations.

## HowTo:
* Use Docker compose to run it.
  *  Clone repo, cd it, and run "docker compose up" (add -d if you want to run it in background & --build if you want to apply new changes)
* Or just install Meshtastic Python and run the Python file (need modifications).

## Thanks♥:
**[pdxlocations](https://github.com/pdxlocations/Meshtastic-Python-Examples)** Showing in your repo how easy was to work with the CLI.

**[geoffwhittington](https://github.com/geoffwhittington/meshtastic-matrix-relay/)** I learned how to reconnect thanks to you.
More to come?
