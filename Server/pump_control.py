import traceback
import json
from time import sleep
from threading import Timer
import datetime
pump_enable  = True
pump_mode = "Level"
pump_status = 0


blower_status = 0
blower_enable = False

def pump_on(timer=None):
    global pump_enable
    global pump_status
    pump_enable = True
    pump_status = 1
    global blower_status
    while blower_status!=0:
        pass

    with open("controls.json","r") as fp:
        controls = json.load(fp)

    print "Pump On"
    controls['control-pump-main-tank'] = 1

    with open("controls.json","w") as fp:
        json.dump(controls,fp,indent = 4)

    if timer:
        timer.start()


def pump_off(timer=None):
    global pump_status
    pump_status = 0
    with open("controls.json","r") as fp:
        controls = json.load(fp)

    print "Pump Off"
    controls['control-pump-main-tank'] = 0

    with open("controls.json","w") as fp:
        json.dump(controls,fp,indent = 4)

    if timer:
        timer.start()

def blower_on(timer=None):
    global blower_enable
    global blower_status
    blower_enable = True
    blower_status = 1
    global pump_status
    while pump_status!=0:
        pass
    with open("controls.json","r") as fp:
        controls = json.load(fp)

    print "Blower On"
    controls['control-blower'] = 1

    with open("controls.json","w") as fp:
        json.dump(controls,fp,indent = 4)

    if timer:
        timer.start()


def blower_off(timer=None):
    global blower_status
    blower_status = 0
    with open("controls.json","r") as fp:
        controls = json.load(fp)

    print "Blower Off"
    controls['control-blower'] = 0

    with open("controls.json","w") as fp:
        json.dump(controls,fp,indent = 4)

    if timer:
        timer.start()

def close_valves():

    with open("controls.json","r") as fp:
        controls = json.load(fp)

    print "Valves Closed"
    controls["control-valve-raft-tank-1"] = 1
    controls["control-valve-raft-tank-2"] = 1

    with open("controls.json","w") as fp:
        json.dump(controls,fp,indent = 4)

def open_valves():

    with open("controls.json","r") as fp:
        controls = json.load(fp)

    print "Valves Opened"
    controls["control-valve-raft-tank-1"] = 0
    controls["control-valve-raft-tank-2"] = 0

    with open("controls.json","w") as fp:
        json.dump(controls,fp,indent = 4)

def enable_pump():
    global pump_enable
    pump_enable = True

def get_water_level(sensors,mode = "avg"):
    if mode=="avg":
        return int((sensors['sensor-water-level-buffer-tank-2']+sensors['sensor-water-level-buffer-tank-1'])/2)
    elif mode=="min":
        return min(sensors['sensor-water-level-buffer-tank-2'],sensors['sensor-water-level-buffer-tank-1'])
    elif mode=="max":
            return max(sensors['sensor-water-level-buffer-tank-2'],sensors['sensor-water-level-buffer-tank-1'])
    else:
        raise RuntimeError("Unknown mode for get water level")

if pump_mode == "Time":
    pump_on()
elif pump_mode == "Level":
    pump_off()
    open_valves()

print_log = True
while True:
    try:

        with open("configuration.json","r") as fp:
            configuration = json.load(fp)

        if print_log:
            log_dict = {}
            with open("sensors.json","r") as fp:
                sensors = json.load(fp)
                log_dict['sensor-water-level-buffer-tank-1'] = sensors['sensor-water-level-buffer-tank-1']
                log_dict['sensor-water-level-buffer-tank-2'] = sensors['sensor-water-level-buffer-tank-2']
            with open("controls.json","r") as fp:
                controls = json.load(fp)
                log_dict['control-valve-raft-tank-1'] = controls['control-valve-raft-tank-1']
                log_dict['control-valve-raft-tank-2'] = controls['control-valve-raft-tank-2']
                log_dict['control-pump-main-tank'] = controls['control-pump-main-tank']
            with open("system.log","a+") as fp:
                fp.write(json.dumps(log_dict)+"\n")

        print_log = not print_log
        pump_on_time = configuration["time-on-pump-main-tank"]
        pump_off_time = configuration["time-off-pump-main-tank"]
        water_hold_time = configuration["time-valve-water-hold"]
        water_drain_time = configuration["time-valve-water-drain"]

        now = datetime.datetime.now()

        if pump_enable and pump_mode=="Time":
            timer_on = Timer(pump_off_time,pump_on)
            timer_off = Timer(pump_on_time,pump_off,[timer_on,])
            timer_off.start()
            pump_enable = False


        blower_on_time = 4
        blower_off_time = 8
        if blower_enable:
            timer_on = Timer(blower_off_time,blower_on)
            timer_off = Timer(blower_on_time,blower_off,[timer_on,])
            timer_off.start()
            blower_enable = False

        if pump_enable and pump_mode=="Level":
            with open("sensors.json","r") as fp:
                sensors = json.load(fp)
            if pump_status == 0 and get_water_level(sensors,'min')<configuration["water-level-buffer-tank-minimum"]:
                timer_close_valves= Timer(1,close_valves)
                timer_on_pump = Timer(water_drain_time,pump_on,[timer_close_valves,])
                timer_on_pump.start()
                pump_enable = False

            if pump_status == 1 and get_water_level(sensors,'max')>configuration["water-level-buffer-tank-maximum"]:
                pump_off()
                timer_open_valves = Timer(water_hold_time,open_valves)
                timer_open_valves.start()
        sleep(0.5)
    except Exception as e:
        traceback.print_exc()
