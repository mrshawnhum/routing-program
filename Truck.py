# Object class for trucks
from datetime import timedelta


class Truck:
    def __init__(self, capacity, speed, load, mileage, current_address, departure_time):
        self.capacity = capacity
        self.speed = speed
        self.load = load
        self.mileage = mileage
        self.current_address = current_address
        self.departure_time = departure_time

    def __str__(self):
        return "%s %s %s %s %s %s" % (self.capacity, self.speed, self.load, self.mileage,
                                         self.departure_time, self.current_address)

    @property
    def remaining_capacity(self):
        return self.capacity - len(self.load)

    def travel_time(self, miles):
        hours = miles / self.speed
        return timedelta(hours=hours)