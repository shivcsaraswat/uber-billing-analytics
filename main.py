import sys
import os 
import gzip

project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append( project_root)

from utils.email_agent import *
from utils.utils import *
from utils.tripParser import*
from datetime import datetime
import json
from database.dbConnect import *
from database.dbOperations import *
from database.dbUtils import *

from analytics.dfRecords import *

# Loading config files 
emailConfig = load_config('./config/config.yaml')
dbConfig = load_config('./config/dbCreds.yaml')


# DB Credentials 
userName = quote_plus(dbConfig['Login']['userName'])
password = quote_plus(dbConfig['Login']['password'])
index = dbConfig['Database']['indexQuery']


# Mongo Connection String 
uri = f"mongodb+srv://{userName}:{password}@cluster0.raxvjia.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"


# Creating DB connection
dbClient = connectDB(uri)


dbName = dbConfig['Database']['dbName']
collectionName = dbConfig['Database']['collection']


create_index(dbClient, dbName, collectionName, index)

dbOps = DBOperations(dbClient)


# Email Creds
client1 = Email(emailConfig['LOGIN']['EMAIL'], emailConfig['LOGIN']['APP_PASSWORD'], emailConfig['LOGIN']['IMAP_SERVER'])
client1.login()


# EMAIL QUERY
from_date = "2025-07-01"
to_date = "2025-08-31"
keywords = ["uber", "your", "morning", "trip"]  # IMAP pre-filter terms
# Any weekday word between "Your" and "morning" (generic day name)
subject_regex = r"FW:\s+Your\s+[A-Za-z]+\s+morning trip with Uber"

# EMAIL SEARCH
hits = client1.search_by_date_range_keywords_regex(from_date=from_date,to_date=to_date, keywords=keywords,subject_regex=subject_regex,require_all_keywords=False)
dict = {}

trips = []
for h in hits:
    trip= TripParser( h['id'], h['date'], h['text'], gzip)
    trips.append(trip.trip)
print(trips)

dbOps.insert(trips[1], dbName,collectionName)
records = dbOps.findItemsByQuery({}, dbName, collectionName)

dfRecordsObj = DFRecords(records)
dfRecords = dfRecordsObj.getRecordDF()








    



                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        