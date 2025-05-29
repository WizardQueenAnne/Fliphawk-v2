#!/usr/bin/env python3
"""
FlipHawk Real-Time eBay Scraper - FIXED VERSION
Finds arbitrage opportunities across ALL categories with better matching
"""

import requests
import json
import time
import re
import logging
from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime
from urllib.parse import urlencode, quote_plus
from bs4 import BeautifulSoup
import random
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
import hashlib

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
    # Add normalized title for better matching
    normalized_title: str = ""

class RealTimeeBayScraper:
    """Real-time eBay scraper with improved arbitrage detection"""
    
    def __init__(self):
        self.base_url = "https://www.ebay.com"
        self.search_url = f"{self.base_url}/sch/i.html"
        
        # Rotate user agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        self.session = requests.Session()
        self.last_request_time = 0
        self.min_delay = 0.8  # Reduced delay for faster scanning
        
        # Better duplicate tracking
        self.seen_items = set()
        self.seen_titles = set()  # Track normalized titles
        
        # Category-specific keywords for better searches
        self.category_keywords = {
            'gaming': ['ps5', 'playstation 5', 'xbox series x', 'xbox series s', 'nintendo switch', 
                       'switch oled', 'gaming console', 'video games', 'controller', 'headset'],
            'pokemon': ['pokemon cards', 'pokemon tcg', 'charizard', 'pikachu', 'booster box',
                        'elite trainer box', 'pokemon psa', 'japanese pokemon', 'vintage pokemon'],
            'collectibles': ['trading cards', 'sports cards', 'baseball cards', 'basketball cards',
                            'graded cards', 'psa 10', 'vintage toys', 'action figures', 'funko pop'],
            'fashion': ['jordan 1', 'jordan 4', 'air jordan', 'yeezy', 'nike dunk', 'sneakers',
                       'designer shoes', 'supreme', 'off white', 'vintage clothing'],
            'tech': ['airpods pro', 'airpods', 'iphone 14', 'iphone 15', 'macbook', 'ipad',
                    'apple watch', 'samsung galaxy', 'gaming laptop', 'graphics card']
        }
    
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
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.ebay.com/'
        }
    
    def rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            sleep_time = self.min_delay - time_since_last + random.uniform(0.1, 0.3)
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def normalize_title(self, title: str) -> str:
        """Normalize title for better matching"""
        # Convert to lowercase
        normalized = title.lower()
        
        # Remove special characters but keep spaces
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Remove extra spaces
        normalized = ' '.join(normalized.split())
        
        # Remove common words that don't affect product identity
        stop_words = ['for', 'the', 'and', 'with', 'new', 'brand', 'sealed', 'box', 
                     'authentic', 'genuine', 'original', 'usa', 'ship', 'fast', 'free']
        words = normalized.split()
        normalized = ' '.join([w for w in words if w not in stop_words])
        
        return normalized
    
    def extract_key_features(self, title: str) -> Set[str]:
        """Extract key features from title for matching"""
        features = set()
        title_lower = title.lower()
        
        # Extract model numbers
        model_patterns = [
            r'\b\d{1,4}gb\b',  # Storage sizes
            r'\b\d+mm\b',       # Sizes
            r'\bgen\s*\d+\b',   # Generations
            r'\bv\d+\b',        # Versions
            r'\b\d{4}\b',       # Years
            r'\b(?:size|sz)\s*\d+\b',  # Shoe sizes
        ]
        
        for pattern in model_patterns:
            matches = re.findall(pattern, title_lower)
            features.update(matches)
        
        # Extract key product identifiers
        if 'pokemon' in title_lower:
            # Pokemon specific
            pokemon_names = re.findall(r'\b(?:charizard|pikachu|blastoise|venusaur|mewtwo|mew)\b', title_lower)
            features.update(pokemon_names)
            
            # Set names
            set_names = re.findall(r'\b(?:base set|jungle|fossil|team rocket|gym|neo)\b', title_lower)
            features.update(set_names)
        
        if 'jordan' in title_lower or 'nike' in title_lower:
            # Sneaker specific
            colorways = re.findall(r'\b(?:bred|chicago|royal|shadow|banned|mocha|travis)\b', title_lower)
            features.update(colorways)
        
        return features
    
    def calculate_similarity(self, title1: str, title2: str) -> float:
        """Improved similarity calculation"""
        # Basic sequence matching
        basic_similarity = SequenceMatcher(None, title1.lower(), title2.lower()).ratio()
        
        # Normalized title matching
        norm1 = self.normalize_title(title1)
        norm2 = self.normalize_title(title2)
        normalized_similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        # Feature matching
        features1 = self.extract_key_features(title1)
        features2 = self.extract_key_features(title2)
        
        if features1 and features2:
            feature_overlap = len(features1 & features2) / max(len(features1), len(features2))
        else:
            feature_overlap = 0
        
        # Weighted combination
        final_similarity = (
            basic_similarity * 0.3 +
            normalized_similarity * 0.5 +
            feature_overlap * 0.2
        )
        
        # Boost similarity for exact product matches
        key_terms = ['model', 'size', 'color', 'edition', 'version']
        for term in key_terms:
            if term in title1.lower() and term in title2.lower():
                # Extract the value after the term
                pattern = f'{term}\\s*(\\S+)'
                match1 = re.search(pattern, title1.lower())
                match2 = re.search(pattern, title2.lower())
                if match1 and match2 and match1.group(1) == match2.group(1):
                    final_similarity += 0.1
        
        return min(final_similarity, 1.0)
    
    def expand_search_keywords(self, keyword: str) -> List[str]:
        """Expand keywords for better search coverage"""
        keywords = [keyword]
        keyword_lower = keyword.lower()
        
        # Category-specific expansions
        if any(gaming in keyword_lower for gaming in ['nintendo', 'switch', 'oled']):
            keywords.extend(['nintendo switch oled', 'switch oled white', 'switch oled neon', 
                           'nintendo switch console', 'switch oled model'])
        
        elif any(ps5 in keyword_lower for ps5 in ['ps5', 'playstation 5']):
            keywords.extend(['ps5 console', 'playstation 5 disc', 'ps5 digital', 
                           'ps5 bundle', 'ps5 spider-man'])
        
        elif 'pokemon' in keyword_lower:
            keywords.extend(['pokemon cards lot', 'pokemon booster', 'pokemon psa', 
                           'pokemon sealed', 'pokemon japanese'])
        
        elif any(jordan in keyword_lower for jordan in ['jordan', 'air jordan']):
            keywords.extend(['air jordan 1', 'jordan 1 high', 'jordan 4 retro', 
                           'jordan 1 low', 'jordan sneakers'])
        
        elif 'airpods' in keyword_lower:
            keywords.extend(['airpods pro 2nd', 'airpods pro 2', 'airpods 3rd generation',
                           'apple airpods pro', 'airpods pro magsafe'])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw.lower() not in seen:
                seen.add(kw.lower())
                unique_keywords.append(kw)
        
        return unique_keywords[:3]  # Limit to top 3 variations
    
    def build_search_url(self, keyword: str, page: int = 1, sort_order: str = "price") -> str:
        """Build eBay search URL with better parameters"""
        params = {
            '_nkw': keyword,
            '_pgn': page,
            '_ipg': 200,  # Request more items per page
            'LH_BIN': 1,  # Buy It Now only
            'LH_ItemCondition': '1000|1500|2000|2500|3000',  # New, Open Box, Refurb, Used
            'rt': 'nc',
            '_sacat': 0,
        }
        
        # Sort options
        sort_mapping = {
            'price': 15,    # Price + shipping: lowest first
            'newest': 10,   # Time: newly listed
            'best': 12      # Best Match
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
                response = self.session.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Verify it's a valid eBay page
                    if soup.find('title') and 'eBay' in soup.get_text():
                        return soup
                    else:
                        logger.warning(f"Invalid eBay page content")
                        return None
                
                elif response.status_code == 429:
                    wait_time = (2 ** attempt) + random.uniform(3, 8)
                    logger.warning(f"Rate limited, waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    
                else:
                    logger.warning(f"HTTP {response.status_code} for {url}")
                    if attempt < retries - 1:
                        time.sleep(random.uniform(2, 4))
                        
            except Exception as e:
                logger.error(f"Error fetching page (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    time.sleep(random.uniform(3, 6))
        
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
                'results matching fewer words', 'tap to watch'
            ]
            
            if any(pattern in title.lower() for pattern in skip_patterns):
                return None
            
            # Extract price
            price = 0.0
            price_selectors = [
                '.s-item__price .notranslate',
                '.s-item__price span.POSITIVE',
                '.s-item__price',
                'span.s-item__price'
            ]
            
            for selector in price_selectors:
                price_elem = item_soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    
                    # Handle price ranges - take the lower price
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
            
            if price <= 0 or price > 100000:
                return None
            
            # Extract shipping cost
            shipping_cost = 0.0
            shipping_selectors = [
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
                            try:
                                shipping_cost = float(shipping_match.group(1).replace(',', ''))
                                # Cap unreasonable shipping costs
                                shipping_cost = min(shipping_cost, price * 0.3)
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
                # Generate unique ID from URL
                item_id = hashlib.md5(ebay_link.encode()).hexdigest()[:12]
            
            # Check for duplicates using normalized title
            normalized_title = self.normalize_title(title)
            title_hash = hashlib.md5(normalized_title.encode()).hexdigest()
            
            if title_hash in self.seen_titles:
                return None
            self.seen_titles.add(title_hash)
            
            if item_id in self.seen_items:
                return None
            self.seen_items.add(item_id)
            
            # Extract condition
            condition = "Unknown"
            condition_selectors = [
                '.SECONDARY_INFO',
                '.s-item__subtitle',
                'span.SECONDARY_INFO'
            ]
            
            for selector in condition_selectors:
                condition_elem = item_soup.select_one(selector)
                if condition_elem:
                    condition_text = condition_elem.get_text(strip=True)
                    if condition_text and len(condition_text) < 100:
                        condition = condition_text
                        break
            
            # Extract seller info
            seller_username = "Unknown"
            seller_rating = "Not available"
            seller_feedback = "Not available"
            
            seller_selectors = [
                '.s-item__seller-info-text',
                '.s-item__seller-info',
                'span.s-item__seller-info'
            ]
            
            for selector in seller_selectors:
                seller_elem = item_soup.select_one(selector)
                if seller_elem:
                    seller_text = seller_elem.get_text(strip=True)
                    
                    # Extract rating percentage
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
                '.s-item__image-wrapper img',
                'img.s-item__image-img'
            ]
            
            for selector in image_selectors:
                img_elem = item_soup.select_one(selector)
                if img_elem:
                    src = img_elem.get('src') or img_elem.get('data-src')
                    if src:
                        # Get larger image
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
                '.s-item__itemLocation',
                'span.s-item__location'
            ]
            
            for selector in location_selectors:
                location_elem = item_soup.select_one(selector)
                if location_elem:
                    location_text = location_elem.get_text(strip=True)
                    if location_text:
                        location = location_text.replace('From', '').replace('from', '').strip()
                    break
            
            # Additional info
            is_auction = bool(item_soup.select_one('.s-item__time-left'))
            
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
                watchers="Not available",
                bids="0" if not is_auction else "Unknown",
                time_left="Buy It Now" if not is_auction else "Unknown",
                is_auction=is_auction,
                buy_it_now_available=not is_auction,
                normalized_title=normalized_title
            )
            
        except Exception as e:
            logger.error(f"Error extracting listing data: {e}")
            return None
    
    def search_ebay(self, keyword: str, limit: int = 50, sort_order: str = "price", 
                   max_pages: int = 5) -> List[eBayListing]:
        """Search eBay for real listings with expanded keywords"""
        logger.info(f"🔍 Searching eBay for: '{keyword}' (limit: {limit})")
        
        all_listings = []
        expanded_keywords = self.expand_search_keywords(keyword)
        
        logger.info(f"📝 Expanded search terms: {expanded_keywords}")
        
        for search_keyword in expanded_keywords:
            logger.info(f"🔎 Searching for: '{search_keyword}'")
            
            for page in range(1, max_pages + 1):
                try:
                    url = self.build_search_url(search_keyword, page, sort_order)
                    soup = self.get_page(url)
                    
                    if not soup:
                        logger.warning(f"Failed to get page {page} for '{search_keyword}'")
                        break
                    
                    # Find item containers
                    items = soup.select('.s-item__wrapper')
                    if not items:
                        items = soup.select('.s-item')
                    
                    if not items:
                        logger.warning(f"No items found on page {page}")
                        break
                    
                    logger.info(f"Found {len(items)} items on page {page}")
                    
                    page_listings = []
                    for item in items:
                        listing = self.extract_listing_data(item, search_keyword)
                        if listing:
                            page_listings.append(listing)
                    
                    all_listings.extend(page_listings)
                    logger.info(f"Extracted {len(page_listings)} valid listings from page {page}")
                    
                    # Stop if we have enough unique listings
                    if len(all_listings) >= limit * 2:  # Get extra to account for filtering
                        break
                    
                    # Only get first 2 pages per keyword variation
                    if page >= 2:
                        break
                    
                    # Rate limiting between pages
                    time.sleep(random.uniform(1.0, 2.0))
                    
                except Exception as e:
                    logger.error(f"Error searching page {page}: {e}")
                    continue
            
            # Don't search too many variations if we have enough
            if len(all_listings) >= limit * 1.5:
                break
        
        # Remove any remaining duplicates based on title similarity
        unique_listings = self.remove_duplicate_listings(all_listings)
        
        # Sort by price
        if sort_order == "price":
            unique_listings.sort(key=lambda x: x.total_cost)
        
        logger.info(f"✅ Search completed: {len(unique_listings)} unique listings found")
        return unique_listings[:limit]
    
    def remove_duplicate_listings(self, listings: List[eBayListing]) -> List[eBayListing]:
        """Remove duplicate listings based on title similarity"""
        unique_listings = []
        seen_titles = []
        
        for listing in listings:
            is_duplicate = False
            
            for seen_title in seen_titles:
                similarity = self.calculate_similarity(listing.title, seen_title)
                if similarity > 0.85:  # Very similar titles
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_listings.append(listing)
                seen_titles.append(listing.title)
        
        return unique_listings
    
    def find_arbitrage_opportunities(self, listings: List[eBayListing], min_profit: float = 15.0) -> List[Dict]:
        """Find arbitrage opportunities with improved matching"""
        logger.info(f"🎯 Analyzing {len(listings)} listings for arbitrage opportunities...")
        
        opportunities = []
        processed_pairs = set()  # Track processed pairs to avoid duplicates
        
        # Sort listings by price for better comparison
        sorted_listings = sorted(listings, key=lambda x: x.total_cost)
        
        for i, buy_listing in enumerate(sorted_listings):
            for j, sell_listing in enumerate(sorted_listings[i+1:], i+1):
                # Create unique pair identifier
                pair_id = tuple(sorted([buy_listing.item_id, sell_listing.item_id]))
                if pair_id in processed_pairs:
                    continue
                processed_pairs.add(pair_id)
                
                # Skip if price difference is too small
                price_diff = sell_listing.total_cost - buy_listing.total_cost
                if price_diff < min_profit * 0.5:  # At least half of min profit before fees
                    continue
                
                # Calculate similarity with improved matching
                similarity = self.calculate_similarity(buy_listing.title, sell_listing.title)
                
                # Lower threshold for different categories
                min_similarity = 0.25  # Much lower threshold
                
                # Category-specific adjustments
                if any(cat in buy_listing.title.lower() for cat in ['pokemon', 'cards', 'tcg']):
                    min_similarity = 0.2  # Even lower for trading cards
                elif any(cat in buy_listing.title.lower() for cat in ['ps5', 'xbox', 'nintendo']):
                    min_similarity = 0.3  # Gaming consoles
                elif any(cat in buy_listing.title.lower() for cat in ['jordan', 'nike', 'yeezy']):
                    min_similarity = 0.25  # Sneakers
                
                if similarity < min_similarity:
                    continue
                
                # Check if items are likely the same product
                if not self.are_same_product(buy_listing, sell_listing):
                    continue
                
                # Calculate realistic fees and profit
                gross_profit = sell_listing.price - buy_listing.total_cost
                
                # More realistic fee structure
                ebay_fees = sell_listing.price * 0.087  # 8.7% average eBay fees
                payment_fees = sell_listing.price * 0.029 + 0.30  # 2.9% + $0.30
                
                # Shipping cost if we need to ship
                estimated_shipping = 5.0 if sell_listing.shipping_cost == 0 else 0
                
                total_fees = ebay_fees + payment_fees + estimated_shipping
                net_profit = gross_profit - total_fees
                
                # Check if still profitable
                if net_profit < min_profit:
                    continue
                
                roi = (net_profit / buy_listing.total_cost) * 100 if buy_listing.total_cost > 0 else 0
                
                # Calculate confidence score
                confidence = self.calculate_confidence(buy_listing, sell_listing, similarity, net_profit, roi)
                
                # Determine risk level
                if roi < 20:
                    risk_level = 'LOW'
                elif roi < 50:
                    risk_level = 'MEDIUM'
                else:
                    risk_level = 'HIGH'
                
                opportunity = {
                    'opportunity_id': f"ARB_{int(time.time())}_{random.randint(1000, 9999)}",
                    'buy_listing': asdict(buy_listing),
                    'sell_reference': asdict(sell_listing),
                    'similarity_score': round(similarity, 3),
                    'confidence_score': confidence,
                    'risk_level': risk_level,
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
                            'ebay_fee': round(ebay_fees, 2),
                            'payment_fee': round(payment_fees, 2),
                            'shipping_cost': estimated_shipping
                        }
                    },
                    'created_at': datetime.now().isoformat()
                }
                
                opportunities.append(opportunity)
        
        # Sort by net profit
        opportunities.sort(key=lambda x: x['net_profit_after_fees'], reverse=True)
        
        # Remove similar opportunities
        unique_opportunities = self.remove_duplicate_opportunities(opportunities)
        
        logger.info(f"✅ Found {len(unique_opportunities)} unique arbitrage opportunities")
        return unique_opportunities
    
    def are_same_product(self, listing1: eBayListing, listing2: eBayListing) -> bool:
        """Check if two listings are likely the same product"""
        title1_lower = listing1.title.lower()
        title2_lower = listing2.title.lower()
        
        # Extract key identifiers
        identifiers1 = set()
        identifiers2 = set()
        
        # Model numbers
        model_pattern = r'\b[A-Z0-9]{3,}(?:-[A-Z0-9]+)*\b'
        models1 = re.findall(model_pattern, listing1.title)
        models2 = re.findall(model_pattern, listing2.title)
        
        if models1 and models2:
            common_models = set(models1) & set(models2)
            if common_models:
                return True
        
        # Size/capacity matching
        size_pattern = r'\b\d+(?:gb|tb|mm|ml|oz|inch|")\b'
        sizes1 = re.findall(size_pattern, title1_lower)
        sizes2 = re.findall(size_pattern, title2_lower)
        
        if sizes1 and sizes2 and set(sizes1) != set(sizes2):
            return False  # Different sizes = different products
        
        # Generation/version matching
        gen_pattern = r'\b(?:gen|generation|version|v)\s*(\d+)\b'
        gen1 = re.findall(gen_pattern, title1_lower)
        gen2 = re.findall(gen_pattern, title2_lower)
        
        if gen1 and gen2 and gen1 != gen2:
            return False  # Different generations
        
        # Color matching for fashion items
        if any(fashion in title1_lower for fashion in ['jordan', 'nike', 'shoe', 'sneaker']):
            colors = ['black', 'white', 'red', 'blue', 'green', 'grey', 'gray', 'yellow', 'purple', 'pink', 'orange']
            colors1 = [c for c in colors if c in title1_lower]
            colors2 = [c for c in colors if c in title2_lower]
            
            if colors1 and colors2 and set(colors1) != set(colors2):
                return False  # Different colors
        
        # Pokemon card specific
        if 'pokemon' in title1_lower and 'pokemon' in title2_lower:
            # Check for same pokemon
            pokemon_names = ['charizard', 'pikachu', 'blastoise', 'venusaur', 'mewtwo', 'mew']
            poke1 = [p for p in pokemon_names if p in title1_lower]
            poke2 = [p for p in pokemon_names if p in title2_lower]
            
            if poke1 and poke2 and poke1 != poke2:
                return False
        
        return True
    
    def calculate_confidence(self, buy_listing: eBayListing, sell_listing: eBayListing, 
                           similarity: float, net_profit: float, roi: float) -> int:
        """Calculate confidence score for arbitrage opportunity"""
        confidence = 50  # Base confidence
        
        # Similarity boost
        if similarity > 0.7:
            confidence += 20
        elif similarity > 0.5:
            confidence += 15
        elif similarity > 0.3:
            confidence += 10
        else:
            confidence += 5
        
        # Profit boost
        if net_profit >= 50:
            confidence += 15
        elif net_profit >= 30:
            confidence += 10
        elif net_profit >= 20:
            confidence += 5
        
        # ROI boost
        if roi >= 40:
            confidence += 10
        elif roi >= 25:
            confidence += 5
        
        # Condition boost
        buy_condition_lower = buy_listing.condition.lower()
        if any(good in buy_condition_lower for good in ['new', 'sealed', 'mint']):
            confidence += 10
        elif any(good in buy_condition_lower for good in ['like new', 'excellent']):
            confidence += 5
        
        # Seller rating boost
        try:
            if buy_listing.seller_rating != "Not available":
                rating = float(buy_listing.seller_rating.rstrip('%'))
                if rating >= 99:
                    confidence += 10
                elif rating >= 98:
                    confidence += 5
        except:
            pass
        
        # Price difference boost
        price_ratio = sell_listing.total_cost / buy_listing.total_cost if buy_listing.total_cost > 0 else 1
        if price_ratio >= 1.5:  # 50% or more price difference
            confidence += 10
        elif price_ratio >= 1.3:
            confidence += 5
        
        return min(confidence, 95)  # Cap at 95%
    
    def remove_duplicate_opportunities(self, opportunities: List[Dict]) -> List[Dict]:
        """Remove duplicate arbitrage opportunities"""
        unique_opportunities = []
        seen_combinations = set()
        
        for opp in opportunities:
            # Create a unique identifier for the opportunity
            buy_title = opp['buy_listing']['title'].lower()
            sell_title = opp['sell_reference']['title'].lower()
            
            # Normalize titles for comparison
            buy_normalized = self.normalize_title(buy_title)
            sell_normalized = self.normalize_title(sell_title)
            
            # Create combination key
            combo_key = tuple(sorted([buy_normalized[:50], sell_normalized[:50]]))
            
            if combo_key not in seen_combinations:
                seen_combinations.add(combo_key)
                unique_opportunities.append(opp)
        
        return unique_opportunities

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
    """Find real arbitrage opportunities with better detection"""
    try:
        start_time = datetime.now()
        
        # Clear previous search data
        scraper.seen_items.clear()
        scraper.seen_titles.clear()
        
        # Determine category for better search
        keyword_lower = keyword.lower()
        search_limit = limit * 3  # Get more listings to find better matches
        
        # Get real listings
        listings = scraper.search_ebay(keyword, search_limit, "price")
        
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
                'total_searches_performed': len(scraper.expand_search_keywords(keyword)),
                'total_listings_analyzed': len(listings),
                'arbitrage_opportunities_found': total_opportunities,
                'scan_efficiency': round((total_opportunities / max(len(listings), 1)) * 100, 2),
                'keywords_used': scraper.expand_search_keywords(keyword),
                'unique_products_found': len(listings),
                'search_term': keyword
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
            'top_opportunities': opportunities[:limit]  # Return requested number
        }
        
    except Exception as e:
        logger.error(f"Arbitrage analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            'scan_metadata': {'error': str(e)},
            'opportunities_summary': {'total_opportunities': 0},
            'top_opportunities': []
        }

