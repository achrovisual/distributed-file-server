from server import Server

def main():
    manila_server = Server("Manila", 5003, [5001, 5002])

if __name__ == "__main__":
    main()
