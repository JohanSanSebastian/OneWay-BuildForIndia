"""
Kerala Authority Directory

Provides contact information for emergency services and government departments
across Kerala districts and municipalities.
"""
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class KeralaAuthorityDirectory:
    """
    Directory of Kerala government authorities and emergency services.
    Maps incident types to relevant departments and provides contact information.
    """
    
    # Authority type to department mapping
    AUTHORITY_MAPPING = {
        # Natural Disasters
        "landslide": ["SDMA", "Fire_Rescue", "PWD", "Police"],
        "flood": ["SDMA", "Fire_Rescue", "KWA", "Police"],
        "cyclone": ["SDMA", "KSEB", "Fire_Rescue", "Police"],
        "earthquake": ["SDMA", "Fire_Rescue", "PWD", "Police"],
        "storm_damage": ["SDMA", "KSEB", "Fire_Rescue"],
        
        # Infrastructure
        "broken_power_line": ["KSEB"],
        "pothole": ["PWD", "LSGD"],
        "road_damage": ["PWD", "LSGD"],
        "water_main_break": ["KWA"],
        "collapsed_structure": ["Fire_Rescue", "PWD", "Police"],
        
        # Obstructions
        "fallen_tree": ["Fire_Rescue", "LSGD", "Forest"],
        "vehicle_accident": ["Police", "Fire_Rescue"],
        "debris": ["LSGD", "PWD"],
        "blocked_drain": ["LSGD", "KWA"],
        "construction_hazard": ["LSGD", "PWD", "Police"],
    }
    
    # State-level emergency contacts
    STATE_AUTHORITIES = {
        "SDMA": {
            "name": "State Disaster Management Authority",
            "department": "SDMA Kerala",
            "phone": "1070",
            "alt_phone": "0471-2364424",
            "email": "sdma.kerala@nic.in",
            "type": "emergency"
        },
        "Fire_Rescue": {
            "name": "Kerala Fire & Rescue Services",
            "department": "Fire & Rescue",
            "phone": "101",
            "alt_phone": "0471-2320181",
            "email": "dgpfr.ker@gov.in",
            "type": "emergency"
        },
        "Police": {
            "name": "Kerala Police",
            "department": "Police",
            "phone": "100",
            "alt_phone": "0471-2721547",
            "email": "dgpkl@gmail.com",
            "type": "emergency"
        },
        "KSEB": {
            "name": "Kerala State Electricity Board",
            "department": "KSEB Ltd",
            "phone": "1912",
            "alt_phone": "0471-2514688",
            "email": "prokseb@gmail.com",
            "type": "utility"
        },
        "KWA": {
            "name": "Kerala Water Authority",
            "department": "KWA",
            "phone": "1916",
            "alt_phone": "0471-2324903",
            "email": "md@kwa.kerala.gov.in",
            "type": "utility"
        },
        "PWD": {
            "name": "Public Works Department",
            "department": "PWD Kerala",
            "phone": "0471-2328496",
            "email": "pwdker@gmail.com",
            "type": "government"
        },
        "LSGD": {
            "name": "Local Self Government Department",
            "department": "LSGD",
            "phone": "0471-2518222",
            "email": "lsgdkerala@gmail.com",
            "type": "government"
        },
        "Forest": {
            "name": "Kerala Forest Department",
            "department": "Forest",
            "phone": "1800-425-5525",
            "email": "pccf@kerala.gov.in",
            "type": "government"
        }
    }
    
    # District-wise authorities (sample - can be expanded)
    DISTRICT_AUTHORITIES = {
        "Thiruvananthapuram": {
            "collectorate": "0471-2731177",
            "district_emergency": "0471-2730045",
            "control_room": "0471-2338100"
        },
        "Ernakulam": {
            "collectorate": "0484-2422201",
            "district_emergency": "0484-2422221",
            "control_room": "0484-2423001"
        },
        "Kozhikode": {
            "collectorate": "0495-2371400",
            "district_emergency": "0495-2371100",
            "control_room": "0495-2370002"
        },
        "Thrissur": {
            "collectorate": "0487-2360800",
            "district_emergency": "0487-2362424",
            "control_room": "0487-2361020"
        },
        "Kannur": {
            "collectorate": "0497-2700645",
            "district_emergency": "0497-2706645",
            "control_room": "0497-2712359"
        },
        "Malappuram": {
            "collectorate": "0483-2734096",
            "district_emergency": "0483-2734800",
            "control_room": "0483-2734201"
        },
        "Palakkad": {
            "collectorate": "0491-2505273",
            "district_emergency": "0491-2505176",
            "control_room": "0491-2515102"
        },
        "Alappuzha": {
            "collectorate": "0477-2251720",
            "district_emergency": "0477-2238630",
            "control_room": "0477-2238530"
        },
        "Kottayam": {
            "collectorate": "0481-2562201",
            "district_emergency": "0481-2560200",
            "control_room": "0481-2564100"
        },
        "Kollam": {
            "collectorate": "0474-2794900",
            "district_emergency": "0474-2793300",
            "control_room": "0474-2745001"
        },
        "Idukki": {
            "collectorate": "0486-2232003",
            "district_emergency": "0486-2233105",
            "control_room": "0486-2232500"
        },
        "Pathanamthitta": {
            "collectorate": "0468-2322515",
            "district_emergency": "0468-2220206",
            "control_room": "0468-2322636"
        },
        "Wayanad": {
            "collectorate": "0493-6202276",
            "district_emergency": "0493-6202276",
            "control_room": "0493-2602255"
        },
        "Kasaragod": {
            "collectorate": "0467-2234700",
            "district_emergency": "0467-2230530",
            "control_room": "0467-2230345"
        }
    }
    
    # Approximate district boundaries (lat/lon centers)
    DISTRICT_COORDINATES = {
        "Thiruvananthapuram": (8.5241, 76.9366),
        "Kollam": (8.8932, 76.6141),
        "Pathanamthitta": (9.2648, 76.7870),
        "Alappuzha": (9.4981, 76.3388),
        "Kottayam": (9.5916, 76.5222),
        "Idukki": (9.8453, 76.9715),
        "Ernakulam": (9.9312, 76.2673),
        "Thrissur": (10.5276, 76.2144),
        "Palakkad": (10.7867, 76.6548),
        "Malappuram": (11.0510, 76.0711),
        "Kozhikode": (11.2588, 75.7804),
        "Wayanad": (11.6854, 76.1320),
        "Kannur": (11.8745, 75.3704),
        "Kasaragod": (12.4996, 74.9869)
    }
    
    def __init__(self):
        logger.info("KeralaAuthorityDirectory initialized")
    
    def get_district_from_coordinates(
        self, 
        latitude: Optional[float], 
        longitude: Optional[float]
    ) -> Optional[str]:
        """
        Determine the district based on GPS coordinates.
        Uses simple nearest-center approach.
        """
        if latitude is None or longitude is None:
            return None
        
        # Kerala bounding box check
        if not (8.0 <= latitude <= 13.0 and 74.0 <= longitude <= 78.0):
            logger.warning(f"Coordinates {latitude}, {longitude} outside Kerala")
            return None
        
        # Find nearest district center
        min_distance = float('inf')
        nearest_district = None
        
        for district, (lat, lon) in self.DISTRICT_COORDINATES.items():
            distance = ((latitude - lat) ** 2 + (longitude - lon) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                nearest_district = district
        
        return nearest_district
    
    def get_authorities(
        self,
        category: str,
        subcategory: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> List[dict]:
        """
        Get list of relevant authorities for an incident.
        """
        authorities = []
        
        # Get authority types for this subcategory
        authority_keys = self.AUTHORITY_MAPPING.get(
            subcategory.lower(), 
            ["LSGD", "Police"]  # Default fallback
        )
        
        # Add state-level authorities
        for key in authority_keys:
            if key in self.STATE_AUTHORITIES:
                auth = self.STATE_AUTHORITIES[key].copy()
                auth["level"] = "state"
                auth["key"] = key
                authorities.append(auth)
        
        # Add district-level contacts if location available
        district = self.get_district_from_coordinates(latitude, longitude)
        if district and district in self.DISTRICT_AUTHORITIES:
            district_info = self.DISTRICT_AUTHORITIES[district]
            authorities.append({
                "name": f"{district} District Collectorate",
                "department": "District Administration",
                "phone": district_info.get("collectorate", ""),
                "alt_phone": district_info.get("control_room", ""),
                "type": "government",
                "level": "district",
                "key": "collectorate",
                "district": district
            })
            
            # Add district emergency operations center
            authorities.append({
                "name": f"{district} Emergency Operations Center",
                "department": "District Emergency Management",
                "phone": district_info.get("district_emergency", ""),
                "type": "emergency",
                "level": "district", 
                "key": "deoc",
                "district": district
            })
        
        return authorities
    
    def get_all_emergency_contacts(self) -> dict:
        """Get all emergency contacts organized by type."""
        return {
            "emergency": [
                auth for auth in self.STATE_AUTHORITIES.values() 
                if auth.get("type") == "emergency"
            ],
            "utility": [
                auth for auth in self.STATE_AUTHORITIES.values()
                if auth.get("type") == "utility"
            ],
            "government": [
                auth for auth in self.STATE_AUTHORITIES.values()
                if auth.get("type") == "government"
            ],
            "districts": self.DISTRICT_AUTHORITIES
        }
    
    def search_authority(self, query: str) -> List[dict]:
        """Search for authorities by name or department."""
        query = query.lower()
        results = []
        
        for key, auth in self.STATE_AUTHORITIES.items():
            if (query in auth["name"].lower() or 
                query in auth["department"].lower() or
                query in key.lower()):
                result = auth.copy()
                result["key"] = key
                results.append(result)
        
        return results
