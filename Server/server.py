from time import sleep
import socket
from threading import Thread
import json
server_socket = socket.socket()
server_socket_port = 3212
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(("",3212))
server_socket.listen(10)
import alert

clients = []
sensor_status = {
    "sensor-water-level-main-tank-2": 0,
    "sensor-water-level-main-tank-1": 0,
    "sensor-water-level-buffer-tank-2": 0,
    "sensor-temperature-1": 0,
    "sensor-water-level-buffer-tank-1": 0,
    "sensor-level-switch-low-tank-1":0,
    "sensor-level-switch-high-tank-1":0,
    "sensor-level-switch-low-tank-2":0,
    "sensor-level-switch-high-tank-2":0
}
control_status =  json.load(open("controls.json","r"))
def getSensorStatus(in_string):
    global sensor_status
    #print sensor_status
    try:
        values = json.loads(in_string)
    except ValueError as e:
        print e
        return

    control_echo = {}
    sensor_echo = {}
    for val in values.keys():
        if val in sensor_status:
            sensor_status[val] = values[val]
            sensor_echo[val] = values[val]
	if "control" in val:
            control_echo[val] = values[val]
    print "Got from client",control_echo,sensor_echo
    json.dump(sensor_status,open("sensors.json","w"),indent = 4)





class ClientHandler(Thread):
    def __init__(self,client,addr):
        print "New Connection from ",addr
        super(ClientHandler,self).__init__()
        self.client = client
        self.addr = addr
        self.setDaemon(True)
    def run(self):
        data = ""
        while True:
            try:
                char_in = self.client.recv(1)
            except socket.error as err:
                print err
                clients.remove(self)
                break
            if not char_in:
                print "Closing connection with client",self.addr
                break
            if "~" in char_in:
                print self.addr,
                getSensorStatus(data)
                data = ""
            else:
                data += char_in
            # print "Received data from ",self.addr
            # print data
            # setSensorStatus(data)
    def send_data(self,data):
        data_string = json.dumps(data)
        self.client.send(data_string)
        self.client.send("~")

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
server = ServerHandler()
server.start()
num_clients = 0
last_alert_sent_time = 0
while True:
    try:
        sensor_status = json.load(open("sensors.json","r"))
        control_status =  json.load(open("controls.json","r"))
        if len(clients)==0 and num_clients > 0:
            numbers = json.load(open("numbers.json","r"))
            alert.send_sms("Power Lost at the Farm",numbers)
        num_clients = len(clients)

        for client in clients:
            try:
                client.send_data(control_status)
            except:
                clients.remove(client)
        sleep(1)
    except Exception as e:
        print e
