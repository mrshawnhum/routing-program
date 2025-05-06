# Student ID: 012214405
from typing import List

# Imports
from CreateHashTable import CreateHashTable
from Package import Package
from Truck import Truck
import csv
from datetime import datetime, time, timedelta

# Global variables
HUB_ADDRESS = "4001 South 700 East"
truck1 = Truck(1, 16, [], 0, HUB_ADDRESS, time(8, 00))
truck2 = Truck(2, 16, [], 0, HUB_ADDRESS, time(9, 00))
truck3 = Truck(3, 16, [], 0, HUB_ADDRESS, time(10, 00))

def load_packages(filename="CSV/WGUPS-data.csv"):
    package_table = CreateHashTable(initial_capacity=40)

    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            # unpack data
            pkg_ID, address, city, state, zip_code, deadline, pkg_weight = row

            # convert type
            ID = int(pkg_ID)
            weight = int(pkg_weight)

            # convert deadline to time objects
            raw_time = row[5].strip().upper()
            if raw_time == "EOD":
                deadline = None
            else:
                deadline = datetime.strptime(raw_time, "%I:%M %p").time()

            # defaults
            status = "At Hub"

            # build Package objects
            package = Package(ID, address.strip(), city.strip(), state.strip(), zip_code.strip(), deadline, weight,
                              status)

            package_table.insert(ID, package)

    return package_table
# load package table
package_hash_table = load_packages()

def load_distances_and_addresses(filename):
    with open(filename, newline='') as csvfile:
        # read the data
        reader = csv.reader(csvfile)
        next(reader)
        rows = list(reader)

        # find addresses
        addresses = [row[1].rsplit("(", 1)[0].strip() for row in rows]
        addresses[0] = HUB_ADDRESS

        # find distances
        num = len(addresses)
        distance_matrix = [
            [float(x) if x else None for x in row[2: 2 + num]]
            for row in rows
        ]

        return addresses, distance_matrix


# load distance and address list
address_list, distance_list = load_distances_and_addresses("CSV/WGUPS-distance.csv")


def distance_between(address1, address2):
    x = address_list.index(address1)
    y = address_list.index(address2)

    distance = distance_list[x][y]
    if distance is None:
        distance = distance_list[y][x]

    return distance

# Load packages to trucks with hard requirements (delayed, into a certain truck, with certain packages, etc)
def load_constraint_package():
    # Loop through all the package IDs
    for packageID in range(1, 41):
        # If the package ID match the following numbers, load into truck1
        if packageID in (13, 14, 15, 16, 19, 20, 21):
            package = package_hash_table.lookup(packageID)
            truck1.load.append(package)

        # If the package ID match the following numbers, load into truck2
        if packageID in (3, 18, 36, 37, 38):
            package = package_hash_table.lookup(packageID)
            truck2.load.append(package)

        # If the package ID match the following numbers, load into truck3
        if packageID in (6, 9, 25, 26, 28, 31, 32):
            package = package_hash_table.lookup(packageID)
            truck3.load.append(package)

# convert time to minutes since midnight
def time_to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute

# Algorithm to assign packages to trucks based on priority, distance, and available space in truck
def assign_packages_to_trucks(fleet: List["Truck"], packages: List["Package"]):
    # helper function to map package deadline to amount of minutes
    def dl_min(p):
        return time_to_minutes(p.deadline) if isinstance(p.deadline, time) else 23 * 60 + 59

    # filter out packages already loaded into truck
    preloaded = {p.ID for t in fleet for p in t.load}
    pool = [p for p in packages if p.ID not in preloaded]

    # Store any package that can't fit
    unassigned = []

    # assign all deadline-sensitive packages and sort by earliest deadline
    timed = sorted([p for p in pool if isinstance(p.deadline, time)],
                   key=dl_min)
    # print("Timed packages:", [(p.ID, p.deadline) for p in timed])

    for pkg in timed:
        best = None  # will hold (truck, arrival_min)
        # print("Trying timed:", pkg.ID, pkg.deadline)
        # skip any truck that is full
        for tr in fleet:
            if len(tr.load) >= tr.capacity:
                continue

            # truck's current clock (in minutes)
            curr = getattr(tr, 'next_available_min',
                           time_to_minutes(tr.departure_time))
            # truck's current location
            loc = tr.current_address

            # Compute travel time
            dist = distance_between(loc, pkg.address)
            travel_min = (dist / tr.speed) * 60
            arrive = curr + travel_min

            # if we can make the deadline, pick the earliest arrival time
            if arrive <= dl_min(pkg) and (best is None or arrive < best[1]):
                best = (tr, arrive)

        # Assign the best truck to meet deadline
        if best:
            tr, arrive = best
            tr.load.append(pkg)
            tr.next_available_min = arrive
            tr.current_address = pkg.address
            pool.remove(pkg)
            # print(f"-- Assigned pkg {pkg.ID} to Truck {tr.ID} at minute {arrive}")
        else:
            unassigned.append(pkg)  # assumes no truck could handle the deadline

    # Assign remaining EOD packages
    eod_left = [p for p in pool if not isinstance(p.deadline, time)]

    # loop through remaining packages with the least priority
    for pkg in eod_left:
        # print("Trying eod:", pkg.ID, pkg.deadline)
        best = None
        for tr in fleet:
            if len(tr.load) >= tr.capacity:
                continue
            curr = getattr(tr, 'next_available_min',
                           time_to_minutes(tr.departure_time))
            dist = distance_between(tr.current_address, pkg.address)
            travel_min = (dist / tr.speed) * 60
            arrive = curr + travel_min

            # pick the truck that can finish prior work and arrive soonest
            if best is None or arrive < best[1]:
                best = (tr, arrive)

        if best:
            tr, arrive = best
            tr.load.append(pkg)
            tr.next_available_min = arrive
            tr.current_address = pkg.address
            pool.remove(pkg)
        else:
            unassigned.append(pkg)


