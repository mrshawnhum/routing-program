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

# Calculate distance using distance list
def distance_between(address1, address2):
    x = address_list.index(address1)
    y = address_list.index(address2)

    distance = distance_list[x][y]
    if distance is None:
        distance = distance_list[y][x]

    return distance

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
    def dl_min(p):
        return time_to_minutes(p.deadline) if isinstance(p.deadline, time) else 23 * 60 + 59

    # filter out packages already loaded into trucks
    preloaded = {p.ID for t in fleet for p in t.load}
    pool = [p for p in packages if p.ID not in preloaded]

    # assign all deadline-sensitive packages and sort by earliest deadline
    timed = sorted([p for p in pool if isinstance(p.deadline, time)],
                   key=dl_min)

    # Loop through all deadline packages
    for pkg in timed:
        best = None  # will hold (truck, arrival_min)

        # skip any truck that is full
        for tr in fleet:
            # Pass any truck with full loads
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
            tr, arrive = best # Assign best truck
            tr.load.append(pkg) # Load package to assigned truck
            pkg.in_truck_id = tr.ID # Update ID of truck that package is assigned to
            tr.next_available_min = arrive # Update attribute
            tr.current_address = pkg.address # Update truck address(for determining best packages
            pool.remove(pkg) # Remove the package from pool of packages left to assign

    # Assign remaining packages with EOD deadline
    eod_left = [p for p in pool if not isinstance(p.deadline, time)]

    # loop through trucks with remaining loads while packages were left to assign
    for tr in fleet:
        while len(tr.load) < tr.capacity and eod_left:
            # pick the nearest package to this truck’s current spot
            pkg = min(
                eod_left,
                key=lambda p: distance_between(tr.current_address, p.address)
            )
            tr.load.append(pkg) # Load into truck
            pkg.in_truck_id = tr.ID # Update ID of truck the package is in
            eod_left.remove(pkg) # Remove package from pool
            tr.current_address = pkg.address # move the “cluster center” forward

            # advance its clock
            curr = getattr(tr, 'next_available_min',
                            time_to_minutes(tr.departure_time))
            d = distance_between(tr.current_address, pkg.address)
            tr.next_available_min = curr + (d / tr.speed) * 60


# Routing algorithm for delivering packages based on nearest neighbor
def deliver_packages(truck, lookup_fn):
    truck.current_address = HUB_ADDRESS # Reset location of truck
    not_delivered = [] # Empty list of packages not delivered

    # Assign packages from truck to list
    for entry in truck.load:
        if isinstance(entry, Package): # Already a Package object
            not_delivered.append(entry) # Add to list
        else:
            package_entry = lookup_fn(entry) # Assumes it's an ID
            if package_entry is None: # If ID doesn't exist
                print(f"[WARNING] {entry} is not a valid package") # Print warning error
            else:
                not_delivered.append(package_entry) # Upload to list
    truck.load.clear() # Clear truck table to load back in order

    # Record the time package left the hub
    start_time = truck.time
    for pkg in not_delivered:
        pkg.departure_time = start_time

    # Loop until the load list is empty
    while not_delivered:
        next_available_package = None # Which package is next to deliver?
        closest_package_distance = float("inf") # What is the distance between current spot and closest address?
        next_address = None # Which address is the closest?

        # loop through packages in list
        for pkg in not_delivered:
            effective_address = get_effective_address(pkg, truck.time, lookup_fn) # Find package's address if different from original (relevalent for  ID #9)
            distance = distance_between(truck.current_address, effective_address) # Find distance between where truck is to the package
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
        # print(f"Delivered: {next_available_package.ID} by truck ID: {truck.ID} at address: {next_address} on {next_available_package.arrival_time.strftime('%H:%M')}, mileage: {closest_package_distance}")

        # Move the truck
        truck.current_address = next_address

        # Mark it done and remove from load
        truck.load.append(next_available_package.ID)
        not_delivered.remove(next_available_package)

# Address correction dictionary
ADDRESS_CORRECTIONS = { 9: (37, time(10, 20))} # pkg 9 copies pkg 37 (actual address) by 10:20 AM

