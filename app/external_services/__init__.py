from external_services.mongo_manager import MongoManager
from external_services.faiss_manager import FaissManager
from external_services.opensearch_manager import OpenSearchManager


dbm = MongoManager()
fm = FaissManager()
osm = OpenSearchManager()


