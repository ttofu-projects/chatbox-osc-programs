from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
import time
import json
from interfering_process_killer import kill_interfering_process
from logger import log

global server
global client


def open_or_create_config():
    try:
        file = open("config.json", "rt")
    except FileNotFoundError:
        log("[ERROR] No config file found! Run config_setup.py first")
        raise KeyboardInterrupt
    return file


def interacted(name):
    config_file = open_or_create_config()
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


class OSCServer:
    def __init__(self, port):
        log("[OSC server] Loading config file")
        config_file = open_or_create_config()
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
    config_file = open_or_create_config()
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