# Test function
def test_scraper():
    """Test the scraper with various categories"""
    print("🚀 Testing Fixed FlipHawk Scraper...")
    
    test_keywords = [
        ("airpods pro", 10),
        ("nintendo switch oled", 10),
        ("pokemon cards", 10),
        ("air jordan 1", 10)
    ]
    
    for keyword, min_profit in test_keywords:
        print(f"\n{'='*60}")
        print(f"Testing: {keyword} (min profit: ${min_profit})")
        
        try:
            results = find_arbitrage_real(keyword, min_profit=min_profit, limit=5)
            
            print(f"✅ Found {results['opportunities_summary']['total_opportunities']} opportunities")
            print(f"📊 Avg profit: ${results['opportunities_summary']['average_profit_after_fees']:.2f}")
            print(f"📈 Avg ROI: {results['opportunities_summary']['average_roi']:.1f}%")
            
            if results['top_opportunities']:
                opp = results['top_opportunities'][0]
                print(f"\n💎 Best opportunity:")
                print(f"   Buy: ${opp['buy_listing']['total_cost']:.2f} - {opp['buy_listing']['title'][:50]}...")
                print(f"   Sell: ${opp['sell_reference']['price']:.2f}")
                print(f"   Net Profit: ${opp['net_profit_after_fees']:.2f} ({opp['roi_percentage']:.1f}% ROI)")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n{'='*60}")
    print("✅ Test completed!")

if __name__ == "__main__":
    test_scraper()
