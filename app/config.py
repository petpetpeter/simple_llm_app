import os

class Config:

    MONGO_URI = os.getenv('MONGO_URI')
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME')
    OPENSEARCH_USER = os.getenv('OPENSEARCH_USER')
    OPENSEARCH_PASSWORD = os.getenv('OPENSEARCH_INITIAL_ADMIN_PASSWORD')


# Optional: Create a function to print the config for debugging
def print_config():
    print(f"MONGO_URI: {Config.MONGO_URI}")
    print(f"MONGO_DB_NAME: {Config.MONGO_DB_NAME}")

if __name__ == "__main__":
    print_config()
