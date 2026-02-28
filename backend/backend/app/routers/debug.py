from fastapi import APIRouter
from app.models import ServiceType
from app.services.navigator import UtilityNavigator

router = APIRouter()

@router.get("/debug/page-structure/{service_type}/{consumer_id}")
async def debug_page_structure(service_type: ServiceType, consumer_id: str):
    """Debug endpoint to see what's extracted from the page"""
    navigator = UtilityNavigator()
    
    # Fetch bill which will extract history
    scraped_data = await navigator.fetch_bill_data(
        service_type=service_type,
        consumer_id=consumer_id
    )
    
    return {
        "consumer_name": scraped_data.consumer_name,
        "amount_due": scraped_data.amount_due,
        "history_count": len(scraped_data.history),
        "history_sample": scraped_data.history[:3] if scraped_data.history else [],
        "message": f"Extracted {len(scraped_data.history)} historical bills"
    }
