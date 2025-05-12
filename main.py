# Student ID: 012214405
from typing import List

# Imports
from CreateHashTable import CreateHashTable
from Package import Package
from Truck import Truck
import csv
from datetime import datetime, time

# Global variables
HUB_ADDRESS = "4001 South 700 East"
truck1 = Truck(1, 16, [], 0, HUB_ADDRESS, time(8, 00))
truck2 = Truck(2, 16, [], 0, HUB_ADDRESS, time(9, 00))
truck3 = Truck(3, 16, [], 0, HUB_ADDRESS, time(10, 00))


# Upload package data from CSV and insert into a table
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

            # Insert into hash table
            package_table.insert(ID, package)
    # Return Hash table
    return package_table


# load package table
package_hash_table = load_packages()


# Upload distance/addresses from CSV and create lists for each
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


# load distance and address list to predefined variables
address_list, distance_list = load_distances_and_addresses("CSV/WGUPS-distance.csv")
# Build the map once for fast distance comparison
ADDRESS_IDX: dict[str, int] = {addr: i for i, addr in enumerate(address_list)}


# Calculate distance using distance list
def distance_between(address1: str, address2: str):
    # Assign coordinates from address list
    x, y = ADDRESS_IDX[address1], ADDRESS_IDX[address2]

    # Return distance between coordinates
    distance = distance_list[x][y]
    return distance if distance is not None else distance_list[y][x]


# Packages that are required to be in certain trucks
PRELOAD = {
    1: [13, 14, 15, 16, 19, 20, 21, 34],
    2: [3, 18, 36, 37, 38],
    3: [6, 9, 25, 26, 28, 31, 32],
}


# Load predefined packages to trucks
def load_constraint_package():
    # Loop through all the trucks
    for tr in (truck1, truck2, truck3):
        # look up the list of package IDs for this truck
        ids = PRELOAD.get(tr.ID, [])
        for pid in ids:
            pkg = package_hash_table.lookup(pid)
            if pkg is None:
                continue
            pkg.in_truck_id = tr.ID
            tr.load.append(pkg)


# convert time to minutes since midnight
def time_to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute


# Algorithm to assign packages to trucks based on priority, distance, and available space in truck based on nearest-neighbor concepts
def assign_packages_to_trucks(fleet: List["Truck"], packages: List["Package"]):
    # helper function to map package deadline to amount of minutes
    def deadline_min(pkg: Package):
        return (pkg.deadline.hour * 60 + pkg.deadline.minute) if pkg.deadline else 23 * 60 + 59

    # filter out packages already loaded into trucks and split tables with deadline vs EOD deadline
    preloaded = {p.ID for t in fleet for p in t.load}
    timed_pkgs = [p for p in packages if p.ID not in preloaded and p.deadline]
    eod_pkgs = [p for p in packages if p.ID not in preloaded and not p.deadline]

    # Sort for deterministic behaviour
    timed_pkgs.sort(key=deadline_min)
    eod_pkgs.sort(key=lambda p: p.ID)
    fleet.sort(key=lambda t: time_to_minutes(t.departure_time))

    # Assign all deadline packages to a truck
    for tr in fleet:
        curr_addr = tr.current_address
        curr_min = time_to_minutes(tr.departure_time)

        while timed_pkgs and len(tr.load) < tr.capacity:
            # find the closest timed package that we can still deliver on time
            possible = [
                (pkg,
                 curr_min + distance_between(curr_addr, pkg.address) / tr.speed * 60)
                for pkg in timed_pkgs
            ]
            # filter those we can reach before their deadline
            feasible = [(pkg, arr) for pkg, arr in possible if arr <= deadline_min(pkg)]
            if not feasible:
                break  # nothing more this truck can do

            # pick the package with earliest arrival (ties = earliest deadline)
            pkg, arrive = min(feasible, key=lambda x: (x[1], deadline_min(x[0])))

            # Load it to truck
            tr.load.append(pkg)
            pkg.in_truck_id = tr.ID
            timed_pkgs.remove(pkg)

            # Advance truck cursor
            curr_addr = pkg.address
            curr_min = arrive

        # store the updated cursor back on the truck for later use
        tr.current_address = curr_addr
        tr.next_available_min = curr_min

        # fast exit: if every truck is now full, no point continuing
        if all(len(t.load) >= t.capacity for t in fleet):
            break

        # Loop until no more packages or truck is full
        while eod_pkgs and any(len(t.load) < t.capacity for t in fleet):
            for tr in fleet:
                if not eod_pkgs or len(tr.load) >= tr.capacity:
                    continue

                # choose nearest point to truck's current spot
                nearest = min(
                    eod_pkgs,
                    key=lambda p: distance_between(tr.current_address, p.address)
                )

                # load and update
                tr.load.append(nearest)
                nearest.in_truck_id = tr.ID
                tr.current_address = nearest.address
                eod_pkgs.remove(nearest)

                if not eod_pkgs:  # all done
                    break


