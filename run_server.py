import uvicorn
from src.config import Config

if __name__ == "__main__":
    uvicorn.run("src.api.server:app", host="0.0.0.0", port=Config.PORT)
