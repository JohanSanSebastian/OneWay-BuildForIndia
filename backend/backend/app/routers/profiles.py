from fastapi import APIRouter, HTTPException
from typing import List
from app.models import Profile, UtilityAccount, ServiceType
from app import database as db

router = APIRouter()


@router.post("/", response_model=Profile)
async def create_profile(profile: Profile):
    """Create a new user profile"""
    result = db.create_profile(name=profile.name)
    return Profile(
        id=result["id"],
        name=result["name"],
        accounts=[UtilityAccount(**acc) for acc in result.get("accounts", [])]
    )


@router.get("/", response_model=List[Profile])
async def get_all_profiles():
    """Get all profiles"""
    profiles = db.get_all_profiles()
    return [
        Profile(
            id=p["id"],
            name=p["name"],
            accounts=[UtilityAccount(**acc) for acc in p.get("accounts", [])]
        )
        for p in profiles
    ]


@router.get("/{profile_id}", response_model=Profile)
async def get_profile(profile_id: str):
    """Get a specific profile"""
    profile = db.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return Profile(
        id=profile["id"],
        name=profile["name"],
        accounts=[UtilityAccount(**acc) for acc in profile.get("accounts", [])]
    )


@router.delete("/{profile_id}")
async def delete_profile(profile_id: str):
    """Delete a profile"""
    success = db.delete_profile(profile_id)
    if not success:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"message": "Profile deleted successfully"}


@router.post("/{profile_id}/accounts", response_model=UtilityAccount)
async def add_account(profile_id: str, account: UtilityAccount):
    """Add a utility account to a profile"""
    # Check if profile exists
    profile = db.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    result = db.create_account(
        profile_id=profile_id,
        service_type=account.service_type,
        consumer_id=account.consumer_id,
        label=account.label,
        number_plate=getattr(account, 'number_plate', None)
    )
    
    return UtilityAccount(**result)


@router.get("/{profile_id}/accounts", response_model=List[UtilityAccount])
async def get_profile_accounts(profile_id: str):
    """Get all accounts for a profile"""
    profile = db.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    accounts = db.get_profile_accounts(profile_id)
    return [UtilityAccount(**acc) for acc in accounts]


@router.delete("/{profile_id}/accounts/{account_id}")
async def remove_account(profile_id: str, account_id: str):
    """Remove an account from a profile"""
    profile = db.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    success = db.delete_account(account_id)
    if not success:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return {"message": "Account removed successfully"}
