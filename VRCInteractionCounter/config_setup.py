import json
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
from interfering_process_killer import kill_interfering_process

global config

parameter_blacklist = ["Grounded", "Seated", "AFK", "InStation", "Earmuffs", "MuteSelf"]


class OSCServer:
    def __init__(self, port):
        self.dispatcher = Dispatcher()
        self.dispatcher.set_default_handler(self.osc_parameter_change)
        try:
            self.server = BlockingOSCUDPServer(("127.0.0.1", port), self.dispatcher)
        except OSError:
            kill_interfering_process(port)
            self.server = BlockingOSCUDPServer(("127.0.0.1", port), self.dispatcher)
        self.busy = False

    def osc_parameter_change(self, adress, *args):
        if "/parameters/" not in adress:
            return
        param_name = adress.split("/parameters/")[1]
        if (not isinstance(args[0], bool)) or (param_name in parameter_blacklist) or self.busy:
            return
        self.busy = True
        parameter_blacklist.append(param_name)
        if input("Change in boolean parameter \"" + adress.split("/parameters/")[1] +
                 "\" found! do you want to add it to config? [y/n]: ").lower() == "n":
            return

        global config
        try:
            config_file = open("config.json", "rt")
            config = json.loads(config_file.read())
        except FileNotFoundError:
            config = {
                "interactions": {
                },
                "receiving_port": 9001,
                "sending_port": 9000
            }

        text_format = ""
        while self.busy:
            config["interactions"][param_name] = {
                "count": 0,
                "text_format": ""
            }
            print("What text do you want to appear in the chatbox for the parameter \"" + param_name + "\"?")
            text_format = ""
            while "{count}" not in text_format:
                print("Please include the string \"{count}\" in your responce",
                      "so the program knows where to put the count.")
                text_format = input("Chatbox text format:")
            print("Chatbox will display this text when \"" + param_name + "\" parameter updates:")
            for i in range(3):
                print(text_format.format(count=i))
            self.busy = input("Save changes to the config? [y/n]: ").lower() == "n"
        config["interactions"][param_name]["text_format"] = text_format

        file = open("config.json", "wt")
        file.write(json.dumps(config, sort_keys=True, indent=4))
        file.close()
        if input("Changes saved. Exit the tool? [y/n]: ").lower() == "y":
            raise KeyboardInterrupt

    def launch(self):
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        self.server.shutdown()


def main():
    server = OSCServer(9001)
    print("Welcome to the config setup tool! This tool will help you write the config.json file.")
    print("Get into your VRChat avatar and receive a contact that needs to be counted, like getting your nose booped.")
    print("This program will try finding any boolean avatar parameter changes which may be tied with the contact.")
    print("You have to judge by the name of the parameter to see if it's the one that you're looking for.")
    server.launch()


if __name__ == "__main__":
    main()