# Address corrector method for package ID 9
def apply_address_correction(packages, current_time):
    ct = current_time.time() if isinstance(current_time, datetime) else current_time # Normalize current_time to a time object

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
            print(f"Applied address correction: pkg {target_id} -> {source_pkg.address}")
        else:
            pass

# Helper method for finding if addresses were corrected
def get_effective_address(pkg, current_time, lookup_fn):
    ct = current_time.time() if isinstance(current_time, datetime) else current_time # Normalize current_time to a time object

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
    fleet = [truck1, truck2, truck3] # Current fleet list of trucks
    packages = [pkg for bucket in package_hash_table.table for (_, pkg) in bucket] # Package list to illiterate through
    assign_packages_to_trucks(fleet, packages) # Assign remaining packages to trucks

    # Run delivery program for 1st & 2nd truck
    deliver_packages(truck1, package_hash_table.lookup)
    deliver_packages(truck2, package_hash_table.lookup)

    # Since there are only two drivers but three truck, 3rd truck departure won't leave until there is a driver available
    # Helper method for updating when 3rd truck leaves
    def update_departure(returning_truck, truck_at_hub):
        return_distance = distance_between(returning_truck.current_address, HUB_ADDRESS) # Distance from last package address to hub
        returning_truck.mileage += return_distance # Add distance it took to get back to hub
        returning_truck.time += returning_truck.travel_time(return_distance) # Update time it took to get there
        print(
            f"Truck {returning_truck.ID} has returned to the hub at {returning_truck.time.strftime('%I:%M %p')} (+{return_distance:.1f} miles)")

        # Update when 3rd truck leaves
        truck_at_hub.departure_time = returning_truck.time
        truck_at_hub.time = returning_truck.time
        truck_at_hub.current_address = HUB_ADDRESS
        print(f"Truck 3 departs at {truck3.time.strftime('%I:%M %p')}")

    # Update time 3rd truck leaves and start delivery program
    update_departure(truck1, truck3)
    deliver_packages(truck3, package_hash_table.lookup)

    # UI
    print("Welcome to WGUPS Routing Program!")
    print("The total mileage driven is: " + str(truck1.mileage + truck2.mileage + truck3.mileage))
    # Main menu
    def main_menu():
        print("\nWhat would you like to do?")
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
        package = lookup_fn(pkg_ID)
        package.update_status(input_time)
        eff_address = get_effective_address(package, input_time,
                                                  lookup_fn)  # Get the address of package if changed

        # If ID doesn't exist, print error
        if package is None:
            print("Package not found")

        # Print status of package
        print(
            f"\nPackage ID: {package.ID} | Address: {eff_address} | Weight: {package.weight} Kilo | Assigned to Truck ID: {package.in_truck_id if package.in_truck_id else 'N/A'}")
        print(
            f"Deadline: {package.deadline.strftime('%I:%M %p') if package.deadline else "EOD"} | Departure Time: {package.departure_time.strftime('%I:%M %p') if package.departure_time else "N/A"} | Arrival Time: {package.arrival_time.strftime('%I:%M %p') if package.status == "Delivered" else "N/A"} | Status: {package.status}")

    # Run until told to stop
    while True:
        # Ask user what they want to do
        main_menu()
        user_input = input("Enter your choice: ").strip()

        # Only ask for time when viewing package history
        if user_input == "1" or user_input == "2":
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
                truck_locator = input("Enter your truck ID: ").strip() # Ask for Truck ID to view summary

                # If Truck ID is invalid, print error
                try:
                    total = 0
                    found_truck = None
                    for truck in fleet:
                        total += truck.mileage
                        print(f"Truck {truck.ID} departed at {truck.departure_time} & drove {truck.mileage} miles")
                        if truck.ID == int(truck_locator):
                            found_truck = truck

                    print("Summary of chosen truck:")
                    print(str(found_truck))

                except ValueError:
                    raise ValueError("Please enter a valid truck ID")

            # Option 4 = Exit program
            case "4":
                print("Thank you for using WGUPS Routing Program!")
                break

# Run Program
if __name__ == "__main__":
    main()
