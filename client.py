import socket, sys, os, json, time, hashlib
# os.environ["PYTHONHASHSEED"] = '1234' # Not needed for local

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

BUFFER_SIZE = 4096

host = "0.0.0.0"
port = 5001

try:
    #s = socket.socket()

    print(f"[+] Connecting to {host}:{port}")
    # s.connect((host, port))

    firstPass = True
    while True:
        s = socket.socket()
        disconnected = True
        while disconnected:
            try:
                s.connect((host, port))
                disconnected = False
                if firstPass:
                    firstPass = False
                    print("[+] Connected.")
            except Exception as e:
                time.sleep(2)
        try:
            args = input("Client > ")

            args = args.split(" ", 1)

            if args[0] == "upload":
                try:
                    bytes_read = None
                    bytes_read_list = []
                    checksum = None
                    with open(args[1], "rb") as f:
                        while True:
                            data = f.read(BUFFER_SIZE)
                            if bytes_read:
                                bytes_read += data
                                bytes_read_list.append(data)
                            else:
                                bytes_read = data
                                bytes_read_list.append(data)
                            if not data:
                                break
                    checksum = hashlib.md5(bytes_read).hexdigest()

                    msg = {"command" : args[0], "filename" : args[1], "checksum" : checksum}

                    s.sendall(bytes(json.dumps(msg), encoding = "utf-8"))
                    time.sleep(2)

                    while True:
                        message = s.recv(BUFFER_SIZE).decode("utf-8")
                        if message:
                            parsed = json.loads(message)
                            # print(str(parsed))
                            if parsed["command"] == "ack":
                                while bytes_read_list:
                                    s.sendall(bytes_read_list.pop(0))
                                break

                            elif parsed["command"] == "nack":
                                print("[!] File already exists in the server.")
                                break

                    s.close()
                except Exception as e:
                    print(e)
                    print("File not found.")

            elif args[0] == "download":
                try:
                    msg = {"command" : args[0], "filename" : args[1], "flag" : True}
                    s.sendall(bytes(json.dumps(msg), encoding = "utf-8"))

                    with open(args[1], "wb") as f:
                        while True:
                            bytes_read = s.recv(BUFFER_SIZE)
                            if not bytes_read:
                                break
                            f.write(bytes_read)
                except Exception as e:
                    print(e)

            elif args[0] == "list":
                try:
                    msg = {"command" : args[0]}
                    s.sendall(bytes(json.dumps(msg), encoding = "utf-8"))

                    message = None

                    while True:
                        message = s.recv(BUFFER_SIZE).decode("utf-8")

                        if message:
                            break

                    parsed = json.loads(message)
                    files_list = parsed["files"]
                    # print(files_list)

                    for file in files_list:
                        print(f'{bcolors.OKGREEN}{file["filename"]}{bcolors.ENDC}')

                except Exception as e:
                    print(e)

            elif args[0] == "delete":
                try:
                    msg = {"command" : args[0], "filename" : args[1]}
                    s.sendall(bytes(json.dumps(msg), encoding = "utf-8"))

                except Exception as e:
                    print(e)

            elif args[0] == "rename":
                try:
                    names = args[1].split(' ', 1)
                    msg = {"command" : args[0], "filename" : names[0], "newfilename" : names[1]}

                    # print(msg)
                    s.sendall(bytes(json.dumps(msg), encoding = "utf-8"))

                except Exception as e:
                    print(e)

            elif args[0] == "exit":
                s.close()
                sys.exit(0)

        except Exception as e:
            print(e)

except KeyboardInterrupt:
    s.close()
    sys.exit(0)
finally:
    s.close()
