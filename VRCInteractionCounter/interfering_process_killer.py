import time
import psutil
from logger import log


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
    time.sleep(0.5)
    return
