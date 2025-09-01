

def create_index(client, db, collection, indexQuery):
    collection = client[db][collection]
    collection.create_index(indexQuery, unique = True)
