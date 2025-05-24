"""
Robust FlipHawk eBay Arbitrage Scanner - Addresses Real Scraping Issues
Fixed: Rate limiting, bot detection, headers, delays, and anti-scraping measures
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
    normalized_title: str
    product_hash: str

@dataclass
class ArbitrageOpportunity:
    """Arbitrage opportunity with buy/sell pair"""
    opportunity_id: str
    similarity_score: float
    confidence_score: int
    risk_level: str
    gross_profit: float
    net_profit_after_fees: float
    roi_percentage: float
    estimated_fees: float
    buy_listing: Dict
    sell_reference: Dict
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
        normalized = re.sub(r'[^\w\s]', ' ', title.lower())
        words = normalized.split()
        filtered_words = [w for w in words if w not in self.stopwords and len(w) > 2]
        return ' '.join(sorted(filtered_words))
    
    def extract_brand_model(self, title: str) -> Tuple[str, str]:
        """Extract brand and model from title"""
        title_lower = title.lower()
        
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
        
        model_patterns = [
            r'(\d+(?:st|nd|rd|th)?\s*gen(?:eration)?)',
            r'(pro\s*\d*)', r'(max\s*\d*)', r'(\d+gb|\d+tb)',
            r'(series\s*[a-z])', r'(\d{4})'
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
        norm1 = self.normalize_title(title1)
        norm2 = self.normalize_title(title2)
        
        seq_similarity = difflib.SequenceMatcher(None, norm1, norm2).ratio()
        
        brand1, model1 = self.extract_brand_model(title1)
        brand2, model2 = self.extract_brand_model(title2)
        
        brand_match = 1.0 if brand1 == brand2 and brand1 != 'unknown' else 0.0
        model_match = 1.0 if model1 and model2 and model1 == model2 else 0.0
        
        final_score = (seq_similarity * 0.6) + (brand_match * 0.25) + (model_match * 0.15)
        return min(final_score, 1.0)

class RobustArbitrageScanner:
    """Robust scanner addressing real eBay scraping challenges"""
    
    def __init__(self):
        self.base_url = "https://www.ebay.com/sch/i.html"
        self.product_matcher = ProductMatcher()
        self.seen_items = set()
        self.session_stats = {
            'total_searches': 0,
            'total_listings_found': 0,
            'arbitrage_opportunities_found': 0,
            'unique_products_found': 0,
            'start_time': datetime.now(),
            'scan_efficiency': 0.0
        }
        
        # Realistic browser headers to avoid detection
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
    
    def get_realistic_headers(self) -> Dict[str, str]:
        """Generate realistic browser headers to avoid detection"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
    
    def build_search_url(self, keyword: str, page: int = 1) -> str:
        """Build eBay search URL with proper parameters"""
        params = {
            '_nkw': keyword,
            '_pgn': page,
            'LH_BIN': 1,           # Buy It Now only
            'LH_Complete': 0,      # Active listings only
            'LH_Sold': 0,          # Not sold
            '_sop': 15,            # Price + shipping: lowest first
            '_ipg': 60,            # Reduced items per page to avoid suspicion
            'rt': 'nc',            # No categories redirect
            '_sacat': 0,           # All categories
            'LH_ItemCondition': '1000|1500|2000|3000|4000|5000|6000'  # All conditions
        }
        
        query_string = urllib.parse.urlencode(params)
        return f"{self.base_url}?{query_string}"
    
    def fetch_page_safely(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """Fetch page with advanced anti-detection measures"""
        for attempt in range(retries):
            try:
                # Realistic delay between requests (human-like behavior)
                if attempt > 0:
                    delay = random.uniform(3.0, 8.0) * (attempt + 1)
                    logger.info(f"Retry {attempt}, waiting {delay:.1f}s...")
                    time.sleep(delay)
                else:
                    # Initial human-like delay
                    time.sleep(random.uniform(2.0, 5.0))
                
                # Build request with realistic headers
                headers = self.get_realistic_headers()
                request = urllib.request.Request(url, headers=headers)
                
                # Set timeout
                with urllib.request.urlopen(request, timeout=15) as response:
                    if response.getcode() == 200:
                        content = response.read()
                        
                        # Handle encoding properly
                        encoding = response.info().get_content_charset() or 'utf-8'
                        try:
                            html = content.decode(encoding)
                        except UnicodeDecodeError:
                            html = content.decode('utf-8', errors='ignore')
                        
                        # Check if we got blocked (common block indicators)
                        if any(indicator in html.lower() for indicator in [
                            'blocked', 'captcha', 'robot', 'automated', 'suspicious'
                        ]):
                            logger.warning(f"Potential block detected on attempt {attempt + 1}")
                            continue
                        
                        return BeautifulSoup(html, 'html.parser')
                    
                    elif response.getcode() == 429:
                        logger.warning(f"Rate limited (429) on attempt {attempt + 1}")
                        time.sleep(random.uniform(10.0, 20.0))
                        continue
                    
                    else:
                        logger.warning(f"HTTP {response.getcode()} on attempt {attempt + 1}")
                        continue
                        
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    logger.warning(f"Rate limited (429) on attempt {attempt + 1}")
                    time.sleep(random.uniform(15.0, 30.0))
                elif e.code == 403:
                    logger.warning(f"Forbidden (403) on attempt {attempt + 1}")
                    time.sleep(random.uniform(10.0, 20.0))
                else:
                    logger.warning(f"HTTP Error {e.code} on attempt {attempt + 1}")
                    time.sleep(random.uniform(5.0, 10.0))
                continue
                
            except Exception as e:
                logger.warning(f"Request failed on attempt {attempt + 1}: {e}")
                time.sleep(random.uniform(3.0, 7.0))
                continue
        
        logger.error(f"Failed to fetch {url} after {retries} attempts")
        return None
    
    def extract_listing_data(self, item_soup: BeautifulSoup, matched_keyword: str) -> Optional[eBayListing]:
        """Extract listing data with improved selectors"""
        try:
            # Enhanced title extraction with more selectors
            title_selectors = [
                'h3.s-item__title span[role="heading"]',
                'h3.s-item__title',
                '.s-item__title span',
                '.s-item__title',
                'h3[role="heading"]',
                '.it-ttl a'
            ]
            
            title = None
            for selector in title_selectors:
                title_elem = item_soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    title = re.sub(r'\s+', ' ', title)
                    # Clean common eBay noise
                    title = title.replace('New Listing', '').replace('SPONSORED', '').strip()
                    if title and not any(skip in title.upper() for skip in [
                        'SHOP ON EBAY', 'SEE MORE LIKE THIS', 'ADVERTISEMENT'
                    ]):
                        break
            
            if not title or len(title) < 10:
                return None
            
            # Enhanced price extraction
            price_selectors = [
                '.s-item__price .notranslate',
                '.s-item__price span.BOLD',
                '.s-item__price',
                '.adp-price .notranslate'
            ]
            
            price = 0.0
            for selector in price_selectors:
                price_elem = item_soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    
                    # Handle price ranges (take lower price)
                    if 'to' in price_text.lower() or '-' in price_text:
                        prices = re.findall(r'\$?([\d,]+\.?\d*)', price_text)
                        if prices:
                            price = float(prices[0].replace(',', ''))
                    else:
                        # Single price
                        price_match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
                        if price_match:
                            price = float(price_match.group(1).replace(',', ''))
                    
                    if price > 0:
                        break
            
            # Skip if no valid price or unrealistic price
            if price <= 0 or price > 50000:
                return None
            
            # Enhanced shipping cost extraction
            shipping_cost = 0.0
            shipping_selectors = [
                '.s-item__shipping .vi-price .notranslate',
                '.s-item__shipping',
                '.s-item__logisticsCost',
                '.vi-acc-del-range'
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
                            break
            
            total_cost = price + shipping_cost
            
            # Enhanced link extraction
            link_selectors = [
                '.s-item__link',
                '.s-item__title a',
                '.it-ttl a'
            ]
            
            ebay_link = ""
            for selector in link_selectors:
                link_elem = item_soup.select_one(selector)
                if link_elem:
                    href = link_elem.get('href', '')
                    if href:
                        # Clean URL
                        ebay_link = href.split('?')[0] if '?' in href else href
                        if not ebay_link.startswith('http'):
                            ebay_link = 'https://www.ebay.com' + ebay_link
                        break
            
            if not ebay_link:
                return None
            
            # Extract item ID with multiple patterns
            item_id_patterns = [
                r'/(\d{12,})',
                r'itm/(\d+)',
                r'item/(\d+)',
                r'/p/(\d+)'
            ]
            
            item_id = None
            for pattern in item_id_patterns:
                match = re.search(pattern, ebay_link)
                if match:
                    item_id = match.group(1)
                    break
            
            if not item_id:
                item_id = str(abs(hash(title + str(price))))[:12]
            
            # Skip duplicates
            if item_id in self.seen_items:
                return None
            self.seen_items.add(item_id)
            
            # Enhanced image extraction
            image_selectors = [
                '.s-item__image img',
                '.s-item__wrapper img',
                'img[src*="ebayimg"]'
            ]
            
            image_url = ""
            for selector in image_selectors:
                img_elem = item_soup.select_one(selector)
                if img_elem:
                    image_url = img_elem.get('src', '') or img_elem.get('data-src', '')
                    if image_url:
                        # Enhance image quality
                        image_url = image_url.replace('s-l64', 's-l400').replace('s-l140', 's-l400')
                        if not image_url.startswith('http'):
                            image_url = 'https:' + image_url if image_url.startswith('//') else image_url
                        break
            
            # Enhanced condition extraction
            condition_selectors = [
                '.SECONDARY_INFO',
                '.s-item__subtitle',
                '.s-item__condition-text',
                '.s-item__condition'
            ]
            
            condition = "Unknown"
            for selector in condition_selectors:
                condition_elem = item_soup.select_one(selector)
                if condition_elem:
                    condition_text = condition_elem.get_text(strip=True)
                    if any(word in condition_text.lower() for word in [
                        'new', 'used', 'like new', 'very good', 'excellent',
                        'good', 'fair', 'refurbished', 'open box', 'mint'
                    ]):
                        condition = condition_text
                        break
            
            # Enhanced seller info extraction
            seller_selectors = [
                '.s-item__seller-info-text',
                '.s-item__seller',
                '.mbg-nw',
                '.s-item__etrs-text'
            ]
            
            seller_rating = "Not available"
            feedback_count = "0"
            
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
            
            # Enhanced location extraction
            location_selectors = [
                '.s-item__location .s-item__itemLocation',
                '.s-item__location',
                '.s-item__itemLocation'
            ]
            
            location = "Unknown"
            for selector in location_selectors:
                location_elem = item_soup.select_one(selector)
                if location_elem:
                    location_text = location_elem.get_text(strip=True)
                    location_text = location_text.replace('From', '').replace('from', '').strip()
                    if location_text and len(location_text) > 2:
                        location = location_text
                        break
            
            # Generate normalized data for matching
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
            logger.debug(f"Error extracting listing: {e}")
            return None
    
    def scan_listings_safely(self, keywords: str, max_pages: int = 3) -> List[eBayListing]:
        """Safely scan eBay with proper rate limiting and error handling"""
        logger.info(f"🔍 Starting safe scan for: '{keywords}'")
        
        keyword_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
        all_listings = []
        
        # Limit keywords to prevent excessive requests
        for keyword in keyword_list[:2]:  # Max 2 keywords
            logger.info(f"📍 Scanning keyword: '{keyword}'")
            
            for page in range(1, min(max_pages + 1, 4)):  # Max 3 pages
                try:
                    url = self.build_search_url(keyword, page)
                    soup = self.fetch_page_safely(url)
                    
                    if not soup:
                        logger.warning(f"Failed to fetch page {page} for '{keyword}'")
                        break
                    
                    # Find item containers with multiple selectors
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
                    
                    # Update stats
                    self.session_stats['total_searches'] += 1
                    self.session_stats['total_listings_found'] += len(items)
                    
                    # Extract listings with progress tracking
                    page_listings = 0
                    for i, item in enumerate(items[:40]):  # Limit items per page
                        if i > 0 and i % 10 == 0:
                            # Small delay every 10 items to appear more human
                            time.sleep(random.uniform(0.5, 1.5))
                        
                        listing = self.extract_listing_data(item, keyword)
                        if listing:
                            all_listings.append(listing)
                            page_listings += 1
                    
                    logger.info(f"Page {page} for '{keyword}': {page_listings} listings extracted")
                    
                    # Progressive delay between pages (very important!)
                    time.sleep(random.uniform(3.0, 7.0))
                    
                except Exception as e:
                    logger.error(f"Error scanning page {page} for '{keyword}': {e}")
                    # On error, wait longer before continuing
                    time.sleep(random.uniform(5.0, 10.0))
                    continue
            
            # Longer delay between keywords to avoid detection
            if len(keyword_list) > 1:
                time.sleep(random.uniform(5.0, 10.0))
        
        logger.info(f"✅ Safe scan completed: {len(all_listings)} total listings")
        return all_listings
    
    def find_arbitrage_opportunities(self, listings: List[eBayListing], 
                                   min_profit: float = 15.0) -> List[ArbitrageOpportunity]:
        """Find arbitrage opportunities with improved matching"""
        logger.info(f"🔍 Analyzing {len(listings)} listings for arbitrage...")
        
        if len(listings) < 2:
            logger.warning("Need at least 2 listings to find arbitrage opportunities")
            return []
        
        opportunities = []
        
        # Group by normalized product hash
        product_groups = defaultdict(list)
        for listing in listings:
            product_groups[listing.product_hash].append(listing)
        
        # Also try similarity-based grouping for broader matching
        processed_listings = set()
        
        for i, listing1 in enumerate(listings):
            if listing1.item_id in processed_listings:
                continue
                
            matches = [listing1]
            processed_listings.add(listing1.item_id)
            
            # Find similar listings
            for j, listing2 in enumerate(listings[i+1:], i+1):
                if listing2.item_id in processed_listings:
                    continue
                    
                similarity = self.product_matcher.calculate_similarity(
                    listing1.title, listing2.title
                )
                
                if similarity >= 0.7:  # Lower threshold for more matches
                    matches.append(listing2)
                    processed_listings.add(listing2.item_id)
            
            # If we found matches, check for arbitrage
            if len(matches) >= 2:
                matches.sort(key=lambda x: x.total_cost)
                
                for buy_listing in matches[:-1]:
                    for sell_listing in matches[1:]:
                        if buy_listing.total_cost >= sell_listing.total_cost:
                            continue
                            
                        # Calculate profit
                        gross_profit = sell_listing.price - buy_listing.total_cost
                        
                        if gross_profit < min_profit:
                            continue
                        
                        # Calculate fees
                        ebay_fee = sell_listing.price * 0.13
                        payment_fee = sell_listing.price * 0.029 + 0.30
                        shipping_out = 12.0
                        
                        total_fees = ebay_fee + payment_fee + shipping_out
                        net_profit = gross_profit - total_fees
                        
                        if net_profit < min_profit * 0.3:  # Lower threshold
                            continue
                        
                        roi_percentage = (net_profit / buy_listing.total_cost) * 100
                        
                        # Calculate similarity for this pair
                        similarity = self.product_matcher.calculate_similarity(
                            buy_listing.title, sell_listing.title
                        )
                        
                        # Create opportunity
                        opportunity = ArbitrageOpportunity(
                            opportunity_id=f"ARB_{int(time.time())}_{buy_listing.item_id[:6]}",
                            similarity_score=similarity,
                            confidence_score=self.calculate_confidence_score(
                                buy_listing, sell_listing, similarity, net_profit
                            ),
                            risk_level=self.assess_risk_level(buy_listing, sell_listing, roi_percentage),
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
                                'product_identifier': buy_listing.product_hash
                            },
                            created_at=datetime.now().isoformat()
                        )
                        
                        opportunities.append(opportunity)
        
        # Sort by net profit
        opportunities.sort(key=lambda x: x.net_profit_after_fees, reverse=True)
        
        logger.info(f"✅ Found {len(opportunities)} arbitrage opportunities")
        return opportunities
    
    def calculate_confidence_score(self, buy_listing: eBayListing, 
                                 sell_listing: eBayListing, 
                                 similarity: float, net_profit: float) -> int:
        """Calculate confidence score"""
        score = 40  # Lower base score
        
        # Similarity bonus
        if similarity >= 0.85:
            score += 25
        elif similarity >= 0.75:
            score += 20
        elif similarity >= 0.65:
            score += 15
        
        # Profit bonus
        if net_profit >= 50:
            score += 20
        elif net_profit >= 25:
            score += 15
        elif net_profit >= 10:
            score += 10
        
        # Seller rating bonus
        try:
            buy_rating = float(buy_listing.seller_rating.replace('%', ''))
            sell_rating = float(sell_listing.seller_rating.replace('%', ''))
            
            if buy_rating >= 98 and sell_rating >= 98:
                score += 10
            elif buy_rating >= 95 and sell_rating >= 95:
                score += 5
        except:
            pass
        
        # Condition bonus
        if 'new' in buy_listing.condition.lower():
            score += 5
        
        return max(0, min(100, score))
    
    def assess_risk_level(self, buy_listing: eBayListing, 
                         sell_listing: eBayListing, roi: float) -> str:
        """Assess risk level"""
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
        
        # Large price difference
        price_ratio = sell_listing.price / buy_listing.price
        if price_ratio > 2.5:
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
        """Main scanning function with robust error handling"""
        logger.info(f"🚀 Starting robust arbitrage scan for: '{keywords}'")
        start_time = datetime.now()
        self.session_stats['start_time'] = start_time
        
        try:
            # Scan listings with safety measures
            all_listings = self.scan_listings_safely(keywords, max_pages=3)
            
            if not all_listings:
                logger.warning("No listings found - this could be due to:")
                logger.warning("1. eBay blocking/rate limiting")
                logger.warning("2. No results for this keyword")
                logger.warning("3. Network issues")
                
                return {
                    'scan_metadata': {
                        'duration_seconds': 0,
                        'total_searches_performed': self.session_stats['total_searches'],
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
            
            logger.info(f"Found {len(all_listings)} listings, analyzing for arbitrage...")
            
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
            
            logger.info(f"✅ Robust scan completed: {len(top_opportunities)} opportunities in {duration:.1f}s")
            return result
            
        except Exception as e:
            logger.error(f"Scan failed with error: {e}")
            # Return error result
            return {
                'scan_metadata': {
                    'duration_seconds': (datetime.now() - start_time).total_seconds(),
                    'total_searches_performed': self.session_stats['total_searches'],
                    'total_listings_analyzed': self.session_stats['total_listings_found'],
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


# Create alias for backward compatibility
TrueArbitrageScanner = RobustArbitrageScanner

def create_arbitrage_api_endpoints(scanner):
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
            
            # Validate inputs
            if min_profit < 0 or min_profit > 1000:
                min_profit = 15.0
            
            if max_results < 1 or max_results > 50:
                max_results = 25
            
            results = scanner.scan_arbitrage_opportunities(
                keywords=keywords,
                categories=categories,
                min_profit=min_profit,
                max_results=max_results
            )
            
            opportunities_count = results["opportunities_summary"]["total_opportunities"]
            
            if opportunities_count > 0:
                message = f'Found {opportunities_count} arbitrage opportunities'
            else:
                message = 'No arbitrage opportunities found. Try different keywords or lower the minimum profit.'
            
            return {
                'status': 'success',
                'data': results,
                'message': message
            }
            
        except Exception as e:
            logger.error(f"API scan failed: {e}")
            return {
                'status': 'error',
                'message': f'Scan failed: {str(e)}',
                'data': None
            }
    
    def quick_scan_endpoint() -> Dict:
        """Quick scan with popular keywords"""
        try:
            results = scanner.scan_arbitrage_opportunities(
                keywords="airpods pro, nintendo switch",
                categories=['General'],
                min_profit=20.0,
                max_results=15
            )
            
            opportunities_count = results["opportunities_summary"]["total_opportunities"]
            message = f'Quick scan found {opportunities_count} opportunities'
            
            return {
                'status': 'success',
                'data': results,
                'message': message
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
                keywords="pokemon cards, magic cards",
                categories=['General'],
                min_profit=25.0,
                max_results=20
            )
            
            opportunities_count = results["opportunities_summary"]["total_opportunities"]
            message = f'Trending scan found {opportunities_count} opportunities'
            
            return {
                'status': 'success',
                'data': results,
                'message': message
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


# Test function
def test_robust_scanner():
    """Test the robust scanner with debugging"""
    scanner = RobustArbitrageScanner()
    
    print("🚀 Testing Robust eBay Arbitrage Scanner...")
    print("=" * 60)
    
    test_keywords = "iphone 15"
    print(f"🔍 Testing with: '{test_keywords}'")
    print(f"💰 Min Profit: $15")
    print()
    
    results = scanner.scan_arbitrage_opportunities(
        keywords=test_keywords,
        categories=['General'],
        min_profit=15.0,
        max_results=10
    )
    
    print("📊 RESULTS:")
    print(f"⏱️  Duration: {results['scan_metadata']['duration_seconds']}s")
    print(f"🔍 Searches: {results['scan_metadata']['total_searches_performed']}")
    print(f"📋 Listings: {results['scan_metadata']['total_listings_analyzed']}")
    print(f"💡 Opportunities: {results['opportunities_summary']['total_opportunities']}")
    print(f"📈 Efficiency: {results['scan_metadata']['scan_efficiency']}%")
    
    if results['top_opportunities']:
        print(f"\n🏆 TOP OPPORTUNITIES:")
        for i, opp in enumerate(results['top_opportunities'][:3], 1):
            print(f"{i}. {opp['buy_listing']['title'][:50]}...")
            print(f"   💰 Net Profit: ${opp['net_profit_after_fees']:.2f}")
            print(f"   🎯 Confidence: {opp['confidence_score']}%")
    else:
        print("\n❌ No opportunities found")
        print("This could be due to:")
        print("- eBay blocking/rate limiting the requests")
        print("- No matching products found")
        print("- Profit margins below minimum threshold")
    
    print("\n" + "=" * 60)
    return results


if __name__ == "__main__":
    test_robust_scanner()
