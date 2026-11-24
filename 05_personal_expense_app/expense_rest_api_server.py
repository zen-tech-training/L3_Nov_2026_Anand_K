from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from expenses_agent import invoke, initialize_graph, personal_expenses_graph
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):

    print("Initializing LangGraph agent...")

    # Initialize graph only once
    await initialize_graph()

    print("LangGraph agent initialized successfully!")

    yield

    # Cleanup when server shuts down
    print("Shutting down FastAPI...")

app = FastAPI(title="Personal Expenses Application", lifespan=lifespan)
router = APIRouter()

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    # Add more allowed origins here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # or ["*"] for all origins
    allow_credentials=True,
    allow_methods=["*"],            # or ["GET", "POST", ...]
    allow_headers=["*"],            # or specific headers
)

@app.get("/chatbot/")
async def get_answer(query: str):
    response = await invoke(query)
    print("Response from expenses agent:", response)
    return {"response": response}


# Run below command to start the server
# py -m uvicorn expense_rest_api_server:app --reload --port 8000