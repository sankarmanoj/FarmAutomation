from time import sleep
import socket
from threading import Thread,Timer
import json
import logging
from logging.handlers import RotatingFileHandler
from enum import Enum


class CycleState(Enum):
    HOLDING_FULL = 1
    HOLDING_EMPTY = 2
    FILLING = 3
    EMPTYING = 4

current_state = CycleState.EMPTYING

log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
logFile = 'events.log'
my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=5*1024*1024,backupCount=2, encoding=None, delay=0)
my_handler.setFormatter(log_formatter)
my_handler.setLevel(logging.INFO)

app_log = logging.getLogger('root')
app_log.setLevel(logging.INFO)
app_log.addHandler(my_handler)

server_socket = socket.socket()
server_socket_port = 3213
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(("",3213))
server_socket.listen(10)
clients = []



def safe_json_read(path):
    while True:
        try:
            with open(path,"r") as fp:
                data = json.load(fp)
                return data
        except:
            print "Got Error in reading JSON"
            pass


class ClientHandler(Thread):
    def __init__(self,client,addr):
        print "New Connection from ",addr
        super(ClientHandler,self).__init__()
        self.client = client
        self.addr = addr
        self.setDaemon(True)
    def run(self):
        while True:
            try:
                data = self.client.recv(1000)
            except socket.error as err:
                print err
                clients.remove(self)
                break
            if not data:
                print "Closing connection with client",self.addr
                break
            try:
                json_data = json.loads(data)
                print json_data
                write_back = False
                control_status =  json.load(open("controls.json","r"))
                if "control-pump-main-tank" in json_data:
                    control_status["control-pump-main-tank"]=json_data["control-pump-main-tank"]
                    if control_status["control-pump-main-tank"]==0:
                        app_log.info("Pump OFF by Remote")
                    else:
                        app_log.info("Pump ON  by Remote")

                    write_back = True

                if "control-blower" in json_data:
                    control_status["control-blower"]=json_data["control-blower"]
                    if control_status["control-blower"]==0:
                        app_log.info("Blower OFF by Remote")
                    else:
                        app_log.info("Blower ON  by Remote")

                    write_back = True


                if "control-valve-raft-tank-1" in json_data:
                    control_status["control-valve-raft-tank-1"]=json_data["control-valve-raft-tank-1"]
                    if control_status["control-valve-raft-tank-1"]==0:
                        app_log.info("Valve 1 Opened By Remote ")
                    else:
                        app_log.info("Valve 1 Closed By Remote ")

                    write_back = True

                if "control-valve-raft-tank-2" in json_data:
                    control_status["control-valve-raft-tank-2"]=json_data["control-valve-raft-tank-2"]
                    if control_status["control-valve-raft-tank-2"]==0:
                        app_log.info("Valve 2 Opened By Remote ")
                    else:
                        app_log.info("Valve 2 Closed By Remote ")

                    write_back = True

                if write_back:
                    with open("controls.json","w") as fp:
                        json.dump(control_status,fp,indent = 4)

            except err :
                print err
                continue


    def send_data(self,data):
        data_string = json.dumps(data)
        self.client.send(data_string)

class ServerHandler(Thread):
    def __init__(self,):
        super(ServerHandler,self).__init__()
        self.setDaemon(True)
    def run(self):
        while True:
            client,client_addr = server_socket.accept()
            clients_handler = ClientHandler(client,client_addr)
            clients.append(clients_handler)
            clients_handler.start()

def pump_on(timer=None):                  # what does timer =None mean??
    global current_state
    controls = safe_json_read("controls.json")        # read Jason file contents to  'cont
    app_log.info("pump_on")
    controls['control-pump-main-tank'] = 1 # Set Pump
    with open("controls.json","w") as fp:  # open Jasone file in write mode
        json.dump(controls,fp,indent = 4)  #  WHAT IS THIS?  write to Jason file? what does json.dump do? what is indent?
    if timer:
        timer.start()
    current_state = CycleState.FILLING

def pump_off(timer=None):
    controls = safe_json_read("controls.json")
    app_log.info("pump_off")
    controls['control-pump-main-tank'] = 0
    with open("controls.json","w") as fp:
        json.dump(controls,fp,indent = 4)
    if timer:
        timer.start()                     # start pump off timer



def close_valves():
    controls = safe_json_read("controls.json")
    app_log.info("valves_closed")
    controls["control-valve-raft-tank-1"] = 1
    controls["control-valve-raft-tank-2"] = 1
    with open("controls.json","w") as fp:
        json.dump(controls,fp,indent = 4)

def open_valves():
    global current_state

    controls = safe_json_read("controls.json")
    app_log.info("valves_opened")
    controls["control-valve-raft-tank-1"] = 0
    controls["control-valve-raft-tank-2"] = 0
    with open("controls.json","w") as fp:
        json.dump(controls,fp,indent = 4)

    current_state = CycleState.EMPTYING

server = ServerHandler()
server.start()
pump_off()
open_valves()

while True:
    try:
        sensor_status = json.load(open("sensors.json","r"))
    	configuration = json.load(open("configuration.json","r"))
        control_status =  safe_json_read("controls.json")

        pump_status = control_status['control-pump-main-tank']
        pump_on_time = configuration["time-on-pump-main-tank"]       # read pump and hold settings from configuration jsn file
        pump_off_time = configuration["time-off-pump-main-tank"]
        water_hold_time = configuration["time-valve-water-hold"]
        water_drain_time = configuration["time-valve-water-drain"]

        print current_state.name

        if pump_status == 0 and sensor_status["sensor-level-switch-low-tank-2"]==0 and current_state==CycleState.EMPTYING:
            timer_close_valves= Timer(1,close_valves)
            timer_on_pump = Timer(water_drain_time,pump_on,[timer_close_valves,])
            timer_on_pump.start()
            pump_enable = False
            app_log.info("Pump Off and Tank Empty. Waiting Drain Time %d"%(water_drain_time))
            current_state = CycleState.HOLDING_EMPTY

        if pump_status == 1 and sensor_status["sensor-level-switch-high-tank-2"]==1 and current_state==CycleState.FILLING:
            pump_off()
            timer_open_valves = Timer(water_hold_time,open_valves)
            timer_open_valves.start()
            app_log.info("Pump On and Tank Full. Holding for %d"%(water_hold_time))
            current_state = CycleState.HOLDING_FULL

        control_status =  json.load(open("controls.json","r"))

        all_data = sensor_status.copy()
        all_data.update(control_status)
    	all_data["alert-message"]=configuration["alert-message"]
        all_data["current_state"]=current_state.name
        for client in clients:
            try:
                client.send_data(all_data)
            except:
                clients.remove(client)

    except Exception as e:
        print e
    sleep(1)
