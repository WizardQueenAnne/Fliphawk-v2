"""
Enhanced FlipHawk eBay Arbitrage Scanner - True Arbitrage Implementation
Finds actual price differences between identical products for real arbitrage opportunities
File: backend/scraper/enhanced_arbitrage_scanner.py
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
    """Enhanced eBay listing data structure"""
    title: str
    price: float
    shipping_cost: float
    total_cost: float
    condition: str
    seller_rating: str
    seller_feedback_count: str
    image_url: str
    ebay_link: str
    item_id: str
    location: str
    sold_count: str
    availability: str
    buy_it_now_price: float
    normalized_title: str  # For product matching
    product_hash: str     # For deduplication

@dataclass
class ArbitrageOpportunity:
    """Arbitrage opportunity with buy/sell pair"""
    opportunity_id: str
    similarity_score: float
    confidence_score: int
    risk_level: str
    
    # Profit calculations
    gross_profit: float
    net_profit_after_fees: float
    roi_percentage: float
    estimated_fees: float
    
    # Buy listing (lower price)
    buy_listing: Dict
    
    # Sell reference (higher price)
    sell_reference: Dict
    
    # Product information
    product_info: Dict
    
    created_at: str

class ProductMatcher:
    """Advanced product matching for arbitrage detection"""
    
    def __init__(self):
        self.stopwords = {
            'new', 'used', 'like', 'very', 'good', 'excellent', 'mint', 'condition',
            'brand', 'original', 'authentic', 'genuine', 'rare', 'vintage', 'limited',
            'edition', 'sealed', 'open', 'box', 'free', 'shipping', 'fast', 'quick',
            'sale', 'deal', 'price', 'cheap', 'best', 'great', 'amazing', 'awesome'
        }
        
    def normalize_title(self, title: str) -> str:
        """Normalize title for product matching"""
        # Convert to lowercase and remove special characters
        normalized = re.sub(r'[^\w\s]', ' ', title.lower())
        
        # Remove common noise words
        words = normalized.split()
        filtered_words = [w for w in words if w not in self.stopwords and len(w) > 2]
        
        # Sort words to handle different word orders
        return ' '.join(sorted(filtered_words))
    
    def extract_brand_model(self, title: str) -> Tuple[str, str]:
        """Extract brand and model from title"""
        title_lower = title.lower()
        
        # Common brands
        brands = [
            'apple', 'samsung', 'sony', 'nintendo', 'microsoft', 'google',
            'beats', 'bose', 'nike', 'adidas', 'supreme', 'pokemon',
            'magic', 'yugioh', 'disney', 'marvel', 'lego', 'funko'
        ]
        
        brand = 'unknown'
        for b in brands:
            if b in title_lower:
                brand = b
                break
        
        # Extract model (numbers, generation info)
        model_patterns = [
            r'(\d+(?:st|nd|rd|th)?\s*gen(?:eration)?)',
            r'(pro\s*\d*)',
            r'(max\s*\d*)',
            r'(\d+gb|\d+tb)',
            r'(series\s*[a-z])',
            r'(\d{4})'  # Year
        ]
        
        model = ''
        for pattern in model_patterns:
            matches = re.findall(pattern, title_lower)
            if matches:
                model = ' '.join(matches)
                break
        
        return brand, model
    
    def calculate_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two product titles"""
        # Normalize both titles
        norm1 = self.normalize_title(title1)
        norm2 = self.normalize_title(title2)
        
        # Use difflib for sequence matching
        seq_similarity = difflib.SequenceMatcher(None, norm1, norm2).ratio()
        
        # Check brand/model matching
        brand1, model1 = self.extract_brand_model(title1)
        brand2, model2 = self.extract_brand_model(title2)
        
        brand_match = 1.0 if brand1 == brand2 and brand1 != 'unknown' else 0.0
        model_match = 1.0 if model1 and model2 and model1 == model2 else 0.0
        
        # Weighted similarity score
        final_score = (seq_similarity * 0.6) + (brand_match * 0.25) + (model_match * 0.15)
        
        return min(final_score, 1.0)
    
    def is_same_product(self, listing1: eBayListing, listing2: eBayListing, 
                       min_similarity: float = 0.75) -> bool:
        """Determine if two listings are for the same product"""
        similarity = self.calculate_similarity(listing1.title, listing2.title)
        return similarity >= min_similarity

