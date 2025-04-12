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






def main():
    print("hell")



if __name__ == "__main__":
   main()