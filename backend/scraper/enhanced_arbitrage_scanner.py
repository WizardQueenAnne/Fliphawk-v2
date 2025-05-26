def calculate_arbitrage_confidence(self, buy_listing: eBayListing, sell_listing: eBayListing,
                                     similarity_score: float, profit_analysis: Dict, risk_assessment: Dict) -> int:
        """Calculate overall confidence in arbitrage opportunity with more generous scoring"""
        confidence = 40  # Increased base confidence
        
        # Similarity bonus (more generous)
        if similarity_score >= 0.8:
            confidence += 25
        elif similarity_score >= 0.6:
            confidence += 20
        elif similarity_score >= 0.5:
            confidence += 15
        elif similarity_score >= 0.4:
            confidence += 10
        elif similarity_score >= 0.35:
            confidence += 5
        
        # Profit bonus (more accessible)
        net_profit = profit_analysis['net_profit_after_fees']
        if net_profit >= 100:
            confidence += 25
        elif net_profit >= 50:
            confidence += 20
        elif net_profit >= 30:
            confidence += 15
        elif net_profit >= 20:
            confidence += 12
        elif net_profit >= 15:
            confidence += 10
        elif net_profit >= 10:
            confidence += 8
        elif net_profit >= 8:
            confidence += 5
        
        # ROI bonus (but penalize if too high)
        roi = profit_analysis['roi_percentage']
        if 20 <= roi <= 60:        # Sweet spot
            confidence += 15
        elif 10 <= roi <= 80:      # Good range
            confidence += 10
        elif 5 <= roi <= 100:      # Acceptable range
            confidence += 5
        elif roi > 200:            # Too high is suspicious
            confidence -= 15
        elif roi > 150:
            confidence -= 10
        
        # Reduced risk penalty
        confidence -= risk_assessment['score'] // 8  # Reduced from //5
        
        # Seller quality bonus (more forgiving)
        try:
            buy_rating = float(re.search(r'([\d.]+)', buy_listing.seller_rating).group(1))
            if buy_rating >= 98:
                confidence += 15
            elif buy_rating >= 95:
                confidence += 10
            elif buy_rating >= 90:
                confidence += 5
            # No penalty for ratings above 85
        except:
            confidence -= 5  # Reduced penalty
        
        # Title similarity bonus
        title_sim = difflib.SequenceMatcher(
            None, buy_listing.title.lower(), sell_listing.title.lower()
        ).ratio()
        
        if title_sim >= 0.7:
            confidence += 10
        elif title_sim >= 0.5:
            confidence += 5
        
        # Price difference reasonableness bonus
        price_diff = sell_listing.price - buy_listing.price
        if 10 <= price_diff <= 100:  # Reasonable price differences
            confidence += 10
        elif 5 <= price_diff <= 200:
            confidence += 5
        
        # Condition compatibility bonus
        buy_cond = buy_listing.condition.lower()
        sell_cond = sell_listing.condition.lower()
        
        if buy_cond == sell_cond:
            confidence += 10
        elif any(word in buy_cond for word in ['new', 'sealed']) and any(word in sell_cond for word in ['new', 'mint']):
            confidence += 8
        elif any(word in buy_cond for word in ['good', 'very good']) and any(word in sell_cond for word in ['good', 'excellent']):
            confidence += 6
        
        return max(0, min(100, confidence))
    
    def scan_with_keyword_variations(self, base_keyword: str, category: str, 
                                   subcategory: str = None, max_pages: int = 2, 
                                   min_profit: float = 15.0) -> List[eBayListing]:
        """Scan eBay using keyword variations for comprehensive coverage"""
        logger.info(f"🔍 Scanning with keyword: '{base_keyword}' in {category}/{subcategory}")
        
        # Generate keyword variations (but limit them)
        keyword_variations = self.keyword_generator.generate_keyword_variations(base_keyword)
        trending_keywords = self.keyword_generator.generate_trending_keywords([base_keyword])
        
        # Combine and prioritize keywords (reduced to prevent over-scanning)
        all_keywords = [base_keyword] + keyword_variations[:3] + trending_keywords[:2]
        
        all_listings = []
        self.session_stats['categories_searched'].add(f"{category}/{subcategory or 'All'}")
        
        for keyword_index, keyword in enumerate(all_keywords[:6]):  # Further limited
            try:
                for page in range(1, max_pages + 1):
                    try:
                        url = self.build_search_url(keyword, page)
                        soup = self.fetch_page_with_retry(url)
                        
                        if not soup:
                            logger.warning(f"Failed to fetch page {page} for keyword '{keyword}'")
                            break
                        
                        # Item container selectors
                        item_selectors = [
                            '.s-item__wrapper',
                            '.s-item',
                            '.srp-results .s-item'
                        ]
                        
                        items = []
                        for selector in item_selectors:
                            items = soup.select(selector)
                            if items:
                                break
                        
                        if not items:
                            logger.warning(f"No items found on page {page} for keyword '{keyword}'")
                            break
                        
                        self.session_stats['total_searches'] += 1
                        self.session_stats['total_listings_found'] += len(items)
                        
                        page_listings = 0
                        for item in items:
                            listing = self.extract_listing_data(
                                item, category, subcategory or 'General', keyword
                            )
                            
                            # More lenient profit requirement during collection
                            if listing and listing.estimated_profit >= (min_profit * 0.5):  # 50% of target
                                all_listings.append(listing)
                                page_listings += 1
                                self.session_stats['profitable_listings'] += 1
                        
                        logger.info(f"Page {page} for '{keyword}': {page_listings} listings found")
                        
                        # Smart rate limiting (reduced delays)
                        delay = random.uniform(1.0, 2.0) + (keyword_index * 0.2)
                        time.sleep(delay)
                        
                    except Exception as e:
                        logger.error(f"Error scanning page {page} for keyword '{keyword}': {e}")
                        continue
                
                # Reduced delay between keywords
                keyword_delay = random.uniform(0.5, 1.5) + (keyword_index * 0.1)
                time.sleep(keyword_delay)
                
            except Exception as e:
                logger.error(f"Error processing keyword '{keyword}': {e}")
                continue
        
        logger.info(f"Completed scan for '{base_keyword}': {len(all_listings)} total listings found")
        return all_listings"""
FlipHawk Enhanced eBay Arbitrage Scanner - Production Ready
Advanced scraper with real arbitrage detection, intelligent matching, and comprehensive error handling
"""

import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import json
import re
import time
import random
from typing import List, Dict, Optional, Set, Tuple
import hashlib
from dataclasses import dataclass, asdict
from collections import defaultdict
from datetime import datetime, timedelta
import difflib
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class eBayListing:
    """Enhanced eBay listing data structure with all required fields"""
    title: str
    price: float
    shipping_cost: float
    total_cost: float
    estimated_resale_price: float
    estimated_profit: float
    profit_margin_percent: float
    confidence_score: int
    condition: str
    seller_rating: str
    seller_feedback_count: str
    return_policy: str
    shipping_time: str
    image_url: str
    ebay_link: str
    item_id: str
    category: str
    subcategory: str
    matched_keyword: str
    listing_date: str
    views_count: str
    watchers_count: str
    is_auction: bool
    buy_it_now_price: float
    time_left: str
    location: str
    sold_count: str
    availability: str

