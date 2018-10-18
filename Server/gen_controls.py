import json
import time
with open("controls.json","r") as fp:
    controls = json.load(fp)

# Initalize all controls to 0
controls['control-pump-main-tank'] = 1
controls['control-pump-circulation'] = 0
controls['control-valve-raft-tank-2'] = 0
controls['control-valve-raft-tank-1'] = 0

print controls

with open("configuration.json","r") as fp:
    configuration = json.load(fp)

print configuration
motor_start_time = 0
motor_stop_time = 0
valve_open_time = 0
valve_close_time = 0
valve_status = False

while True:
    with open("sensors.json","r") as fp:
        sensors = json.load(fp)

    if controls['control-pump-main-tank'] == 1:
        if sensors['sensor-water-level-main-tank-1'] > configuration['water-level-main-tank-maximum'] or sensors['sensor-water-level-main-tank-2'] > configuration['water-level-main-tank-maximum']:
            print "Turning pump off, main tank too low"
            controls['control-pump-main-tank'] = 0
        elif sensors['sensor-water-level-buffer-tank-1'] < configuration['water-level-buffer-tank-minimum'] or sensors['sensor-water-level-buffer-tank-2'] < configuration['water-level-buffer-tank-minimum']:
            print " Turning pump off, buffer tank full"
            controls['control-pump-main-tank'] = 0
            valve_open_time = time.time() + 30      #Set open time to 30 minutes from now
    elif controls['control-pump-main-tank'] == 0 and motor_start_time!= 0 and time.time() >   motor_start_time:
        print " Turning pump on, hit start time"
        controls['control-pump-main-tank'] = 1
        motor_start_time = 0

    if valve_close_time !=0  and time.time() > valve_close_time:
        print "Closing valves"
        controls['control-valve-raft-tank-1'] = 0
        controls['control-valve-raft-tank-2'] = 0
        valve_close_time = 0
        motor_start_time = time.time() + 30

    if valve_open_time !=0  and time.time() > valve_open_time:
        print "Opening valves"
        controls['control-valve-raft-tank-1'] = 1
        controls['control-valve-raft-tank-2'] = 1
        valve_close_time = time.time() + 30      #Set close time to 30 minutes for now
        valve_open_time = 0

    with open("controls.json","w") as fp:
        json.dump(controls,fp,indent = 4)
    time.sleep(5)
