#%%
from pymongo.mongo_client import MongoClient

c_file = '/Users/indra/Documents/Masters in Data Science/Data to Decision/IND320_Indra/No_sync/MongoDB.txt'
USR, PWD = open(c_file).read().splitlines()
#/Users/indra/Documents/Masters in Data Science/Data to Decision/IND320_Indra/No_sync/MongoDB.txt
print(PWD)

uri = "mongodb+srv://"+USR+":"+PWD+"@cluster0.wmoqhtp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
print(uri)
# Create a new client and connect to the server
client = MongoClient(uri)
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

#%%
from pymongo.mongo_client import MongoClient

# Find the URI for your MongoDB cluster in the MongoDB dashboard:
# `Connect` -> `Drivers` -> Under heading 3.

uri = ("mongodb+srv://{}:{}@cluster0.wmoqhtp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")


# Connecting to MongoDB with the chosen username and password.
USR, PWD = open(c_file).read().splitlines()
client = MongoClient(uri.format(USR, PWD))

# Selecting a database and a collection.
database = client['indra']
collection = database['data']
#%%
# Inserting a single document (dictionary).
collection.insert_one({'name': 'Hallvard', 'age': 23})

# Inserting multiple documents (list of dictionaries).
collection.insert_many([
    {'name': 'Indra', 'age': 25},
    {'name': 'Ihn Duck', 'age': 15},
])
# %%
# Reading ALL documents from a collection.
# ........................................

documents = collection.find({})
# A cursor is returned.

# The cursor can be iterated over:
for document in documents:
    print(document)

# Or directly converted to a list:
documents = list(documents)
#%%
# Reading SPECIFIC documents from a collection.
# .............................................

hallvard = collection.find({'name': 'Indra'})

for document in hallvard:
    print(document)

hallvard = list(hallvard)
# %%
# Updating a single document.
# ...........................
collection.update_one(
    {'name': 'Indra'},
    {'$set': {'name': 'Indra Adhikari'}}  # Sets the `name` to `Hallvard Lavik`.
)

# Updating multiple documents.
# ............................
collection.update_many(
    {},
       {'$inc': {'age': 1}}  # Increments the `age` of all documents by `1`.
)
# %%
pipeline = [
    {'$match': {'age': {'$gt': 20}}},
    {'$group': {'_id': None, 'average_age_over_20': {'$avg': '$age'}}},
]
result = collection.aggregate(pipeline)
result = list(result)
print(result)
# %%
# Deleting a single document.
# ...........................
collection.delete_one({'name': 'Hallvard'})  # Deletes the document with `name = Ihn Duck`.

# Deleting multiple documents.
# ............................
#collection.delete_many({'age': {'$gt': 25}})  # Deletes documents where `age > 25`.

# Deleting all documents.
# .......................
#collection.delete_many({})
# %%