class TrueArbitrageScanner:
    """Enhanced arbitrage scanner with real price comparison"""
    
    def __init__(self):
        self.base_url = "https://www.ebay.com/sch/i.html"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        self.seen_items = set()
        self.product_matcher = ProductMatcher()
        self.session_stats = {
            'total_searches': 0,
            'total_listings_found': 0,
            'arbitrage_opportunities_found': 0,
            'unique_products_found': 0,
            'start_time': datetime.now(),
            'scan_efficiency': 0.0
        }
    
    def build_search_url(self, keyword: str, page: int = 1, 
                        sort_order: str = "price") -> str:
        """Build eBay search URL"""
        params = {
            '_nkw': keyword,
            '_pgn': page,
            'LH_BIN': 1,      # Buy It Now only
            'LH_Complete': 0,  # Active listings only
            'LH_Sold': 0,     # Not sold
            '_sop': {
                'price': 15,   # Price + shipping: lowest first
                'newest': 10,  # Time: newly listed
                'ending': 1,   # Time: ending soonest
                'popular': 12  # Best Match
            }.get(sort_order, 15),
            '_ipg': 240,      # Max items per page
            'rt': 'nc',       # No categories redirect
            '_sacat': 0,      # All categories
        }
        
        query_string = urllib.parse.urlencode(params)
        return f"{self.base_url}?{query_string}"
    
    def fetch_page_with_retry(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """Fetch page with retry logic"""
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
                
                # Random delay
                time.sleep(random.uniform(1.0, 3.0))
                
                request = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(request, timeout=30) as response:
                    if response.getcode() == 200:
                        content = response.read()
                        encoding = response.info().get_content_charset() or 'utf-8'
                        try:
                            html = content.decode(encoding)
                        except UnicodeDecodeError:
                            html = content.decode('utf-8', errors='ignore')
                        
                        return BeautifulSoup(html, 'html.parser')
                    else:
                        logger.warning(f"HTTP {response.getcode()} for {url}")
                        
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(2, 5)
                    time.sleep(wait_time)
                    
        logger.error(f"Failed to fetch {url} after {retries} attempts")
        return None
    
    def extract_listing_data(self, item_soup: BeautifulSoup, 
                           matched_keyword: str) -> Optional[eBayListing]:
        """Extract listing data from soup"""
        try:
            # Title extraction with multiple selectors
            title_selectors = [
                'h3.s-item__title',
                '.s-item__title',
                'h3[role="heading"]',
                '.it-ttl a',
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
            
            if not title or any(skip in title for skip in [
                'Shop on eBay', 'SPONSORED', 'See more like this'
            ]):
                return None
            
            # Price extraction
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
                    if 'to' in price_text.lower() or '-' in price_text:
                        # Price range - take the lower price
                        prices = re.findall(r'\$?([\d,]+\.?\d*)', price_text)
                        if prices:
                            price = float(prices[0].replace(',', ''))
                    else:
                        price_match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
                        if price_match:
                            price = float(price_match.group(1).replace(',', ''))
                    
                    if price > 0:
                        break
            
            if price <= 0 or price > 10000:
                return None
            
            # Shipping cost - FIXED THE SYNTAX ERROR HERE
            shipping_cost = 0.0
            shipping_selectors = [
                '.s-item__shipping',
                '.s-item__logisticsCost'
            ]
            
            for selector in shipping_selectors:
                shipping_elem = item_soup.select_one(selector)
                if shipping_elem:
                    shipping_text = shipping_elem.get_text(strip=True).lower()
                    if 'free' in shipping_text:
                        shipping_cost = 0.0
                        break
                    elif '$' in shipping_text:  # FIXED: Added missing '$' character
                        shipping_match = re.search(r'\$?([\d,]+\.?\d*)', shipping_text)
                        if shipping_match:
                            shipping_cost = float(shipping_match.group(1).replace(',', ''))
                            break
            
            total_cost = price + shipping_cost
            
            # Link extraction
            link_selectors = [
                '.s-item__link',
                '.it-ttl a',
                '.s-item__title a'
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
            
            # Item ID extraction
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
            
            # Image URL
            image_selectors = [
                '.s-item__image img',
                '.s-item__image',
                'img[src*="ebayimg"]'
            ]
            
            image_url = ""
            for selector in image_selectors:
                img_elem = item_soup.select_one(selector)
                if img_elem:
                    image_url = img_elem.get('src', '') or img_elem.get('data-src', '')
                    if image_url:
                        image_url = image_url.replace('s-l64', 's-l400').replace('s-l140', 's-l400')
                        if not image_url.startswith('http'):
                            image_url = 'https:' + image_url if image_url.startswith('//') else 'https://i.ebayimg.com' + image_url
                        break
            
            # Condition
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
                    if any(word in condition_text.lower() for word in [
                        'new', 'used', 'like new', 'very good', 'excellent',
                        'good', 'fair', 'refurbished', 'open box'
                    ]):
                        condition = condition_text
                        break
            
            # Seller information
            seller_selectors = [
                '.s-item__seller-info-text',
                '.s-item__seller',
                '.mbg-nw'
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
            
            # Location
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
                        location = location_text.replace('From', '').replace('from', '').strip()
                        break
                    elif any(word in location_text.lower() for word in [
                        'usa', 'united states', 'china', 'japan', 'uk', 'canada'
                    ]):
                        location = location_text
                        break
            
            # Normalize title for matching
            normalized_title = self.product_matcher.normalize_title(title)
            product_hash = hashlib.md5(normalized_title.encode()).hexdigest()[:8]
            
            return eBayListing(
                title=title,
                price=price,
                shipping_cost=shipping_cost,
                total_cost=total_cost,
                condition=condition,
                seller_rating=seller_rating,
                seller_feedback_count=feedback_count,
                image_url=image_url,
                ebay_link=ebay_link,
                item_id=item_id,
                location=location,
                sold_count="0",
                availability="Available",
                buy_it_now_price=price,
                normalized_title=normalized_title,
                product_hash=product_hash
            )
            
        except Exception as e:
            logger.error(f"Error extracting listing data: {e}")
            return None
    
    def scan_comprehensive_listings(self, keywords: str, max_pages: int = 5) -> List[eBayListing]:
        """Comprehensive scan for all listings"""
        logger.info(f"🔍 Starting comprehensive scan for: '{keywords}'")
        
        keyword_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
        all_listings = []
        
        for keyword in keyword_list[:3]:  # Limit to 3 keywords for thorough scanning
            logger.info(f"📍 Scanning keyword: '{keyword}'")
            
            for page in range(1, max_pages + 1):
                try:
                    url = self.build_search_url(keyword, page)
                    soup = self.fetch_page_with_retry(url)
                    
                    if not soup:
                        logger.warning(f"Failed to fetch page {page} for '{keyword}'")
                        break
                    
                    # Find items with multiple selectors
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
                        logger.warning(f"No items found on page {page} for '{keyword}'")
                        break
                    
                    self.session_stats['total_searches'] += 1
                    self.session_stats['total_listings_found'] += len(items)
                    
                    page_listings = 0
                    for item in items:
                        listing = self.extract_listing_data(item, keyword)
                        if listing:
                            all_listings.append(listing)
                            page_listings += 1
                    
                    logger.info(f"Page {page} for '{keyword}': {page_listings} listings extracted")
                    
                    # Progressive delay to avoid rate limiting
                    time.sleep(random.uniform(2.0, 4.0))
                    
                except Exception as e:
                    logger.error(f"Error scanning page {page} for '{keyword}': {e}")
                    continue
            
            # Delay between keywords
            time.sleep(random.uniform(1.0, 2.0))
        
        logger.info(f"✅ Comprehensive scan completed: {len(all_listings)} total listings")
        return all_listings
    
    def find_arbitrage_opportunities(self, listings: List[eBayListing], 
                                   min_profit: float = 15.0) -> List[ArbitrageOpportunity]:
        """Find real arbitrage opportunities by comparing prices"""
        logger.info(f"🔍 Analyzing {len(listings)} listings for arbitrage opportunities...")
        
        opportunities = []
        
        # Group listings by product hash for initial matching
        product_groups = defaultdict(list)
        for listing in listings:
            product_groups[listing.product_hash].append(listing)
        
        # Remove groups with only one listing
        product_groups = {k: v for k, v in product_groups.items() if len(v) > 1}
        
        logger.info(f"📊 Found {len(product_groups)} product groups with multiple listings")
        
        # Analyze each product group
        for product_hash, group_listings in product_groups.items():
            try:
                # Sort by total cost
                group_listings.sort(key=lambda x: x.total_cost)
                
                # Compare each listing with others in the group
                for i, buy_listing in enumerate(group_listings[:-1]):
                    for sell_listing in group_listings[i+1:]:
                        
                        # Verify they're actually the same product
                        similarity = self.product_matcher.calculate_similarity(
                            buy_listing.title, sell_listing.title
                        )
                        
                        if similarity < 0.75:  # Not similar enough
                            continue
                        
                        # Calculate potential profit
                        gross_profit = sell_listing.price - buy_listing.total_cost
                        
                        if gross_profit < min_profit:
                            continue
                        
                        # Calculate fees and net profit
                        ebay_fee = sell_listing.price * 0.13  # ~13% eBay fee
                        paypal_fee = sell_listing.price * 0.029 + 0.30  # PayPal fee
                        shipping_out = 10.0  # Estimated shipping cost
                        
                        total_fees = ebay_fee + paypal_fee + shipping_out
                        net_profit = gross_profit - total_fees
                        
                        if net_profit < min_profit * 0.5:  # Net profit too low
                            continue
                        
                        # Calculate ROI
                        roi_percentage = (net_profit / buy_listing.total_cost) * 100
                        
                        # Confidence scoring
                        confidence_score = self.calculate_confidence_score(
                            buy_listing, sell_listing, similarity, net_profit
                        )
                        
                        # Risk assessment
                        risk_level = self.assess_risk_level(buy_listing, sell_listing, roi_percentage)
                        
                        # Create opportunity
                        opportunity = ArbitrageOpportunity(
                            opportunity_id=f"ARB_{int(time.time())}_{buy_listing.item_id[:6]}",
                            similarity_score=similarity,
                            confidence_score=confidence_score,
                            risk_level=risk_level,
                            gross_profit=gross_profit,
                            net_profit_after_fees=net_profit,
                            roi_percentage=roi_percentage,
                            estimated_fees=total_fees,
                            buy_listing={
                                'title': buy_listing.title,
                                'price': buy_listing.price,
                                'shipping_cost': buy_listing.shipping_cost,
                                'total_cost': buy_listing.total_cost,
                                'condition': buy_listing.condition,
                                'seller_rating': buy_listing.seller_rating,
                                'seller_feedback': buy_listing.seller_feedback_count,
                                'location': buy_listing.location,
                                'image_url': buy_listing.image_url,
                                'ebay_link': buy_listing.ebay_link,
                                'item_id': buy_listing.item_id
                            },
                            sell_reference={
                                'title': sell_listing.title,
                                'price': sell_listing.price,
                                'shipping_cost': sell_listing.shipping_cost,
                                'total_cost': sell_listing.total_cost,
                                'condition': sell_listing.condition,
                                'seller_rating': sell_listing.seller_rating,
                                'seller_feedback': sell_listing.seller_feedback_count,
                                'location': sell_listing.location,
                                'image_url': sell_listing.image_url,
                                'ebay_link': sell_listing.ebay_link,
                                'item_id': sell_listing.item_id
                            },
                            product_info={
                                'brand': self.product_matcher.extract_brand_model(buy_listing.title)[0],
                                'model': self.product_matcher.extract_brand_model(buy_listing.title)[1],
                                'category': 'General',
                                'subcategory': 'Other',
                                'key_features': buy_listing.normalized_title.split()[:5],
                                'product_identifier': product_hash
                            },
                            created_at=datetime.now().isoformat()
                        )
                        
                        opportunities.append(opportunity)
                        
            except Exception as e:
                logger.error(f"Error analyzing product group {product_hash}: {e}")
                continue
        
        # Sort by net profit descending
        opportunities.sort(key=lambda x: x.net_profit_after_fees, reverse=True)
        
        logger.info(f"✅ Found {len(opportunities)} arbitrage opportunities")
        return opportunities
    
    def calculate_confidence_score(self, buy_listing: eBayListing, 
                                 sell_listing: eBayListing, 
                                 similarity: float, net_profit: float) -> int:
        """Calculate confidence score for arbitrage opportunity"""
        score = 50  # Base score
        
        # Similarity bonus
        if similarity >= 0.9:
            score += 25
        elif similarity >= 0.8:
            score += 15
        elif similarity >= 0.75:
            score += 10
        
        # Profit bonus
        if net_profit >= 100:
            score += 20
        elif net_profit >= 50:
            score += 15
        elif net_profit >= 25:
            score += 10
        
        # Seller rating bonus
        try:
            buy_rating = float(buy_listing.seller_rating.replace('%', ''))
            sell_rating = float(sell_listing.seller_rating.replace('%', ''))
            
            if buy_rating >= 99 and sell_rating >= 99:
                score += 15
            elif buy_rating >= 98 and sell_rating >= 98:
                score += 10
            elif buy_rating >= 95 and sell_rating >= 95:
                score += 5
        except:
            pass
        
        # Condition bonus
        if 'new' in buy_listing.condition.lower():
            score += 10
        if 'new' in sell_listing.condition.lower():
            score += 5
        
        return max(0, min(100, score))
    
    def assess_risk_level(self, buy_listing: eBayListing, 
                         sell_listing: eBayListing, roi: float) -> str:
        """Assess risk level of arbitrage opportunity"""
        risk_factors = 0
        
        # High ROI might be risky
        if roi > 100:
            risk_factors += 1
        
        # Low seller ratings
        try:
            buy_rating = float(buy_listing.seller_rating.replace('%', ''))
            if buy_rating < 95:
                risk_factors += 1
        except:
            risk_factors += 1
        
        # Price difference too large
        price_ratio = sell_listing.price / buy_listing.price
        if price_ratio > 3:
            risk_factors += 1
        
        # Different conditions
        if buy_listing.condition.lower() != sell_listing.condition.lower():
            risk_factors += 1
        
        if risk_factors == 0:
            return "LOW"
        elif risk_factors <= 2:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def scan_arbitrage_opportunities(self, keywords: str, categories: List[str],
                                   min_profit: float = 15.0, max_results: int = 25) -> Dict:
        """Main scanning function with comprehensive analysis"""
        logger.info("🚀 Starting true arbitrage scan...")
        
        start_time = datetime.now()
        self.session_stats['start_time'] = start_time
        
        # Comprehensive listing scan
        all_listings = self.scan_comprehensive_listings(keywords, max_pages=6)
        
        if not all_listings:
            return {
                'scan_metadata': {
                    'duration_seconds': 0,
                    'total_searches_performed': 0,
                    'total_listings_analyzed': 0,
                    'arbitrage_opportunities_found': 0,
                    'scan_efficiency': 0,
                    'unique_products_found': 0
                },
                'opportunities_summary': {
                    'total_opportunities': 0,
                    'average_profit_after_fees': 0,
                    'average_roi': 0,
                    'average_confidence': 0,
                    'highest_profit': 0,
                    'risk_distribution': {'low': 0, 'medium': 0, 'high': 0},
                    'profit_ranges': {
                        'under_25': 0, '25_to_50': 0, '50_to_100': 0, 'over_100': 0
                    }
                },
                'top_opportunities': []
            }
        
        # Find arbitrage opportunities
        opportunities = self.find_arbitrage_opportunities(all_listings, min_profit)
        
        # Limit results
        top_opportunities = opportunities[:max_results]
        
        # Calculate statistics
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        self.session_stats['arbitrage_opportunities_found'] = len(opportunities)
        self.session_stats['unique_products_found'] = len(set(listing.product_hash for listing in all_listings))
        
        if self.session_stats['total_listings_found'] > 0:
            self.session_stats['scan_efficiency'] = (
                self.session_stats['arbitrage_opportunities_found'] / 
                self.session_stats['total_listings_found'] * 100
            )
        
        # Generate summary
        if top_opportunities:
            avg_profit = sum(op.net_profit_after_fees for op in top_opportunities) / len(top_opportunities)
            avg_roi = sum(op.roi_percentage for op in top_opportunities) / len(top_opportunities)
            avg_confidence = sum(op.confidence_score for op in top_opportunities) / len(top_opportunities)
            highest_profit = max(op.net_profit_after_fees for op in top_opportunities)
            
            # Risk distribution
            risk_dist = {'low': 0, 'medium': 0, 'high': 0}
            for op in top_opportunities:
                risk_dist[op.risk_level.lower()] += 1
            
            # Profit ranges
            profit_ranges = {'under_25': 0, '25_to_50': 0, '50_to_100': 0, 'over_100': 0}
            for op in top_opportunities:
                profit = op.net_profit_after_fees
                if profit < 25:
                    profit_ranges['under_25'] += 1
                elif profit < 50:
                    profit_ranges['25_to_50'] += 1
                elif profit < 100:
                    profit_ranges['50_to_100'] += 1
                else:
                    profit_ranges['over_100'] += 1
        else:
            avg_profit = avg_roi = avg_confidence = highest_profit = 0
            risk_dist = {'low': 0, 'medium': 0, 'high': 0}
            profit_ranges = {'under_25': 0, '25_to_50': 0, '50_to_100': 0, 'over_100': 0}
        
        result = {
            'scan_metadata': {
                'duration_seconds': round(duration, 2),
                'total_searches_performed': self.session_stats['total_searches'],
                'total_listings_analyzed': self.session_stats['total_listings_found'],
                'arbitrage_opportunities_found': len(opportunities),
                'scan_efficiency': round(self.session_stats['scan_efficiency'], 2),
                'unique_products_found': self.session_stats['unique_products_found']
            },
            'opportunities_summary': {
                'total_opportunities': len(top_opportunities),
                'average_profit_after_fees': round(avg_profit, 2),
                'average_roi': round(avg_roi, 2),
                'average_confidence': round(avg_confidence, 1),
                'highest_profit': round(highest_profit, 2),
                'risk_distribution': risk_dist,
                'profit_ranges': profit_ranges
            },
            'top_opportunities': [asdict(op) for op in top_opportunities]
        }
        
        logger.info(f"✅ Arbitrage scan completed: {len(top_opportunities)} opportunities found in {duration:.1f}s")
        return result


# Flask Integration Functions
def create_arbitrage_api_endpoints(scanner: TrueArbitrageScanner):
    """Create Flask-compatible API endpoint functions"""
    
    def scan_arbitrage_opportunities(request_data: Dict) -> Dict:
        """Main arbitrage scanning endpoint"""
        try:
            keywords = request_data.get('keywords', '')
            categories = request_data.get('categories', ['General'])
            min_profit = float(request_data.get('min_profit', 15.0))
            max_results = int(request_data.get('max_results', 25))
            
            if not keywords.strip():
                return {
                    'status': 'error',
                    'message': 'Keywords are required',
                    'data': None
                }
            
            results = scanner.scan_arbitrage_opportunities(
                keywords=keywords,
                categories=categories,
                min_profit=min_profit,
                max_results=max_results
            )
            
            return {
                'status': 'success',
                'data': results,
                'message': f'Found {results["opportunities_summary"]["total_opportunities"]} arbitrage opportunities'
            }
            
        except Exception as e:
            logger.error(f"Arbitrage scan failed: {e}")
            return {
                'status': 'error',
                'message': f'Scan failed: {str(e)}',
                'data': None
            }
    
    def quick_scan_endpoint() -> Dict:
        """Quick scan with popular keywords"""
        try:
            results = scanner.scan_arbitrage_opportunities(
                keywords="airpods pro, nintendo switch oled, pokemon cards",
                categories=['General'],
                min_profit=20.0,
                max_results=15
            )
            
            return {
                'status': 'success',
                'data': results,
                'message': f'Quick scan found {results["opportunities_summary"]["total_opportunities"]} opportunities'
            }
            
        except Exception as e:
            logger.error(f"Quick scan failed: {e}")
            return {
                'status': 'error',
                'message': f'Quick scan failed: {str(e)}',
                'data': None
            }
    
    def trending_scan_endpoint() -> Dict:
        """Trending keywords scan"""
        try:
            results = scanner.scan_arbitrage_opportunities(
                keywords="viral tiktok products, trending 2025, pokemon cards, supreme",
                categories=['General'],
                min_profit=25.0,
                max_results=20
            )
            
            return {
                'status': 'success',
                'data': results,
                'message': f'Trending scan found {results["opportunities_summary"]["total_opportunities"]} opportunities'
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


# Demo function for testing
def demo_true_arbitrage_scanner():
    """Demo function to test the true arbitrage scanner"""
    scanner = TrueArbitrageScanner()
    
    print("🚀 Starting True Arbitrage Scanner Demo...")
    print("=" * 70)
    
    test_keywords = "airpods pro, pokemon charizard"
    
    print(f"🔍 Testing Keywords: {test_keywords}")
    print(f"💰 Min Profit: $20")
    print(f"📊 Max Results: 5")
    print()
    
    results = scanner.scan_arbitrage_opportunities(
        keywords=test_keywords,
        categories=['General'],
        min_profit=20.0,
        max_results=5
    )
    
    # Display results
    print(f"📊 DEMO RESULTS:")
    print(f"⏱️  Duration: {results['scan_metadata']['duration_seconds']} seconds")
    print(f"🔍 Total searches: {results['scan_metadata']['total_searches_performed']}")
    print(f"📋 Listings analyzed: {results['scan_metadata']['total_listings_analyzed']}")
    print(f"💡 Arbitrage opportunities: {results['opportunities_summary']['total_opportunities']}")
    print(f"💰 Average profit: ${results['opportunities_summary']['average_profit_after_fees']}")
    print(f"📈 Average ROI: {results['opportunities_summary']['average_roi']}%")
    print(f"🎯 Average confidence: {results['opportunities_summary']['average_confidence']}%")
    print()
    
    if results['top_opportunities']:
        print(f"🏆 TOP ARBITRAGE OPPORTUNITIES:")
        for i, opportunity in enumerate(results['top_opportunities'][:3], 1):
            print(f"\n{i}. OPPORTUNITY #{opportunity['opportunity_id']}")
            print(f"   📱 Product: {opportunity['buy_listing']['title'][:60]}...")
            print(f"   💰 Net Profit: ${opportunity['net_profit_after_fees']:.2f}")
            print(f"   📊 ROI: {opportunity['roi_percentage']:.1f}%")
            print(f"   🎯 Confidence: {opportunity['confidence_score']}%")
            print(f"   ⚡ Risk Level: {opportunity['risk_level']}")
            print(f"   🛒 BUY:  ${opportunity['buy_listing']['total_cost']:.2f} - {opportunity['buy_listing']['condition']}")
            print(f"   🏪 SELL: ${opportunity['sell_reference']['price']:.2f} - {opportunity['sell_reference']['condition']}")
            print(f"   📈 Similarity: {opportunity['similarity_score']:.2f}")
    else:
        print("❌ No arbitrage opportunities found")
    
    print(f"\n💼 PROFIT ANALYSIS:")
    ranges = results['opportunities_summary']['profit_ranges']
    print(f"   💵 Under $25: {ranges['under_25']} opportunities")
    print(f"   💰 $25-$50: {ranges['25_to_50']} opportunities")
    print(f"   💸 $50-$100: {ranges['50_to_100']} opportunities")
    print(f"   💎 Over $100: {ranges['over_100']} opportunities")
    
    print(f"\n⚖️ RISK DISTRIBUTION:")
    risk_dist = results['opportunities_summary']['risk_distribution']
    print(f"   🟢 Low Risk: {risk_dist['low']} opportunities")
    print(f"   🟡 Medium Risk: {risk_dist['medium']} opportunities")
    print(f"   🔴 High Risk: {risk_dist['high']} opportunities")
    
    print("\n" + "=" * 70)
    print("✅ True Arbitrage Scanner Demo completed!")
    
    return results


if __name__ == "__main__":
    # Run demo
    try:
        demo_true_arbitrage_scanner()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        logger.exception("Demo failed")
