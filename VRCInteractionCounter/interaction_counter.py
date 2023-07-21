from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
import datetime
import time
import psutil
import json

# This is what will be saved in the JSON file if it doesn't exist.
# Do not modify the template below. Modify the JSON which gets generated after first launch
config_template = {
    "interactions": {
        "boop": {  # Avatar parameter name the activation of which needs to be counted.
            # If the parameter type is float then the amount of times it has reached 1.0 gets counted
            "count": 0,  # The saved count amount
            "text_format": "Boops: {count}"  # What will be displayed in the chatbox.
            # In this case, it will show "Boops: 1", "Boops: 2", etc
        },
        "headpat": {
            "count": 0,
            "text_format": "Headpats: {count}"
        }
    },
    "receiving_port": 9001,
    "sending_port": 9000
}

global server
global client


def get_time():
    return datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S.%f")


def log(text):
    print("[" + get_time() + "]" + text)


def open_or_create_json(file_name):
    try:
        file = open(file_name, "rt")
    except FileNotFoundError:
        log("[Config file loader] No config file found, creating a new one from template")
        file = open(file_name, "wt")
        file.write(json.dumps(config_template, sort_keys=True, indent=4))
        file.close()
        file = open(file_name, "rt")
    return file


def interacted(name):
    config_file = open_or_create_json("config.json")
    config = json.loads(config_file.read())
    interactions = config["interactions"]
    config_file.close()

    interaction = interactions[name]
    interaction["count"] += 1
    text = interaction["text_format"].format(count=interaction["count"])
    client.send(text)
    interactions[name] = interaction
    config["interactions"] = interactions

    config_file = open("config.json", "wt")
    config_file.write(json.dumps(config, sort_keys=True, indent=4))
    config_file.close()


class ChatboxClient:
    def __init__(self, port):
        self.client = udp_client.SimpleUDPClient("127.0.0.1", port)
        log("[Chatbox client] Client successfully created with port " + str(port))
        self.last_time = time.time()

    def send(self, text):
        if time.time() - self.last_time < 1.5:  # Chatbox cooldown
            return
        self.client.send_message("/chatbox/input", [text, True])
        log("[Chatbox client] Sent a message: \"" + text + "\"")
        self.last_time = time.time()


def find_interfering_process(port):
    connections = psutil.net_connections()
    for con in connections:
        if con.raddr != tuple():
            if con.raddr.port == port:
                return con.pid
        if con.laddr != tuple():
            if con.laddr.port == port:
                return con.pid
    return -1


def kill_interfering_process(port):
    log("[Interfering process killer] Searching for interfering process")
    pid = find_interfering_process(port)
    if pid == -1:
        log("[Interfering process killer] No interfering processes are found")
        return
    psutil.Process(pid).kill()
    log("[Interfering process killer] Interfering process is found and killed")
    return


class OSCServer:
    def __init__(self, port):
        log("[OSC server] Loading config file")
        config_file = open_or_create_json("config.json")
        config = json.loads(config_file.read())
        config_file.close()
        interactions = config["interactions"]

        self.dispatcher = Dispatcher()
        self.dispatcher.set_default_handler(self.osc_default)

        log("[OSC server] Applying handlers for parameters specified in config")
        for name in interactions.keys():
            self.dispatcher.map("/avatar/parameters/" + name, self.osc_interact)

        log("[OSC server] Creating server with port " + str(port))
        try:
            self.server = BlockingOSCUDPServer(("127.0.0.1", port), self.dispatcher)
        except OSError:
            log("[OSC server] The socket is already in use, attempting to kill the interfering process")
            kill_interfering_process(port)
            time.sleep(0.5)  # Safety wait
            self.server = BlockingOSCUDPServer(("127.0.0.1", port), self.dispatcher)
        log("[OSC server] Server successfully created with port " + str(port))

    def osc_interact(self, address, *args):
        name = address.split("parameters/")[1]
        log("[OSC server] " + name + " is now " + str(args[0]))
        if args[0] == 1:
            interacted(name)

    def osc_default(self, adress, *args):
        pass

    def launch(self):
        self.server.serve_forever()

    def shutdown(self):
        log("[OSC server] Shutting down")
        self.server.shutdown()


def main():
    config_file = open_or_create_json("config.json")
    config = json.loads(config_file.read())
    global client
    client = ChatboxClient(config["sending_port"])
    global server
    server = OSCServer(config["receiving_port"])

    try:
        server.launch()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
