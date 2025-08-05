import logging
import sys
from ..config import settings

def setup_logging():
    level = logging.DEBUG if settings.environment == "development" else logging.INFO
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(level)
    logging.getLogger("fastapi").setLevel(level)
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)