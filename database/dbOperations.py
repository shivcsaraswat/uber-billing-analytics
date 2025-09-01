

import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append( project_root)


from pymongo import MongoClient
from pymongo.errors import PyMongoError, DuplicateKeyError, WriteError, BulkWriteError
from typing import List, Dict, Any, Optional, Union
import logging
import copy
from datetime import datetime
from errors.invalidRecordNumError import *

class DBOperations(): 
    def __init__(self, client):
        self.client = client   
                                                                                                                                                                                                                                                                                                 

    def findItemsByQuery(self, query: Dict[str, Any], db: str, collection: str,  
                    limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Finds items in a MongoDB collection based on a query
        
        Args:
            query (Dict[str, Any]): MongoDB query dictionary
            db (str): Database name
            collection (str): Collection name
            client (MongoClient): Valid MongoDB client instance
            limit (Optional[int]): Maximum number of records to return
            
        Returns:
            List[Dict[str, Any]]: List of matching documents
            
        Raises:
            PyMongoError: If there's an error with the MongoDB operation
            Exception: For other general errors
    """
        try:
            # Get the database and collection
            print(db)
            print(self.client)
            database = self.client[db]
            print(database)
            coll = database[collection]
            
            # Execute the find operation
            cursor = coll.find(query)
            
            # Apply limit if specified
            if limit and limit > 0:
                cursor = cursor.limit(limit)
            
            # Convert cursor to list and return
            results = list(cursor)
            
            logging.info(f"Found {len(results)} documents in {db}.{collection}")
            return results
            
        except PyMongoError as e:
            logging.error(f"MongoDB error in findItemsByQuery: {e}")
            raise
        except Exception as e:
            logging.error(f"General error in findItemsByQuery: {e}")
            raise

    
        
    def insert(self, record: Union[Dict[str, Any], list[Dict[str, Any]]], db: str, collection: str, 
          limit: Optional[int] = None) -> Dict[str, Union[bool, List[str], int]]:
        """
        Inserts records into MongoDB collection after checking if they already exist
        
        Args:
            record (Dict[str, Any]): Record template to insert
            db (str): Database name
            collection (str): Collection name
            client (MongoClient): Valid MongoDB client instance
            limit (Optional[int]): Number of records to insert (default: 1)
            
        Returns:
            Dict containing:
                - 'success': bool - whether operation was successful
                - 'inserted_ids': List[str] - list of inserted document IDs
                - 'inserted_count': int - number of documents inserted
                - 'message': str - descriptive message about the operation
                
        Raises:
            PyMongoError: If there's an error with the MongoDB operation
            Exception: For other general errors
        """
        if not isinstance(record, list) and limit != None and limit > 1:
            raise invalidRecordInputError('We request you to provide a list of records for multiple insertions. Multiple insertions of the same record are not permitted')
            
        try:
            logging.info(f"Starting insert operation for {limit} record(s) in {db}.{collection}")
            database = self.client[db]
            
            collection = database[collection]
            if isinstance(record, dict):
                try:
                    collection.insert_one(record)
                except DuplicateKeyError as e:
                    error_message = f"Record already exists :  {e}"
                    print(error_message)
                    logging.error(error_message)
            else:
                try:
                    if limit == None:
                         collection.insert_many(record, ordered = False)
                    else:
                        collection.insert_many(record[:limit], ordered = False)
                except BulkWriteError as e:
                    error_message = f"OnrRecord already exists :  {e}"
                    print(error_message)
                    logging.error(error_message)
            
        except PyMongoError as e:
            error_message = f"MongoDB error during insertion: {e}"
            print(error_message)
            logging.error(error_message)
            raise
            
        except Exception as e:
            error_message = f"Unexpected error during insertion: {e}"
            print(error_message)
            logging.error(error_message)
            raise
    def delete(self, query: Dict[str, Any], db: str, collection: str, 
          delete_all: bool = False) -> Dict[str, Union[bool, int, List[str], str]]:
            """
            Deletes records from MongoDB collection after validating they exist
            
            Args:
                query (Dict[str, Any]): Query to identify records to delete
                db (str): Database name
                collection (str): Collection name
                client (MongoClient): Valid MongoDB client instance
                delete_all (bool): If True, delete all matching records. If False, delete only first match
                
            Returns:
                Dict containing:
                    - 'success': bool - whether operation was successful
                    - 'deleted_count': int - number of documents deleted
                    - 'deleted_ids': List[str] - list of deleted document IDs (if available)
                    - 'message': str - descriptive message about the operation
                    
            Raises:
                PyMongoError: If there's an error with the MongoDB operation
                Exception: For other general errors
            """
            try:
                logging.info(f"Starting delete operation in {db}.{collection}")
                logging.debug(f"Delete query: {query}")
                
                # Step 1: Validate that records exist using findItemsByQuery
                logging.info("Checking if records exist before deletion")
                
                # Find records that match the query
                if delete_all:
                    # Find all matching records
                    existing_records = self.findItemsByQuery(query, db, collection)
                    operation_type = "delete all matching"
                else:
                    # Find only the first matching record
                    existing_records = self.findItemsByQuery(query, db, collection, limit=1)
                    operation_type = "delete first matching"
                
                # Step 2: If no records found, print message and return
                if not existing_records:
                    message = f"No records found matching the query in {db}.{collection}. Nothing to delete."
                    print(message)
                    logging.info(message)
                    
                    return {
                        'success': False,
                        'deleted_count': 0,
                        'deleted_ids': [],
                        'message': message,
                        'found_records': 0
                    }
                
                # Step 3: Records exist, show what will be deleted
                found_count = len(existing_records)
                deleted_ids = [str(record.get('_id', 'unknown')) for record in existing_records]
                
                message = f"Found {found_count} record(s) to delete in {db}.{collection}"
                print(message)
                logging.info(message)
                
                # Log the records that will be deleted (for audit trail)
                for i, record in enumerate(existing_records):
                    logging.debug(f"Record {i+1} to delete: ID={record.get('_id')}")
                
                # Step 4: Perform the deletion
                database = self.client[db]
                coll = database[collection]
                
                if delete_all:
                    # Delete all matching records
                    delete_result = coll.delete_many(query)
                    deleted_count = delete_result.deleted_count
                else:
                    # Delete only the first matching record
                    delete_result = coll.delete_one(query)
                    deleted_count = delete_result.deleted_count
                
                # Step 5: Verify deletion and return result
                if deleted_count > 0:
                    success_message = f"Successfully deleted {deleted_count} record(s) from {db}.{collection}"
                    print(success_message)
                    logging.info(success_message)
                    
                    # Log deleted IDs for audit trail
                    logging.info(f"Deleted record IDs: {deleted_ids[:deleted_count]}")
                    
                    return {
                        'success': True,
                        'deleted_count': deleted_count,
                        'deleted_ids': deleted_ids[:deleted_count],
                        'message': success_message,
                        'operation_type': operation_type
                    }
                else:
                    # This shouldn't happen if we found records, but handle it
                    error_message = f"Delete operation failed - no records were actually deleted from {db}.{collection}"
                    print(error_message)
                    logging.warning(error_message)
                    
                    return {
                        'success': False,
                        'deleted_count': 0,
                        'deleted_ids': [],
                        'message': error_message,
                        'found_records': found_count
                    }
                
            except WriteError as e:
                error_message = f"Write error during deletion: {e}"
                print(error_message)
                logging.error(error_message)
                raise
                
            except PyMongoError as e:
                error_message = f"MongoDB error during deletion: {e}"
                print(error_message)
                logging.error(error_message)
                raise
                
            except Exception as e:
                error_message = f"Unexpected error during deletion: {e}"
                print(error_message)
                logging.error(error_message)
                raise
        
