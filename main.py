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
        self.is_broken = False
        self.lock = threading.Lock()

    def dispense_fuel(self, fuel_quantity):
        with self.lock:
            if self.is_broken:
                print(f"Tanker {self.tanker_id} is broken and cannot dispense fuel!")
                return False
            if self.fuel_level >= fuel_quantity:
                self.fuel_level -= fuel_quantity
                print(
                    f"Gived {fuel_quantity} l of fuel {self.fuel_type} from {self.tanker_id}! Fuel level is {self.fuel_level} l"
                )
                return True
            else:
                print(f"Not enough fuel in {self.tanker_id}!")
                return False

    def update(self, level, temperature, pressure):
        with self.lock:
            if random.random() < 0.6:
                temperature = random.randint(45, 60)
                pressure = round(random.uniform(2.5, 3.0), 1)

            self.fuel_level = max(0, min(level, self.capacity))
            self.temperature = temperature
            self.pressure = round(pressure, 1)

            if self.temperature > 40 or self.temperature < -10 or self.pressure > 2.0 or self.pressure < 0.5:
                self.is_broken = True
            else:
                self.is_broken = False

            print(f"Tanker {self.tanker_id} fuel level is: {self.fuel_level} l, temperature is: {self.temperature}°C, pressure is: {self.pressure:.1f} Bar")
            return True

    def repair(self):
        with self.lock:
            self.is_broken = False
            if self.temperature > 40 or self.temperature < -10:
                self.temperature = 20.0
            if self.pressure > 2.0 or self.pressure < 0.5:
                self.pressure = 1.0
            print(f"Tanker {self.tanker_id} repaired! Temperature: {self.temperature}°C, Pressure: {self.pressure:.1f} Bar")
            return True