# Routing algorithm
def deliver_packages(truck):
    not_delivered = []
    for pkg in truck.load:
        package = package_hash_table.lookup(pkg.ID)
        not_delivered.append(package)

    # Clear truck table to load back in order
    truck.load.clear()

    # Loop until the load is empty
    while len(not_delivered) > 0:
        next_available_package = None
        closest_package_distance = 999.99
        for pkg in not_delivered:
            if distance_between(truck.current_address, pkg.address) <= closest_package_distance:
                next_available_package = pkg
                closest_package_distance = distance_between(truck.current_address, pkg.address)

        next_available_package.departure_time = truck.time
        truck.load.append(next_available_package.ID)
        truck.current_address = next_available_package.address
        # Remove package from not delivered list
        not_delivered.remove(next_available_package)
        # Update miles truck traveled
        truck.mileage += closest_package_distance
        # Update departure time and how long it took to travel package
        truck.time += truck.travel_time(closest_package_distance)
        next_available_package.arrival_time = truck.time
        next_available_package.update_status(truck.time)
        print(f"Delivered: {next_available_package.ID} at {next_available_package.arrival_time.strftime('%H:%M')}")
# Address correction dictionary
ADDRESS_CORRECTIONS = { 9: (37, time(10, 20))} # pkg 9 copies pkg 37 before delivery
# Address corrector for package ID 9
def apply_address_correction(packages, current_time):
    # Normalize current_time to a time object
    ct = current_time.time() if isinstance(current_time, datetime) else current_time

    # Build or use existing ID->Package map for quick lookups
    if isinstance(packages, dict):
        pkg_map = packages
    else:
        pkg_map = {p.ID: p for p in packages}

    # Apply each correction rule
    for target_id, (source_id, correction_time) in ADDRESS_CORRECTIONS.items():
        target_pkg = pkg_map.get(target_id)
        source_pkg = pkg_map.get(source_id)

        # Warn if packages aren't present in the provided collection
        if target_pkg is None:
            print(f"[WARN] target pkg {target_id} not found in packages")
            continue
        if source_pkg is None:
            print(f"[WARN] source pkg {source_id} not found in packages")
            continue

        # Only change address once the clock has reached correction_time
        if ct >= correction_time:
            target_pkg.address = source_pkg.address
            print(f"Applied address correction: pkg {target_id} -> {source_pkg.address}")
        else:
            # Optionally reset to original if needed (not usually necessary)
            pass


