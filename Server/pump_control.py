import traceback
import json
from time import sleep
from threading import Timer
import pytz
import datetime
pump_enable  = True                       #
pump_mode = "Level"
pump_status = 0


blower_status = 0
blower_enable = False
blower_on_delay = 5
blower_off_delay = 30


def is_night():
    ist = pytz.timezone("Asia/Kolkata")
    x = datetime.datetime.now().replace(tzinfo = ist)
    if x.hour<=8 or x.hour>=16:
        return True:
    else:
        return False
def safe_json_read(path):
    while True:
        try:
            with open(path,"r") as fp:
                data = json.load(fp)
                return data
        except:
            print "Got Error in reading JSON"
            pass


def mean(array):
    return int(sum(array)/len(array))

def blower_on(timer=None):
    global blower_enable
    global blower_status
    blower_enable = True
    blower_status = 1
    controls = safe_json_read("controls.json")

    print "Blower On"
    controls['control-blower'] = 1

    with open("controls.json","w") as fp:
        json.dump(controls,fp,indent = 4)

    if timer:
        timer.start()


def blower_off(timer=None):
    global blower_status
    blower_status = 0
    controls = safe_json_read("controls.json")

    print "Blower Off"
    controls['control-blower'] = 0

    with open("controls.json","w") as fp:
        json.dump(controls,fp,indent = 4)

    if timer:
        timer.start()


def pump_on(timer=None):                  # what does timer =None mean??
    global pump_enable                    # is this definition of pump_enable variable? assignment already happened??
    global pump_status
    pump_enable = True
    pump_status = 1

    controls = safe_json_read("controls.json")        # read Jason file contents to  'cont

    print "Pump On"
    controls['control-pump-main-tank'] = 1 # Set Pump

    with open("controls.json","w") as fp:  # open Jasone file in write mode
        json.dump(controls,fp,indent = 4)  #  WHAT IS THIS?  write to Jason file? what does json.dump do? what is indent?

    if timer:
        timer.start()

    Timer(blower_on_delay,blower_on).start()

def pump_off(timer=None):
    global pump_status
    pump_status = 0                       # WHAT IS THIS? is it needed to clear pump_enable? if not, why was that needed in 'pump_on?
    controls = safe_json_read("controls.json")

    print "Pump Off"
    controls['control-pump-main-tank'] = 0

    with open("controls.json","w") as fp:
        json.dump(controls,fp,indent = 4)

    if timer:
        timer.start()                     # start pump off timer

    Timer(blower_off_delay,blower_off).start()



def close_valves():

    controls = safe_json_read("controls.json")

    print "Valves Closed"
    controls["control-valve-raft-tank-1"] = 1
    controls["control-valve-raft-tank-2"] = 1

    with open("controls.json","w") as fp:
        json.dump(controls,fp,indent = 4)

def open_valves():

    controls = safe_json_read("controls.json")

    print "Valves Opened"
    controls["control-valve-raft-tank-1"] = 0
    controls["control-valve-raft-tank-2"] = 0

    with open("controls.json","w") as fp:
        json.dump(controls,fp,indent = 4)

def enable_pump():
    global pump_enable
    pump_enable = True

tank_1_levels = []
tank_2_levels = []