class Station:
    def __init__(self, station_id, fuel_type, price):
        self.station_id = station_id
        self.fuel_type = fuel_type
        self.price = price
        self.dispensed_fuel = 0.0
        self.sold_fuel = 0.0
        self.is_busy = False
        self.is_broken = False
        self.lock = threading.Lock()

    def start_fueling(self, fuel_quantity):
        with self.lock:
            if self.is_broken:
                print(f"Station {self.station_id} is broken and cannot start fueling!")
                return False
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
            if self.is_broken:
                print(f"Station {self.station_id} is broken and cannot stop fueling!")
                return False
            if self.is_busy:
                self.sold_fuel += fuel_quantity
                print(
                    f"Station {self.station_id} sold fuel: {fuel_quantity}l, total price: {fuel_quantity * self.price}")
                self.is_busy = False
                self.dispensed_fuel = 0.0
                print(f"Station {self.station_id} with fuel {self.fuel_type} is free!")
                return True
            else:
                print(f"Station {self.station_id} with fuel {self.fuel_type} is not busy!")
                return False

    def repair(self):
        with self.lock:
            self.is_broken = False
            if self.is_busy:
                self.is_busy = False
                self.dispensed_fuel = 0.0
                print(f"Station {self.station_id} was busy and has been freed.")
            print(f"Station {self.station_id} repaired!")
            return True

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
        self.tanker_nodes = {}
        self.station_nodes = {}
        self.lock = threading.Lock()

    def auto_fueling(self, fuel_type, fuel_quantity):
        print(f"Attempting to fuel {fuel_type} with {fuel_quantity}l")
        try:
            tanker = next(tanker for tanker in self.Tankers if tanker.fuel_type == fuel_type)
            station = next(station for station in self.Stations if station.fuel_type == fuel_type)
        except StopIteration:
            print(f"Can't find tanker or station for fuel type: {fuel_type}")
            return False

        if station.start_fueling(fuel_quantity):
            if tanker.dispense_fuel(fuel_quantity):
                time.sleep(1)
                station.stop_fueling(fuel_quantity)
                return True
            else:
                station.stop_fueling(0)
                return False
        return False

    def system_monitoring(self):
        while self.running:
            try:
                for tanker in self.Tankers:
                    self.tanker_nodes[tanker.tanker_id]["FuelLevel"].set_value(tanker.fuel_level)
                    self.tanker_nodes[tanker.tanker_id]["Temperature"].set_value(tanker.temperature)
                    self.tanker_nodes[tanker.tanker_id]["Pressure"].set_value(tanker.pressure)
                    self.tanker_nodes[tanker.tanker_id]["IsBroken"].set_value(tanker.is_broken)

                    if tanker.is_broken:
                        if -10 <= tanker.temperature <= 40 and 0.5 <= tanker.pressure <= 2.0:
                            tanker.repair()

                    if tanker.fuel_level < 500:
                        self.add_alert(f"Low fuel in {tanker.tanker_id}: {tanker.fuel_level} l")
                    if tanker.temperature > 40:
                        self.add_alert(f"Abnormal temperature in {tanker.tanker_id}: {tanker.temperature:.1f} °C")
                    if tanker.temperature < -10:
                        self.add_alert(f"Abnormal low temperature in {tanker.tanker_id}: {tanker.temperature:.1f} °C")
                    if tanker.pressure > 2.0:
                        self.add_alert(f"Abnormal pressure in {tanker.tanker_id}: {tanker.pressure:.1f} Bar")
                    if tanker.pressure < 0.5:
                        self.add_alert(f"Abnormal low pressure in {tanker.tanker_id}: {tanker.pressure:.1f} Bar")

                for station in self.Stations:
                    self.station_nodes[station.station_id]["DispensedFuel"].set_value(station.dispensed_fuel)
                    self.station_nodes[station.station_id]["SoldFuel"].set_value(station.sold_fuel)
                    self.station_nodes[station.station_id]["IsBusy"].set_value(station.is_busy)
                    self.station_nodes[station.station_id]["IsBroken"].set_value(station.is_broken)

                    if station.is_broken:
                        station.repair()

                time.sleep(1)
            except Exception as e:
                print(f"Error in system_monitoring: {e}")
                time.sleep(1)

    def add_alert(self, message):
        print(f"Adding alert: {message}")
        with self.lock:
            self.alerts.append(message)
            try:
                self.alerts_node.set_value(message)
            except Exception as e:
                print(f"Failed to update alerts_node: {e}")
        print(f"ACCIDENT: {message}")
        self.handle_emergency(message)

    def handle_emergency(self, message):
        print(f"Handling emergency: {message}")
        with self.lock:
            if "Low fuel" in message:
                print("Started fuel order procedure...")
                time.sleep(3)
                for tanker in self.Tankers:
                    tanker.update(tanker.capacity, tanker.temperature, tanker.pressure)
                    tanker.repair()
                print("Fuel was delivered!")

            elif "Abnormal temperature" in message or "Abnormal pressure" in message:
                print("Stopping all stations and repairing tankers...")
                for station in self.Stations:
                    if station.is_busy:
                        station.stop_fueling(0)
                    station.repair()

                for tanker in self.Tankers:
                    time.sleep(1)
                    if tanker.temperature > 40 or tanker.temperature < -10:
                        tanker.temperature = random.uniform(-10, 40)
                        print(f"Corrected temperature for {tanker.tanker_id}: {tanker.temperature:.1f} °C")
                    if tanker.pressure > 2.0 or tanker.pressure < 0.5:
                        tanker.pressure = round(random.uniform(0.5, 2.0), 1)
                        print(f"Corrected pressure for {tanker.tanker_id}: {tanker.pressure:.1f} Bar")
                    tanker.repair()

            self.alerts = [msg for msg in self.alerts if msg != message]
            try:
                self.alerts_node.set_value("; ".join(self.alerts) if self.alerts else "")
            except Exception as e:
                print(f"Failed to update alerts_node: {e}")

    def run_opcua_server(self):
        try:
            self.server.set_endpoint("opc.tcp://127.0.0.1:4840/")
            self.server.set_server_name("GasStationServer")
            idx = self.server.register_namespace("TankerSystemControl")
            objects = self.server.get_objects_node()

            tankers_node = objects.add_object(idx, "Tankers")
            stations_node = objects.add_object(idx, "Stations")
            alerts_obj = objects.add_object(idx, "Alerts")

            self.alerts_node = alerts_obj.add_variable(idx, "Messages", "")
            self.alerts_node.set_writable()

            for tanker in self.Tankers:
                tanker_node = tankers_node.add_object(idx, tanker.tanker_id)
                self.tanker_nodes[tanker.tanker_id] = {
                    "FuelType": tanker_node.add_variable(idx, "FuelType", tanker.fuel_type),
                    "FuelLevel": tanker_node.add_variable(idx, "FuelLevel", tanker.fuel_level),
                    "Temperature": tanker_node.add_variable(idx, "Temperature", tanker.temperature),
                    "Pressure": tanker_node.add_variable(idx, "Pressure", tanker.pressure),
                    "IsBroken": tanker_node.add_variable(idx, "IsBroken", tanker.is_broken)
                }

                self.tanker_nodes[tanker.tanker_id]["FuelType"].set_read_only()
                self.tanker_nodes[tanker.tanker_id]["FuelLevel"].set_writable()
                self.tanker_nodes[tanker.tanker_id]["Temperature"].set_writable()
                self.tanker_nodes[tanker.tanker_id]["Pressure"].set_writable()
                self.tanker_nodes[tanker.tanker_id]["IsBroken"].set_writable()

            for station in self.Stations:
                station_node = stations_node.add_object(idx, station.station_id)
                self.station_nodes[station.station_id] = {
                    "FuelType": station_node.add_variable(idx, "FuelType", station.fuel_type),
                    "Price": station_node.add_variable(idx, "Price", station.price),
                    "DispensedFuel": station_node.add_variable(idx, "DispensedFuel", station.dispensed_fuel),
                    "SoldFuel": station_node.add_variable(idx, "SoldFuel", station.sold_fuel),
                    "IsBusy": station_node.add_variable(idx, "IsBusy", station.is_busy),
                    "IsBroken": station_node.add_variable(idx, "IsBroken", station.is_broken)
                }

                self.station_nodes[station.station_id]["Price"].set_read_only()
                self.station_nodes[station.station_id]["DispensedFuel"].set_writable()
                self.station_nodes[station.station_id]["SoldFuel"].set_writable()
                self.station_nodes[station.station_id]["IsBusy"].set_writable()
                self.station_nodes[station.station_id]["IsBroken"].set_writable()

        except Exception as e:
            print(f"Error setting up OPC UA server: {e}")

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
    try:
        tanker_system.server.stop()
        print("OPC UA server was stopped")
    except Exception as e:
        print(f"Error stopping server: {e}")

def main():
    print("Starting...")
    tanker_system_control = TankerSystemControl()
    start(tanker_system_control)
    try:
        while True:
            for station in tanker_system_control.Stations:
                fuel_quantity = random.randint(50, 200)
                tanker_system_control.auto_fueling(station.fuel_type, fuel_quantity)

            for tanker in tanker_system_control.Tankers:
                fuel_change = random.randint(-100, 50)
                new_fuel_level = max(0, min(tanker.fuel_level + fuel_change, tanker.capacity))
                temperature = random.randint(-15, 50)
                pressure = round(random.uniform(0.1, 3.0), 1)
                tanker.update(new_fuel_level, temperature, pressure)

            time.sleep(10)
    except Exception as e:
        print(f"Error in main loop: {e}")
    finally:
        stop(tanker_system_control)

if __name__ == "__main__":
    main()