def main():
    fleet = [truck1, truck2, truck3]
    packages = [pkg for bucket in package_hash_table.table for (_, pkg) in bucket]
    load_constraint_package()
    assign_packages_to_trucks(fleet, packages)
    for truck in fleet:
        deliver_packages(truck)

    # UI
    print("Welcome to WGUPS Routing Program!")
    print("The total mileage driven is: " + str(truck1.mileage + truck2.mileage + truck3.mileage))
    def main_menu():
        print("\nWhat would you like to do?")
        print("1. View All Packages")
        print("2. Look Up a Package")
        print("3. View Truck Summary")
        print("4. Exit")

    def current_time() -> datetime:
        input_raw = input("Please enter a time in the format (HH:MM): ").strip()
        try:
            t = datetime.strptime(input_raw, "%H:%M").time()
        except ValueError:
            raise ValueError("Please enter a valid time in the format HH:MM")

        return datetime.combine(datetime.today(), t)

    while True:
        main_menu()
        user_input = input("Enter your choice: ").strip()
        # Does not ask for time when user exits program
        if user_input != "4":
            convert_time = current_time()
            apply_address_correction(packages, convert_time)
            for pkg in packages:
                pkg.update_status(convert_time)

        match user_input:
            case "1":
                for packageID in range(1, 41):
                    package = package_hash_table.lookup(packageID)
                    print(str(package))

            case "2":
                package_locator = int(input("Enter your package ID: ").strip())
                package = package_hash_table.lookup(package_locator)
                if package is None:
                    print("Package not found")

                print(str(package))

            case "3":
                try:
                    truck_locator = input("Enter your truck ID: ").strip()
                    found_truck = None
                    for truck in fleet:
                        if truck.ID == int(truck_locator):
                            found_truck = truck
                            break
                    print(str(found_truck))
                except ValueError:
                    raise ValueError("Please enter a valid truck ID")

            case "4":
                print("Thank you for using WGUPS Routing Program!")
                break
    '''
    # Truck 1 preload
    pkg15 = table.lookup(15)
    pkg16 = table.lookup(16)
    pkg13 = table.lookup(13)
    pkg19 = table.lookup(19)
    pkg14 = table.lookup(14)
    pkg20 = table.lookup(20)
    pkg21 = table.lookup(21)
    # Truck 2 preload
    pkg36 = table.lookup(36)
    pkg38 = table.lookup(38)
    pkg37 = table.lookup(37)
    pkg18 = table.lookup(18)
    pkg3 = table.lookup(3)
    # Truck 3 preload
    pkg6 = table.lookup(6)
    pkg25 = table.lookup(25)
    pkg26 = table.lookup(26)
    pkg28 = table.lookup(28)
    pkg31 = table.lookup(31)
    pkg32 = table.lookup(32)
    pkg9 = table.lookup(9)
    # Example postloads
    pkg1 = table.lookup(1)
    pkg2 = table.lookup(2)
    pkg4 = table.lookup(4)
    pkg5 = table.lookup(5)
    pkg7 = table.lookup(7)
    pkg8 = table.lookup(8)
    pkg10 = table.lookup(10)
    pkg11 = table.lookup(11)
    pkg12 = table.lookup(12)
    pkg17 = table.lookup(17)
    pkg24 = table.lookup(24)
    pkg27 = table.lookup(27)
    pkg29 = table.lookup(29)
    pkg30 = table.lookup(30)
    pkg33 = table.lookup(33)
    pkg34 = table.lookup(34)
    pkg35 = table.lookup(35)
    pkg39 = table.lookup(39)
    pkg40 = table.lookup(40)

    Truck1 = Truck(1, 16, [pkg15, pkg16, pkg13, pkg19, pkg14, pkg20, pkg21], 0, HUB_ADDRESS, time(8, 00))
    Truck2 = Truck(2, 16, [pkg36, pkg38, pkg37, pkg18, pkg3], 0, HUB_ADDRESS, time(9, 00))
    Truck3 = Truck(3, 16, [pkg6, pkg25, pkg26, pkg28, pkg31, pkg32, pkg9], 0, HUB_ADDRESS, time(10, 00))

    fleet = [Truck1, Truck2, Truck3]
    all_packages = [pkg1, pkg2, pkg4, pkg5, pkg7, pkg8, pkg10, pkg11, pkg12, pkg17, pkg24, pkg27, pkg29, pkg30, pkg33,
                    pkg34, pkg35, pkg39, pkg40]

    leftovers = assign_packages_to_trucks(fleet, all_packages)

    print("Assigned loads:")
    for t in fleet:
        print(f" Truck {t.ID}: {[p.ID for p in t.load]}")
    print("Couldn't assign: ", [p.ID for p in leftovers])

    table = load_packages()[0]

    print("test package")
    testPkg = table.lookup(7)
    print(testPkg.address)
    print(table.lookup(1).address)

    print("test address/distance")
    print(address_list[2])
    print(distance_list[2])

    print("The distance of two points is: " + str(distance_between(testPkg.address, table.lookup(1).address)))

    
    table, test_pkg_list = load_packages()

    print("All packages")
    for pkg in test_pkg_list:
        print(pkg.ID, pkg.status)

    bootStrap = [
        [1, "test1"],
        [2, "test2"],
        [3, "test3"],
        [4, "test4"],
        [5, "test5"],
    ]

    testTable = CreateHashTable()

    print("<---- testing bootstrap --->")
    testTable.insert(bootStrap[0][0], bootStrap[0][1])
    print(testTable.table)

    testTable.insert(bootStrap[1][0], bootStrap[1][1])

    print("\nSearch")
    print(testTable.lookup(1))
    print(testTable.lookup(2))
    print(testTable.lookup(11))

    print("\nUpdate")
    testTable.insert(1, "new tester")
    print(testTable.table)

    print("\nRemove")
    testTable.remove(1)
    print(testTable.table)
    '''


if __name__ == "__main__":
    main()