class AdvancedKeywordGenerator:
    """Generates comprehensive keyword variations for maximum eBay coverage"""
    
    def __init__(self):
        # Common typos and misspellings database
        self.common_typos = {
            'pokemon': ['pokeman', 'pokmon', 'pokémon', 'pocket monsters', 'pkmn'],
            'nintendo': ['nintedo', 'nintndo', 'nitendo', 'ninendo'],
            'playstation': ['play station', 'playstaton', 'ps', 'playstaion'],
            'iphone': ['i phone', 'ifone', 'apple phone', 'iphome'],
            'airpods': ['air pods', 'air pod', 'aripos', 'airpds', 'apple earbuds'],
            'supreme': ['suprme', 'supremme', 'suprem'],
            'jordan': ['jordon', 'air jordan', 'aj', 'jordans'],
            'xbox': ['x box', 'xobx', 'x-box'],
            'macbook': ['mac book', 'mackbook', 'macbok'],
            'samsung': ['samung', 'samsang', 'samsug'],
            'magic': ['magik', 'majik', 'mgic'],
            'charizard': ['charizrd', 'charzard'],
            'vintage': ['vintge', 'vintag', 'vintaje'],
            'sealed': ['seled', 'seald', 'seeled']
        }
        
        # Brand variations
        self.brand_variations = {
            'apple': ['apple inc', 'aapl'],
            'nike': ['just do it', 'swoosh'],
            'adidas': ['three stripes', '3 stripes'],
            'sony': ['sonny', 'soney'],
            'samsung': ['galaxy', 'sam'],
            'bose': ['boss', 'boze'],
            'beats': ['dr dre', 'dre', 'beats by dre'],
            'supreme': ['sup', 'bogo'],
            'nintendo': ['nin', 'tendo']
        }
        
        # Condition keywords
        self.condition_keywords = [
            'new', 'sealed', 'mint', 'new with tags', 'nwt', 'bnib', 'brand new',
            'used', 'pre-owned', 'preowned', 'like new', 'excellent', 'very good',
            'good', 'fair', 'acceptable', 'refurbished', 'open box', 'certified'
        ]
        
    def generate_keyword_variations(self, base_keyword: str, max_variations: int = 20) -> List[str]:
        """Generate comprehensive keyword variations"""
        variations = set([base_keyword.lower().strip()])
        
        # Clean base keyword
        clean_keyword = re.sub(r'[^\w\s]', '', base_keyword.lower())
        variations.add(clean_keyword)
        
        # Add common typos
        for correct, typos in self.common_typos.items():
            if correct in clean_keyword:
                for typo in typos[:3]:  # Limit typos to prevent too many variations
                    variations.add(clean_keyword.replace(correct, typo))
        
        # Add brand variations
        for brand, brand_vars in self.brand_variations.items():
            if brand in clean_keyword:
                for variation in brand_vars[:2]:  # Limit brand variations
                    variations.add(clean_keyword.replace(brand, variation))
        
        # Space and punctuation variations
        variations.add(clean_keyword.replace(' ', ''))
        variations.add(clean_keyword.replace(' ', '-'))
        
        # Plural/singular forms
        if clean_keyword.endswith('s') and len(clean_keyword) > 3:
            variations.add(clean_keyword[:-1])
        elif not clean_keyword.endswith('s'):
            variations.add(clean_keyword + 's')
        
        # Remove empty strings and filter
        variations = [v for v in variations if v and len(v) > 2]
        return list(variations)[:max_variations]

    def generate_trending_keywords(self, base_keywords: List[str]) -> List[str]:
        """Generate trending keyword variations"""
        trending_prefixes = ['viral', 'trending', 'hot', 'new', 'latest', 'rare', 'limited']
        trending_suffixes = ['2024', '2025', 'edition', 'version', 'model', 'drop', 'release']
        
        trending_variations = []
        
        for keyword in base_keywords[:3]:  # Limit to prevent too many
            # Add prefixes (limited)
            for prefix in trending_prefixes[:2]:
                trending_variations.append(f"{prefix} {keyword}")
            
            # Add suffixes (limited)
            for suffix in trending_suffixes[:2]:
                trending_variations.append(f"{keyword} {suffix}")
        
        return trending_variations[:10]  # Limit total trending variations

