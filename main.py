import threading
from opcua import Server, ua




class Tanker:
    def __init__(self, fuel_type, fuel_level, capacity):
        self.fuel_type = fuel_type
        self.fuel_level = fuel_level
        self.capacity = capacity
        self.temperature = 20.0
        self.pressure = 1.0


class gas_station:
    def __init__(self, fuel_type, price):
        self.fuel_type = fuel_type
        self.price = price
        self.dispenced_fuel = int
        self.sold_fuel = int


# Information about OPC UA server is from: https://habr.com/ru/articles/341728/
def run_opcua_server():
    server = Server()
    server.set_endpoint("opc.tcp://127.0.0.1:4840/")
    server.set_server_name("Server")

    idx = server.register_namespace("TankerSystemControl")
    tankers = server.nodes.objects.add_object(idx, "Tankers")
    station = server.nodes.objects.add_object(idx, "Station")

    objects = server.get_objects_node()
    server.start()
    print("OPC UA Servers was started")


def main():
    print("Starting...")
    run_opcua_server()


if __name__ == "__main__":
   main()