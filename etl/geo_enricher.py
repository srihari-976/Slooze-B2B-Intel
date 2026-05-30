import logging
from typing import Dict, Any, Optional
import re

logger = logging.getLogger(__name__)

class GeoEnricher:
    """Handles geographical enrichment of supplier locations."""
    
    def __init__(self):
        """Initialize the geo enricher with location mapping data."""
        # Indian state to region mapping
        self.state_to_region = {
            'North India': [
                'Delhi', 'Haryana', 'Himachal Pradesh', 'Jammu and Kashmir',
                'Ladakh', 'Punjab', 'Rajasthan', 'Uttar Pradesh', 'Uttarakhand'
            ],
            'West India': [
                'Goa', 'Gujarat', 'Maharashtra'
            ],
            'South India': [
                'Andhra Pradesh', 'Karnataka', 'Kerala', 'Tamil Nadu', 'Telangana'
            ],
            'East India': [
                'Bihar', 'Jharkhand', 'Odisha', 'West Bengal', 'Sikkim'
            ],
            'Northeast India': [
                'Arunachal Pradesh', 'Assam', 'Manipur', 'Meghalaya',
                'Mizoram', 'Nagaland', 'Tripura'
            ],
            'Central India': [
                'Chhattisgarh', 'Madhya Pradesh'
            ]
        }
        
        # Create reverse mapping (state -> region)
        self.state_to_region_map = {}
        for region, states in self.state_to_region.items():
            for state in states:
                self.state_to_region_map[state] = region
        
        # Major cities to state mapping (Indian cities)
        self.city_to_state = {
            # North India
            'Delhi': 'Delhi',
            'New Delhi': 'Delhi',
            'Chandigarh': 'Punjab',
            'Jaipur': 'Rajasthan',
            'Lucknow': 'Uttar Pradesh',
            'Kanpur': 'Uttar Pradesh',
            'Agra': 'Uttar Pradesh',
            'Varanasi': 'Uttar Pradesh',
            'Amritsar': 'Punjab',
            'Dehradun': 'Uttarakhand',
            'Shimla': 'Himachal Pradesh',
            
            # West India
            'Mumbai': 'Maharashtra',
            'Pune': 'Maharashtra',
            'Nagpur': 'Maharashtra',
            'Ahmedabad': 'Gujarat',
            'Surat': 'Gujarat',
            'Vadodara': 'Gujarat',
            'Rajkot': 'Gujarat',
            'Goa': 'Goa',
            'Panaji': 'Goa',
            
            # South India
            'Bangalore': 'Karnataka',
            'Bengaluru': 'Karnataka',
            'Mysore': 'Karnataka',
            'Hubli': 'Karnataka',
            'Chennai': 'Tamil Nadu',
            'Coimbatore': 'Tamil Nadu',
            'Madurai': 'Tamil Nadu',
            'Hyderabad': 'Telangana',
            'Warangal': 'Telangana',
            'Kochi': 'Kerala',
            'Thiruvananthapuram': 'Kerala',
            'Kozhikode': 'Kerala',
            'Visakhapatnam': 'Andhra Pradesh',
            'Vijayawada': 'Andhra Pradesh',
            'Tirupati': 'Andhra Pradesh',
            
            # East India
            'Kolkata': 'West Bengal',
            'Howrah': 'West Bengal',
            'Patna': 'Bihar',
            'Ranchi': 'Jharkhand',
            'Jamshedpur': 'Jharkhand',
            'Bhubaneswar': 'Odisha',
            'Cuttack': 'Odisha',
            
            # Northeast India
            'Guwahati': 'Assam',
            'Shillong': 'Meghalaya',
            'Imphal': 'Manipur',
            'Aizawl': 'Mizoram',
            'Agartala': 'Tripura',
            'Kohima': 'Nagaland',
            
            # Central India
            'Bhopal': 'Madhya Pradesh',
            'Indore': 'Madhya Pradesh',
            'Jabalpur': 'Madhya Pradesh',
            'Raipur': 'Chhattisgarh'
        }
    
    def enrich_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a product with geographical information.
        
        Args:
            product: Product dictionary to enrich
            
        Returns:
            Enriched product dictionary with geo information
        """
        enriched = product.copy()
        
        # Extract and enrich location information
        location_raw = product.get('supplier_location_raw') or product.get('supplier_location')
        if location_raw:
            geo_info = self._parse_and_enrich_location(location_raw)
            enriched.update(geo_info)
        
        return enriched
    
    def _parse_and_enrich_location(self, location_str: str) -> Dict[str, Any]:
        """
        Parse location string and extract city, state, country, and region.
        
        Args:
            location_str: Raw location string (e.g., "Mumbai, Maharashtra, India")
            
        Returns:
            Dictionary with geo information
        """
        geo_info = {
            'supplier_location_raw': location_str,
            'supplier_city': None,
            'supplier_state': None,
            'supplier_country': None,
            'supplier_region': None
        }
        
        if not location_str or not isinstance(location_str, str):
            return geo_info
        
        # Clean the location string
        location_str = location_str.strip()
        
        # Split by common separators
        parts = [part.strip() for part in re.split(r'[,/-]', location_str) if part.strip()]
        
        # Try to parse as city, state, country format
        if len(parts) >= 3:
            # Format: city, state, country
            city, state, country = parts[0], parts[1], ','.join(parts[2:])
            geo_info['supplier_city'] = city
            geo_info['supplier_state'] = state
            geo_info['supplier_country'] = country
        elif len(parts) == 2:
            # Format: city, state or state, country
            # Assume first part is city, second is state/country
            city = parts[0]
            second = parts[1]
            
            # Check if second part looks like a state
            if second in self.state_to_region_map:
                geo_info['supplier_city'] = city
                geo_info['supplier_state'] = second
                geo_info['supplier_country'] = 'India'  # Default assumption
            else:
                # Might be state, country format
                geo_info['supplier_state'] = city
                geo_info['supplier_country'] = second
        elif len(parts) == 1:
            # Just one part - could be city, state, or country
            single_part = parts[0]
            
            # Check if it's a known city
            if single_part in self.city_to_state:
                geo_info['supplier_city'] = single_part
                geo_info['supplier_state'] = self.city_to_state[single_part]
                geo_info['supplier_country'] = 'India'
            # Check if it's a known state
            elif single_part in self.state_to_region_map:
                geo_info['supplier_state'] = single_part
                geo_info['supplier_country'] = 'India'
            else:
                # Assume it's a city and try to infer state
                geo_info['supplier_city'] = single_part
                # Try to find state from known cities (partial match)
                for city, state in self.city_to_state.items():
                    if single_part.lower() in city.lower() or city.lower() in single_part.lower():
                        geo_info['supplier_state'] = state
                        geo_info['supplier_country'] = 'India'
                        break
        
        # Determine region from state
        if geo_info['supplier_state']:
            state = geo_info['supplier_state']
            geo_info['supplier_region'] = self.state_to_region_map.get(state)
        
        # If country is not specified but we're dealing with Indian cities/states, default to India
        if (geo_info['supplier_city'] in self.city_to_state or 
            geo_info['supplier_state'] in self.state_to_region_map) and \
           not geo_info['supplier_country']:
            geo_info['supplier_country'] = 'India'
        
        return geo_info