class TrueArbitrageScanner:
    """Production-ready eBay arbitrage scanner with advanced matching"""
    
    def __init__(self):
        self.base_url = "https://www.ebay.com/sch/i.html"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        self.seen_items = set()
        self.keyword_generator = AdvancedKeywordGenerator()
        self.session_stats = {
            'total_searches': 0,
            'total_listings_found': 0,
            'profitable_listings': 0,
            'categories_searched': set(),
            'start_time': datetime.now(),
            'success_rate': 0.0
        }
        
    def build_search_url(self, keyword: str, page: int = 1, sort_order: str = "price") -> str:
        """Build eBay search URL with optimized parameters"""
        params = {
            '_nkw': keyword,
            '_pgn': page,
            'LH_BIN': 1,  # Buy It Now only
            'LH_Complete': 0,  # Active listings
            'LH_Sold': 0,  # Not sold
            '_sop': {
                'price': 15,  # Price + shipping: lowest first
                'newest': 10,  # Time: newly listed
                'ending': 1,   # Time: ending soonest
                'popular': 12  # Best Match
            }.get(sort_order, 15),
            '_ipg': 240,  # Items per page (max)
            'rt': 'nc',   # No categories redirect
            '_sacat': 0,  # All categories
            'LH_FS': 0    # Include all shipping types
        }
        
        query_string = urllib.parse.urlencode(params)
        return f"{self.base_url}?{query_string}"
    
    def fetch_page_with_retry(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """Robust page fetching with retry logic and error handling"""
        for attempt in range(retries):
            try:
                # Rotate User-Agent
                user_agents = [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
                ]
                
                headers = self.headers.copy()
                headers['User-Agent'] = random.choice(user_agents)
                
                # Add random delay
                time.sleep(random.uniform(1.0, 3.0))
                
                request = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(request, timeout=30) as response:
                    if response.getcode() == 200:
                        content = response.read()
                        
                        # Handle encoding
                        encoding = response.info().get_content_charset() or 'utf-8'
                        try:
                            html = content.decode(encoding)
                        except UnicodeDecodeError:
                            html = content.decode('utf-8', errors='ignore')
                        
                        return BeautifulSoup(html, 'html.parser')
                    else:
                        logger.warning(f"HTTP {response.getcode()} for {url}")
                        
            except urllib.error.HTTPError as e:
                logger.warning(f"HTTP Error {e.code} on attempt {attempt + 1}")
                if e.code == 429:  # Rate limited
                    wait_time = (2 ** attempt) + random.uniform(5, 15)
                    logger.info(f"Rate limited, waiting {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                elif e.code in [403, 406]:  # Blocked
                    logger.warning("Potentially blocked, using longer delay...")
                    time.sleep(random.uniform(10, 30))
                    
            except Exception as e:
                logger.warning(f"Error on attempt {attempt + 1}: {e}")
                if attempt < retries - 1:
                    time.sleep(random.uniform(2, 5))
                    
        logger.error(f"Failed to fetch {url} after {retries} attempts")
        return None
    
    def extract_listing_data(self, item_soup: BeautifulSoup, category: str, 
                           subcategory: str, matched_keyword: str) -> Optional[eBayListing]:
        """Extract comprehensive listing data with validation"""
        try:
            # Enhanced title extraction
            title_selectors = [
                'h3.s-item__title',
                '.s-item__title',
                'h3[role="heading"]',
                '.s-item__title-text'
            ]
            
            title = None
            for selector in title_selectors:
                title_elem = item_soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    title = re.sub(r'\s+', ' ', title)
                    title = title.replace('New Listing', '').strip()
                    break
            
            # Filter out non-product listings
            if not title or any(skip in title for skip in [
                'Shop on eBay', 'SPONSORED', 'See more like this', 'Advertisement'
            ]):
                return None
            
            # Enhanced price extraction
            price_selectors = [
                '.s-item__price .notranslate',
                '.s-item__price',
                '.adp-price .notranslate'
            ]
            
            price = 0.0
            for selector in price_selectors:
                price_elem = item_soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    # Handle price ranges - take lower price
                    if 'to' in price_text.lower() or '-' in price_text:
                        prices = re.findall(r'\$?([\d,]+\.?\d*)', price_text)
                        if prices:
                            price = float(prices[0].replace(',', ''))
                    else:
                        price_match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
                        if price_match:
                            price = float(price_match.group(1).replace(',', ''))
                    
                    if price > 0:
                        break
            
            # Validate price range
            if price <= 0 or price > 10000:
                return None
            
            # Enhanced shipping cost extraction
            shipping_cost = 0.0
            shipping_selectors = [
                '.s-item__shipping',
                '.s-item__logisticsCost',
                '.s-item__detail--secondary'
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
                            shipping_cost = float(shipping_match.group(1).replace(',', ''))
                            # Cap unrealistic shipping
                            shipping_cost = min(shipping_cost, price * 0.3)
                            break
            
            total_cost = price + shipping_cost
            
            # Enhanced link extraction
            link_selectors = [
                '.s-item__link',
                '.s-item__title a',
                'a.s-item__link'
            ]
            
            ebay_link = ""
            for selector in link_selectors:
                link_elem = item_soup.select_one(selector)
                if link_elem:
                    href = link_elem.get('href', '')
                    if href:
                        ebay_link = href.split('?')[0] if '?' in href else href
                        if not ebay_link.startswith('http'):
                            ebay_link = 'https://www.ebay.com' + ebay_link
                        break
            
            if not ebay_link:
                return None
            
            # Enhanced item ID extraction
            item_id_patterns = [
                r'/(\d{12,})',
                r'itm/(\d+)',
                r'item/(\d+)'
            ]
            
            item_id = None
            for pattern in item_id_patterns:
                match = re.search(pattern, ebay_link)
                if match:
                    item_id = match.group(1)
                    break
            
            if not item_id:
                item_id = str(abs(hash(title + str(price))))[:12]
            
            # Duplicate prevention
            if item_id in self.seen_items:
                return None
            self.seen_items.add(item_id)
            
            # Enhanced image extraction
            image_selectors = [
                '.s-item__image img',
                'img[src*="ebayimg"]',
                '.s-item__wrapper img'
            ]
            
            image_url = ""
            for selector in image_selectors:
                img_elem = item_soup.select_one(selector)
                if img_elem:
                    image_url = img_elem.get('src', '') or img_elem.get('data-src', '')
                    if image_url:
                        image_url = image_url.replace('s-l64', 's-l500')
                        if not image_url.startswith('http'):
                            image_url = 'https:' + image_url if image_url.startswith('//') else image_url
                        break
            
            # Enhanced condition extraction
            condition_selectors = [
                '.SECONDARY_INFO',
                '.s-item__subtitle',
                '.s-item__condition'
            ]
            
            condition = "Unknown"
            for selector in condition_selectors:
                condition_elem = item_soup.select_one(selector)
                if condition_elem:
                    condition_text = condition_elem.get_text(strip=True)
                    condition_keywords = [
                        'new', 'brand new', 'sealed', 'mint',
                        'used', 'pre-owned', 'like new', 'very good',
                        'good', 'fair', 'refurbished', 'open box'
                    ]
                    if any(word in condition_text.lower() for word in condition_keywords):
                        condition = condition_text
                        break
            
            # Enhanced seller information
            seller_selectors = [
                '.s-item__seller-info-text',
                '.s-item__seller'
            ]
            
            seller_rating = "Not available"
            feedback_count = "Not available"
            
            for selector in seller_selectors:
                seller_elem = item_soup.select_one(selector)
                if seller_elem:
                    seller_text = seller_elem.get_text(strip=True)
                    rating_match = re.search(r'([\d.]+)%', seller_text)
                    if rating_match:
                        seller_rating = f"{rating_match.group(1)}%"
                    
                    count_match = re.search(r'\(([\d,]+)\)', seller_text)
                    if count_match:
                        feedback_count = count_match.group(1).replace(',', '')
                    
                    if rating_match or count_match:
                        break
            
            # Location extraction
            location_selectors = [
                '.s-item__location',
                '.s-item__itemLocation'
            ]
            
            location = "Unknown"
            for selector in location_selectors:
                location_elem = item_soup.select_one(selector)
                if location_elem:
                    location_text = location_elem.get_text(strip=True)
                    if 'from' in location_text.lower():
                        location = location_text.replace('From', '').replace('from', '').strip()[:30]
                        break
            
            # Check if auction or Buy It Now
            is_auction = bool(item_soup.select_one('.s-item__time-left, .timeMs'))
            
            # Extract time left for auctions
            time_left = "Buy It Now"
            if is_auction:
                time_elem = item_soup.select_one('.s-item__time-left, .timeMs')
                if time_elem:
                    time_left = time_elem.get_text(strip=True)
            
            # Additional metrics
            views_count = "Not available"
            watchers_count = "Not available"
            sold_count = "Not available"
            availability = "Available"
            
            # Enhanced profitability calculations
            estimated_resale_price = self.calculate_resale_price(
                title, price, condition, category, subcategory, location
            )
            estimated_profit = estimated_resale_price - total_cost
            profit_margin_percent = (estimated_profit / estimated_resale_price * 100) if estimated_resale_price > 0 else 0
            
            # Enhanced confidence scoring
            confidence_score = self.calculate_confidence_score(
                title, price, condition, seller_rating, estimated_profit, 
                category, subcategory, matched_keyword, location, feedback_count
            )
            
            return eBayListing(
                title=title,
                price=price,
                shipping_cost=shipping_cost,
                total_cost=total_cost,
                estimated_resale_price=estimated_resale_price,
                estimated_profit=estimated_profit,
                profit_margin_percent=profit_margin_percent,
                confidence_score=confidence_score,
                condition=condition,
                seller_rating=seller_rating,
                seller_feedback_count=feedback_count,
                return_policy="30-day returns",
                shipping_time="3-7 business days",
                image_url=image_url,
                ebay_link=ebay_link,
                item_id=item_id,
                category=category,
                subcategory=subcategory,
                matched_keyword=matched_keyword,
                listing_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                views_count=views_count,
                watchers_count=watchers_count,
                is_auction=is_auction,
                buy_it_now_price=price if not is_auction else 0.0,
                time_left=time_left,
                location=location,
                sold_count=sold_count,
                availability=availability
            )
            
        except Exception as e:
            logger.error(f"Error extracting listing data: {e}")
            return None
    
    def calculate_resale_price(self, title: str, current_price: float, 
                             condition: str, category: str, subcategory: str, location: str) -> float:
        """Advanced resale price estimation with market intelligence"""
        base_multiplier = 1.4  # 40% base markup
        
        # Category-specific multipliers
        category_multipliers = {
            'Tech': 1.3,
            'Gaming': 1.5,
            'Collectibles': 2.2,
            'Fashion': 1.8,
            'Vintage': 2.5
        }
        
        # Apply category multiplier
        if category in category_multipliers:
            base_multiplier *= category_multipliers[category]
        
        # Condition-based adjustments
        condition_multipliers = {
            'new': 1.6, 'brand new': 1.6, 'sealed': 1.8,
            'like new': 1.4, 'mint': 1.5, 'very good': 1.3,
            'good': 1.2, 'fair': 1.05, 'used': 1.15,
            'refurbished': 1.25, 'open box': 1.3
        }
        
        condition_key = next(
            (k for k in condition_multipliers.keys() if k in condition.lower()), 
            'used'
        )
        base_multiplier *= condition_multipliers[condition_key]
        
        # High-demand keywords analysis
        demand_keywords = [
            'rare', 'limited', 'exclusive', 'vintage', 'first edition',
            'sealed', 'mint', 'grail', 'psa 10', 'trending', 'viral'
        ]
        
        demand_boost = 1.0
        title_lower = title.lower()
        for keyword in demand_keywords:
            if keyword in title_lower:
                demand_boost += 0.15
        
        base_multiplier *= min(demand_boost, 2.0)
        
        # Price range optimization
        if 10 <= current_price <= 50:
            base_multiplier *= 1.2
        elif 50 <= current_price <= 200:
            base_multiplier *= 1.15
        elif 200 <= current_price <= 500:
            base_multiplier *= 1.1
        elif current_price > 1000:
            base_multiplier *= 0.9
        
        # Brand recognition boost
        premium_brands = [
            'apple', 'google', 'microsoft', 'sony', 'samsung',
            'nike', 'jordan', 'adidas', 'supreme', 'nintendo',
            'pokemon', 'rolex', 'louis vuitton', 'gucci'
        ]
        
        for brand in premium_brands:
            if brand in title_lower:
                base_multiplier *= 1.2
                break
        
        # Final price calculation
        estimated_price = round(current_price * base_multiplier, 2)
        
        # Sanity check
        min_price = current_price * 1.1
        max_price = current_price * 5.0
        
        return max(min_price, min(estimated_price, max_price))
    
    def calculate_confidence_score(self, title: str, price: float, condition: str,
                                 seller_rating: str, estimated_profit: float,
                                 category: str, subcategory: str, matched_keyword: str,
                                 location: str, feedback_count: str) -> int:
        """Advanced confidence scoring with multi-factor analysis"""
        score = 50  # Base score
        
        # Price range scoring
        if 20 <= price <= 200:
            score += 25
        elif 10 <= price <= 500:
            score += 15
        elif 5 <= price <= 1000:
            score += 10
        
        # Condition scoring
        condition_scores = {
            'new': 30, 'brand new': 30, 'sealed': 35,
            'mint': 28, 'like new': 25, 'very good': 20,
            'good': 15, 'fair': 8, 'used': 12,
            'refurbished': 18, 'open box': 20
        }
        
        for cond, points in condition_scores.items():
            if cond in condition.lower():
                score += points
                break
        
        # Profit-based scoring
        if estimated_profit >= 100:
            score += 35
        elif estimated_profit >= 50:
            score += 30
        elif estimated_profit >= 30:
            score += 25
        elif estimated_profit >= 15:
            score += 15
        elif estimated_profit >= 5:
            score += 5
        elif estimated_profit < 0:
            score -= 30
        
        # Seller quality scoring
        try:
            if '%' in seller_rating and seller_rating != "Not available":
                rating_value = float(re.search(r'([\d.]+)', seller_rating).group(1))
                if rating_value >= 99.5:
                    score += 25
                elif rating_value >= 98.0:
                    score += 15
                elif rating_value >= 95.0:
                    score += 10
                elif rating_value >= 90.0:
                    score += 5
                elif rating_value < 85.0:
                    score -= 15
        except (ValueError, AttributeError):
            pass
        
        # Feedback count scoring
        try:
            if feedback_count != "Not available":
                count = int(feedback_count.replace(',', ''))
                if count >= 10000:
                    score += 15
                elif count >= 1000:
                    score += 10
                elif count >= 100:
                    score += 5
                elif count < 10:
                    score -= 10
        except (ValueError, AttributeError):
            pass
        
        # Title quality assessment
        title_words = len(title.split())
        if title_words >= 10:
            score += 15
        elif title_words >= 6:
            score += 10
        elif title_words >= 4:
            score += 5
        else:
            score -= 5
        
        # Keyword matching accuracy
        keyword_similarity = difflib.SequenceMatcher(
            None, matched_keyword.lower(), title.lower()
        ).ratio()
        
        if keyword_similarity > 0.8:
            score += 20
        elif keyword_similarity > 0.6:
            score += 15
        elif keyword_similarity > 0.4:
            score += 10
        elif keyword_similarity > 0.2:
            score += 5
        else:
            score -= 10
        
        return max(0, min(100, score))
    
    def scan_with_keyword_variations(self, base_keyword: str, category: str, 
                                   subcategory: str = None, max_pages: int = 2, 
                                   min_profit: float = 15.0) -> List[eBayListing]:
        """Scan eBay using keyword variations for comprehensive coverage"""
        logger.info(f"🔍 Scanning with keyword: '{base_keyword}' in {category}/{subcategory}")
        
        # Generate keyword variations
        keyword_variations = self.keyword_generator.generate_keyword_variations(base_keyword)
        trending_keywords = self.keyword_generator.generate_trending_keywords([base_keyword])
        
        # Combine and prioritize keywords
        all_keywords = [base_keyword] + keyword_variations[:5] + trending_keywords[:3]
        
        all_listings = []
        self.session_stats['categories_searched'].add(f"{category}/{subcategory or 'All'}")
        
        for keyword_index, keyword in enumerate(all_keywords[:8]):  # Limit to prevent rate limiting
            try:
                for page in range(1, max_pages + 1):
                    try:
                        url = self.build_search_url(keyword, page)
                        soup = self.fetch_page_with_retry(url)
                        
                        if not soup:
                            logger.warning(f"Failed to fetch page {page} for keyword '{keyword}'")
                            break
                        
                        # Item container selectors
                        item_selectors = [
                            '.s-item__wrapper',
                            '.s-item',
                            '.srp-results .s-item'
                        ]
                        
                        items = []
                        for selector in item_selectors:
                            items = soup.select(selector)
                            if items:
                                break
                        
                        if not items:
                            logger.warning(f"No items found on page {page} for keyword '{keyword}'")
                            break
                        
                        self.session_stats['total_searches'] += 1
                        self.session_stats['total_listings_found'] += len(items)
                        
                        page_listings = 0
                        for item in items:
                            listing = self.extract_listing_data(
                                item, category, subcategory or 'General', keyword
                            )
                            
                            if listing and listing.estimated_profit >= min_profit:
                                all_listings.append(listing)
                                page_listings += 1
                                self.session_stats['profitable_listings'] += 1
                        
                        logger.info(f"Page {page} for '{keyword}': {page_listings} profitable listings")
                        
                        # Smart rate limiting
                        delay = random.uniform(1.5, 3.0) + (keyword_index * 0.3)
                        time.sleep(delay)
                        
                    except Exception as e:
                        logger.error(f"Error scanning page {page} for keyword '{keyword}': {e}")
                        continue
                
                # Delay between keywords
                keyword_delay = random.uniform(1.0, 2.5) + (keyword_index * 0.2)
                time.sleep(keyword_delay)
                
            except Exception as e:
                logger.error(f"Error processing keyword '{keyword}': {e}")
                continue
        
        logger.info(f"Completed scan for '{base_keyword}': {len(all_listings)} total profitable listings")
        return all_listings
    
    def find_arbitrage_opportunities(self, all_listings: List[eBayListing]) -> List[Dict]:
        """Advanced arbitrage detection with intelligent product matching"""
        logger.info(f"🔍 Analyzing {len(all_listings)} listings for arbitrage opportunities...")
        
        opportunities = []
        
        # Group listings by product similarity for comparison
        product_groups = self.group_similar_products(all_listings)
        logger.info(f"📊 Created {len(product_groups)} product groups from {len(all_listings)} listings")
        
        for group_key, listings in product_groups.items():
            if len(listings) < 2:
                continue
            
            logger.info(f"🔍 Analyzing group '{group_key}' with {len(listings)} listings")
            
            # Sort by total cost
            listings.sort(key=lambda x: x.total_cost)
            
            # Find arbitrage opportunities within the group
            for i, buy_listing in enumerate(listings[:-1]):
                for sell_listing in listings[i+1:]:
                    # Must have meaningful price difference
                    price_diff = sell_listing.total_cost - buy_listing.total_cost
                    if price_diff < 10.0:  # At least $10 difference
                        continue
                    
                    # Calculate actual arbitrage potential
                    arbitrage_data = self.analyze_arbitrage_pair(buy_listing, sell_listing)
                    
                    if arbitrage_data and arbitrage_data['net_profit_after_fees'] >= 10.0:  # Lowered from 15
                        opportunities.append(arbitrage_data)
                        logger.info(f"✅ Found arbitrage: ${arbitrage_data['net_profit_after_fees']:.2f} profit")
        
        # Also try simple price-based arbitrage for same keywords
        keyword_groups = defaultdict(list)
        for listing in all_listings:
            # Group by matched keyword for broader matching
            keyword_groups[listing.matched_keyword.lower()].append(listing)
        
        for keyword, listings in keyword_groups.items():
            if len(listings) < 2:
                continue
                
            listings.sort(key=lambda x: x.total_cost)
            
            # Look for price gaps in same keyword searches
            for i in range(len(listings) - 1):
                buy_listing = listings[i]
                for j in range(i + 1, min(i + 5, len(listings))):  # Check next 4 listings
                    sell_listing = listings[j]
                    
                    price_diff = sell_listing.total_cost - buy_listing.total_cost
                    if price_diff < 15.0:  # Skip small differences
                        continue
                    
                    # Quick similarity check
                    title_sim = difflib.SequenceMatcher(
                        None, 
                        buy_listing.title.lower(), 
                        sell_listing.title.lower()
                    ).ratio()
                    
                    if title_sim >= 0.4:  # Lowered threshold for broader matching
                        arbitrage_data = self.analyze_arbitrage_pair(buy_listing, sell_listing)
                        
                        if arbitrage_data and arbitrage_data['net_profit_after_fees'] >= 10.0:
                            # Check if we already have this opportunity
                            exists = any(
                                opp['buy_listing']['item_id'] == arbitrage_data['buy_listing']['item_id'] and
                                opp['sell_reference']['item_id'] == arbitrage_data['sell_reference']['item_id']
                                for opp in opportunities
                            )
                            
                            if not exists:
                                opportunities.append(arbitrage_data)
                                logger.info(f"✅ Found keyword arbitrage: ${arbitrage_data['net_profit_after_fees']:.2f} profit")
        
        # Sort by profit and confidence
        opportunities.sort(
            key=lambda x: x['net_profit_after_fees'] * (x['confidence_score'] / 100),
            reverse=True
        )
        
        logger.info(f"✅ Found {len(opportunities)} total arbitrage opportunities")
        return opportunities[:25]  # Return top 25 opportunities
    
    def group_similar_products(self, listings: List[eBayListing]) -> Dict[str, List[eBayListing]]:
        """Group listings by product similarity for arbitrage analysis"""
        groups = defaultdict(list)
        
        for listing in listings:
            # Create grouping key based on normalized product characteristics
            title_words = self.normalize_title(listing.title).split()
            
            # Extract brand if present
            brand = self.extract_brand(listing.title)
            
            # Extract model/version if present
            model = self.extract_model(listing.title)
            
            # Create grouping key with multiple strategies
            key_parts = []
            
            # Strategy 1: Brand + Model
            if brand and model:
                key_parts.append(f"{brand}_{model}")
            elif brand:
                key_parts.append(brand)
            
            # Strategy 2: Key product words (more flexible)
            # Get most important words (longer than 3 chars, not common words)
            important_words = []
            common_words = {'with', 'from', 'this', 'that', 'your', 'will', 'have', 'been', 'they', 'were', 'said', 'each', 'which', 'their', 'time', 'more', 'very', 'what', 'know', 'just', 'first', 'into', 'over', 'think', 'also', 'back', 'after', 'work', 'well', 'year', 'come', 'where', 'much', 'way', 'get', 'use', 'man', 'new', 'now', 'old', 'see', 'him', 'two', 'how', 'its', 'who', 'oil', 'sit', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'may', 'say', 'she', 'use', 'him', 'way', 'too', 'any', 'may', 'try'}
            
            for word in title_words:
                if (len(word) > 3 and 
                    word.isalpha() and 
                    word not in common_words and
                    not word.isdigit()):
                    important_words.append(word)
            
            # Take top 3-4 most descriptive words
            if important_words:
                key_parts.extend(important_words[:4])
            
            # Create multiple grouping strategies
            group_keys = []
            
            # Primary key: All key parts
            if key_parts:
                primary_key = '_'.join(key_parts[:3]).lower()  # Limit to prevent over-specificity
                if len(primary_key) > 6:  # Ensure meaningful key
                    group_keys.append(primary_key)
            
            # Secondary key: Just brand + first important word
            if brand and important_words:
                secondary_key = f"{brand}_{important_words[0]}".lower()
                group_keys.append(secondary_key)
            
            # Tertiary key: First two important words
            if len(important_words) >= 2:
                tertiary_key = f"{important_words[0]}_{important_words[1]}".lower()
                group_keys.append(tertiary_key)
            
            # Add to all relevant groups
            for group_key in group_keys:
                if group_key and len(group_key) > 5:  # Ensure meaningful grouping
                    groups[group_key].append(listing)
        
        # Filter groups to only those with potential for arbitrage
        filtered_groups = {}
        for k, v in groups.items():
            if len(v) >= 2:
                # Sort by price to make arbitrage detection easier
                v.sort(key=lambda x: x.total_cost)
                # Only keep if there's meaningful price variation
                price_range = v[-1].total_cost - v[0].total_cost
                if price_range >= 10.0:  # At least $10 price difference
                    filtered_groups[k] = v
        
        logger.info(f"📊 Created {len(filtered_groups)} product groups with price variation")
        for k, v in list(filtered_groups.items())[:5]:  # Log first 5 groups
            prices = [listing.total_cost for listing in v]
            logger.info(f"   Group '{k}': {len(v)} items, prices ${min(prices):.2f}-${max(prices):.2f}")
        
        return filtered_groups
    
    def normalize_title(self, title: str) -> str:
        """Normalize title for better matching"""
        # Remove common noise words
        noise_words = [
            'new', 'used', 'brand', 'authentic', 'genuine', 'original',
            'fast', 'free', 'shipping', 'ship', 'look', 'wow', 'rare',
            'limited', 'edition', 'special', 'oem', 'obo', 'nr'
        ]
        
        # Clean title
        clean_title = re.sub(r'[^\w\s]', ' ', title.lower())
        words = clean_title.split()
        
        # Filter out noise words
        filtered_words = [word for word in words if word not in noise_words and len(word) > 2]
        
        return ' '.join(filtered_words)
    
    def extract_brand(self, title: str) -> Optional[str]:
        """Extract brand from title"""
        brands = [
            'apple', 'samsung', 'google', 'microsoft', 'sony', 'nintendo',
            'nike', 'adidas', 'jordan', 'supreme', 'pokemon', 'magic',
            'topps', 'panini', 'funko', 'lego', 'rolex', 'omega'
        ]
        
        title_lower = title.lower()
        for brand in brands:
            if brand in title_lower:
                return brand
        
        return None
    
    def extract_model(self, title: str) -> Optional[str]:
        """Extract model/version from title"""
        # Common model patterns
        model_patterns = [
            r'\b(pro|max|plus|mini|air|ultra|lite|slim|xl|xs|se)\b',
            r'\b(\d{1,2}(?:st|nd|rd|th)?)\b',  # Generation numbers
            r'\b(\d{4})\b',  # Year models
            r'\b(v\d+|version\s*\d+)\b'
        ]
        
        title_lower = title.lower()
        for pattern in model_patterns:
            match = re.search(pattern, title_lower)
            if match:
                return match.group(1)
        
        return None
    
    def analyze_arbitrage_pair(self, buy_listing: eBayListing, sell_listing: eBayListing) -> Optional[Dict]:
        """Analyze a pair of listings for arbitrage potential with more flexible criteria"""
        try:
            # Calculate similarity score
            similarity_score = self.calculate_similarity(buy_listing, sell_listing)
            
            # More flexible similarity requirement
            if similarity_score < 0.35:  # Lowered from 0.75
                return None
            
            # Calculate profit after fees
            profit_analysis = self.calculate_detailed_profit(buy_listing, sell_listing)
            
            # More flexible profit requirement
            if profit_analysis['net_profit_after_fees'] < 8.0:  # Lowered from 15.0
                return None
            
            # Calculate risk assessment
            risk_assessment = self.assess_risk(buy_listing, sell_listing, profit_analysis)
            
            # Calculate overall confidence
            confidence_score = self.calculate_arbitrage_confidence(
                buy_listing, sell_listing, similarity_score, profit_analysis, risk_assessment
            )
            
            # More flexible confidence requirement
            if confidence_score < 40:  # Lowered from 60
                return None
            
            return {
                'opportunity_id': f"ARB_{int(time.time())}_{random.randint(1000, 9999)}",
                'buy_listing': asdict(buy_listing),
                'sell_reference': asdict(sell_listing),
                'similarity_score': round(similarity_score, 3),
                'confidence_score': confidence_score,
                'risk_level': risk_assessment['level'],
                'gross_profit': round(profit_analysis['gross_profit'], 2),
                'net_profit_after_fees': round(profit_analysis['net_profit_after_fees'], 2),
                'roi_percentage': round(profit_analysis['roi_percentage'], 1),
                'estimated_fees': round(profit_analysis['estimated_fees'], 2),
                'profit_analysis': profit_analysis,
                'risk_factors': risk_assessment['factors'],
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing arbitrage pair: {e}")
            return None
    
    def calculate_similarity(self, listing1: eBayListing, listing2: eBayListing) -> float:
        """Calculate similarity between two listings with more flexible matching"""
        # Normalize titles
        title1_norm = self.normalize_title(listing1.title)
        title2_norm = self.normalize_title(listing2.title)
        
        # Calculate title similarity
        title_similarity = difflib.SequenceMatcher(None, title1_norm, title2_norm).ratio()
        
        # Brand and model matching
        brand1 = self.extract_brand(listing1.title)
        brand2 = self.extract_brand(listing2.title)
        
        # More flexible brand matching
        if brand1 and brand2:
            brand_match = 1.0 if brand1 == brand2 else 0.0
        elif brand1 or brand2:
            brand_match = 0.3  # Partial credit if only one has identifiable brand
        else:
            brand_match = 0.5  # Neutral if neither has clear brand
        
        model1 = self.extract_model(listing1.title)
        model2 = self.extract_model(listing2.title)
        
        if model1 and model2:
            model_match = 1.0 if model1 == model2 else 0.3
        elif model1 or model2:
            model_match = 0.4
        else:
            model_match = 0.6  # Neutral if neither has clear model
        
        # Condition compatibility (more lenient)
        condition_compat = self.calculate_condition_compatibility(listing1.condition, listing2.condition)
        
        # Check for common keywords in titles
        words1 = set(title1_norm.split())
        words2 = set(title2_norm.split())
        common_words = words1.intersection(words2)
        
        # Filter meaningful common words
        meaningful_common = [w for w in common_words if len(w) > 3]
        keyword_overlap = len(meaningful_common) / max(len(words1), len(words2), 1)
        
        # Weighted similarity score (adjusted for more flexibility)
        similarity = (
            title_similarity * 0.3 +      # Reduced weight
            brand_match * 0.25 +          # Reduced weight
            model_match * 0.15 +          # Reduced weight
            condition_compat * 0.1 +      # Reduced weight
            keyword_overlap * 0.2         # Added keyword overlap
        )
        
        # Bonus for exact keyword matches in different words
        title1_words = listing1.title.lower().split()
        title2_words = listing2.title.lower().split()
        
        # Look for product-specific terms
        product_terms = ['pro', 'max', 'plus', 'mini', 'air', 'ultra', 'lite', 'slim']
        term_matches = 0
        for term in product_terms:
            if (any(term in word for word in title1_words) and 
                any(term in word for word in title2_words)):
                term_matches += 1
        
        if term_matches > 0:
            similarity += 0.1 * min(term_matches, 2)  # Bonus up to 0.2
        
        return min(1.0, similarity)
    
    def calculate_condition_compatibility(self, condition1: str, condition2: str) -> float:
        """Calculate condition compatibility for arbitrage"""
        cond1_lower = condition1.lower()
        cond2_lower = condition2.lower()
        
        # Exact match
        if cond1_lower == cond2_lower:
            return 1.0
        
        # Compatible condition groups
        new_conditions = ['new', 'brand new', 'sealed', 'mint']
        good_conditions = ['like new', 'very good', 'excellent']
        used_conditions = ['used', 'good', 'fair']
        
        def get_condition_group(condition):
            if any(c in condition for c in new_conditions):
                return 'new'
            elif any(c in condition for c in good_conditions):
                return 'good'
            elif any(c in condition for c in used_conditions):
                return 'used'
            return 'other'
        
        group1 = get_condition_group(cond1_lower)
        group2 = get_condition_group(cond2_lower)
        
        if group1 == group2:
            return 0.8
        elif (group1 == 'new' and group2 == 'good') or (group1 == 'good' and group2 == 'new'):
            return 0.6
        else:
            return 0.3
    
    def calculate_detailed_profit(self, buy_listing: eBayListing, sell_listing: eBayListing) -> Dict:
        """Calculate detailed profit analysis with realistic fees"""
        # eBay and payment processing fees
        ebay_final_value_fee = sell_listing.price * 0.125  # 12.5% eBay fee
        payment_processing_fee = sell_listing.price * 0.029 + 0.30  # PayPal/similar
        
        # Shipping costs
        selling_shipping_cost = 0
        if sell_listing.shipping_cost == 0:  # If reference has free shipping
            selling_shipping_cost = 8.0  # Estimated shipping cost to buyer
        
        # Risk factors
        return_shipping_risk = sell_listing.price * 0.015  # 1.5% risk for returns
        
        total_fees = ebay_final_value_fee + payment_processing_fee + selling_shipping_cost + return_shipping_risk
        
        gross_profit = sell_listing.price - buy_listing.total_cost
        net_profit_after_fees = gross_profit - total_fees
        
        roi_percentage = (net_profit_after_fees / buy_listing.total_cost) * 100 if buy_listing.total_cost > 0 else 0
        
        return {
            'gross_profit': gross_profit,
            'net_profit_after_fees': net_profit_after_fees,
            'roi_percentage': roi_percentage,
            'estimated_fees': total_fees,
            'fee_breakdown': {
                'ebay_fee': ebay_final_value_fee,
                'payment_fee': payment_processing_fee,
                'shipping_cost': selling_shipping_cost,
                'return_risk': return_shipping_risk
            }
        }
    
    def assess_risk(self, buy_listing: eBayListing, sell_listing: eBayListing, profit_analysis: Dict) -> Dict:
        """Assess risk factors for arbitrage opportunity with more balanced scoring"""
        risk_score = 0
        risk_factors = []
        
        # High ROI risk (but more lenient)
        if profit_analysis['roi_percentage'] > 300:  # Increased threshold
            risk_score += 25  # Reduced penalty
            risk_factors.append("Very high ROI may indicate different products")
        elif profit_analysis['roi_percentage'] > 150:  # Increased threshold
            risk_score += 10  # Reduced penalty
            risk_factors.append("High ROI requires verification")
        
        # Seller risk (more lenient)
        try:
            buy_rating = float(re.search(r'([\d.]+)', buy_listing.seller_rating).group(1))
            if buy_rating < 90:  # Lowered threshold
                risk_score += 15  # Reduced penalty
                risk_factors.append("Lower seller rating")
            elif buy_rating < 95:
                risk_score += 5   # Minor penalty
                risk_factors.append("Moderate seller rating")
        except:
            risk_score += 10  # Reduced penalty
            risk_factors.append("Unknown seller rating")
        
        # Price point risk (more balanced)
        if buy_listing.total_cost > 1000:  # Increased threshold
            risk_score += 15
            risk_factors.append("High-value item requires more capital")
        elif buy_listing.total_cost < 10:  # Lowered threshold
            risk_score += 10
            risk_factors.append("Very low-value item may have hidden issues")
        
        # Condition mismatch risk (reduced)
        if buy_listing.condition.lower() != sell_listing.condition.lower():
            # Check if conditions are compatible
            compatible_conditions = [
                (['new', 'brand new', 'sealed'], ['new', 'brand new', 'sealed', 'mint']),
                (['used', 'good', 'very good'], ['used', 'good', 'very good', 'excellent']),
                (['like new', 'excellent'], ['like new', 'excellent', 'very good'])
            ]
            
            buy_cond = buy_listing.condition.lower()
            sell_cond = sell_listing.condition.lower()
            
            is_compatible = False
            for group1, group2 in compatible_conditions:
                if (any(c in buy_cond for c in group1) and any(c in sell_cond for c in group2)) or \
                   (any(c in sell_cond for c in group1) and any(c in buy_cond for c in group2)):
                    is_compatible = True
                    break
            
            if not is_compatible:
                risk_score += 15  # Reduced from 20
                risk_factors.append("Different conditions between buy/sell")
            else:
                risk_score += 5   # Minor penalty for compatible conditions
                risk_factors.append("Compatible but different conditions")
        
        # Location risk (reduced)
        if 'china' in buy_listing.location.lower() or 'hong kong' in buy_listing.location.lower():
            risk_score += 5  # Reduced from 10
            risk_factors.append("International shipping may cause delays")
        
        # Similarity-based risk adjustment
        # If items are very similar in title, reduce risk
        title_sim = difflib.SequenceMatcher(
            None, buy_listing.title.lower(), sell_listing.title.lower()
        ).ratio()
        
        if title_sim >= 0.7:
            risk_score = max(0, risk_score - 10)  # Reduce risk for very similar titles
        elif title_sim >= 0.5:
            risk_score = max(0, risk_score - 5)   # Slight risk reduction
        
        # Determine risk level with adjusted thresholds
        if risk_score <= 15:      # Lowered threshold
            risk_level = "LOW"
        elif risk_score <= 35:    # Lowered threshold
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        
        return {
            'score': risk_score,
            'level': risk_level,
            'factors': risk_factors
        }
    
    def calculate_arbitrage_confidence(self, buy_listing: eBayListing, sell_listing: eBayListing,
                                     similarity_score: float, profit_analysis: Dict, risk_assessment: Dict) -> int:
        """Calculate overall confidence in arbitrage opportunity"""
        confidence = 50  # Base confidence
        
        # Similarity bonus
        if similarity_score >= 0.9:
            confidence += 25
        elif similarity_score >= 0.8:
            confidence += 20
        elif similarity_score >= 0.75:
            confidence += 15
        
        # Profit bonus
        net_profit = profit_analysis['net_profit_after_fees']
        if net_profit >= 50:
            confidence += 20
        elif net_profit >= 30:
            confidence += 15
        elif net_profit >= 20:
            confidence += 10
        
        # ROI bonus (but penalize if too high)
        roi = profit_analysis['roi_percentage']
        if 25 <= roi <= 75:
            confidence += 15
        elif 15 <= roi <= 100:
            confidence += 10
        elif roi > 150:
            confidence -= 20  # Too high ROI is suspicious
        
        # Risk penalty
        confidence -= risk_assessment['score'] // 5
        
        # Seller quality bonus
        try:
            buy_rating = float(re.search(r'([\d.]+)', buy_listing.seller_rating).group(1))
            if buy_rating >= 99:
                confidence += 15
            elif buy_rating >= 95:
                confidence += 10
        except:
            confidence -= 10
        
        return max(0, min(100, confidence))
    
    def scan_arbitrage_opportunities(self, keywords: str = None, target_categories: List[str] = None, 
                                   target_subcategories: Dict[str, List[str]] = None,
                                   min_profit: float = 15.0, max_results: int = 25) -> Dict:
        """Main scanning function with comprehensive analysis"""
        logger.info("🚀 Starting FlipHawk arbitrage scan...")
        
        # Reset session stats
        self.session_stats = {
            'total_searches': 0,
            'total_listings_found': 0,
            'profitable_listings': 0,
            'categories_searched': set(),
            'start_time': datetime.now(),
            'success_rate': 0.0
        }
        
        # Default categories if none specified
        if not target_categories:
            target_categories = ['Tech', 'Gaming', 'Collectibles']
        
        # Process keywords
        if keywords:
            search_keywords = [kw.strip() for kw in keywords.split(',') if kw.strip()]
        else:
            search_keywords = ['trending items', 'viral products', 'popular deals']
        
        logger.info(f"Scanning categories: {target_categories}")
        logger.info(f"Using keywords: {search_keywords}")
        
        all_listings = []
        
        # Scan each category with keywords
        for category in target_categories:
            try:
                subcategories_to_scan = []
                
                if target_subcategories and category in target_subcategories:
                    subcategories_to_scan = target_subcategories[category]
                else:
                    # Default subcategories
                    default_subcategories = {
                        'Tech': ['Headphones', 'Smartphones'],
                        'Gaming': ['Consoles', 'Video Games'],
                        'Collectibles': ['Trading Cards', 'Action Figures'],
                        'Fashion': ['Sneakers', 'Designer Clothing'],
                        'Vintage': ['Electronics', 'Cameras']
                    }
                    subcategories_to_scan = default_subcategories.get(category, ['General'])
                
                # Limit subcategories for performance
                for subcategory in subcategories_to_scan[:2]:
                    for keyword in search_keywords[:3]:  # Limit keywords
                        try:
                            category_listings = self.scan_with_keyword_variations(
                                keyword, category, subcategory, max_pages=2, min_profit=min_profit
                            )
                            all_listings.extend(category_listings)
                            
                            # Break if we have enough results
                            if len(all_listings) >= max_results * 3:
                                logger.info(f"Reached target of {max_results * 3} listings, stopping scan")
                                break
                                
                        except Exception as e:
                            logger.error(f"Error scanning {category}/{subcategory} with keyword '{keyword}': {e}")
                            continue
                    
                    if len(all_listings) >= max_results * 3:
                        break
                
                if len(all_listings) >= max_results * 3:
                    break
                    
            except Exception as e:
                logger.error(f"Error processing category {category}: {e}")
                continue
        
        # Calculate success rate
        if self.session_stats['total_listings_found'] > 0:
            self.session_stats['success_rate'] = (
                self.session_stats['profitable_listings'] / 
                self.session_stats['total_listings_found'] * 100
            )
        
        # Find arbitrage opportunities
        arbitrage_opportunities = self.find_arbitrage_opportunities(all_listings)
        
        # Generate comprehensive summary
        end_time = datetime.now()
        duration = end_time - self.session_stats['start_time']
        
        # Calculate metrics
        total_opportunities = len(arbitrage_opportunities)
        if total_opportunities > 0:
            avg_profit = sum(opp['net_profit_after_fees'] for opp in arbitrage_opportunities) / total_opportunities
            avg_confidence = sum(opp['confidence_score'] for opp in arbitrage_opportunities) / total_opportunities
            avg_roi = sum(opp['roi_percentage'] for opp in arbitrage_opportunities) / total_opportunities
            highest_profit = max(opp['net_profit_after_fees'] for opp in arbitrage_opportunities)
        else:
            avg_profit = avg_confidence = avg_roi = highest_profit = 0
        
        summary = {
            'scan_metadata': {
                'scan_id': hashlib.md5(str(self.session_stats['start_time']).encode()).hexdigest()[:8],
                'timestamp': end_time.isoformat(),
                'duration_seconds': round(duration.total_seconds(), 2),
                'total_searches_performed': self.session_stats['total_searches'],
                'total_listings_analyzed': self.session_stats['total_listings_found'],
                'arbitrage_opportunities_found': total_opportunities,
                'categories_scanned': list(self.session_stats['categories_searched']),
                'scan_efficiency': round(self.session_stats['success_rate'], 2),
                'keywords_used': search_keywords,
                'unique_products_found': len(set(listing.item_id for listing in all_listings))
            },
            'opportunities_summary': {
                'total_opportunities': total_opportunities,
                'average_profit_after_fees': round(avg_profit, 2),
                'average_roi': round(avg_roi, 1),
                'average_confidence': round(avg_confidence, 1),
                'highest_profit': round(highest_profit, 2),
                'risk_distribution': {
                    'low': len([opp for opp in arbitrage_opportunities if opp['risk_level'] == 'LOW']),
                    'medium': len([opp for opp in arbitrage_opportunities if opp['risk_level'] == 'MEDIUM']),
                    'high': len([opp for opp in arbitrage_opportunities if opp['risk_level'] == 'HIGH'])
                },
                'profit_ranges': {
                    'under_25': len([opp for opp in arbitrage_opportunities if opp['net_profit_after_fees'] < 25]),
                    '25_to_50': len([opp for opp in arbitrage_opportunities if 25 <= opp['net_profit_after_fees'] < 50]),
                    '50_to_100': len([opp for opp in arbitrage_opportunities if 50 <= opp['net_profit_after_fees'] < 100]),
                    'over_100': len([opp for opp in arbitrage_opportunities if opp['net_profit_after_fees'] >= 100])
                }
            },
            'top_opportunities': arbitrage_opportunities[:max_results]
        }
        
        logger.info(f"✅ Scan completed: {total_opportunities} arbitrage opportunities found in {duration.total_seconds():.1f}s")
        return summary

# Flask Integration Functions
def create_arbitrage_api_endpoints(scraper: TrueArbitrageScanner):
    """Create Flask-compatible API endpoint functions"""
    
    def scan_arbitrage_opportunities(request_data: Dict) -> Dict:
        """Main API endpoint for arbitrage scanning"""
        try:
            keywords = request_data.get('keywords', '')
            target_categories = request_data.get('categories', ['Tech', 'Gaming', 'Collectibles'])
            target_subcategories = request_data.get('subcategories', {})
            min_profit = float(request_data.get('min_profit', 15.0))
            max_results = int(request_data.get('max_results', 25))
            
            # Validate inputs
            if not keywords.strip():
                return {
                    'status': 'error',
                    'message': 'Keywords are required',
                    'data': None
                }
            
            results = scraper.scan_arbitrage_opportunities(
                keywords=keywords,
                target_categories=target_categories,
                target_subcategories=target_subcategories,
                min_profit=min_profit,
                max_results=max_results
            )
            
            return {
                'status': 'success',
                'data': results,
                'message': 'Arbitrage scan completed successfully'
            }
            
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            return {
                'status': 'error',
                'message': f'Scan failed: {str(e)}',
                'data': None
            }
    
    def quick_scan_endpoint() -> Dict:
        """Quick scan with popular keywords"""
        try:
            trending_keywords = "airpods pro, nintendo switch oled, pokemon cards"
            
            results = scraper.scan_arbitrage_opportunities(
                keywords=trending_keywords,
                target_categories=['Tech', 'Gaming', 'Collectibles'],
                target_subcategories={
                    'Tech': ['Headphones', 'Smartphones'],
                    'Gaming': ['Consoles', 'Video Games'],
                    'Collectibles': ['Trading Cards']
                },
                min_profit=20.0,
                max_results=15
            )
            
            return {
                'status': 'success',
                'data': results,
                'message': 'Quick scan completed successfully'
            }
            
        except Exception as e:
            logger.error(f"Quick scan failed: {e}")
            return {
                'status': 'error',
                'message': f'Quick scan failed: {str(e)}',
                'data': None
            }
    
    def trending_scan_endpoint() -> Dict:
        """Trending scan with viral keywords"""
        try:
            trending_keywords = "viral tiktok products, trending 2025, supreme drops, jordan release"
            
            results = scraper.scan_arbitrage_opportunities(
                keywords=trending_keywords,
                target_categories=['Fashion', 'Tech', 'Collectibles'],
                target_subcategories={
                    'Fashion': ['Sneakers', 'Designer Clothing'],
                    'Tech': ['Smartphones', 'Headphones'],
                    'Collectibles': ['Trading Cards', 'Action Figures']
                },
                min_profit=25.0,
                max_results=20
            )
            
            return {
                'status': 'success',
                'data': results,
                'message': 'Trending scan completed successfully'
            }
            
        except Exception as e:
            logger.error(f"Trending scan failed: {e}")
            return {
                'status': 'error',
                'message': f'Trending scan failed: {str(e)}',
                'data': None
            }
    
    return {
        'scan_arbitrage': scan_arbitrage_opportunities,
        'quick_scan': quick_scan_endpoint,
        'trending_scan': trending_scan_endpoint
    }

# Demo and Testing Functions
def demo_arbitrage_scanner():
    """Demonstration function for testing the scanner"""
    scraper = TrueArbitrageScanner()
    
    print("🚀 Starting FlipHawk Arbitrage Demo...")
    print("=" * 70)
    
    # Test with popular keywords
    test_keywords = "airpods pro, pokemon charizard, nintendo switch"
    
    print(f"🔍 Testing Keywords: {test_keywords}")
    print(f"📂 Categories: Tech, Collectibles, Gaming")
    print(f"💰 Min Profit: $25")
    print(f"📊 Max Results: 5")
    print()
    
    results = scraper.scan_arbitrage_opportunities(
        keywords=test_keywords,
        target_categories=['Tech', 'Collectibles', 'Gaming'],
        target_subcategories={
            'Tech': ['Headphones'],
            'Collectibles': ['Trading Cards'],
            'Gaming': ['Consoles']
        },
        min_profit=25.0,
        max_results=5
    )
    
    # Display results
    print(f"📊 DEMO RESULTS:")
    print(f"⏱️  Duration: {results['scan_metadata']['duration_seconds']} seconds")
    print(f"🔍 Total searches: {results['scan_metadata']['total_searches_performed']}")
    print(f"📋 Listings analyzed: {results['scan_metadata']['total_listings_analyzed']}")
    print(f"💡 Arbitrage opportunities: {results['opportunities_summary']['total_opportunities']}")
    print(f"💰 Average profit: ${results['opportunities_summary']['average_profit_after_fees']}")
    print(f"🎯 Average confidence: {results['opportunities_summary']['average_confidence']}%")
    print(f"📈 Success rate: {results['scan_metadata']['scan_efficiency']}%")
    print()
    
    if results['top_opportunities']:
        print(f"🏆 TOP ARBITRAGE OPPORTUNITIES:")
        for i, opportunity in enumerate(results['top_opportunities'][:3], 1):
            buy = opportunity['buy_listing']
            sell = opportunity['sell_reference']
            
            print(f"\n{i}. ARBITRAGE OPPORTUNITY")
            print(f"   🛒 Buy: {buy['title'][:60]}...")
            print(f"   💰 Buy Price: ${buy['total_cost']:.2f}")
            print(f"   💸 Sell Reference: ${sell['price']:.2f}")
            print(f"   💵 Net Profit: ${opportunity['net_profit_after_fees']:.2f}")
            print(f"   📈 ROI: {opportunity['roi_percentage']:.1f}%")
            print(f"   🎯 Confidence: {opportunity['confidence_score']}%")
            print(f"   ⚠️  Risk: {opportunity['risk_level']}")
            print(f"   🔗 Buy Link: {buy['ebay_link'][:60]}...")
    else:
        print("❌ No arbitrage opportunities found with current criteria")
    
    print("\n" + "=" * 70)
    print("✅ Demo completed successfully!")
    
    return results

# Export main components
__all__ = [
    'TrueArbitrageScanner',
    'AdvancedKeywordGenerator', 
    'eBayListing',
    'create_arbitrage_api_endpoints',
    'demo_arbitrage_scanner'
]

if __name__ == "__main__":
    # Run demo
    try:
        demo_arbitrage_scanner()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        logger.exception("Demo failed")
