# Imports
from datetime import timedelta, datetime

# Object class for trucks
class Truck:
    def __init__(self, ID, capacity, load, mileage, current_address, departure_time):
        self.ID = ID # Truck ID
        self.capacity = capacity # Limit that truck can carry
        self.speed = 18 # Set speed of truck
        self.load = load # How many packages are in the truck
        self.mileage = mileage # How many miles truck traveled
        self.current_address = current_address # Where the truck is currently
        # Times associated with truck
        self.departure_time = departure_time
        self.time = datetime.combine(datetime.today(), departure_time)

    # Default string
    def __str__(self):
        return "%s %s %s %s %s %s %s" % (self.ID, self.capacity, self.speed, self.load, self.mileage,
                                         self.departure_time, self.current_address)

    # How many hours the truck traveled based on speed
    def travel_time(self, miles):
        hours = miles / self.speed
        return timedelta(hours=hours)