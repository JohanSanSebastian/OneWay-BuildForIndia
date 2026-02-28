from fastapi import APIRouter, HTTPException
import logging
from functools import lru_cache
from typing import List, Dict, Any
from collections import defaultdict
from datetime import datetime
from app.models import (
    ServiceType, UtilityBill, BillingHistory, 
    NavigationRequest, ScrapedData, PaymentStatus
)
from app.services.navigator import UtilityNavigator
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)


class ChartDataRequest(BaseModel):
    """Request model for chart data endpoint."""
    accounts: List[Dict[str, Any]]
    bill_data: Dict[str, Dict[str, Any]]


@lru_cache(maxsize=1)
def get_navigator() -> UtilityNavigator:
    """Return cached UtilityNavigator instance."""
    return UtilityNavigator()

# In-memory storage for demo (replace with database in production)
billing_history_db: dict = {}


@router.get("/services")
async def get_available_services():
    """Get list of available utility services"""
    return {
        "services": [
            {
                "id": ServiceType.KSEB,
                "name": "KSEB (Kerala State Electricity Board)",
                "icon": "⚡",
                "color": "#f59e0b"
            },
            {
                "id": ServiceType.KWA,
                "name": "KWA (Kerala Water Authority)",
                "icon": "💧",
                "color": "#3b82f6"
            },
            {
                "id": ServiceType.ECHALLAN,
                "name": "e-Challan (Traffic Fines)",
                "icon": "🚗",
                "color": "#ef4444"
            },
            {
                "id": ServiceType.KSMART,
                "name": "K-Smart (Municipal Services)",
                "icon": "🏛️",
                "color": "#10b981"
            }
        ]
    }


@router.post("/fetch-bill")
async def fetch_bill(request: NavigationRequest) -> UtilityBill:
    """Fetch current bill details for a utility account"""
    try:
        navigator = get_navigator()
        scraped_data = await navigator.fetch_bill_data(
            service_type=request.service_type,
            consumer_id=request.consumer_id,
            number_plate=request.number_plate,
        )
        
        # Store historical data for this account
        account_key = f"{request.service_type.value}_{request.consumer_id}"
        if scraped_data.history:
            billing_history_db[account_key] = scraped_data.history
            logger.info(f"Stored {len(scraped_data.history)} historical bills for {account_key}")
        
        return UtilityBill(
            account_id=account_key,
            service_type=request.service_type,
            consumer_name=scraped_data.consumer_name,
            amount_due=scraped_data.amount_due,
            due_date=scraped_data.additional_info.get("due_date"),
            status=scraped_data.status,
            units_consumed=scraped_data.additional_info.get("units"),
            billing_period=scraped_data.additional_info.get("billing_period")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{service_type}/{consumer_id}")
async def get_billing_history(
    service_type: ServiceType, 
    consumer_id: str
) -> List[BillingHistory]:
    """Get billing history for visualization"""
    try:
        account_key = f"{service_type.value}_{consumer_id}"
        
        # First check if we have stored historical data from bill fetch
        if account_key in billing_history_db:
            logger.info(f"Returning {len(billing_history_db[account_key])} stored historical bills for {account_key}")
            return billing_history_db[account_key]
        
        # Fallback to fetching from navigator (legacy behavior)
        logger.info(f"No stored history, fetching for {account_key}")
        navigator = get_navigator()
        history = await navigator.fetch_billing_history(
            service_type=service_type,
            consumer_id=consumer_id
        )
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/{profile_id}")
async def get_profile_summary(profile_id: str):
    """Get aggregated summary for all accounts in a profile"""
    # This would aggregate data from all accounts
    return {
        "profile_id": profile_id,
        "total_due": 0,
        "accounts_with_dues": 0,
        "total_accounts": 0
    }


SERVICE_META = {
    "kseb": {"name": "KSEB", "color": "#d97706"},
    "kwa": {"name": "KWA", "color": "#119bb0"},
    "echallan": {"name": "e-Challan", "color": "#f59e0b"},
    "ksmart": {"name": "K-Smart", "color": "#fbbf24"},
}


@router.post("/chart-data")
async def get_chart_data(request: ChartDataRequest):
    """
    Compute chart data from real historical data.
    Zero-fabrication policy: returns only actual data, no padding or mock values.
    """
    accounts = request.accounts
    bill_data = request.bill_data
    
    # Build comparison data (current amounts per service type)
    service_totals = defaultdict(float)
    for acc in accounts:
        service_type = acc.get("service_type", "")
        acc_id = acc.get("id", "")
        amount = bill_data.get(acc_id, {}).get("amount_due", 0) or 0
        service_totals[service_type] += amount
    
    comparison_data = []
    for svc, total in service_totals.items():
        meta = SERVICE_META.get(svc, {"name": svc, "color": "#94a3b8"})
        comparison_data.append({
            "service": meta["name"],
            "amount": round(total, 2),
            "fill": meta["color"]
        })
    
    # Build trend data from REAL historical data only
    # Collect all historical records from billing_history_db
    month_data = defaultdict(lambda: defaultdict(float))
    available_months = set()
    
    for acc in accounts:
        service_type = acc.get("service_type", "")
        consumer_id = acc.get("consumer_id", "")
        account_key = f"{service_type}_{consumer_id}"
        
        history = billing_history_db.get(account_key, [])
        for record in history:
            # Parse date to get month
            date_str = record.date if hasattr(record, 'date') else record.get("date", "")
            amount = record.amount if hasattr(record, 'amount') else record.get("amount", 0)
            
            try:
                # Try parsing different date formats
                for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%B %Y", "%b %Y"]:
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        month_key = dt.strftime("%b %Y")
                        month_data[month_key][service_type] += amount
                        available_months.add((dt.year, dt.month, month_key))
                        break
                    except ValueError:
                        continue
            except Exception:
                pass
    
    # Sort months chronologically and build trend data
    sorted_months = sorted(available_months, key=lambda x: (x[0], x[1]))
    trend_data = []
    for _, _, month_key in sorted_months:
        row = {"month": month_key}
        for svc in service_totals.keys():
            row[svc] = round(month_data[month_key].get(svc, 0), 2)
        trend_data.append(row)
    
    # Build trend lines config
    trend_lines = []
    for svc in service_totals.keys():
        meta = SERVICE_META.get(svc, {"name": svc, "color": "#94a3b8"})
        trend_lines.append({
            "key": svc,
            "color": meta["color"],
            "label": meta["name"]
        })
    
    return {
        "comparison_data": comparison_data,
        "trend_data": trend_data,
        "trend_lines": trend_lines
    }
