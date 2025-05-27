#!/usr/bin/env python3
"""
FlipHawk eBay Browse API Integration - PRODUCTION VERSION
Uses REAL eBay data from production API (no more dummy data!)
"""

import requests
import base64
import time
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductioneBayAPI:
    """eBay Browse API client using PRODUCTION endpoints with real data"""
    
    def __init__(self, app_id: str, dev_id: str, cert_id: str):
        self.app_id = app_id
        self.dev_id = dev_id
        self.cert_id = cert_id
        
        # PRODUCTION API endpoints (REAL eBay data)
        self.api_base = "https://api.ebay.com"
        self.oauth_base = "https://api.ebay.com"
        
        self.browse_endpoint = f"{self.api_base}/buy/browse/v1"
        self.oauth_endpoint = f"{self.oauth_base}/identity/v1/oauth2/token"
        
        # OAuth token management
        self.access_token = None
        self.token_expires_at = 0
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.2  # 200ms between requests for production
        
        # Keyword variations for better search coverage
        self.keyword_variations = {
            'airpods': ['airpod', 'air pods', 'apple earbuds'],
            'iphone': ['i phone', 'apple phone'],
            'macbook': ['mac book', 'apple laptop'],
            'nintendo switch': ['switch console', 'nintendo swich'],
            'playstation': ['ps5', 'ps4', 'sony playstation'],
            'xbox': ['microsoft xbox', 'xbox series'],
            'pokemon': ['pokémon', 'pokemon cards'],
            'charizard': ['charizard card'],
            'jordan': ['air jordan', 'jordan sneakers'],
            'yeezy': ['adidas yeezy'],
            'supreme': ['supreme clothing'],
            'beats': ['beats headphones', 'beats by dre'],
            'bose': ['bose headphones']
        }
        
        # eBay category IDs
        self.category_ids = {
            "Tech": {
                "Headphones": "15052",
                "Smartphones": "9355",
                "Laptops": "177",
                "Tablets": "171485",
                "Graphics Cards": "27386"
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
                "Watches": "14324"
            }
        }
    
    def get_access_token(self) -> str:
        """Get OAuth access token for PRODUCTION API calls"""
        current_time = time.time()
        
        # Check if current token is still valid (with 5 min buffer)
        if self.access_token and current_time < (self.token_expires_at - 300):
            return self.access_token
        
        try:
            # Encode credentials for OAuth
            credentials = f"{self.app_id}:{self.cert_id}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Basic {encoded_credentials}'
            }
            
            data = {
                'grant_type': 'client_credentials',
                'scope': 'https://api.ebay.com/oauth/api_scope'
            }
            
            logger.info("🔑 Requesting PRODUCTION eBay OAuth token...")
            response = requests.post(self.oauth_endpoint, headers=headers, data=data, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                self.token_expires_at = current_time + token_data['expires_in']
                
                logger.info("✅ PRODUCTION eBay OAuth token obtained successfully")
                return self.access_token
            else:
                logger.error(f"❌ OAuth failed: {response.status_code} - {response.text}")
                raise Exception(f"OAuth authentication failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error getting OAuth token: {e}")
            raise
    
    def _rate_limit(self):
        """Implement rate limiting for production API"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def expand_keywords(self, keyword: str) -> List[str]:
        """Expand keywords with variations"""
        if not keyword:
            return ['']
            
        expanded = [keyword.lower().strip()]
        
        # Add variations from our dictionary
        for base_word, variations in self.keyword_variations.items():
            if base_word in keyword.lower():
                expanded.extend(variations[:2])  # Limit to 2 variations
                break
        
        # Remove duplicates
        seen = set()
        unique_keywords = []
        for kw in expanded:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)
        
        return unique_keywords[:2]  # Max 2 keywords for production API limits
    
    def search_ebay(self, keyword: str = None, category: str = None, subcategory: str = None, 
                   limit: int = 20, sort_order: str = "price") -> List[Dict]:
        """
        Search PRODUCTION eBay for REAL listings
        """
        
        try:
            # Get fresh access token
            token = self.get_access_token()
            
            # Prepare headers for PRODUCTION
            headers = {
                'Authorization': f'Bearer {token}',
                'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US',
                'X-EBAY-C-ENDUSERCTX': 'contextualLocation=country=US,zip=10001',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Get keyword variations
            keywords_to_search = self.expand_keywords(keyword) if keyword else ['']
            all_listings = []
            
            for search_keyword in keywords_to_search:
                logger.info(f"🔍 Searching PRODUCTION eBay for: '{search_keyword or 'category browse'}'")
                
                # Build search parameters
                params = {
                    'limit': min(limit, 50),  # Conservative limit for production
                    'sort': sort_order,
                    'filter': []
                }
                
                # Add keyword if provided
                if search_keyword:
                    params['q'] = search_keyword
                
                # Add category filter if specified
                if category and subcategory:
                    category_id = self.category_ids.get(category, {}).get(subcategory)
                    if category_id:
                        params['filter'].append(f'categoryIds:{category_id}')
                
                # Add filters for better results
                params['filter'].extend([
                    'buyingOptions:{FIXED_PRICE}',  # Buy It Now only
                    'itemLocationCountry:US',       # US sellers only
                    'deliveryCountry:US',           # Ships to US
                ])
                
                # Convert filter array to string
                if params['filter']:
                    params['filter'] = '|'.join(params['filter'])
                else:
                    del params['filter']
                
                # Rate limiting
                self._rate_limit()
                
                # Make PRODUCTION API request
                url = f"{self.browse_endpoint}/item_summary/search"
                response = requests.get(url, headers=headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('itemSummaries', [])
                    
                    logger.info(f"✅ Found {len(items)} REAL items for '{search_keyword}'")
                    
                    # Parse each item
                    for item in items:
                        try:
                            parsed_item = self._parse_item(item)
                            if parsed_item and parsed_item['price'] > 0:
                                all_listings.append(parsed_item)
                        except Exception as e:
                            logger.warning(f"⚠️ Error parsing item: {e}")
                            continue
                
                elif response.status_code == 429:
                    logger.warning("⚠️ Rate limited by eBay API, waiting...")
                    time.sleep(10)
                    continue
                    
                elif response.status_code == 401:
                    logger.warning("🔑 Token expired, refreshing...")
                    self.access_token = None
                    token = self.get_access_token()
                    headers['Authorization'] = f'Bearer {token}'
                    continue
                    
                else:
                    logger.error(f"❌ API error: {response.status_code} - {response.text}")
                    continue
                
                # Delay between keyword variations
                time.sleep(1)
            
            # Remove duplicates and sort
            unique_listings = self._deduplicate_listings(all_listings)
            
            if sort_order == "price":
                unique_listings.sort(key=lambda x: x['total_cost'])
            elif sort_order == "newest":
                unique_listings.sort(key=lambda x: x['item_creation_date'], reverse=True)
            
            logger.info(f"🎯 PRODUCTION search completed: {len(unique_listings)} REAL listings")
            return unique_listings[:limit]
            
        except Exception as e:
            logger.error(f"❌ PRODUCTION eBay search failed: {e}")
            return []
    
    def _parse_item(self, item: Dict) -> Optional[Dict]:
        """Parse eBay API item response into clean format"""
        try:
            # Basic item info
            item_id = item.get('itemId', '')
            title = item.get('title', '')
            
            if not item_id or not title:
                return None
            
            # Price information
            price_info = item.get('price', {})
            price = float(price_info.get('value', 0))
            currency = price_info.get('currency', 'USD')
            
            # Shipping information
            shipping_cost = 0.0
            shipping_options = item.get('shippingOptions', [])
            if shipping_options:
                shipping_info = shipping_options[0]
                shipping_cost_info = shipping_info.get('shippingCost', {})
                if shipping_cost_info:
                    shipping_cost = float(shipping_cost_info.get('value', 0))
            
            total_cost = price + shipping_cost
            
            # Condition
            condition_info = item.get('condition', {})
            condition = condition_info.get('conditionDisplayName', 'Unknown')
            
            # Category
            categories = item.get('categories', [])
            category_path = ' > '.join([cat.get('categoryName', '') for cat in categories]) if categories else 'Unknown'
            
            # Seller information
            seller_info = item.get('seller', {})
            seller_username = seller_info.get('username', 'Unknown')
            seller_feedback = float(seller_info.get('feedbackPercentage', 0))
            seller_score = int(seller_info.get('feedbackScore', 0))
            
            # Images
            image_info = item.get('image', {})
            image_url = image_info.get('imageUrl', '')
            
            # Item URL
            ebay_link = item.get('itemWebUrl', '')
            
            # Location
            item_location = item.get('itemLocation', {})
            location = item_location.get('city', 'Unknown')
            if item_location.get('country'):
                location = f"{location}, {item_location.get('country')}"
            
            # Additional attributes
            returns_accepted = item.get('returnsAccepted', False)
            top_rated = item.get('topRatedListing', False)
            buying_options = item.get('buyingOptions', [])
            creation_date = item.get('itemCreationDate', '')
            
            return {
                'item_id': item_id,
                'title': title,
                'price': price,
                'currency': currency,
                'shipping_cost': shipping_cost,
                'total_cost': total_cost,
                'condition': condition,
                'category_path': category_path,
                'seller_username': seller_username,
                'seller_feedback_percentage': seller_feedback,
                'seller_feedback_score': seller_score,
                'image_url': image_url,
                'ebay_link': ebay_link,
                'location': location,
                'returns_accepted': returns_accepted,
                'top_rated_listing': top_rated,
                'buying_options': buying_options,
                'item_creation_date': creation_date,
                'parsed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing item: {e}")
            return None
    
    def _deduplicate_listings(self, listings: List[Dict]) -> List[Dict]:
        """Remove duplicate listings based on item_id"""
        seen_ids = set()
        unique_listings = []
        
        for listing in listings:
            if listing['item_id'] not in seen_ids:
                seen_ids.add(listing['item_id'])
                unique_listings.append(listing)
        
        return unique_listings

# Initialize the PRODUCTION API client
ebay_api = ProductioneBayAPI(
    app_id="JackDail-FlipHawk-SBX-bf00e7bcf-34d63630",  # Your App ID
    dev_id="f20a1274-fea2-4041-a8dc-721ecf5f38e9",      # Your Dev ID
    cert_id="SBX-f00e7bcfbabb-98f9-4d3a-bd03-5ff9"      # Your Cert ID
)

def search_ebay(keyword: str = None, category: str = None, subcategory: str = None, 
               limit: int = 20, sort: str = "price") -> List[Dict]:
    """
    Main search function for FlipHawk - REAL eBay data only!
    """
    try:
        logger.info(f"🚀 FlipHawk PRODUCTION search: '{keyword}' in {category}/{subcategory}")
        
        # Search using PRODUCTION eBay API
        listings = ebay_api.search_ebay(
            keyword=keyword,
            category=category,
            subcategory=subcategory,
            limit=limit,
            sort_order=sort
        )
        
        logger.info(f"✅ FlipHawk PRODUCTION search completed: {len(listings)} REAL listings found")
        return listings
        
    except Exception as e:
        logger.error(f"❌ FlipHawk PRODUCTION search failed: {e}")
        return []

def get_categories() -> Dict:
    """Get available categories and keyword suggestions"""
    try:
        return {
            'categories': ebay_api.category_ids,
            'keyword_suggestions': {
                "Tech": {
                    "Headphones": ["airpods", "beats", "bose", "sony headphones"],
                    "Smartphones": ["iphone", "samsung galaxy", "google pixel"],
                    "Laptops": ["macbook", "thinkpad", "dell xps", "gaming laptop"],
                    "Graphics Cards": ["rtx 4090", "rtx 4080", "nvidia", "amd gpu"],
                    "Tablets": ["ipad", "samsung tablet", "surface pro"]
                },
                "Gaming": {
                    "Consoles": ["ps5", "xbox series x", "nintendo switch"],
                    "Video Games": ["call of duty", "fifa", "pokemon", "zelda"],
                    "Gaming Accessories": ["gaming chair", "mechanical keyboard"]
                },
                "Collectibles": {
                    "Trading Cards": ["pokemon cards", "magic cards", "charizard"],
                    "Action Figures": ["hot toys", "funko pop", "marvel legends"],
                    "Coins": ["morgan dollar", "gold coin", "silver coin"]
                },
                "Fashion": {
                    "Sneakers": ["air jordan", "yeezy", "nike dunk", "adidas"],
                    "Designer Clothing": ["supreme", "off white", "gucci"],
                    "Watches": ["rolex", "omega", "apple watch"]
                }
            }
        }
    except Exception as e:
        logger.error(f"❌ Error getting categories: {e}")
        return {'categories': {}, 'keyword_suggestions': {}}

# For backward compatibility
api_client = ebay_api

if __name__ == "__main__":
    # Test the PRODUCTION API
    print("🚀 Testing PRODUCTION eBay API")
    print("=" * 50)
    
    results = search_ebay("airpods", limit=3)
    
    if results:
        print(f"✅ Found {len(results)} REAL eBay listings:")
        for i, item in enumerate(results, 1):
            print(f"{i}. {item['title'][:60]}...")
            print(f"   💰 ${item['price']:.2f} + ${item['shipping_cost']:.2f} = ${item['total_cost']:.2f}")
            print(f"   🏪 {item['seller_username']} ({item['seller_feedback_percentage']:.1f}%)")
            print(f"   🔗 {item['ebay_link']}")
            print()
    else:
        print("❌ No results found")