# Routing algorithm for delivering packages based on nearest neighbor
def deliver_packages(truck, lookup_fn):
    truck.current_address = HUB_ADDRESS  # Reset location of truck
    not_delivered = []  # Empty list of packages not delivered

    # Assign packages from truck to list
    for entry in truck.load:
        if isinstance(entry, Package):  # Already a Package object
            not_delivered.append(entry)  # Add to list
        else:
            package_entry = lookup_fn(entry)  # Assumes it's an ID
            if package_entry is None:  # If ID doesn't exist
                print(f"[WARNING] {entry} is not a valid package")  # Print warning error
            else:
                not_delivered.append(package_entry)  # Upload to list
    truck.load.clear()  # Clear truck table to load back in order

    # Record the time package left the hub
    start_time = truck.time
    for pkg in not_delivered:
        pkg.departure_time = start_time

    # Loop until the load list is empty
    while not_delivered:
        next_available_package = None  # Which package is next to deliver?
        closest_package_distance = float("inf")  # What is the distance between current spot and closest address?
        next_address = None  # Which address is the closest?

        # loop through packages in list
        for pkg in not_delivered:
            effective_address = get_effective_address(pkg, truck.time,
                                                      lookup_fn)  # Find package's address if different from original (relevalent for  ID #9)
            distance = distance_between(truck.current_address,
                                        effective_address)  # Find distance between where truck is to the package
            # Assign package with least amount of distance
            if distance <= closest_package_distance:
                closest_package_distance = distance
                next_available_package = pkg
                next_address = effective_address

        # Drive there and update miles truck traveled
        truck.mileage += closest_package_distance
        truck.time += truck.travel_time(closest_package_distance)

        # Stamp arrival
        next_available_package.arrival_time = truck.time
        next_available_package.update_status(truck.time)

        # Move the truck
        truck.current_address = next_address

        # Mark it done and remove from load
        truck.load.append(next_available_package.ID)
        not_delivered.remove(next_available_package)


# Address correction dictionary
ADDRESS_CORRECTIONS = {9: (37, time(10, 20))}  # pkg 9 copies pkg 37 (actual address) by 10:20 AM


# Address corrector method for package ID 9
def apply_address_correction(packages, current_time):
    ct = current_time.time() if isinstance(current_time,
                                           datetime) else current_time  # Normalize current_time to a time object

    # Build or use existing ID; Package map for quick lookups
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
            target_pkg.city = source_pkg.city
            target_pkg.state = source_pkg.state
            target_pkg.zip_code = source_pkg.zip_code
            print(
                f"Applied address correction: pkg {target_id} -> {source_pkg.address}, {source_pkg.city}, {source_pkg.state}, {source_pkg.zip_code}")
        else:
            pass


# Helper method for finding if addresses were corrected
def get_effective_address(pkg, current_time, lookup_fn):
    ct = current_time.time() if isinstance(current_time,
                                           datetime) else current_time  # Normalize current_time to a time object

    # If correction applys, follow correction
    rule = ADDRESS_CORRECTIONS.get(pkg.ID)
    if rule:
        source_id, correction_time = rule
        if ct >= correction_time:
            source_package = lookup_fn(source_id)
            return source_package.original_address

    return pkg.original_address


