import socket
from threading import Thread
import json
server_socket = socket.socket()
server_socket_port = 3212
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(("",3212))
server_socket.listen(10)

clients = []

sensor_status = {}
control_status = {}
def getSensorStatus(in_string):
    global sensor_status
    print sensor_status
    try:
        values = json.loads(in_string)
    except ValueError as e:
        print e
        return


    for val in values.keys():
        sensor_status[val] = values[val]
    print sensor_status

def setControlStatus():
    global sensor_status
    global control_status
    global clients
    # if "sensor-water-level-1" in sensor_status and sensor_status["sensor-water-level-1"] > 10:
    for client in clients:
        client.send_data(control_status)




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
            char_in = self.client.recv(1)
            if not char_in:
                print "Closing connection with client",self.addr
                break
            if "~" in char_in:
                getSensorStatus(data)
                data = ""
            else:
                data += char_in
            # print "Received data from ",self.addr
            # print data
            # setSensorStatus(data)
    def send_data(data):
        data_string = json.dumps(data)
        self.client.send(data_string)
        self.client.send("~")


while True:
    client,client_addr = server_socket.accept()
    clients_handler = ClientHandler(client,client_addr)
    clients.append(clients_handler)
    clients_handler.start()
