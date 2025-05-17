import logging
import pymongo
from pymongo.database import Database
from pymongo.operations import SearchIndexModel
from bson import ObjectId
from config import Config

logger = logging.getLogger(__name__)
class MongoManager:
    def __init__(self):
        self.client = None
        self.db = None
        self.mongo_db_uri = Config.MONGO_URI
        self.db_name = Config.MONGO_DB_NAME
        # Constants
        self.vector_dim = 384  # or 1536 if you use OpenAI model
        self.vector_field = "embedding"
        self.vector_index_name = "embedding_index"
        

    def connect_to_database(self):
        logger.info(f"Connecting to MongoDB at {self.mongo_db_uri}...")
        self.client = pymongo.MongoClient(self.mongo_db_uri)
        self.db = self.client[Config.MONGO_DB_NAME]
        # self.client.list_databases()
        existing_collections = self.db.list_collection_names()
        logger.info(f"Collection name: {existing_collections}")
        # Ensure "documents" collection exists
        if "documents" not in existing_collections:
            logger.info('Creating "documents" collection...')
            self.db.create_collection("documents")
            logger.info('"documents" collection created.')
        logging.info("Connected to MongoDB.")

    def close_database_connection(self):
        logging.info("Closing connection with MongoDB.")
        self.client.close()
        logging.info("Closed connection with MongoDB.")

    def find_data_from_db(self,db_collection, filters):
        if "_id" in filters:
            filters["_id"] = ObjectId(filters["_id"])

        result = db_collection.find(filters)
        return result
    
    def delete_data_from_db(self,db_collection, filters):
        logger.debug("Deleting data from db...")
        result = db_collection.delete_many(filters)
        logger.debug("OK")
        return result
    
    def upsert_data_into_db(self,db_collection, filters, to_upsert_data_list):
        logger.debug(f"Inserting data into database ({db_collection.database.name}/{db_collection.name}) with filter {filters} and data {to_upsert_data_list}...")
        self.delete_data_from_db(db_collection, filters)
        result = db_collection.insert_many(to_upsert_data_list)
        logger.debug("OK")
        return result
    

    def create_collection(self, collection_name):
        logger.info(f"Creating collection {collection_name}...")
        self.db.create_collection(collection_name)
        logger.info("Collection created.")
    
    def get_db(self):
        return self.db
    
    def get_collection(self, collection_name):
        return self.db[collection_name]
