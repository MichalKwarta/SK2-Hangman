import select
import socket
import threading
from os.path import exists
from queue import Queue

import PyQt5.QtCore as Qt
import PyQt5.QtWidgets as qtw


class Communication:
    messageQueue: Queue = Queue()
    timeLimit: int = 15
    connectionStable: bool = True

    def __init__(self, GUIReference=None, address: str = '127.0.0.1', port: int = 2137, isHost: bool = False):
        self.address: str = address
        self.port: int = port
        self.isHost: bool = isHost
        self.GUI = GUIReference

    def listen(self, s: socket):
        while self.connectionStable:
            ready_to_read, _, _ = select.select([s], [], [], self.timeLimit)
            if ready_to_read:
                msg_size = int(s.recv(2, socket.MSG_WAITALL).decode("UTF-8"))
                print(msg_size, " size")

                message = s.recv(msg_size, socket.MSG_WAITALL).decode("UTF-8")

                print(list(message))

                self.handleMessage(Message(message))

                # handle message

            else:
                print("timed out")
                # TODO: handling timeout + change time limit to 30(?)

    def write(self, s: socket):

        # it is blocking, but it blocks in a thread, so it doesnt really matter
        # theoretically it will block until it gets message from queue,
        # then it will block on select, which should respect timeout unlike get

        while self.connectionStable:
            message: str = self.messageQueue.get(block=True)
            _, ready_to_write, _ = select.select([], [s], [], self.timeLimit)
            if ready_to_write:
                sent = s.send((str(message)).encode("UTF-8"))
            else:
                print("timed out")
                # TODO: handling timeout + change time limit to 30(?)

    def addTexttoQueue(self, text):
        self.messageQueue.put(text)

    def getMessage(self) -> "Message":
        try:
            msg = self.readQueue.get(block=True, timeout=self.timeLimit)
        except:
            msg = "9##!"
        return msg

    def run(self):
        self.messageQueue.queue.clear()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.address, self.port))
            readerThread = threading.Thread(target=self.listen, args=(s,))
            writerThread = threading.Thread(target=self.write, args=(s,))

            readerThread.start()
            writerThread.start()

            readerThread.join()
            writerThread.join()

    def handleMessage(self, msg: "Message") -> None:

        
        if msg.code ==1:
                    
            if msg.text.isnumeric():  # received id, need to save it to file
                self.GUI.QtStack.setCurrentWidget(self.GUI.GameScene)
                with open("id.txt", "w+") as f:
                    f.write(msg.text)
            else:
                self.GUI.setErrorScene(
                    '''This nick is taken!
                    \nPlease connect once more with different name ;-)''')


        elif msg.code ==2:
            player, score = msg.text.split('SCORE')
            self.GUI.playersDict[player] = score
            self.GUI.updateLeaderBoard()

        elif msg.code ==3:
            pass

        elif msg.code ==4:
            
                if msg.text == "sendID":
                    if exists("id.txt"):
                        with open("id.txt", "r+") as f:
                            id = f.readline()
                        # send id to let server verify if i was connected
                        self.addTexttoQueue(Message(id, 4))
                    else:  # cant find id file
                        self.GUI.setErrorScene(
                            "You weren't playing in this game\n Please wait for the game to end")

                elif msg.text == "valid":
                    self.GUI.QtStack.setCurrentWidget(self.GUI.GameScene)

                elif msg.text == "invalid":
                    self.GUI.setErrorScene(
                        '''Someone else was playing under this nickname,
                        \nEnter your nickname or wait for the game to end''')
                else:
                    print("No idea what happened")

        elif msg.code == 5:
            self.GUI.setPassword(msg.text)

        else:  # default case
            self.GUI.setErrorScene("No idea what happened")
            self.connectionStable = False
            # TODO: Handle socket error


class Message:

    def __init__(self, text: str, code=None):
        if code:
            self.code: int = int(code)
            self.text: str = text

        else:
            self.code = int(text[0])
            self.text = text[2:-1]
        self.length = str(len(self.text)+3)  # +3 because of code + 2*#

    def __str__(self):
        return f"{self.length.zfill(2)}{self.code}#{self.text}#"
