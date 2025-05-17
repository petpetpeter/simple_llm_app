from fastapi import FastAPI
from contextlib import asynccontextmanager
from routers.llm import chat
from routers.docs import document
import logging
from colorlog import ColoredFormatter
import os

from external_services import dbm,osm

LOG_LEVEL = logging.DEBUG
LOGFORMAT = "%(log_color)s%(asctime)-8s%(reset)s - %(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"
logging.root.setLevel(LOG_LEVEL)
formatter = ColoredFormatter(LOGFORMAT)
stream = logging.StreamHandler()
stream.setLevel(LOG_LEVEL)
stream.setFormatter(formatter)
logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)
logger.addHandler(stream)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to MongoDB
    # dbm.connect_to_database()
    osm.connect()
    yield
    # Close log file
    # dbm.close_database_connection()
    osm.disconnect()


app = FastAPI(lifespan=lifespan)

# Include the router from router/llm/chat.py
# All routes defined in llm_chat.router will be prefixed with /llm
# (e.g., /llm/start-chat, /llm/chat)
# If you don't want the prefix, remove prefix="/llm"
app.include_router(chat.router, prefix="/llm", tags=["LLM Chat"])
app.include_router(document.router, prefix="/docs", tags=["Documents"])

# You could add other routers or root-level endpoints here if needed
@app.get("/")
def read_root():
    return {"message": "Ollama Chat API is running"}