# Main function
def main():
    load_constraint_package()  # Run predefined package program
    fleet = [truck1, truck2, truck3]  # Current fleet list of trucks
    packages = [pkg for bucket in package_hash_table.table for (_, pkg) in bucket]  # Package list to illiterate through
    assign_packages_to_trucks(fleet, packages)  # Assign remaining packages to trucks

    # Run delivery program for 1st & 2nd truck
    deliver_packages(truck1, package_hash_table.lookup)
    deliver_packages(truck2, package_hash_table.lookup)

    # Since there are only two drivers but three truck, 3rd truck departure won't leave until there is a driver available
    # Helper method for updating when 3rd truck leaves
    def update_departure(returning_truck, truck_at_hub):
        return_distance = distance_between(returning_truck.current_address,
                                           HUB_ADDRESS)  # Distance from last package address to hub
        returning_truck.mileage += return_distance  # Add distance it took to get back to hub
        returning_truck.time += returning_truck.travel_time(return_distance)  # Update time it took to get there
        returning_truck.current_address = HUB_ADDRESS  # Truck is now parked at hub

        # Update when 3rd truck left
        depart_time = returning_truck.time
        truck_at_hub.departure_time = depart_time.time()
        truck_at_hub.time = depart_time
        truck_at_hub.current_address = HUB_ADDRESS

    # Update time 3rd truck leaves and start delivery program
    update_departure(truck1, truck3)
    deliver_packages(truck3, package_hash_table.lookup)

    # UI
    print("Welcome to WGUPS Routing Program!")
    print("The total mileage driven is: " + str(truck1.mileage + truck2.mileage + truck3.mileage))

    # Main menu
    def main_menu():
        print("What would you like to do?")
        print("1. View All Packages")
        print("2. Look Up a Package")
        print("3. View Truck Summary")
        print("4. Exit")

    # Convert user input as time; print error if invalid input given
    def current_time() -> datetime:
        input_raw = input("Please enter a time in the format (HH:MM): ").strip()
        try:
            t = datetime.strptime(input_raw, "%H:%M").time()
        except ValueError:
            raise ValueError("Please enter a valid time in the format HH:MM")

        return datetime.combine(datetime.today(), t)

    # Method to print status of packages
    def print_status(pkg_ID, input_time, lookup_fn):
        package = lookup_fn(pkg_ID)  # Find package with associated ID

        # If ID doesn't exist, print error
        if package is None:
            print("Package not found")

        package.update_status(input_time)  # Update status based on time
        eff_address = get_effective_address(package, input_time, lookup_fn)  # Get the address of package if changed

        # Print status of package
        print(
            f'Package ID: {package.ID} | Address: {eff_address} | City: {package.city} | State: {package.state} | Zip Code: {package.zip_code} | Weight: {package.weight} Kilo | Assigned to Truck ID: {package.in_truck_id if package.in_truck_id else 'N/A'}')
        print(
            f'Deadline: {package.deadline.strftime('%I:%M %p') if package.deadline else "EOD"} | Departure Time: {package.departure_time.strftime('%I:%M %p') if package.status == "Delivered" or package.status == "On The Way" else "N/A"} | Arrival Time: {package.arrival_time.strftime('%I:%M %p') if package.status == "Delivered" else "N/A"} | Status: {package.status}\n')

    # Run until told to stop
    while True:
        # Ask user what they want to do
        main_menu()
        user_input = input("Enter your choice: ").strip()

        # Only ask for time when viewing package history
        if user_input in {"1", "2"}:
            convert_time = current_time()
            apply_address_correction(packages, convert_time)

        # Run operation based on user input
        match user_input:

            # First option = View status of all packages
            case "1":
                for packageID in range(1, 41):
                    print_status(packageID, convert_time, package_hash_table.lookup)

            # Second option = View a package
            case "2":
                package_id = int(input("Enter your package ID: ").strip())
                print_status(package_id, convert_time, package_hash_table.lookup)

            # Third option = truck summary
            case "3":
                truck_locator = input("Enter your truck ID: ").strip()  # Ask for Truck ID to view summary

                # If Truck ID is invalid, print error
                try:
                    total = 0
                    found_truck = None
                    for truck in fleet:
                        total += truck.mileage
                        print(
                            f"Truck {truck.ID} departed at {truck.departure_time.strftime('%I:%M %p')} & drove {truck.mileage} miles")
                        if truck.ID == int(truck_locator):
                            found_truck = truck

                    print(f"Total mileage driven: {total} miles\n")

                    print("Summary of chosen truck:")
                    print(
                        f'ID: {found_truck.ID}, Load: {found_truck.load}, Mileage: {found_truck.mileage}, Departure Time: {found_truck.departure_time.strftime('%I:%M %p')}\n')

                except ValueError:
                    raise ValueError("Please enter a valid truck ID")

            # Option 4 = Exit program
            case "4":
                print("Thank you for using WGUPS Routing Program!")
                break


# Run Program
if __name__ == "__main__":
    main()
