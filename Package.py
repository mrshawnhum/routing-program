# Object class for packages
class Package:
    def __init__(self, packageID, address, deadline, city, zipCode, weight, status):
        self.packageID = packageID
        self.address = address
        self.deadline = deadline
        self.city = city
        self.zipCode = zipCode
        self.weight = weight
        self.status = status
        self.departureTime = None
        self.arrivalTime = None