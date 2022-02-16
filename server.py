import socket, sys, tqdm, os, json, time
from _thread import *

class Server():
    def __init__(self, name, port, peers):
        # Initialize server attributes
        self.SERVER_NAME = name
        SERVER_HOST = "0.0.0.0"
        SERVER_PORT = port
        self.SERVER_PEERS = peers
        self.BUFFER_SIZE = 4096

        # Initialize list for storing server peer sockets
        self.server_sockets = []

        # Initialize list for storing server client sockets
        client_list = []

        # Initialize list for files that need to be uploaded across all servers
        self.upload_queue = []

        # Create server socket and bind address and port
        server_socket = socket.socket()
        server_socket.bind((SERVER_HOST, SERVER_PORT))
        server_socket.listen(5)
        print(f"[*] {self.SERVER_NAME} server listening as {SERVER_HOST}:{SERVER_PORT}.")

        # Start a new thread the connects to server peers
        start_new_thread(self.connect_to_slaves, ())

        # Listen for clients
        while True:
            # Create socket for client and store address
            client_socket, address = server_socket.accept()
            print(f"[+] {address} is connected.")

            # Append client socket to list
            client_list.append(start_new_thread(self.on_new_client, (client_socket, address)))

    def connect_to_slaves(self):
        # Wait for 5 seconds before connecting to peers
        time.sleep(5)

        # Connect to peers if not yet connected
        if self.server_sockets == []:
            try:
                # Iterate through server peer ports
                for port in self.SERVER_PEERS:
                    # Connect to peer
                    server_socket = socket.socket()
                    print(f"[+] Connecting to 0.0.0.0:{port}.")
                    server_socket.connect(("0.0.0.0", port))
                    print(f"[+] Connected to 0.0.0.0:{port}.")

                    # Append server peer socket to list
                    self.server_sockets.append(server_socket)

                # Keep synchronizing servers
                self.synchronize_servers()

            except Exception as e:
                print(e)
                for port in self.SERVER_PEERS:
                    self.port.close()

    def download(self, client_socket, address, filename):
        print(f"[*] Sending {filename} to {address}.")
        try:
            filesize = os.path.getsize(filename)

            with open(self.SERVER_NAME + "/" + filename, "rb") as f:
                while True:
                    bytes_read = f.read(self.BUFFER_SIZE)
                    if not bytes_read:
                        break
                    client_socket.sendall(bytes_read)
        except:
            print("[!] File not found.")

    def upload(self, client_socket, address, filename):
        print(f"[*] Receiving {filename} from {address}.")
        try:
            with open(self.SERVER_NAME + "/" + filename, "wb") as f:
                while True:
                    bytes_read = client_socket.recv(self.BUFFER_SIZE)
                    if not bytes_read:
                        break
                    f.write(bytes_read)
            self.upload_queue.append(filename)
        except Exception as e:
            print(e)
            print("[!] Can't write file.")

    def synchronize_servers(self):
        while True:
            # print(self.upload_queue)
            try:
                if self.upload_queue:
                    for filename in self.upload_queue:
                        print("[*] New file was uploaded. Synchronizing servers.")
                        for peer in self.server_sockets:
                            filesize = os.path.getsize(filename)
                            msg = {"command" : "upload", "filename" : filename, "filesize" : filesize}

                            peer.sendall(bytes(json.dumps(msg), encoding = "utf-8"))

                            self.download(peer, "127.0.0.1", filename)
                        self.upload_queue.remove(filename)
            except Exception as e:
                print(e)
                pass


    def on_new_client(self, client_socket, address):
        while True:
            message = client_socket.recv(self.BUFFER_SIZE)
            if message:
                parsed = json.loads(message)
                if parsed["command"] == "download":
                    filename = parsed["filename"]
                    self.download(client_socket, address, filename)

                elif parsed["command"] == "upload":
                    filename = parsed["filename"]
                    self.upload(client_socket, address, filename)

                elif parsed["command"] == "exit":
                    client_socket.close()
