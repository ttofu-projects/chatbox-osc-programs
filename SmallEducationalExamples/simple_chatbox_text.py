from pythonosc import udp_client
import time

text = "YOUR TEXT HERE"


class ChatboxClient:
    def __init__(self, port):
        self.client = udp_client.SimpleUDPClient("127.0.0.1", port)

    def send(self, text):
        self.client.send_message("/chatbox/input", [text, True])
        print("[Chatbox client] Sent a message: \"" + text + "\"")


if __name__ == "__main__":
    client = ChatboxClient(9000)
    while True:
        client.send(text)
        time.sleep(5)
