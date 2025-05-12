# Source citation: C950 - Webinar-1 - Let’s Go Hashing - Complete Python Code 2024
class CreateHashTable:
    def __init__(self, initial_capacity=10): # Set initial capacity unless specified
        self.table = [] # Assign table to empty list
        # Add each item to table
        for i in range(initial_capacity):
            self.table.append([])

    # Insert and update
    def insert(self, key, item):
        # Grab bucket lis
        bucket = hash(key) % len(self.table)
        bucket_list = self.table[bucket]

        # update key if it is already in the bucket
        for kv in bucket_list:
            if kv[0] == key:
                kv[1] = item
                return True

        # if not, insert the item to the end of the bucket list
        key_value = [key, item]
        bucket_list.append(key_value)
        return True

    def lookup(self, key):
        # Grab bucket list
        bucket = hash(key) % len(self.table)
        bucket_list = self.table[bucket]

        # search for the key in the bucket list
        for kv in bucket_list:
            if kv[0] == key:
                return kv[1]
        return None

    # Remove from hash table
    def remove(self, key):
        # Grab bucket list
        bucket = hash(key) % len(self.table)
        bucket_list = self.table[bucket]

        # remove the item from the bucket list if present
        for kv in bucket_list:
            if kv[0] == key:
                bucket_list.remove(kv)
                break