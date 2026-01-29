# Dynamic Master Data API Routes
from .meta_entities import router as meta_entities_router
from .meta_attributes import router as meta_attributes_router
from .master_data import router as master_data_router
from .fact_definitions import router as fact_definitions_router
from .fact_data import router as fact_data_router

__all__ = [
    "meta_entities_router",
    "meta_attributes_router", 
    "master_data_router",
    "fact_definitions_router",
    "fact_data_router"
]
