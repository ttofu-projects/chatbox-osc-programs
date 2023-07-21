from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
import time
import psutil

avatar_parameters_to_track = ["parameter_a", "parameter_b"]


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
    print("[Interfering process killer] Searching for interfering process")
    pid = find_interfering_process(port)
    if pid == -1:
        print("[Interfering process killer] No interfering processes are found")
        return
    psutil.Process(pid).kill()
    print("[Interfering process killer] Interfering process is found and killed")
    return


class OSCServer:
    def __init__(self, port):
        self.dispatcher = Dispatcher()
        self.dispatcher.set_default_handler(self.osc_default)

        print("[OSC server] Applying handlers for parameters specified in the beginning of the file")
        for name in avatar_parameters_to_track:
            self.dispatcher.map("/avatar/parameters/" + name, self.parameter_updated)

        print("[OSC server] Creating server with port " + str(port))
        try:
            self.server = BlockingOSCUDPServer(("127.0.0.1", port), self.dispatcher)
        except OSError:
            print("[OSC server] The socket is already in use, attempting to kill the interfering process")
            kill_interfering_process(port)
            time.sleep(0.5)  # Safety wait
            self.server = BlockingOSCUDPServer(("127.0.0.1", port), self.dispatcher)
        print("[OSC server] Server successfully created with port " + str(port))

    def parameter_updated(self, address, *args):
        name = address.split("parameters/")[1]
        print("[OSC server] " + name + " is now " + str(args[0]))

    def osc_default(self, adress, *args):
        pass

    def launch(self):
        self.server.serve_forever()

    def shutdown(self):
        print("[OSC server] Shutting down")
        self.server.shutdown()


if __name__ == "__main__":
    server = OSCServer(9001)
    try:
        server.launch()
    except KeyboardInterrupt:
        server.shutdown()
