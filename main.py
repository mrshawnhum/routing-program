# Student ID: 012214405

# Imports
from CreateHashTable import CreateHashTable
from Package import Package
import csv
from datetime import datetime

def load_packages(filename="WGUPS-data.csv"):
    package_table = CreateHashTable(initial_capacity=40)
    test_all_packages = []

    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            # unpack data
            pkg_ID, address, city, state, zip_code, deadline, pkg_weight = row

            # convert type
            ID = int(pkg_ID)
            weight = int(pkg_weight)

            # defaults
            status = "At Hub"

            # build Package objects
            package = Package(ID, address.strip(), city.strip(), state.strip(), zip_code.strip(), deadline, weight, status)

            package_table.insert(ID, package)
            test_all_packages.append(package)

    return package_table, test_all_packages



def main():


    table, test_pkg_list = load_packages()

    print("All packages")
    for pkg in test_pkg_list:
        print(pkg.ID, pkg.status)

    '''
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