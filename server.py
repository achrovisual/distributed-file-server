import socket, sys, os, json, time, hashlib
from _thread import *
# os.environ["PYTHONHASHSEED"] = '1234' # Not needed for local

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

        self.files_list = []
        self.get_files_list()
        # print(self.files_list)

        # Create server socket and bind address and port
        server_socket = socket.socket()
        server_socket.bind((SERVER_HOST, SERVER_PORT))
        server_socket.listen(5)
        print(f"[*] {self.SERVER_NAME} server listening as {SERVER_HOST}:{SERVER_PORT}.")

        # Create server file directory
        if not os.path.exists(self.SERVER_NAME):
            print(f"[*] Server file directory created ({os.getcwd()}/{self.SERVER_NAME})")
            os.mkdir(self.SERVER_NAME)

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

        while True:
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
                    # time.sleep(10)
                    self.synchronize_servers()

                except Exception as e:
                    print(e)
                    for port in self.server_sockets:
                        port.close()
            else:
                self.synchronize_servers()


    def download(self, client_socket, address, filename, flag=False):
        print(f"[*] Request to download {filename} from {address} received.")
        try:
            with open(self.SERVER_NAME + "/" + filename, "rb") as f:
                while True:
                    bytes_read = f.read(self.BUFFER_SIZE)
                    if not bytes_read:
                        break
                    client_socket.sendall(bytes_read)

            if flag:
                client_socket.close()

        except:
            print("[!] File not found.")

    def upload(self, client_socket, address, filename, checksum=None):
        print(f"[*] Request to upload {filename} from {address} received.")
        try:
            if self.check(self.files_list, "checksum", checksum):
                print("[!] File already exists in the server.")
                print("[-] Aborting download.")
                msg = {"command" : "nack"}
                client_socket.sendall(bytes(json.dumps(msg), encoding = "utf-8"))
                pass
            else:
                print("[*] File transfer started")
                # data = None

                msg = {"command" : "ack"}
                client_socket.sendall(bytes(json.dumps(msg), encoding = "utf-8"))

                with open(self.SERVER_NAME + "/" + filename, "wb") as f:
                    while True:
                        bytes_read = client_socket.recv(self.BUFFER_SIZE)
                        # if data:
                        #     data += bytes_read
                        # else:
                        #     data = bytes_read
                        if not bytes_read:
                            break
                        f.write(bytes_read)

                self.files_list.append({"filename" : filename, "checksum" : checksum})
                self.upload_queue.append({"filename" : filename, "checksum" : checksum})

            # print(self.files_list)
            # print(checksum)

        except Exception as e:
            print(e)
            print("[!] Can't write file.")

    def list_files(self, client_socket, address):
        print(f"[*] Request to get files list from {address} received.")
        try:
            print("[*] Sending files list.")

            msg = {"files" : self.files_list}

            client_socket.sendall(bytes(json.dumps(msg), encoding = "utf-8"))

        except Exception as e:
            print(e)
            print("[!] An error occured while sending files list.")

    def delete_file(self, client_socket, address, filename):
        print(f"[*] Request to delete {filename} from {address} received.")
        try:
            print("[*] Deleting file...")
            os.remove(self.SERVER_NAME + "/" + filename)

            for file in self.files_list:
                if(file["filename"] == filename):
                    self.files_list.remove(file)
                    break

            print(f"[*] {filename} deleted.")

        except Exception as e:
            print(e)
            print("[!] An error occured while deleting file.")

    def rename_file(self, client_socket, address, filename, newfilename):
        print(f"[*] Request to rename {filename} to {newfilename} from {address} received.")
        try:
            print("[*] Renaming file...")
            os.rename(self.SERVER_NAME + "/" + filename, self.SERVER_NAME + "/" + newfilename)

            for file in self.files_list:
                if(file["filename"] == filename):
                    file["filename"] = newfilename
                    break

            print(f"[*] {filename} renamed to {newfilename}.")

        except Exception as e:
            print(e)
            print("[!] An error occured while renaming file.")

    def synchronize_servers(self):
        # print(self.upload_queue)
        try:
            if self.upload_queue:
                for file in self.upload_queue:
                    print("[*] New file was uploaded. Synchronizing servers.")
                    for peer in self.server_sockets:

                        msg = {"command" : "upload", "filename" : file["filename"], "checksum" : file["checksum"]}

                        peer.sendall(bytes(json.dumps(msg), encoding = "utf-8"))

                        while True:
                            message = peer.recv(self.BUFFER_SIZE).decode("utf-8")
                            if message:
                                parsed = json.loads(message)
                                # print(str(parsed))
                                if parsed["command"] == "ack":
                                    self.download(peer, "127.0.0.1", file["filename"])
                                    break

                                elif parsed["command"] == "nack":
                                    print("[!] File already exists in the server.")
                                    break
                        peer.close()
                    self.upload_queue.remove(file)
                    print("[*] Re-establishing connection with slaves...")
                    self.server_sockets = []
        except Exception as e:
            print(e)
            pass

    def get_files_list(self):
        for root, dir, files in os.walk(self.SERVER_NAME + "/"):
            for file in files:
                data = open(self.SERVER_NAME + "/" + file, "rb").read()
                self.files_list.append({"filename" : file, "checksum" : hashlib.md5(data).hexdigest()})
                # self.upload_queue.append(file)

    def on_new_client(self, client_socket, address):
        while True:
            message = client_socket.recv(self.BUFFER_SIZE).decode("utf-8")

            if message:
                try:
                    parsed = json.loads(message)
                    # print(str(parsed))
                    if parsed["command"] == "download":
                        filename = parsed["filename"]
                        flag = parsed["flag"]
                        self.download(client_socket, address, filename, flag)

                    elif parsed["command"] == "upload":
                        filename = parsed["filename"]
                        checksum = parsed["checksum"]
                        self.upload(client_socket, address, filename, checksum)

                    elif parsed["command"] == "list":
                        self.list_files(client_socket, address)

                    elif parsed["command"] == "delete":
                        filename = parsed["filename"]
                        self.delete_file(client_socket, address, filename)

                    elif parsed["command"] == "rename":
                        filename = parsed["filename"]
                        newfilename = parsed["newfilename"]
                        self.rename_file(client_socket, address, filename, newfilename)

                    elif parsed["command"] == "exit":
                        client_socket.close()

                except Exception as e:
                    print(e)
                    print(message)
                    print("[!] Malformed message received.")

    def check(self, data, key, value):
        for i in data:
            try:
                # print(i[key])
                # print(value)
                if(i[key]==value):
                    # print('pass')
                    return True
            except:
                pass
        return False