def get_water_level(sensors,mode = "avg"):

    if mode=="avg":
        # TODO: Implement value checking and buffering
        return int((sensors['sensor-water-level-buffer-tank-2']+sensors['sensor-water-level-buffer-tank-1'])/2)
    elif mode=="min":
        # TODO: Implement value checking and buffering
        return min(sensors['sensor-water-level-buffer-tank-2'],sensors['sensor-water-level-buffer-tank-1'])
    elif mode=="max":
            # TODO: Implement value checking and buffering
            return max(sensors['sensor-water-level-buffer-tank-2'],sensors['sensor-water-level-buffer-tank-1'])
    elif mode=="first":
        if sensors['sensor-water-level-buffer-tank-1'] < 76:
            tank_1_levels.append(sensors['sensor-water-level-buffer-tank-1'])

        if len(tank_1_levels)>3:
            del tank_1_levels[0]

        if len(tank_1_levels)>0:
        	return mean(tank_1_levels)
        else:
            return 25

    elif mode=="second":
        if sensors['sensor-water-level-buffer-tank-2'] < 76:
            tank_2_levels.append(sensors['sensor-water-level-buffer-tank-2'])
        if len(tank_2_levels)>3:
            del tank_2_levels[0]

        if len(tank_2_levels)>0:
        	return mean(tank_2_levels)
        else:
            return 25

    else:
        raise RuntimeError("Unknown mode for get water level")

if pump_mode == "Time":                          # WHAT IS THIS?? is this start of main code??
    pump_on()
elif pump_mode == "Level":
    pump_off()                                   # so, for the first time, pump_enable is not set!! is tha ok?
    open_valves()

print_log = True
while True:
    try:

        with open("configuration.json","r") as fp:
            configuration = json.load(fp)       # read the  configuration jason file

        if print_log:
            log_dict = {}                       # WHAT IS THIS?? data strucutre??
            with open("sensors.json","r") as fp:
                sensor_string = fp.read()
                sensors = json.loads(sensor_string)
                log_dict['sensor-water-level-buffer-tank-1'] = sensors['sensor-water-level-buffer-tank-1']
                log_dict['sensor-water-level-buffer-tank-2'] = sensors['sensor-water-level-buffer-tank-2']
            with open("controls.json","r") as fp:
                controls = json.load(fp)
                log_dict['control-valve-raft-tank-1'] = controls['control-valve-raft-tank-1']
                log_dict['control-valve-raft-tank-2'] = controls['control-valve-raft-tank-2']
                log_dict['control-pump-main-tank'] = controls['control-pump-main-tank']
            with open("system.log","a+") as fp:
                fp.write(json.dumps(log_dict)+"\n")  # read sensor values and valve status from jsn files and write to system.log file

        print_log = not print_log
        pump_on_time = configuration["time-on-pump-main-tank"]       # read pump and hold settings from configuration jsn file
        pump_off_time = configuration["time-off-pump-main-tank"]
        water_hold_time = configuration["time-valve-water-hold"]
        water_drain_time = configuration["time-valve-water-drain"]

        if is_night():
            water_hold_time = configuration["hold-time-night-multiplier"]*water_hold_time

        now = datetime.datetime.now()

        if pump_enable and pump_mode=="Time":           # when is the first time pump_enable is set?? esp. in Level mode??
            timer_on = Timer(pump_off_time,pump_on)
            timer_off = Timer(pump_on_time,pump_off,[timer_on,])
            timer_off.start()
            pump_enable = False


        # blower_on_time = 4
        # blower_off_time = 8
        # if blower_enable:
        #     timer_on = Timer(blower_off_time,blower_on)
        #     timer_off = Timer(blower_on_time,blower_off,[timer_on,])
        #     timer_off.start()
        #     blower_enable = False

        if pump_enable and pump_mode=="Level":
            with open("sensors.json","r") as fp:
                sensor_string = fp.read()
                sensors = json.loads(sensor_string)
            if pump_status == 0 and get_water_level(sensors,'first')<configuration["water-level-buffer-tank-minimum"]:
                timer_close_valves= Timer(1,close_valves)
                timer_on_pump = Timer(water_drain_time,pump_on,[timer_close_valves,])
                timer_on_pump.start()
                pump_enable = False

            if pump_status == 1 and get_water_level(sensors,'first')>configuration["water-level-buffer-tank-maximum"]:
                pump_off()
                timer_open_valves = Timer(water_hold_time,open_valves)
                timer_open_valves.start()
        sleep(0.5)
    except Exception as e:
        traceback.print_exc()
