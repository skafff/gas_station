import threading
import time
import random
from opcua import Server, ua

fuel_dict = {0: "АИ-92", 1: "АИ-95", 2: "АИ-100", 3: "ДТ"}


class Tanker:
    def __init__(self, tanker_id, fuel_type, fuel_level, capacity=2000):
        self.tanker_id = tanker_id
        self.fuel_type = fuel_type
        self.fuel_level = fuel_level
        self.capacity = capacity
        self.temperature = 20
        self.pressure = 1.0
        self.lock = threading.Lock()

    def dispense_fuel(self, fuel_quantity):
        with self.lock:
            if self.fuel_level >= fuel_quantity:
                self.fuel_level -= fuel_quantity
                print(
                    f"Gived {fuel_quantity} l of fuel {self.fuel_type} from {self.tanker_id}! Fuel level is {self.fuel_level} l")
                return True
            else:
                print(f"Not enough fuel in {self.tanker_id}!")
                return False

    def update(self, level, temperature, pressure):
        with self.lock:
            self.fuel_level = max(0, min(level, self.capacity))
            self.temperature = temperature
            self.pressure = pressure
            print(
                f"Tanker {self.tanker_id} fuel level is: {self.fuel_level} l, temperature is: {self.temperature}°C, pressure is: {self.pressure} Bar")


class Station:
    def __init__(self, station_id, fuel_type, price):
        self.station_id = station_id
        self.fuel_type = fuel_type
        self.price = price
        self.dispensed_fuel = 0.0
        self.sold_fuel = 0.0
        self.is_busy = False
        self.lock = threading.Lock()

    def start_fueling(self, fuel_quantity):
        with self.lock:
            if not self.is_busy:
                print(f"Station {self.station_id} start dispensing {fuel_quantity}l of {self.fuel_type}!")
                self.is_busy = True
                self.dispensed_fuel += fuel_quantity
                return True
            else:
                print(f"Station {self.station_id} with fuel {self.fuel_type} is busy!")
                return False

    def stop_fueling(self, fuel_quantity):
        with self.lock:
            if self.is_busy:
                self.sold_fuel += fuel_quantity
                print(
                    f"Station {self.station_id} sold fuel: {fuel_quantity}l, total cost: {fuel_quantity * self.price}")
                self.is_busy = False
                self.dispensed_fuel = 0.0
                print(f"Station {self.station_id} with fuel {self.fuel_type} is free!")
                return True
            else:
                print(f"Station {self.station_id} with fuel {self.fuel_type} is not busy!")
                return False


