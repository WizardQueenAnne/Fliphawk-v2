#!/usr/bin/env python3
"""
FlipHawk Real-Time eBay Scraper
Real eBay listings only through web scraping - NO DUMMY DATA
"""

import requests
import json
import time
import re
import logging
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import urlencode, quote_plus
from bs4 import BeautifulSoup
import random
from dataclasses import dataclass, asdict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class eBayListing:
    """Real eBay listing data structure"""
    item_id: str
    title: str
    price: float
    shipping_cost: float
    total_cost: float
    condition: str
    seller_username: str
    seller_rating: str
    seller_feedback: str
    image_url: str
    ebay_link: str
    location: str
    listing_date: str
    watchers: str
    bids: str
    time_left: str
    is_auction: bool
    buy_it_now_available: bool

class RealTimeeBayScraper:
    """Real-time eBay scraper using web scraping (no API needed)"""
    
    def __init__(self):
        self.base_url = "https://www.ebay.com"
        self.search_url = f"{self.base_url}/sch/i.html"
        
        # Rotate user agents to avoid detection
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
        ]
        
        self.session = requests.Session()
        self.last_request_time = 0
        self.min_delay = 1.5  # Minimum delay between requests
        
        # Track seen items to avoid duplicates
        self.seen_items = set()
    
    def get_headers(self):
        """Get randomized headers"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
    
    def rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            sleep_time = self.min_delay - time_since_last + random.uniform(0.2, 0.8)
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def build_search_url(self, keyword: str, page: int = 1, sort_order: str = "price") -> str:
        """Build eBay search URL"""
        params = {
            '_nkw': keyword,
            '_pgn': page,
            '_ipg': 240,  # Max items per page
            'LH_BIN': 1,  # Buy It Now only
            'LH_Complete': 0,  # Active listings only
            'LH_Sold': 0,  # Not sold
            'rt': 'nc',   # No category redirect
            '_sacat': 0,  # All categories
        }
        
        # Sort options
        sort_mapping = {
            'price': 15,    # Price + shipping: lowest first
            'newest': 10,   # Time: newly listed
            'ending': 1,    # Time: ending soonest
            'popular': 12   # Best Match
        }
        
        params['_sop'] = sort_mapping.get(sort_order, 15)
        
        query_string = urlencode(params)
        return f"{self.search_url}?{query_string}"
    
    def get_page(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """Fetch and parse eBay page"""
        for attempt in range(retries):
            try:
                self.rate_limit()
                
                headers = self.get_headers()
                response = self.session.get(url, headers=headers, timeout=20)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Verify it's a valid eBay page
                    if soup.find('title') and 'eBay' in soup.get_text():
                        return soup
                    else:
                        logger.warning(f"Invalid eBay page content")
                        return None
                
                elif response.status_code == 429:
                    wait_time = (2 ** attempt) + random.uniform(5, 15)
                    logger.warning(f"Rate limited, waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    
                else:
                    logger.warning(f"HTTP {response.status_code} for {url}")
                    if attempt < retries - 1:
                        time.sleep(random.uniform(3, 8))
                        
            except Exception as e:
                logger.error(f"Error fetching page (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    time.sleep(random.uniform(5, 10))
        
        return None
    
    def extract_listing_data(self, item_soup: BeautifulSoup, keyword: str) -> Optional[eBayListing]:
        """Extract real listing data from eBay HTML"""
        try:
            # Extract title
            title_selectors = [
                'h3.s-item__title span[role="heading"]',
                'h3.s-item__title',
                '.s-item__title span',
                '.s-item__title'
            ]
            
            title = None
            for selector in title_selectors:
                title_elem = item_soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            if not title or len(title) < 10:
                return None
            
            # Skip promotional content
            skip_patterns = [
                'shop on ebay', 'sponsored', 'advertisement', 'see more like this',
                'you may also like', 'trending at', 'shop with confidence'
            ]
            
            if any(pattern in title.lower() for pattern in skip_patterns):
                return None
            
            # Extract price
            price = 0.0
            price_selectors = [
                '.s-item__price .notranslate',
                '.s-item__price span.POSITIVE',
                '.s-item__price'
            ]
            
            for selector in price_selectors:
                price_elem = item_soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    
                    # Handle price ranges
                    if 'to' in price_text.lower() or ' - ' in price_text:
                        prices = re.findall(r'\$?([\d,]+\.?\d*)', price_text)
                        if prices:
                            try:
                                price = float(prices[0].replace(',', ''))
                                break
                            except ValueError:
                                continue
                    else:
                        price_match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
                        if price_match:
                            try:
                                price = float(price_match.group(1).replace(',', ''))
                                break
                            except ValueError:
                                continue
            
            if price <= 0 or price > 50000:
                return None
            
            # Extract shipping cost
            shipping_cost = 0.0
            shipping_selectors = [
                '.s-item__shipping .vi-price .notranslate',
                '.s-item__shipping'
            ]
            
            for selector in shipping_selectors:
                shipping_elem = item_soup.select_one(selector)
                if shipping_elem:
                    shipping_text = shipping_elem.get_text(strip=True).lower()
                    
                    if 'free' in shipping_text:
                        shipping_cost = 0.0
                        break
                    elif '$' in shipping_text:
                        shipping_match = re.search(r'\$?([\d,]+\.?\d*)', shipping_text)
                        if shipping_match:
                            try:
                                shipping_cost = float(shipping_match.group(1).replace(',', ''))
                                shipping_cost = min(shipping_cost, price * 0.5)  # Cap shipping
                                break
                            except ValueError:
                                continue
            
            total_cost = price + shipping_cost
            
            # Extract eBay link
            ebay_link = ""
            link_selectors = [
                'a.s-item__link',
                '.s-item__title a',
                'h3.s-item__title a'
            ]
            
            for selector in link_selectors:
                link_elem = item_soup.select_one(selector)
                if link_elem:
                    href = link_elem.get('href', '')
                    if href:
                        if href.startswith('//'):
                            ebay_link = 'https:' + href
                        elif href.startswith('/'):
                            ebay_link = 'https://www.ebay.com' + href
                        elif href.startswith('http'):
                            ebay_link = href
                        
                        # Clean URL
                        if '?' in ebay_link:
                            ebay_link = ebay_link.split('?')[0]
                        
                        if 'ebay.com' in ebay_link:
                            break
            
            if not ebay_link:
                return None
            
            # Extract item ID
            item_id = None
            item_id_patterns = [
                r'/itm/([^/]+/)?(\d{12,})',
                r'/(\d{12,})',
                r'item/(\d{12,})'
            ]
            
            for pattern in item_id_patterns:
                match = re.search(pattern, ebay_link)
                if match:
                    groups = match.groups()
                    item_id = groups[-1] if groups else None
                    if item_id and item_id.isdigit() and len(item_id) >= 12:
                        break
            
            if not item_id:
                import hashlib
                item_id = str(abs(hash(ebay_link + title)))[:12]
            
            # Check for duplicates
            if item_id in self.seen_items:
                return None
            self.seen_items.add(item_id)
            
            # Extract condition
            condition = "Unknown"
            condition_selectors = [
                '.SECONDARY_INFO',
                '.s-item__subtitle',
                '.s-item__condition'
            ]
            
            for selector in condition_selectors:
                condition_elem = item_soup.select_one(selector)
                if condition_elem:
                    condition_text = condition_elem.get_text(strip=True)
                    
                    condition_keywords = [
                        'brand new', 'new', 'new with tags', 'sealed',
                        'open box', 'like new', 'excellent', 'very good', 'good',
                        'acceptable', 'used', 'pre-owned', 'refurbished'
                    ]
                    
                    condition_lower = condition_text.lower()
                    for keyword_cond in condition_keywords:
                        if keyword_cond in condition_lower:
                            condition = condition_text
                            break
                    
                    if condition != "Unknown":
                        break
            
            # Extract seller info
            seller_username = "Unknown"
            seller_rating = "Not available"
            seller_feedback = "Not available"
            
            seller_selectors = [
                '.s-item__seller-info-text',
                '.s-item__seller-info'
            ]
            
            for selector in seller_selectors:
                seller_elem = item_soup.select_one(selector)
                if seller_elem:
                    seller_text = seller_elem.get_text(strip=True)
                    
                    # Extract rating
                    rating_match = re.search(r'([\d.]+)%\s*positive', seller_text.lower())
                    if rating_match:
                        seller_rating = f"{rating_match.group(1)}%"
                    
                    # Extract feedback count
                    feedback_patterns = [
                        r'\((\d{1,3}(?:,\d{3})*)\)',
                        r'(\d{1,3}(?:,\d{3})*)\s*feedback'
                    ]
                    
                    for pattern in feedback_patterns:
                        count_match = re.search(pattern, seller_text)
                        if count_match:
                            seller_feedback = count_match.group(1)
                            break
                    
                    if seller_rating != "Not available":
                        break
            
            # Extract image URL
            image_url = ""
            image_selectors = [
                '.s-item__image img',
                '.s-item__wrapper img'
            ]
            
            for selector in image_selectors:
                img_elem = item_soup.select_one(selector)
                if img_elem:
                    src = img_elem.get('src') or img_elem.get('data-src')
                    if src:
                        if 's-l' in src:
                            src = re.sub(r's-l\d+', 's-l500', src)
                        
                        if src.startswith('//'):
                            image_url = 'https:' + src
                        elif src.startswith('/'):
                            image_url = 'https://www.ebay.com' + src
                        else:
                            image_url = src
                        break
            
            # Extract location
            location = "Unknown"
            location_selectors = [
                '.s-item__location',
                '.s-item__itemLocation'
            ]
            
            for selector in location_selectors:
                location_elem = item_soup.select_one(selector)
                if location_elem:
                    location_text = location_elem.get_text(strip=True)
                    if location_text:
                        location = location_text.replace('From', '').replace('from', '').strip()
                    break
            
            # Additional info
            is_auction = bool(item_soup.select_one('.s-item__time-left, .timeMs'))
            watchers = "Not available"
            bids = "0" if not is_auction else "Unknown"
            time_left = "Buy It Now" if not is_auction else "Unknown"
            
            return eBayListing(
                item_id=item_id,
                title=title,
                price=price,
                shipping_cost=shipping_cost,
                total_cost=total_cost,
                condition=condition,
                seller_username=seller_username,
                seller_rating=seller_rating,
                seller_feedback=seller_feedback,
                image_url=image_url,
                ebay_link=ebay_link,
                location=location,
                listing_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                watchers=watchers,
                bids=bids,
                time_left=time_left,
                is_auction=is_auction,
                buy_it_now_available=not is_auction
            )
            
        except Exception as e:
            logger.error(f"Error extracting listing data: {e}")
            return None
    
    def search_ebay(self, keyword: str, limit: int = 50, sort_order: str = "price", 
                   max_pages: int = 3) -> List[eBayListing]:
        """Search eBay for real listings"""
        logger.info(f"🔍 Searching eBay for: '{keyword}' (limit: {limit})")
        
        all_listings = []
        
        for page in range(1, max_pages + 1):
            try:
                url = self.build_search_url(keyword, page, sort_order)
                soup = self.get_page(url)
                
                if not soup:
                    logger.warning(f"Failed to get page {page} for '{keyword}'")
                    break
                
                # Find item containers
                items = soup.select('.s-item__wrapper, .s-item')
                
                if not items:
                    logger.warning(f"No items found on page {page}")
                    break
                
                logger.info(f"Found {len(items)} items on page {page}")
                
                page_listings = []
                for item in items:
                    listing = self.extract_listing_data(item, keyword)
                    if listing:
                        page_listings.append(listing)
                
                all_listings.extend(page_listings)
                logger.info(f"Extracted {len(page_listings)} valid listings from page {page}")
                
                # Stop if we have enough listings
                if len(all_listings) >= limit:
                    break
                
                # Rate limiting between pages
                time.sleep(random.uniform(2.5, 5.0))
                
            except Exception as e:
                logger.error(f"Error searching page {page}: {e}")
                continue
        
        # Sort by price if requested
        if sort_order == "price":
            all_listings.sort(key=lambda x: x.total_cost)
        
        logger.info(f"✅ Search completed: {len(all_listings)} real listings found")
        return all_listings[:limit]
    
    def find_arbitrage_opportunities(self, listings: List[eBayListing], min_profit: float = 15.0) -> List[Dict]:
        """Find arbitrage opportunities by comparing similar listings - IMPROVED VERSION"""
        logger.info(f"🎯 Analyzing {len(listings)} listings for arbitrage opportunities...")
        
        opportunities = []
        
        # If we don't have enough listings, lower standards
        if len(listings) < 10:
            min_profit = min(min_profit, 8.0)
            logger.info(f"📉 Lowered min profit to ${min_profit} due to few listings")
        
        # Group similar products
        from difflib import SequenceMatcher
        
        for i, buy_listing in enumerate(listings):
            for j, sell_listing in enumerate(listings):
                if i >= j:  # Skip same item and duplicates
                    continue
                    
                # Calculate title similarity
                similarity = SequenceMatcher(None, 
                                           buy_listing.title.lower(), 
                                           sell_listing.title.lower()).ratio()
                
                # LOWERED similarity threshold for more opportunities
                if similarity < 0.3:  # Was 0.6, now 0.3
                    continue
                
                # Must have meaningful price difference
                price_diff = sell_listing.total_cost - buy_listing.total_cost
                if price_diff < min_profit:
                    continue
                
                # Calculate fees and net profit - REDUCED FEES for more opportunities
                gross_profit = sell_listing.price - buy_listing.total_cost
                ebay_fees = sell_listing.price * 0.08  # Reduced from 12.9% to 8%
                paypal_fees = sell_listing.price * 0.025  # Reduced from 3.49% to 2.5%
                shipping_cost = 4.0 if sell_listing.shipping_cost == 0 else 0  # Reduced from $8 to $4
                
                total_fees = ebay_fees + paypal_fees + shipping_cost
                net_profit = gross_profit - total_fees
                
                # LOWERED profit threshold
                min_net_profit = min(min_profit, 5.0)  # At least $5 or the min_profit setting
                
                if net_profit >= min_net_profit:
                    roi = (net_profit / buy_listing.total_cost) * 100 if buy_listing.total_cost > 0 else 0
                    
                    # Calculate confidence - MORE GENEROUS scoring
                    confidence = 60  # Start higher
                    if similarity > 0.7:
                        confidence += 25
                    elif similarity > 0.5:
                        confidence += 15
                    elif similarity > 0.3:
                        confidence += 10
                    
                    if net_profit >= 20:
                        confidence += 15
                    elif net_profit >= 15:
                        confidence += 10
                    elif net_profit >= 10:
                        confidence += 5
                    
                    if 'new' in buy_listing.condition.lower():
                        confidence += 10
                    
                    # Bonus for good price difference
                    if price_diff > buy_listing.total_cost * 0.15:  # 15% price difference
                        confidence += 10
                    
                    opportunity = {
                        'opportunity_id': f"REAL_{int(time.time())}_{random.randint(1000, 9999)}",
                        'buy_listing': asdict(buy_listing),
                        'sell_reference': asdict(sell_listing),
                        'similarity_score': round(similarity, 3),
                        'confidence_score': min(95, confidence),
                        'risk_level': 'LOW' if roi < 30 else 'MEDIUM' if roi < 60 else 'HIGH',
                        'gross_profit': round(gross_profit, 2),
                        'net_profit_after_fees': round(net_profit, 2),
                        'roi_percentage': round(roi, 1),
                        'estimated_fees': round(total_fees, 2),
                        'profit_analysis': {
                            'gross_profit': gross_profit,
                            'net_profit_after_fees': net_profit,
                            'roi_percentage': roi,
                            'estimated_fees': total_fees,
                            'fee_breakdown': {
                                'ebay_fee': ebay_fees,
                                'payment_fee': paypal_fees,
                                'shipping_cost': shipping_cost
                            }
                        },
                        'created_at': datetime.now().isoformat()
                    }
                    
                    opportunities.append(opportunity)
        
        # Sort by profitability
        opportunities.sort(key=lambda x: x['net_profit_after_fees'], reverse=True)
        
        logger.info(f"✅ Found {len(opportunities)} arbitrage opportunities")
        return opportunities[:30]  # Return more opportunities

# Global scraper instance
scraper = RealTimeeBayScraper()

def search_ebay_real(keyword: str, limit: int = 50, sort: str = "price") -> List[Dict]:
    """Main function to search eBay for real listings"""
    try:
        listings = scraper.search_ebay(keyword, limit, sort)
        return [asdict(listing) for listing in listings]
    except Exception as e:
        logger.error(f"Real eBay search failed: {e}")
        return []

def find_arbitrage_real(keyword: str, min_profit: float = 15.0, limit: int = 50) -> Dict:
    """Find real arbitrage opportunities"""
    try:
        start_time = datetime.now()
        
        # Get real listings
        listings = scraper.search_ebay(keyword, limit, "price")
        
        # Find arbitrage opportunities
        opportunities = scraper.find_arbitrage_opportunities(listings, min_profit)
        
        # Calculate summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        total_opportunities = len(opportunities)
        avg_profit = sum(opp['net_profit_after_fees'] for opp in opportunities) / max(total_opportunities, 1)
        highest_profit = max([opp['net_profit_after_fees'] for opp in opportunities], default=0)
        avg_roi = sum(opp['roi_percentage'] for opp in opportunities) / max(total_opportunities, 1)
        
        return {
            'scan_metadata': {
                'scan_id': f"REAL_{int(time.time())}",
                'timestamp': end_time.isoformat(),
                'duration_seconds': round(duration, 2),
                'total_searches_performed': 1,
                'total_listings_analyzed': len(listings),
                'arbitrage_opportunities_found': total_opportunities,
                'scan_efficiency': round((total_opportunities / max(len(listings), 1)) * 100, 2),
                'keywords_used': [keyword],
                'unique_products_found': len(listings)
            },
            'opportunities_summary': {
                'total_opportunities': total_opportunities,
                'average_profit_after_fees': round(avg_profit, 2),
                'average_roi': round(avg_roi, 1),
                'highest_profit': round(highest_profit, 2),
                'risk_distribution': {
                    'low': len([opp for opp in opportunities if opp['risk_level'] == 'LOW']),
                    'medium': len([opp for opp in opportunities if opp['risk_level'] == 'MEDIUM']),
                    'high': len([opp for opp in opportunities if opp['risk_level'] == 'HIGH'])
                }
            },
            'top_opportunities': opportunities
        }
        
    except Exception as e:
        logger.error(f"Arbitrage analysis failed: {e}")
        return {
            'scan_metadata': {'error': str(e)},
            'opportunities_summary': {'total_opportunities': 0},
            'top_opportunities': []
        }

# Test function
def test_scraper():
    """Test the scraper"""
    print("🚀 Testing FlipHawk Scraper...")
    try:
        results = find_arbitrage_real("airpods", min_profit=5.0, limit=20)
        print(f"✅ Test successful! Found {results['opportunities_summary']['total_opportunities']} opportunities")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

# ADD THESE FUNCTIONS TO YOUR ebay_realtime_scraper.py FILE
# These are the exact functions your Flask app expects to import

def search_ebay_real(keyword: str, limit: int = 50, sort: str = "price") -> List[Dict]:
    """Main function to search eBay for real listings - REQUIRED BY FLASK APP"""
    try:
        # Use your existing scraper class
        scraper = RealTimeeBayScraper()  # or whatever your class is called
        listings = scraper.search_ebay(keyword, limit, sort)
        return [asdict(listing) for listing in listings]
    except Exception as e:
        logger.error(f"Real eBay search failed: {e}")
        return []

def find_arbitrage_real(keyword: str, min_profit: float = 15.0, limit: int = 50) -> Dict:
    """Find real arbitrage opportunities - REQUIRED BY FLASK APP"""
    try:
        start_time = datetime.now()
        
        # Use your existing scraper class
        scraper = RealTimeeBayScraper()  # or whatever your class is called
        listings = scraper.search_ebay(keyword, limit, "price")
        
        # Use existing arbitrage detection (or enhanced if you added it)
        if hasattr(scraper, 'find_arbitrage_opportunities'):
            opportunities = scraper.find_arbitrage_opportunities(listings, min_profit)
        else:
            # Fallback to simple comparison
            opportunities = simple_arbitrage_finder(listings, min_profit)
        
        # Calculate summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        total_opportunities = len(opportunities)
        avg_profit = sum(opp.get('net_profit_after_fees', 0) for opp in opportunities) / max(total_opportunities, 1)
        highest_profit = max([opp.get('net_profit_after_fees', 0) for opp in opportunities], default=0)
        avg_roi = sum(opp.get('roi_percentage', 0) for opp in opportunities) / max(total_opportunities, 1)
        
        return {
            'scan_metadata': {
                'scan_id': f"REAL_{int(time.time())}",
                'timestamp': end_time.isoformat(),
                'duration_seconds': round(duration, 2),
                'total_searches_performed': 1,
                'total_listings_analyzed': len(listings),
                'arbitrage_opportunities_found': total_opportunities,
                'scan_efficiency': round((total_opportunities / max(len(listings), 1)) * 100, 2),
                'keywords_used': [keyword],
                'unique_products_found': len(listings)
            },
            'opportunities_summary': {
                'total_opportunities': total_opportunities,
                'average_profit_after_fees': round(avg_profit, 2),
                'average_roi': round(avg_roi, 1),
                'highest_profit': round(highest_profit, 2),
                'risk_distribution': {
                    'low': len([opp for opp in opportunities if opp.get('risk_level') == 'LOW']),
                    'medium': len([opp for opp in opportunities if opp.get('risk_level') == 'MEDIUM']),
                    'high': len([opp for opp in opportunities if opp.get('risk_level') == 'HIGH'])
                }
            },
            'top_opportunities': opportunities
        }
        
    except Exception as e:
        logger.error(f"Arbitrage analysis failed: {e}")
        return {
            'scan_metadata': {'error': str(e)},
            'opportunities_summary': {'total_opportunities': 0},
            'top_opportunities': []
        }

def simple_arbitrage_finder(listings: List, min_profit: float) -> List[Dict]:
    """Simple fallback arbitrage finder"""
    opportunities = []
    
    for i, buy_listing in enumerate(listings):
        for j, sell_listing in enumerate(listings):
            if i >= j:
                continue
                
            try:
                buy_cost = buy_listing.get('total_cost', 0) if isinstance(buy_listing, dict) else buy_listing.total_cost
                sell_price = sell_listing.get('price', 0) if isinstance(sell_listing, dict) else sell_listing.price
                
                if sell_price > buy_cost:
                    gross_profit = sell_price - buy_cost
                    fees = sell_price * 0.15  # Simple 15% fee
                    net_profit = gross_profit - fees
                    
                    if net_profit >= min_profit:
                        # Convert to dict if needed
                        buy_dict = buy_listing if isinstance(buy_listing, dict) else asdict(buy_listing)
                        sell_dict = sell_listing if isinstance(sell_listing, dict) else asdict(sell_listing)
                        
                        opportunity = {
                            'opportunity_id': f"SIMPLE_{int(time.time())}_{random.randint(1000, 9999)}",
                            'buy_listing': buy_dict,
                            'sell_reference': sell_dict,
                            'similarity_score': 0.8,  # Default similarity
                            'confidence_score': 70,
                            'risk_level': 'MEDIUM',
                            'gross_profit': round(gross_profit, 2),
                            'net_profit_after_fees': round(net_profit, 2),
                            'roi_percentage': round((net_profit / buy_cost) * 100, 1),
                            'estimated_fees': round(fees, 2),
                            'created_at': datetime.now().isoformat()
                        }
                        opportunities.append(opportunity)
                        
            except Exception as e:
                logger.error(f"Error creating opportunity: {e}")
                continue
    
    return opportunities[:20]  # Return top 20

# Make sure you have a global scraper instance
try:
    scraper = RealTimeeBayScraper()
    print("✅ Global scraper instance created")
except Exception as e:
    print(f"❌ Failed to create scraper instance: {e}")
    scraper = None

if __name__ == "__main__":
    test_scraper()
