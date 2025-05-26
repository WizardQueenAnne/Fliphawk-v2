# Save this as: ebay_api.py

"""
FlipHawk eBay Browse API Integration
Official eBay API integration for real-time listing data
"""

import requests
import json
import time
import re
import logging
from typing import List, Dict, Optional, Set
from datetime import datetime
from dataclasses import dataclass, asdict
import difflib
import base64

# Set up logging
logger = logging.getLogger(__name__)

@dataclass
class EbayListing:
    """eBay listing data structure from Browse API"""
    item_id: str
    title: str
    price: float
    currency: str
    shipping_cost: float
    total_cost: float
    condition: str
    condition_id: str
    category_path: str
    category_id: str
    seller_username: str
    seller_feedback_percentage: float
    seller_feedback_score: int
    image_url: str
    ebay_link: str
    location: str
    listing_marketplace_id: str
    buying_options: List[str]
    item_creation_date: str
    item_end_date: Optional[str]
    watch_count: Optional[int]
    bid_count: Optional[int]
    current_bid_price: Optional[float]
    shipping_service_cost: float
    shipping_type: str
    returns_accepted: bool
    top_rated_listing: bool
    fast_n_free: bool
    plus_eligible: bool

class EbayBrowseAPI:
    """Official eBay Browse API client for FlipHawk"""
    
    def __init__(self, app_id: str, dev_id: str, cert_id: str, is_sandbox: bool = True):
        self.app_id = app_id
        self.dev_id = dev_id
        self.cert_id = cert_id
        self.is_sandbox = is_sandbox
        
        # API endpoints
        if is_sandbox:
            self.api_base = "https://api.sandbox.ebay.com"
            self.oauth_base = "https://api.sandbox.ebay.com"
        else:
            self.api_base = "https://api.ebay.com"
            self.oauth_base = "https://api.ebay.com"
        
        self.browse_endpoint = f"{self.api_base}/buy/browse/v1"
        self.oauth_endpoint = f"{self.oauth_base}/identity/v1/oauth2/token"
        
        # Access token for API calls
        self.access_token = None
        self.token_expires_at = 0
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
        # Common misspellings and variations
        self.keyword_variations = {
            'airpods': ['airpod', 'air pods', 'air pod', 'apple earbuds', 'aripods', 'airpds'],
            'pokemon': ['pokémon', 'pokeman', 'pokemons', 'pocket monsters'],
            'nintendo': ['nintedo', 'nintndo', 'nintendo'],
            'iphone': ['i phone', 'ifone', 'iphome', 'apple phone'],
            'samsung': ['samung', 'samsng', 'samsung galxy'],
            'macbook': ['mac book', 'mackbook', 'macbok', 'apple laptop'],
            'xbox': ['x box', 'xobx', 'microsoft xbox'],
            'playstation': ['play station', 'playstaton', 'ps5', 'ps4'],
            'charizard': ['charizrd', 'charizard', 'charizrd'],
            'supreme': ['supeme', 'suprme', 'supreme'],
            'jordan': ['jorden', 'jordn', 'air jordan'],
            'nike': ['niki', 'nke', 'nike'],
            'adidas': ['addidas', 'adidas', 'addias']
        }
    
    def get_access_token(self) -> str:
        """Get OAuth access token for API calls"""
        current_time = time.time()
        
        # Check if current token is still valid
        if self.access_token and current_time < self.token_expires_at:
            return self.access_token
        
        # Request new token
        try:
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Basic {self._encode_credentials()}'
            }
            
            data = {
                'grant_type': 'client_credentials',
                'scope': 'https://api.ebay.com/oauth/api_scope'
            }
            
            response = requests.post(self.oauth_endpoint, headers=headers, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                # Set expiry to 5 minutes before actual expiry for safety
                self.token_expires_at = current_time + token_data['expires_in'] - 300
                logger.info("✅ Successfully obtained eBay access token")
                return self.access_token
            else:
                logger.error(f"❌ Failed to get access token: {response.status_code} {response.text}")
                raise Exception(f"OAuth failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error getting access token: {e}")
            raise
    
    def _encode_credentials(self) -> str:
        """Encode app credentials for OAuth"""
        credentials = f"{self.app_id}:{self.cert_id}"
        return base64.b64encode(credentials.encode()).decode()
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def expand_keywords(self, keyword: str) -> List[str]:
        """Expand keywords with common variations and misspellings"""
        keywords = [keyword.lower().strip()]
        
        # Add exact variations from our dictionary
        for base_word, variations in self.keyword_variations.items():
            if base_word in keyword.lower():
                keywords.extend(variations)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)
        
        return unique_keywords[:3]  # Limit to top 3 variations
    
    def search_items(self, keyword: str, category_id: str = None, limit: int = 50, 
                    sort: str = "price", condition_ids: List[str] = None) -> List[EbayListing]:
        """Search eBay items using Browse API"""
        
        try:
            # Get access token
            token = self.get_access_token()
            
            # Prepare headers
            headers = {
                'Authorization': f'Bearer {token}',
                'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US',
                'X-EBAY-C-ENDUSERCTX': 'contextualLocation=country=US,zip=94105',
                'Content-Type': 'application/json'
            }
            
            # Get keyword variations
            keyword_variations = self.expand_keywords(keyword) if keyword else ['']
            all_listings = []
            
            for search_keyword in keyword_variations:
                logger.info(f"🔍 Searching eBay for: '{search_keyword}'")
                
                # Prepare search parameters
                params = {
                    'limit': min(limit, 200),  # eBay API limit
                    'sort': sort,
                    'filter': []
                }
                
                # Add keyword if provided
                if search_keyword:
                    params['q'] = search_keyword
                
                # Add category filter if specified
                if category_id:
                    params['filter'].append(f'categoryIds:{category_id}')
                
                # Add condition filter if specified
                if condition_ids:
                    condition_filter = ','.join(condition_ids)
                    params['filter'].append(f'conditions:{condition_filter}')
                
                # Add additional filters for better results
                params['filter'].extend([
                    'buyingOptions:{FIXED_PRICE}',  # Only Buy It Now
                    'itemLocationCountry:US',       # US only
                    'deliveryCountry:US'            # Ships to US
                ])
                
                # Convert filter list to string format
                if params['filter']:
                    params['filter'] = '|'.join(params['filter'])
                else:
                    del params['filter']
                
                # Rate limiting
                self._rate_limit()
                
                # Make API request
                response = requests.get(
                    f"{self.browse_endpoint}/item_summary/search",
                    headers=headers,
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('itemSummaries', [])
                    
                    logger.info(f"✅ Found {len(items)} items for '{search_keyword}'")
                    
                    # Parse items
                    for item in items:
                        try:
                            listing = self._parse_ebay_item(item)
                            if listing:
                                all_listings.append(listing)
                        except Exception as e:
                            logger.warning(f"⚠️ Error parsing item: {e}")
                            continue
                
                elif response.status_code == 429:
                    logger.warning("⚠️ Rate limited by eBay API, waiting...")
                    time.sleep(2)
                    continue
                    
                else:
                    logger.error(f"❌ API error: {response.status_code} {response.text}")
                    continue
                
                # Small delay between keyword variations
                time.sleep(0.5)
            
            # Remove duplicates based on item_id
            seen_ids = set()
            unique_listings = []
            for listing in all_listings:
                if listing.item_id not in seen_ids:
                    seen_ids.add(listing.item_id)
                    unique_listings.append(listing)
            
            # Sort by price if requested
            if sort == "price":
                unique_listings.sort(key=lambda x: x.total_cost)
            
            logger.info(f"🎯 Total unique listings found: {len(unique_listings)}")
            return unique_listings[:limit]
            
        except Exception as e:
            logger.error(f"❌ Error searching eBay: {e}")
            return []
    
    def _parse_ebay_item(self, item: Dict) -> Optional[EbayListing]:
        """Parse eBay API item response into EbayListing object"""
        try:
            # Basic item info
            item_id = item.get('itemId', '')
            title = item.get('title', '')
            
            # Price information
            price_info = item.get('price', {})
            price = float(price_info.get('value', 0))
            currency = price_info.get('currency', 'USD')
            
            # Shipping information
            shipping_info = item.get('shippingOptions', [{}])[0] if item.get('shippingOptions') else {}
            shipping_cost = 0.0
            shipping_type = 'Unknown'
            
            if shipping_info:
                shipping_cost_info = shipping_info.get('shippingCost', {})
                if shipping_cost_info:
                    shipping_cost = float(shipping_cost_info.get('value', 0))
                shipping_type = shipping_info.get('shippingCostType', 'Unknown')
            
            total_cost = price + shipping_cost
            
            # Condition
            condition_info = item.get('condition', {})
            condition = condition_info.get('conditionDisplayName', 'Unknown')
            condition_id = condition_info.get('conditionId', 'UNKNOWN')
            
            # Category
            categories = item.get('categories', [{}])
            category_path = ' > '.join([cat.get('categoryName', '') for cat in categories])
            category_id = categories[0].get('categoryId', '') if categories else ''
            
            # Seller information
            seller_info = item.get('seller', {})
            seller_username = seller_info.get('username', 'Unknown')
            seller_feedback = seller_info.get('feedbackPercentage', 0.0)
            seller_score = seller_info.get('feedbackScore', 0)
            
            # Images
            image_info = item.get('image', {})
            image_url = image_info.get('imageUrl', '')
            
            # Item web URL
            ebay_link = item.get('itemWebUrl', '')
            
            # Location
            item_location = item.get('itemLocation', {})
            location = item_location.get('city', 'Unknown')
            country = item_location.get('country', '')
            if country:
                location = f"{location}, {country}"
            
            # Additional info
            marketplace_id = item.get('listingMarketplaceId', 'EBAY_US')
            buying_options = item.get('buyingOptions', [])
            creation_date = item.get('itemCreationDate', '')
            end_date = item.get('itemEndDate')
            
            # Optional fields
            watch_count = item.get('watchCount')
            bid_count = item.get('bidCount')
            current_bid = item.get('currentBidPrice', {}).get('value') if item.get('currentBidPrice') else None
            
            # Shipping details
            shipping_service_cost = shipping_cost
            returns_accepted = item.get('returnsAccepted', False)
            top_rated = item.get('topRatedListing', False)
            fast_n_free = item.get('qualifiedPrograms', {}).get('fastNFree', False) if item.get('qualifiedPrograms') else False
            plus_eligible = item.get('plusEligible', False)
            
            return EbayListing(
                item_id=item_id,
                title=title,
                price=price,
                currency=currency,
                shipping_cost=shipping_cost,
                total_cost=total_cost,
                condition=condition,
                condition_id=condition_id,
                category_path=category_path,
                category_id=category_id,
                seller_username=seller_username,
                seller_feedback_percentage=seller_feedback,
                seller_feedback_score=seller_score,
                image_url=image_url,
                ebay_link=ebay_link,
                location=location,
                listing_marketplace_id=marketplace_id,
                buying_options=buying_options,
                item_creation_date=creation_date,
                item_end_date=end_date,
                watch_count=watch_count,
                bid_count=bid_count,
                current_bid_price=current_bid,
                shipping_service_cost=shipping_service_cost,
                shipping_type=shipping_type,
                returns_accepted=returns_accepted,
                top_rated_listing=top_rated,
                fast_n_free=fast_n_free,
                plus_eligible=plus_eligible
            )
            
        except Exception as e:
            logger.error(f"❌ Error parsing eBay item: {e}")
            return None

# Category ID mapping for eBay
EBAY_CATEGORY_IDS = {
    "Tech": {
        "Headphones": "15052",
        "Smartphones": "9355", 
        "Laptops": "177",
        "Graphics Cards": "27386",
        "Tablets": "171485"
    },
    "Gaming": {
        "Consoles": "139971",
        "Video Games": "139973",
        "Gaming Accessories": "54968"
    },
    "Collectibles": {
        "Trading Cards": "2536",
        "Action Figures": "246",
        "Coins": "11116"
    },
    "Fashion": {
        "Sneakers": "15709",
        "Designer Clothing": "1059",
        "Vintage Clothing": "175759"
    },
    "Vintage": {
        "Electronics": "181",
        "Cameras": "625"
    }
}

def get_category_keywords():
    """Get keyword suggestions for categories"""
    return {
        "Tech": {
            "Headphones": ["airpods", "beats", "bose", "sony headphones", "wireless earbuds"],
            "Smartphones": ["iphone", "samsung galaxy", "google pixel", "oneplus", "xiaomi"],
            "Laptops": ["macbook", "thinkpad", "dell xps", "hp laptop", "gaming laptop"],
            "Graphics Cards": ["rtx 4090", "rtx 4080", "rx 7900", "nvidia", "amd gpu"],
            "Tablets": ["ipad", "samsung tablet", "surface pro", "kindle fire"]
        },
        "Gaming": {
            "Consoles": ["ps5", "xbox series x", "nintendo switch", "steam deck"],
            "Video Games": ["call of duty", "fifa", "pokemon", "zelda", "mario"],
            "Gaming Accessories": ["gaming chair", "mechanical keyboard", "gaming mouse"]
        },
        "Collectibles": {
            "Trading Cards": ["pokemon cards", "magic the gathering", "basketball cards", "charizard"],
            "Action Figures": ["hot toys", "funko pop", "marvel legends", "star wars"],
            "Coins": ["morgan dollar", "gold coin", "silver coin", "rare coins"]
        },
        "Fashion": {
            "Sneakers": ["air jordan", "yeezy", "nike dunk", "new balance", "adidas"],
            "Designer Clothing": ["supreme", "off white", "gucci", "louis vuitton"],
            "Vintage Clothing": ["vintage band tee", "90s vintage", "carhartt", "tommy hilfiger"]
        },
        "Vintage": {
            "Electronics": ["vintage mac", "nintendo 64", "walkman", "vintage camera"],
            "Cameras": ["leica", "hasselblad", "nikon", "canon", "polaroid"]
        }
    }

# Main search function for FlipHawk integration
def search_ebay(keyword: str, category: str = None, subcategory: str = None, 
               limit: int = 50, sort: str = "price") -> List[Dict]:
    """
    Main eBay search function for FlipHawk
    Returns list of eBay listings as dictionaries
    """
    
    # Initialize eBay API client
    api = EbayBrowseAPI(
        app_id="JackDail-FlipHawk-SBX-bf00e7bcf-34d63630",
        dev_id="f20a1274-fea2-4041-a8dc-721ecf5f38e9",
        cert_id="SBX-f00e7bcfbabb-98f9-4d3a-bd03-5ff9",
        is_sandbox=True
    )
    
    try:
        # Get category ID if category/subcategory specified
        category_id = None
        if category and subcategory:
            category_id = EBAY_CATEGORY_IDS.get(category, {}).get(subcategory)
        
        # Search eBay
        listings = api.search_items(
            keyword=keyword,
            category_id=category_id,
            limit=limit,
            sort=sort
        )
        
        # Convert to dictionaries
        return [asdict(listing) for listing in listings]
        
    except Exception as e:
        logger.error(f"❌ Error in search_ebay: {e}")
        return []

# Demo function
def demo_ebay_api():
    """Demo the eBay API integration"""
    
    print("🚀 FlipHawk eBay API Demo")
    print("=" * 50)
    
    # Test searches
    test_searches = [
        {"keyword": "airpods pro", "limit": 5},
        {"keyword": "nintendo switch", "limit": 5},
        {"keyword": "pokemon cards charizard", "limit": 3}
    ]
    
    for search in test_searches:
        print(f"\n🔍 Searching: '{search['keyword']}'")
        print("-" * 30)
        
        results = search_ebay(**search)
        
        if results:
            for i, item in enumerate(results, 1):
                print(f"{i}. {item['title'][:60]}...")
                print(f"   💰 Price: ${item['price']:.2f} + ${item['shipping_cost']:.2f} shipping = ${item['total_cost']:.2f}")
                print(f"   📦 Condition: {item['condition']}")
                print(f"   🏪 Seller: {item['seller_username']} ({item['seller_feedback_percentage']:.1f}%)")
                print(f"   🔗 {item['ebay_link']}")
                print()
        else:
            print("   ❌ No results found")
    
    print("✅ Demo completed!")

if __name__ == "__main__":
    demo_ebay_api()