class TankerSystemControl:
    def __init__(self):
        self.Tankers = [
            Tanker("Tanker1", "АИ-92", 1500, 2000),
            Tanker("Tanker2", "АИ-95", 1500, 2000),
            Tanker("Tanker3", "АИ-100", 1500, 2000),
            Tanker("Tanker4", "ДТ", 1500, 2000)
        ]
        self.Stations = [
            Station("Station1", "АИ-92", 56.62),
            Station("Station2", "АИ-95", 60.91),
            Station("Station3", "АИ-100", 83.45),
            Station("Station4", "ДТ", 70.59)
        ]
        self.alerts = []
        self.running = False
        self.server = Server()
        self.lock = threading.Lock()

    def auto_fueling(self, fuel_type, fuel_quantity):
        try:
            tanker = next(tanker for tanker in self.Tankers if tanker.fuel_type == fuel_type)
            station = next(station for station in self.Stations if station.fuel_type == fuel_type)
        except StopIteration:
            print(f"Can't find tanker or station for fuel type: {fuel_type}")
            return False

        if station.start_fueling(fuel_quantity):
            if tanker.dispense_fuel(fuel_quantity):
                time.sleep(3)
                station.stop_fueling(fuel_quantity)
                return True
            else:
                station.stop_fueling(0)
                return False
        return False

    def system_monitoring(self):
        while self.running:
            with self.lock:
                for tanker in self.Tankers:
                    # print(f"Monitoring {tanker.tanker_id}: fuel={tanker.fuel_level} l, temp={tanker.temperature}°C, pressure={tanker.pressure} Bar")
                    if tanker.fuel_level < 500:
                        self.add_alert(f"Low fuel in {tanker.tanker_id}: {tanker.fuel_level} l")
                    if tanker.temperature > 40 or tanker.temperature < -10:
                        self.add_alert(f"Abnormal temperature in {tanker.tanker_id}: {tanker.temperature} °C")
                    if tanker.pressure > 2.0 or tanker.pressure < 0.5:
                        self.add_alert(f"Abnormal pressure in {tanker.tanker_id}: {tanker.pressure} Bar")
            time.sleep(2)

    def add_alert(self, message):
        with self.lock:
            self.alerts.append(message)
            self.alerts_node.set_value("; ".join(self.alerts))
            print(f"ACCIDENT: {message}")
            self.handle_emergency(message)

    def handle_emergency(self, message):
        print(f"Handling emergency: {message}")
        if "Low fuel" in message:
            print("Started fuel order procedure...")
            time.sleep(3)
            for tanker in self.Tankers:  # Исправлена опечатка
                tanker.update(2000, tanker.temperature, tanker.pressure)
            print("Fuel was delivered!")
        elif "Abnormal temperature" in message or "Abnormal pressure" in message:
            print("Stopping all stations...")
            for station in self.Stations:
                if station.is_busy:
                    station.stop_fueling(0)

    def run_opcua_server(self):
        self.server.set_endpoint("opc.tcp://127.0.0.1:4840/")
        self.server.set_server_name("GasStationServer")
        self.server.set_security_policy([ua.SecurityPolicyType.NoSecurity])

        idx = self.server.register_namespace("TankerSystemControl")
        objects = self.server.get_objects_node()
        tankers_node = objects.add_object(idx, "Tankers")
        stations_node = objects.add_object(idx, "Stations")
        self.alerts_node = objects.add_object(idx, "Alerts").add_variable(idx, "Messages", "").set_writable()

        for tanker in self.Tankers:
            tanker_node = tankers_node.add_object(idx, tanker.tanker_id)
            tanker_node.add_variable(idx, "FuelType", tanker.fuel_type).set_read_only()
            tanker_node.add_variable(idx, "FuelLevel", tanker.fuel_level).set_writable()
            tanker_node.add_variable(idx, "Temperature", tanker.temperature).set_writable()
            tanker_node.add_variable(idx, "Pressure", tanker.pressure).set_writable()

        for station in self.Stations:
            station_node = stations_node.add_object(idx, station.station_id)
            station_node.add_variable(idx, "FuelType", station.fuel_type).set_read_only()
            station_node.add_variable(idx, "Price", station.price).set_read_only()
            station_node.add_variable(idx, "DispensedFuel", station.dispensed_fuel).set_writable()
            station_node.add_variable(idx, "SoldFuel", station.sold_fuel).set_read_only()
            station_node.add_variable(idx, "IsBusy", station.is_busy).set_writable()


def start(tanker_system):
    tanker_system.run_opcua_server()
    try:
        tanker_system.server.start()
        print("OPC UA Server was started")
        tanker_system.running = True
        threading.Thread(target=tanker_system.system_monitoring, daemon=True).start()
    except Exception as e:
        print(f"Failed to start server: {e}")


def stop(tanker_system):
    tanker_system.running = False
    tanker_system.server.stop()
    print("OPC UA server was stopped")


def main():
    print("Starting...")
    tanker_system_control = TankerSystemControl()
    start(tanker_system_control)

    try:
        while True:
            # fuel = random.choice(list(fuel_dict.values()))
            for station in tanker_system_control.Stations:
                fuel_quantity = random.randint(50, 200)
                tanker_system_control.auto_fueling(station.fuel_type, fuel_quantity)

            for tanker in tanker_system_control.Tankers:
                fuel_level = random.randint(0, 600)
                temperature = random.uniform(-15, 50)
                pressure = random.uniform(0.1, 3.0)
                # print(f"Updating {tanker.tanker_id} with level={fuel_level}, temp={temperature:.1f}, pressure={pressure:.2f}")
                tanker.update(fuel_level, temperature, pressure)

            time.sleep(5)

    finally:
        stop(tanker_system_control)


if __name__ == "__main__":
    main()