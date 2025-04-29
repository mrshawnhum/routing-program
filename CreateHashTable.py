# Source: C950 - Webinar-1 - Let’s Go Hashing - Complete Python Code 2024
class CreateHashTable:
    def __init__(self, initial_capacity=10):
        self.table = []
        for i in range(initial_capacity):
            self.table.append([])

    # Insert new item into hash table
    #Original
    def insert(self, item):
        bucket = hash(item) % len(self.table)
        bucket_list = self.table[bucket]

        # add the item to the end of the bucket list
        bucket_list.append(item)

    # Insert and update
    def insert(self, key, item):
        # get bucket that item can go
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

    #Original
    def search(self, key):
        # get the bucket list where this key would be
        bucket = hash(key) % len(self.table)
        bucket_list = self.table[bucket]
        print(bucket_list)

        # search for the key in the bucket list
        if key in bucket_list:
            # find the item's index and return the item in the bucket list
            item_index = bucket_list.index(key)
            return bucket_list[item_index]
        else:
            # the key is not found
            return None

    def search(self, key):
        bucket = hash(key) % len(self.table)
        bucket_list = self.table[bucket]

        # search for the key in the bucket list
        for kv in bucket_list:
            if kv[0] == key:
                return kv[1]
        return None