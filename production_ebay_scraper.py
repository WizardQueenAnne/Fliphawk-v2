# production_ebay_scraper.py - Production eBay Browse API Integration

import os
import requests
import base64
import time
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import re
from urllib.parse import urlencode

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class eBayListing:
    """eBay listing data structure from production API"""
    item_id: str
    title: str
    price: float
    currency: str
    shipping_cost: float
    total_cost: float
    condition: str
    condition_id: str
    category_path: str
    seller_username: str
    seller_feedback_percentage: float
    seller_feedback_score: int
    image_url: str
    ebay_link: str
    location: str
    returns_accepted: bool
    top_rated_listing: bool
    fast_n_free: bool
    buying_options: List[str]
    item_creation_date: str
    confidence_score: int
    arbitrage_potential: float

class ProductioneBayAPI:
    """Production eBay Browse API client for FlipHawk"""
    
    def __init__(self):
        # Get credentials from environment variables
        self.app_id = os.getenv('EBAY_APP_ID', 'JackDail-FlipHawk-SBX-bf00e7bcf-34d63630')
        self.cert_id = os.getenv('EBAY_CERT_ID', 'SBX-f00e7bcfbabb-98f9-4d3a-bd03-5ff9')
        self.dev_id = os.getenv('EBAY_DEV_ID', 'f20a1274-fea2-4041-a8dc-721ecf5f38e9')
        
        # Production API endpoints
        self.api_base = "https://api.ebay.com"
        self.browse_endpoint = f"{self.api_base}/buy/browse/v1"
        self.oauth_endpoint = f"{self.api_base}/identity/v1/oauth2/token"
        
        # OAuth token management
        self.access_token = None
        self.token_expires_at = 0
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
        # Keyword variations for better search coverage
        self.keyword_variations = {
            # Headphones
            'airpods': ['airpod', 'air pods', 'air pod', 'apple earbuds', 'aripods', 'airpds', 'apple airpods'],
            'beats': ['beat headphones', 'beats by dre', 'beats audio', 'dr dre'],
            'bose': ['bose headphones', 'bose quietcomfort', 'bose qc', 'bose noise cancelling'],
            
            # Gaming
            'nintendo switch': ['nintendo swich', 'nintedo switch', 'switch console', 'nintendo switch oled'],
            'playstation': ['play station', 'playstaton', 'ps5', 'ps4', 'sony playstation'],
            'xbox': ['x box', 'xobx', 'microsoft xbox', 'xbox series x', 'xbox series s'],
            
            # Phones
            'iphone': ['i phone', 'ifone', 'iphome', 'apple phone', 'iphone 15', 'iphone 14'],
            'samsung': ['samung', 'samsng', 'samsung galaxy', 'galaxy phone'],
            
            # Sneakers
            'jordan': ['jorden', 'jordn', 'air jordan', 'nike jordan', 'jordan retro'],
            'yeezy': ['yezy', 'adidas yeezy', 'kanye west', 'yeezy boost'],
            'nike': ['niki', 'nke', 'nike shoes', 'nike sneakers'],
            
            # Pokemon
            'pokemon': ['pokémon', 'pokeman', 'pokemons', 'pocket monsters', 'pokemon cards'],
            'charizard': ['charizrd', 'charizard card', 'charizrd pokemon'],
            
            # Apple Products
            'macbook': ['mac book', 'mackbook', 'macbok', 'apple laptop', 'macbook pro', 'macbook air'],
            'ipad': ['i pad', 'apple tablet', 'ipad pro', 'ipad air'],
            
            # Fashion
            'supreme': ['supeme', 'suprme', 'supreme clothing', 'supreme box logo'],
            'off white': ['offwhite', 'off-white', 'virgil abloh'],
        }
        
        # eBay category IDs for production API
        self.category_ids = {
            "Tech": {
                "Headphones": "15052",
                "Smartphones": "9355",
                "Laptops": "177",
                "Tablets": "171485",
                "Graphics Cards": "27386",
                "Gaming Accessories": "54968"
            },
            "Gaming": {
                "Consoles": "139971",
                "Video Games": "139973",
                "Gaming Accessories": "54968",
                "Retro Gaming": "139973"
            },
            "Collectibles": {
                "Trading Cards": "2536",
                "Action Figures": "246",
                "Coins": "11116",
                "Sports Memorabilia": "64482"
            },
            "Fashion": {
                "Sneakers": "15709",
                "Designer Clothing": "1059",
                "Vintage Clothing": "175759",
                "Watches": "14324",
                "Handbags": "169291"
            },
            "Electronics": {
                "TV & Audio": "293",
                "Cameras": "625",
                "Smart Home": "184",
                "Car Electronics": "3270"
            }
        }
    
    def get_access_token(self) -> str:
        """Get OAuth access token for production API calls"""
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
            
            logger.info("🔑 Requesting production eBay OAuth token...")
            response = requests.post(self.oauth_endpoint, headers=headers, data=data, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                self.token_expires_at = current_time + token_data['expires_in']
                
                logger.info("✅ Production eBay OAuth token obtained successfully")
                return self.access_token
            else:
                logger.error(f"❌ OAuth failed: {response.status_code} - {response.text}")
                raise Exception(f"OAuth authentication failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error getting OAuth token: {e}")
            raise
    
    def _rate_limit(self):
        """Implement rate limiting to respect eBay API limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def expand_keywords(self, keyword: str) -> List[str]:
        """Expand keywords with variations and common misspellings"""
        expanded = [keyword.lower().strip()]
        
        # Add variations from our dictionary
        for base_word, variations in self.keyword_variations.items():
            if base_word in keyword.lower():
                expanded.extend(variations)
                break
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in expanded:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)
        
        return unique_keywords[:3]  # Limit to top 3 variations for efficiency
    
    def search_items(self, keyword: str, category: str = None, subcategory: str = None, 
                    limit: int = 50, sort: str = "price") -> List[eBayListing]:
        """Search production eBay items using Browse API"""
        
        try:
            # Get fresh access token
            token = self.get_access_token()
            
            # Prepare headers for production API
            headers = {
                'Authorization': f'Bearer {token}',
                'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US',
                'X-EBAY-C-ENDUSERCTX': 'contextualLocation=country=US,zip=10001',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Get keyword variations for better coverage
            keyword_variations = self.expand_keywords(keyword)
            all_listings = []
            
            for search_keyword in keyword_variations:
                logger.info(f"🔍 Searching production eBay for: '{search_keyword}'")
                
                # Build search parameters
                params = {
                    'q': search_keyword,
                    'limit': min(limit, 200),  # eBay API max limit
                    'sort': sort,
                    'filter': []
                }
                
                # Add category filter if specified
                if category and subcategory:
                    category_id = self.category_ids.get(category, {}).get(subcategory)
                    if category_id:
                        params['filter'].append(f'categoryIds:{category_id}')
                
                # Add filters for better arbitrage results
                params['filter'].extend([
                    'buyingOptions:{FIXED_PRICE}',  # Buy It Now only
                    'itemLocationCountry:US',       # US sellers only
                    'deliveryCountry:US',           # Ships to US
                    'conditions:{NEW,LIKE_NEW,VERY_GOOD,GOOD}',  # Good condition items
                    'maxPrice:5000',                # Reasonable price cap
                    'minPrice:1'                    # Minimum price filter
                ])
                
                # Convert filter array to string
                if params['filter']:
                    params['filter'] = '|'.join(params['filter'])
                else:
                    del params['filter']
                
                # Rate limiting
                self._rate_limit()
                
                # Make production API request
                url = f"{self.browse_endpoint}/item_summary/search"
                response = requests.get(url, headers=headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('itemSummaries', [])
                    
                    logger.info(f"✅ Found {len(items)} items for '{search_keyword}'")
                    
                    # Parse each item
                    for item in items:
                        try:
                            parsed_item = self._parse_item(item, search_keyword)
                            if parsed_item and parsed_item.price > 0:
                                all_listings.append(parsed_item)
                        except Exception as e:
                            logger.warning(f"⚠️ Error parsing item: {e}")
                            continue
                
                elif response.status_code == 429:
                    logger.warning("⚠️ Rate limited by eBay API, waiting...")
                    time.sleep(5)
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
                
                # Small delay between keyword variations
                time.sleep(0.5)
            
            # Remove duplicates and sort
            unique_listings = self._deduplicate_listings(all_listings)
            
            if sort == "price":
                unique_listings.sort(key=lambda x: x.total_cost)
            elif sort == "newest":
                unique_listings.sort(key=lambda x: x.item_creation_date, reverse=True)
            
            logger.info(f"🎯 Production search completed: {len(unique_listings)} unique listings")
            return unique_listings[:limit]
            
        except Exception as e:
            logger.error(f"❌ Production eBay search failed: {e}")
            return []
    
    def _parse_item(self, item: Dict, search_keyword: str) -> Optional[eBayListing]:
        """Parse eBay API item response into eBayListing object"""
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
            condition_id = condition_info.get('conditionId', 'UNKNOWN')
            
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
            fast_n_free = bool(item.get('qualifiedPrograms', {}).get('fastNFree', False))
            buying_options = item.get('buyingOptions', [])
            creation_date = item.get('itemCreationDate', '')
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence(item, seller_feedback, search_keyword)
            
            # Calculate arbitrage potential
            arbitrage_potential = self._calculate_arbitrage_potential(price, condition, seller_feedback)
            
            return eBayListing(
                item_id=item_id,
                title=title,
                price=price,
                currency=currency,
                shipping_cost=shipping_cost,
                total_cost=total_cost,
                condition=condition,
                condition_id=condition_id,
                category_path=category_path,
                seller_username=seller_username,
                seller_feedback_percentage=seller_feedback,
                seller_feedback_score=seller_score,
                image_url=image_url,
                ebay_link=ebay_link,
                location=location,
                returns_accepted=returns_accepted,
                top_rated_listing=top_rated,
                fast_n_free=fast_n_free,
                buying_options=buying_options,
                item_creation_date=creation_date,
                confidence_score=confidence_score,
                arbitrage_potential=arbitrage_potential
            )
            
        except Exception as e:
            logger.error(f"❌ Error parsing item: {e}")
            return None
    
    def _calculate_confidence(self, item: Dict, seller_feedback: float, search_keyword: str) -> int:
        """Calculate confidence score for arbitrage potential"""
        confidence = 50  # Base score
        
        # Seller reputation
        if seller_feedback >= 99:
            confidence += 20
        elif seller_feedback >= 95:
            confidence += 15
        elif seller_feedback >= 90:
            confidence += 10
        
        # Top rated seller bonus
        if item.get('topRatedListing'):
            confidence += 10
        
        # Fast n Free shipping
        if item.get('qualifiedPrograms', {}).get('fastNFree'):
            confidence += 5
        
        # Returns accepted
        if item.get('returnsAccepted'):
            confidence += 5
        
        # Title quality (longer, more descriptive titles typically better)
        title_length = len(item.get('title', ''))
        if title_length > 50:
            confidence += 10
        elif title_length > 30:
            confidence += 5
        
        # Price reasonableness
        price = float(item.get('price', {}).get('value', 0))
        if 10 <= price <= 1000:  # Sweet spot for arbitrage
            confidence += 15
        elif 5 <= price <= 2000:
            confidence += 10
        
        return min(100, max(0, confidence))
    
    def _calculate_arbitrage_potential(self, price: float, condition: str, seller_feedback: float) -> float:
        """Calculate arbitrage potential score (0-100)"""
        potential = 0
        
        # Price-based scoring
        if price < 50:
            potential += 30
        elif price < 200:
            potential += 25
        elif price < 500:
            potential += 20
        else:
            potential += 10
        
        # Condition-based scoring
        condition_lower = condition.lower()
        if 'new' in condition_lower:
            potential += 25
        elif 'like new' in condition_lower or 'excellent' in condition_lower:
            potential += 20
        elif 'very good' in condition_lower or 'good' in condition_lower:
            potential += 15
        else:
            potential += 5
        
        # Seller reputation bonus
        if seller_feedback >= 98:
            potential += 20
        elif seller_feedback >= 95:
            potential += 15
        elif seller_feedback >= 90:
            potential += 10
        
        return min(100, potential)
    
    def _deduplicate_listings(self, listings: List[eBayListing]) -> List[eBayListing]:
        """Remove duplicate listings based on item_id"""
        seen_ids = set()
        unique_listings = []
        
        for listing in listings:
            if listing.item_id not in seen_ids:
                seen_ids.add(listing.item_id)
                unique_listings.append(listing)
        
        return unique_listings
    
    def find_arbitrage_opportunities(self, listings: List[eBayListing], min_profit: float = 15.0) -> List[Dict]:
        """Find arbitrage opportunities by comparing similar listings"""
        opportunities = []
        
        if len(listings) < 2:
            return opportunities
        
        # Group similar items
        from difflib import SequenceMatcher
        
        for i, buy_listing in enumerate(listings[:-1]):
            for sell_listing in listings[i+1:]:
                
                # Calculate title similarity
                similarity = SequenceMatcher(None, 
                                           buy_listing.title.lower(), 
                                           sell_listing.title.lower()).ratio()
                
                # Must be similar enough
                if similarity < 0.6:
                    continue
                
                # Calculate potential profit
                price_diff = sell_listing.total_cost - buy_listing.total_cost
                if price_diff < min_profit:
                    continue
                
                # Calculate fees and net profit
                gross_profit = sell_listing.price - buy_listing.total_cost
                ebay_fees = sell_listing.price * 0.129  # ~12.9% eBay final value fee
                paypal_fees = sell_listing.price * 0.0349 + 0.49  # PayPal fees
                shipping_cost = 10.0 if sell_listing.shipping_cost == 0 else 0  # Estimate shipping cost
                
                total_fees = ebay_fees + paypal_fees + shipping_cost
                net_profit = gross_profit - total_fees
                
                if net_profit >= min_profit:
                    roi = (net_profit / buy_listing.total_cost) * 100 if buy_listing.total_cost > 0 else 0
                    
                    opportunity = {
                        'opportunity_id': f"PROD_{int(time.time())}_{buy_listing.item_id[-6:]}",
                        'similarity_score': round(similarity, 3),
                        'confidence_score': min(95, (buy_listing.confidence_score + sell_listing.confidence_score) // 2),
                        'risk_level': 'LOW' if roi < 50 else 'MEDIUM' if roi < 100 else 'HIGH',
                        'gross_profit': round(gross_profit, 2),
                        'net_profit_after_fees': round(net_profit, 2),
                        'roi_percentage': round(roi, 1),
                        'estimated_fees': round(total_fees, 2),
                        'buy_listing': asdict(buy_listing),
                        'sell_reference': asdict(sell_listing),
                        'created_at': datetime.now().isoformat()
                    }
                    
                    opportunities.append(opportunity)
        
        # Sort by profitability
        opportunities.sort(key=lambda x: x['net_profit_after_fees'], reverse=True)
        return opportunities[:15]  # Return top 15 opportunities

# Initialize the production API client
production_api = ProductioneBayAPI()

def search_production_ebay(keyword: str, category: str = None, subcategory: str = None, 
                          limit: int = 50, sort: str = "price") -> List[Dict]:
    """
    Main function to search production eBay for arbitrage opportunities
    
    Args:
        keyword: Search terms
        category: Main category (e.g., 'Tech', 'Gaming')
        subcategory: Subcategory (e.g., 'Headphones', 'Consoles')
        limit: Maximum number of results
        sort: Sort order ('price', 'newest', 'ending')
        
    Returns:
        List of eBay listings as dictionaries
    """
    try:
        logger.info(f"🚀 Starting production eBay search for: '{keyword}'")
        
        # Search using production API
        listings = production_api.search_items(
            keyword=keyword,
            category=category,
            subcategory=subcategory,
            limit=limit,
            sort=sort
        )
        
        # Convert to dictionaries for JSON serialization
        listings_dicts = [asdict(listing) for listing in listings]
        
        logger.info(f"✅ Production search completed: {len(listings_dicts)} listings found")
        return listings_dicts
        
    except Exception as e:
        logger.error(f"❌ Production eBay search failed: {e}")
        return []

def find_production_arbitrage(keyword: str, category: str = None, subcategory: str = None, 
                             min_profit: float = 15.0, limit: int = 50) -> Dict:
    """
    Find arbitrage opportunities using production eBay data
    
    Args:
        keyword: Search terms
        category: Main category
        subcategory: Subcategory
        min_profit: Minimum profit threshold
        limit: Maximum listings to analyze
        
    Returns:
        Dictionary with listings and arbitrage opportunities
    """
    try:
        logger.info(f"🎯 Finding arbitrage opportunities for: '{keyword}'")
        
        # Get production listings
        listings = production_api.search_items(
            keyword=keyword,
            category=category,
            subcategory=subcategory,
            limit=limit,
            sort="price"
        )
        
        # Find arbitrage opportunities
        opportunities = production_api.find_arbitrage_opportunities(listings, min_profit)
        
        # Calculate summary statistics
        total_opportunities = len(opportunities)
        avg_profit = sum(opp['net_profit_after_fees'] for opp in opportunities) / max(total_opportunities, 1)
        highest_profit = max([opp['net_profit_after_fees'] for opp in opportunities], default=0)
        avg_roi = sum(opp['roi_percentage'] for opp in opportunities) / max(total_opportunities, 1)
        
        result = {
            'listings': [asdict(listing) for listing in listings],
            'arbitrage_opportunities': opportunities,
            'summary': {
                'total_listings': len(listings),
                'total_opportunities': total_opportunities,
                'average_profit': round(avg_profit, 2),
                'highest_profit': round(highest_profit, 2),
                'average_roi': round(avg_roi, 1)
            },
            'search_metadata': {
                'keyword': keyword,
                'category': category,
                'subcategory': subcategory,
                'timestamp': datetime.now().isoformat(),
                'api_source': 'eBay Production API'
            }
        }
        
        logger.info(f"✅ Arbitrage analysis completed: {total_opportunities} opportunities found")
        return result
        
    except Exception as e:
        logger.error(f"❌ Arbitrage analysis failed: {e}")
        return {
            'listings': [],
            'arbitrage_opportunities': [],
            'summary': {'total_listings': 0, 'total_opportunities': 0},
            'search_metadata': {'error': str(e)}
        }

# Export main functions
__all__ = [
    'ProductioneBayAPI',
    'search_production_ebay',
    'find_production_arbitrage',
    'eBayListing'
]
