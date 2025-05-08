from datetime import datetime


# Object class for packages
class Package:
    def __init__(self, ID, address, city, state, zip_code, deadline, weight, status):
        self.ID = ID
        self.address = address
        self.original_address = address
        self.city = city
        self.state = state
        self.zip_code = zip_code
        self.deadline = deadline
        self.weight = weight
        self.status = status
        self.departure_time = None
        self.arrival_time = None
        self.in_truck_id = None

    def __str__(self):
        return "%s, %s, %s, %s, %s, %s, %s" % (self.ID, self.address, self.city, self.state, self.zip_code, self.weight,
                                               self.status)

    def update_status(self, current_time: datetime):
        if self.arrival_time is not None and self.arrival_time <= current_time:
            self.status = "Delivered"
        elif self.departure_time is not None and self.departure_time <= current_time:
            self.status = "On The Way"
        else:
            self.status = "At Hub"

