# Object class for trucks
from datetime import timedelta


class Truck:
    def __init__(self, ID, capacity, speed, load, mileage, current_address, departure_time):
        self.ID = ID
        self.capacity = capacity
        self.speed = speed
        self.load = load
        self.mileage = mileage
        self.current_address = current_address
        self.departure_time = departure_time

    def __str__(self):
        return "%s %s %s %s %s %s" % (self.capacity, self.speed, self.load, self.mileage,
                                         self.departure_time, self.current_address)

    def travel_time(self, miles):
        hours = miles / self.speed
        return timedelta(hours=hours)