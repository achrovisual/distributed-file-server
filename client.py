import socket
import os
import json
import sys
import time

BUFFER_SIZE = 4096

host = "0.0.0.0"
port = 5001

try:
    s = socket.socket()

    print(f"[+] Connecting to {host}:{port}")
    s.connect((host, port))
    print("[+] Connected.")

    while True:
        try:
            data = input("Client > ")

            data = data.split(" ", 1)

            if data[0] == "upload":
                try:
                    filesize = os.path.getsize(data[1])
                    msg = {"command" : data[0], "filename" : data[1], "filesize" : filesize}

                    s.sendall(bytes(json.dumps(msg), encoding = "utf-8"))
                    time.sleep(2)
                    with open(msg["filename"], "rb") as f:
                        while True:
                            bytes_read = f.read(BUFFER_SIZE)
                            if not bytes_read:
                                break
                            s.sendall(bytes_read)
                except Exception as e:
                    print(e)
                    print("File not found.")

            elif data[0] == "download":
                try:
                    msg = {"command" : data[0], "filename" : data[1]}
                    s.sendall(bytes(json.dumps(msg), encoding = "utf-8"))
                    with open(data[1], "wb") as f:
                        while True:
                            bytes_read = s.recv(BUFFER_SIZE)
                            if not bytes_read:
                                break
                            f.write(bytes_read)
                except Exception as e:
                    print(e)


            elif data[0] == "exit":
                s.close()
                sys.exit(0)

        except Exception as e:
            print(e)

except KeyboardInterrupt:
    s.close()
    sys.exit(0)
finally:
    s.close()
