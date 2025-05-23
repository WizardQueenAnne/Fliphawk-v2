"""
Enhanced FlipHawk eBay Arbitrage Scanner - True Price Comparison
Finds the same products at different prices for real arbitrage opportunities
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
    category: str
    subcategory: str
    matched_keyword: str
    listing_date: str
    location: str
    sold_count: str
    availability: str
    # New fields for product matching
    normalized_title: str
    product_identifier: str
    brand: str
    model: str
    key_features: Set[str]

@dataclass
class ArbitrageOpportunity:
    """Represents a true arbitrage opportunity between two listings"""
    lower_listing: eBayListing
    higher_listing: eBayListing
    profit_before_fees: float
    profit_after_fees: float
    roi_percentage: float
    confidence_score: int
    similarity_score: float
    risk_level: str
    opportunity_id: str
    created_at: str

class ProductMatcher:
    """Matches similar products across different listings"""
    
    def __init__(self):
        self.brand_patterns = {
            'apple': ['apple', 'iphone', 'ipad', 'macbook', 'airpods', 'imac'],
            'samsung': ['samsung', 'galaxy'],
            'nintendo': ['nintendo', 'switch', 'mario', 'zelda'],
            'sony': ['sony', 'playstation', 'ps5', 'ps4'],
            'microsoft': ['microsoft', 'xbox', 'surface'],
            'pokemon': ['pokemon', 'pikachu', 'charizard'],
            'nike': ['nike', 'jordan', 'air force'],
            'adidas': ['adidas', 'yeezy', 'ultraboost'],
            'beats': ['beats', 'dr dre', 'dre'],
            'bose': ['bose', 'quietcomfort'],
        }
        
        self.model_extractors = [
            r'(iphone\s*(?:1[0-5]|[4-9])(?:\s*pro(?:\s*max)?)?)',
            r'(galaxy\s*s\d+(?:\s*ultra)?)',
            r'(macbook\s*(?:pro|air)?)',
            r'(ps[45]|playstation\s*[45])',
            r'(xbox\s*(?:series\s*[xs]|one))',
            r'(airpods\s*(?:pro|max)?)',
            r'(switch\s*(?:oled|lite)?)',
            r'(jordan\s*\d+)',
            r'(charizard|pikachu|mewtwo)',
        ]
        
        self.condition_normalizers = {
            'brand new': 'new',
            'new with tags': 'new',
            'new in box': 'new',
            'new other': 'new',
            'like new': 'excellent',
            'very good': 'very good',
            'good': 'good',
            'acceptable': 'fair',
            'for parts': 'parts'
        }
    
    def normalize_title(self, title: str) -> str:
        """Normalize title for comparison"""
        # Convert to lowercase
        normalized = title.lower()
        
        # Remove common eBay noise words
        noise_words = [
            'new listing', 'l@@k', 'wow', 'rare find', 'must see', 'nr', 'no reserve',
            'look', 'check out', 'amazing', 'awesome', 'incredible', 'free shipping',
            'fast shipping', 'brand new', 'sealed', 'mint', 'excellent', 'perfect'
        ]
        
        for noise in noise_words:
            normalized = re.sub(r'\b' + re.escape(noise) + r'\b', '', normalized)
        
        # Remove special characters and extra spaces
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized.strip()
    
    def extract_brand(self, title: str) -> str:
        """Extract brand from title"""
        title_lower = title.lower()
        
        for brand, patterns in self.brand_patterns.items():
            for pattern in patterns:
                if pattern in title_lower:
                    return brand
        
        return 'unknown'
    
    def extract_model(self, title: str) -> str:
        """Extract model information from title"""
        title_lower = title.lower()
        
        for pattern in self.model_extractors:
            match = re.search(pattern, title_lower)
            if match:
                return match.group(1)
        
        return 'unknown'
    
    def extract_key_features(self, title: str) -> Set[str]:
        """Extract key features that help identify the same product"""
        title_lower = title.lower()
        features = set()
        
        # Storage capacities
        storage_patterns = [r'(\d+\s*(?:gb|tb))', r'(\d+\s*gig)', r'(\d+\s*terabyte)']
        for pattern in storage_patterns:
            matches = re.findall(pattern, title_lower)
            features.update(matches)
        
        # Colors
        colors = ['black', 'white', 'blue', 'red', 'green', 'yellow', 'purple', 'pink', 'gray', 'grey', 'silver', 'gold', 'rose', 'space']
        for color in colors:
            if color in title_lower:
                features.add(color)
        
        # Sizes
        size_patterns = [r'(size\s*\d+)', r'(\d+\s*inch)', r'(\d+\.\d+\s*inch)', r'(small|medium|large|xl|xxl)']
        for pattern in size_patterns:
            matches = re.findall(pattern, title_lower)
            features.update(matches)
        
        # Generations/Versions
        gen_patterns = [r'(gen\s*\d+)', r'(generation\s*\d+)', r'(\d+(?:st|nd|rd|th)\s*gen)', r'(v\d+)', r'(version\s*\d+)']
        for pattern in gen_patterns:
            matches = re.findall(pattern, title_lower)
            features.update(matches)
        
        return features
    
    def generate_product_identifier(self, listing: eBayListing) -> str:
        """Generate a unique identifier for similar products"""
        components = [
            listing.brand,
            listing.model,
            listing.category,
            listing.subcategory
        ]
        
        # Add key features (sorted for consistency)
        sorted_features = sorted(list(listing.key_features))
        components.extend(sorted_features[:3])  # Top 3 features
        
        # Create hash from components
        identifier_string = '|'.join(str(c) for c in components if c and c != 'unknown')
        return hashlib.md5(identifier_string.encode()).hexdigest()[:12]
    
    def calculate_similarity(self, listing1: eBayListing, listing2: eBayListing) -> float:
        """Calculate similarity score between two listings (0-1)"""
        scores = []
        
        # Brand match (high weight)
        if listing1.brand == listing2.brand and listing1.brand != 'unknown':
            scores.append(0.4)
        elif listing1.brand != 'unknown' and listing2.brand != 'unknown':
            scores.append(0.0)
        else:
            scores.append(0.1)  # Unknown brands get neutral score
        
        # Model match (high weight)
        if listing1.model == listing2.model and listing1.model != 'unknown':
            scores.append(0.3)
        elif listing1.model != 'unknown' and listing2.model != 'unknown':
            scores.append(0.0)
        else:
            scores.append(0.1)
        
        # Title similarity using sequence matcher
        title_similarity = difflib.SequenceMatcher(
            None, listing1.normalized_title, listing2.normalized_title
        ).ratio()
        scores.append(title_similarity * 0.2)
        
        # Feature overlap
        common_features = listing1.key_features.intersection(listing2.key_features)
        total_features = listing1.key_features.union(listing2.key_features)
        
        if total_features:
            feature_similarity = len(common_features) / len(total_features)
            scores.append(feature_similarity * 0.1)
        else:
            scores.append(0.05)
        
        return sum(scores)
    
    def is_same_product(self, listing1: eBayListing, listing2: eBayListing, 
                       similarity_threshold: float = 0.7) -> bool:
        """Determine if two listings are for the same product"""
        similarity = self.calculate_similarity(listing1, listing2)
        return similarity >= similarity_threshold

class EnhancedArbitrageScanner:
    """Enhanced scanner that finds true arbitrage opportunities"""
    
    def __init__(self):
        self.base_url = "https://www.ebay.com/sch/i.html"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        self.seen_items = set()
        self.product_matcher = ProductMatcher()
        self.session_stats = {
            'total_searches': 0,
            'total_listings_found': 0,
            'arbitrage_opportunities': 0,
            'start_time': datetime.now(),
        }
        
        # Fee structure for profit calculations
        self.ebay_fees = {
            'final_value_fee': 0.129,  # 12.9% average
            'payment_processing': 0.029,  # 2.9%
            'insertion_fee': 0.35,  # Per listing
        }
        
        self.tax_rate = 0.08  # 8% average sales tax
    
    def build_comprehensive_search_url(self, keyword: str, page: int = 1, 
                                     sort_order: str = "price") -> str:
        """Build eBay search URL for comprehensive scanning"""
        params = {
            '_nkw': keyword,
            '_pgn': page,
            'LH_BIN': 1,  # Buy It Now only
            'LH_Complete': 0,  # Active listings
            'LH_Sold': 0,  # Not sold
            '_sop': {
                'price': 15,  # Price + shipping: lowest first
                'price_desc': 16,  # Price + shipping: highest first
                'newest': 10,  # Time: newly listed
                'ending': 1,   # Time: ending soonest
            }.get(sort_order, 15),
            '_ipg': 240,  # Items per page (max)
            'rt': 'nc',   # No categories redirect
            '_sacat': 0,  # All categories
        }
        
        query_string = urllib.parse.urlencode(params)
        return f"{self.base_url}?{query_string}"
    
    def fetch_page_with_retry(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """Robust page fetching with retry logic"""
        for attempt in range(retries):
            try:
                # Rotate User-Agent to avoid blocking
                user_agents = [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
                ]
                
                headers = self.headers.copy()
                headers['User-Agent'] = random.choice(user_agents)
                
                # Random delay to appear more human
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
                logger.warning(f"Error on attempt {attempt + 1} for {url}: {e}")
                if attempt < retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(1, 3)
                    time.sleep(wait_time)
                    
        return None
    
    def extract_listing_data(self, item_soup: BeautifulSoup, category: str, 
                           subcategory: str, matched_keyword: str) -> Optional[eBayListing]:
        """Extract comprehensive listing data"""
        try:
            # Title extraction with multiple selectors
            title_selectors = [
                'h3.s-item__title', '.s-item__title', 'h3[role="heading"]',
                '.it-ttl a', '.s-item__title-text'
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
                'Shop on eBay', 'SPONSORED', 'See more like this', 'Advertisement'
            ]):
                return None
            
            # Price extraction
            price_selectors = [
                '.s-item__price .notranslate', '.s-item__price', '.adp-price .notranslate'
            ]
            
            price = 0.0
            for selector in price_selectors:
                price_elem = item_soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
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
            
            if price <= 0 or price > 10000:
                return None
            
            # Shipping cost extraction
            shipping_cost = 0.0
            shipping_selectors = ['.s-item__shipping', '.s-item__logisticsCost']
            
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
            
            # Link extraction
            link_selectors = ['.s-item__link', '.it-ttl a', '.s-item__title a']
            
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
            item_id = None
            for pattern in [r'/(\d{12,})', r'itm/(\d+)', r'item/(\d+)']:
                match = re.search(pattern, ebay_link)
                if match:
                    item_id = match.group(1)
                    break
            
            if not item_id:
                item_id = str(abs(hash(title + str(price))))[:12]
            
            # Prevent duplicates
            if item_id in self.seen_items:
                return None
            self.seen_items.add(item_id)
            
            # Image extraction
            image_url = ""
            img_elem = item_soup.select_one('.s-item__image img')
            if img_elem:
                image_url = img_elem.get('src', '') or img_elem.get('data-src', '')
                if image_url:
                    image_url = image_url.replace('s-l64', 's-l500')
                    if not image_url.startswith('http'):
                        image_url = 'https:' + image_url if image_url.startswith('//') else image_url
            
            # Condition extraction
            condition = "Unknown"
            condition_elem = item_soup.select_one('.SECONDARY_INFO, .s-item__subtitle')
            if condition_elem:
                condition_text = condition_elem.get_text(strip=True)
                condition_keywords = [
                    'new', 'brand new', 'used', 'pre-owned', 'like new', 
                    'very good', 'excellent', 'good', 'fair', 'acceptable'
                ]
                if any(word in condition_text.lower() for word in condition_keywords):
                    condition = condition_text
            
            # Seller information
            seller_rating = "Not available"
            feedback_count = "Not available"
            
            seller_elem = item_soup.select_one('.s-item__seller-info-text')
            if seller_elem:
                seller_text = seller_elem.get_text(strip=True)
                rating_match = re.search(r'([\d.]+)%', seller_text)
                if rating_match:
                    seller_rating = f"{rating_match.group(1)}%"
                
                count_match = re.search(r'\(([\d,]+)\)', seller_text)
                if count_match:
                    feedback_count = count_match.group(1).replace(',', '')
            
            # Location
            location = "Unknown"
            location_elem = item_soup.select_one('.s-item__location')
            if location_elem:
                location_text = location_elem.get_text(strip=True)
                if 'from' in location_text.lower():
                    location = location_text.replace('From', '').replace('from', '').strip()
                else:
                    location = location_text
            
            # Sold count
            sold_count = "0"
            sold_elem = item_soup.select_one('.s-item__quantitySold')
            if sold_elem:
                sold_text = sold_elem.get_text(strip=True)
                sold_match = re.search(r'(\d+)', sold_text)
                if sold_match:
                    sold_count = sold_match.group(1)
            
            # Create listing object
            listing = eBayListing(
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
                category=category,
                subcategory=subcategory,
                matched_keyword=matched_keyword,
                listing_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                location=location,
                sold_count=sold_count,
                availability="Available",
                normalized_title="",
                product_identifier="",
                brand="",
                model="",
                key_features=set()
            )
            
            # Enhanced product matching data
            listing.normalized_title = self.product_matcher.normalize_title(title)
            listing.brand = self.product_matcher.extract_brand(title)
            listing.model = self.product_matcher.extract_model(title)
            listing.key_features = self.product_matcher.extract_key_features(title)
            listing.product_identifier = self.product_matcher.generate_product_identifier(listing)
            
            return listing
            
        except Exception as e:
            logger.error(f"Error extracting listing data: {e}")
            return None
    
    def calculate_fees_and_profit(self, buy_price: float, sell_price: float, 
                                shipping_cost: float = 0) -> Dict[str, float]:
        """Calculate actual profit after all fees and taxes"""
        # eBay fees
        final_value_fee = sell_price * self.ebay_fees['final_value_fee']
        payment_fee = sell_price * self.ebay_fees['payment_processing']
        insertion_fee = self.ebay_fees['insertion_fee']
        
        # Total eBay fees
        total_ebay_fees = final_value_fee + payment_fee + insertion_fee
        
        # Sales tax (on selling price)
        sales_tax = sell_price * self.tax_rate
        
        # Total costs
        total_cost = buy_price + shipping_cost + total_ebay_fees + sales_tax
        
        # Profit calculations
        gross_profit = sell_price - buy_price - shipping_cost
        net_profit = sell_price - total_cost
        
        # ROI calculation
        roi = (net_profit / total_cost) * 100 if total_cost > 0 else 0
        
        return {
            'gross_profit': gross_profit,
            'net_profit': net_profit,
            'total_fees': total_ebay_fees + sales_tax,
            'ebay_fees': total_ebay_fees,
            'sales_tax': sales_tax,
            'roi_percentage': roi,
            'total_cost': total_cost
        }
    
    def comprehensive_scan(self, keywords: str, categories: List[str], 
                         max_pages_per_sort: int = 3, min_profit: float = 15.0) -> List[eBayListing]:
        """Comprehensive scan with multiple sort orders to get all listings"""
        logger.info(f"🔍 Starting comprehensive scan for: '{keywords}'")
        
        all_listings = []
        search_keywords = [kw.strip() for kw in keywords.split(',') if kw.strip()]
        
        # Multiple sort orders to capture different listings
        sort_orders = ['price', 'price_desc', 'newest']
        
        for category in categories[:3]:  # Limit categories for performance
            for keyword in search_keywords[:5]:  # Limit keywords
                for sort_order in sort_orders:
                    try:
                        logger.info(f"Scanning '{keyword}' in {category} (sorted by {sort_order})")
                        
                        for page in range(1, max_pages_per_sort + 1):
                            url = self.build_comprehensive_search_url(keyword, page, sort_order)
                            soup = self.fetch_page_with_retry(url)
                            
                            if not soup:
                                logger.warning(f"Failed to fetch page {page}")
                                break
                            
                            items = soup.select('.s-item__wrapper, .s-item')
                            if not items:
                                logger.warning(f"No items found on page {page}")
                                break
                            
                            self.session_stats['total_searches'] += 1
                            self.session_stats['total_listings_found'] += len(items)
                            
                            page_listings = 0
                            for item in items:
                                listing = self.extract_listing_data(item, category, 'General', keyword)
                                if listing:
                                    all_listings.append(listing)
                                    page_listings += 1
                            
                            logger.info(f"Page {page}: {page_listings} listings extracted")
                            
                            # Rate limiting
                            time.sleep(random.uniform(1.5, 3.0))
                        
                        # Delay between sort orders
                        time.sleep(random.uniform(2.0, 4.0))
                        
                    except Exception as e:
                        logger.error(f"Error scanning {keyword} in {category}: {e}")
                        continue
        
        logger.info(f"✅ Comprehensive scan complete: {len(all_listings)} total listings")
        return all_listings
    
    def find_arbitrage_opportunities(self, listings: List[eBayListing], 
                                   min_profit: float = 15.0) -> List[ArbitrageOpportunity]:
        """Find true arbitrage opportunities by comparing similar products"""
        logger.info(f"🔎 Analyzing {len(listings)} listings for arbitrage opportunities...")
        
        opportunities = []
        
        # Group listings by product identifier for faster comparison
        product_groups = defaultdict(list)
        for listing in listings:
            product_groups[listing.product_identifier].append(listing)
        
        logger.info(f"📊 Found {len(product_groups)} unique product groups")
        
        # Find arbitrage opportunities within each product group
        for product_id, group_listings in product_groups.items():
            if len(group_listings) < 2:
                continue
            
            # Sort by total cost for efficient comparison
            group_listings.sort(key=lambda x: x.total_cost)
            
            for i in range(len(group_listings)):
                for j in range(i + 1, len(group_listings)):
                    lower_listing = group_listings[i]
                    higher_listing = group_listings[j]
                    
                    # Verify they're actually the same product
                    if not self.product_matcher.is_same_product(lower_listing, higher_listing):
                        continue
                    
                    # Skip if same seller (can't arbitrage from yourself)
                    if lower_listing.seller_rating == higher_listing.seller_rating:
                        continue
                    
                    # Calculate profit potential
                    profit_calc = self.calculate_fees_and_profit(
                        lower_listing.total_cost,
                        higher_listing.price,  # Sell at the higher price
                        0  # We're not shipping, buyer pays
                    )
                    
                    # Check if profitable
                    if profit_calc['net_profit'] >= min_profit:
                        # Calculate confidence score
                        confidence = self.calculate_arbitrage_confidence(
                            lower_listing, higher_listing, profit_calc
                        )
                        
                        # Determine risk level
                        risk_level = self.assess_risk_level(lower_listing, higher_listing, profit_calc)
                        
                        # Calculate similarity score
                        similarity = self.product_matcher.calculate_similarity(
                            lower_listing, higher_listing
                        )
                        
                        opportunity = ArbitrageOpportunity(
                            lower_listing=lower_listing,
                            higher_listing=higher_listing,
                            profit_before_fees=profit_calc['gross_profit'],
                            profit_after_fees=profit_calc['net_profit'],
                            roi_percentage=profit_calc['roi_percentage'],
                            confidence_score=confidence,
                            similarity_score=similarity,
                            risk_level=risk_level,
                            opportunity_id=f"ARB_{int(time.time())}_{random.randint(1000, 9999)}",
                            created_at=datetime.now().isoformat()
                        )
                        
                        opportunities.append(opportunity)
        
        # Sort by profit and remove duplicates
        opportunities.sort(key=lambda x: x.profit_after_fees, reverse=True)
        
        # Remove very similar opportunities (same product, similar prices)
        filtered_opportunities = []
        seen_combinations = set()
        
        for opp in opportunities:
            key = f"{opp.lower_listing.product_identifier}_{int(opp.lower_listing.total_cost)}_{int(opp.higher_listing.price)}"
            if key not in seen_combinations:
                seen_combinations.add(key)
                filtered_opportunities.append(opp)
        
        self.session_stats['arbitrage_opportunities'] = len(filtered_opportunities)
        
        logger.info(f"🎯 Found {len(filtered_opportunities)} unique arbitrage opportunities")
        return filtered_opportunities
    
    def calculate_arbitrage_confidence(self, lower_listing: eBayListing, 
                                     higher_listing: eBayListing, 
                                     profit_calc: Dict[str, float]) -> int:
        """Calculate confidence score for arbitrage opportunity (0-100)"""
        score = 50  # Base score
        
        # Product similarity bonus
        similarity = self.product_matcher.calculate_similarity(lower_listing, higher_listing)
        score += int(similarity * 30)  # Up to 30 points
        
        # Profit margin bonus
        if profit_calc['roi_percentage'] >= 50:
            score += 15
        elif profit_calc['roi_percentage'] >= 30:
            score += 10
        elif profit_calc['roi_percentage'] >= 20:
            score += 5
        
        # Seller reliability (lower listing - we're buying from them)
        try:
            if '%' in lower_listing.seller_rating:
                rating = float(re.search(r'([\d.]+)', lower_listing.seller_rating).group(1))
                if rating >= 99:
                    score += 10
                elif rating >= 95:
                    score += 5
                elif rating < 90:
                    score -= 10
        except:
            score -= 5
        
        # Feedback count reliability
        try:
            if lower_listing.seller_feedback_count != "Not available":
                count = int(lower_listing.seller_feedback_count.replace(',', ''))
                if count >= 1000:
                    score += 10
                elif count >= 100:
                    score += 5
                elif count < 10:
                    score -= 15
        except:
            score -= 5
        
        # Condition bonus (better condition = higher confidence)
        condition_lower = lower_listing.condition.lower()
        if 'new' in condition_lower or 'mint' in condition_lower:
            score += 10
        elif 'very good' in condition_lower or 'excellent' in condition_lower:
            score += 5
        elif 'good' in condition_lower:
            score += 2
        elif 'fair' in condition_lower or 'acceptable' in condition_lower:
            score -= 5
        
        # Price difference validation (too good to be true penalty)
        price_diff_ratio = (higher_listing.price - lower_listing.total_cost) / lower_listing.total_cost
        if price_diff_ratio > 2.0:  # More than 200% markup seems suspicious
            score -= 20
        elif price_diff_ratio > 1.0:  # More than 100% markup
            score -= 10
        
        # Location bonus (domestic is safer)
        if 'usa' in lower_listing.location.lower() or 'united states' in lower_listing.location.lower():
            score += 5
        elif lower_listing.location == "Unknown":
            score -= 5
        
        return max(0, min(100, score))
    
    def assess_risk_level(self, lower_listing: eBayListing, higher_listing: eBayListing, 
                         profit_calc: Dict[str, float]) -> str:
        """Assess risk level of arbitrage opportunity"""
        risk_factors = 0
        
        # High profit = higher risk
        if profit_calc['roi_percentage'] > 100:
            risk_factors += 2
        elif profit_calc['roi_percentage'] > 50:
            risk_factors += 1
        
        # Low seller rating = higher risk
        try:
            if '%' in lower_listing.seller_rating:
                rating = float(re.search(r'([\d.]+)', lower_listing.seller_rating).group(1))
                if rating < 95:
                    risk_factors += 1
                if rating < 90:
                    risk_factors += 1
        except:
            risk_factors += 1
        
        # Low feedback count = higher risk
        try:
            if lower_listing.seller_feedback_count != "Not available":
                count = int(lower_listing.seller_feedback_count.replace(',', ''))
                if count < 100:
                    risk_factors += 1
                if count < 10:
                    risk_factors += 1
        except:
            risk_factors += 1
        
        # International shipping = higher risk
        if 'china' in lower_listing.location.lower() or 'hong kong' in lower_listing.location.lower():
            risk_factors += 1
        
        # Condition risk
        condition_lower = lower_listing.condition.lower()
        if 'parts' in condition_lower or 'broken' in condition_lower:
            risk_factors += 2
        elif 'fair' in condition_lower or 'acceptable' in condition_lower:
            risk_factors += 1
        
        if risk_factors >= 4:
            return 'HIGH'
        elif risk_factors >= 2:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def scan_arbitrage_opportunities(self, keywords: str, categories: List[str], 
                                   min_profit: float = 15.0, max_results: int = 25) -> Dict:
        """Main function to scan for arbitrage opportunities"""
        start_time = datetime.now()
        
        # Reset session stats
        self.session_stats = {
            'total_searches': 0,
            'total_listings_found': 0,
            'arbitrage_opportunities': 0,
            'start_time': start_time,
        }
        
        # Step 1: Comprehensive scan
        all_listings = self.comprehensive_scan(keywords, categories, max_pages_per_sort=4)
        
        if not all_listings:
            return self.create_empty_result(start_time)
        
        # Step 2: Find arbitrage opportunities
        opportunities = self.find_arbitrage_opportunities(all_listings, min_profit)
        
        # Step 3: Format results
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Limit results
        top_opportunities = opportunities[:max_results]
        
        return {
            'scan_metadata': {
                'scan_id': hashlib.md5(str(start_time).encode()).hexdigest()[:8],
                'timestamp': end_time.isoformat(),
                'duration_seconds': round(duration, 2),
                'total_searches_performed': self.session_stats['total_searches'],
                'total_listings_analyzed': self.session_stats['total_listings_found'],
                'arbitrage_opportunities_found': len(opportunities),
                'scan_efficiency': round((len(opportunities) / max(len(all_listings), 1)) * 100, 2),
                'keywords_used': keywords.split(','),
                'unique_products_found': len(set(listing.product_identifier for listing in all_listings))
            },
            'opportunities_summary': {
                'total_opportunities': len(top_opportunities),
                'average_profit_after_fees': round(
                    sum(op.profit_after_fees for op in top_opportunities) / 
                    len(top_opportunities), 2
                ) if top_opportunities else 0,
                'average_roi': round(
                    sum(op.roi_percentage for op in top_opportunities) / 
                    len(top_opportunities), 1
                ) if top_opportunities else 0,
                'average_confidence': round(
                    sum(op.confidence_score for op in top_opportunities) / 
                    len(top_opportunities), 1
                ) if top_opportunities else 0,
                'highest_profit': max(
                    (op.profit_after_fees for op in top_opportunities), default=0
                ),
                'risk_distribution': {
                    'low': len([op for op in top_opportunities if op.risk_level == 'LOW']),
                    'medium': len([op for op in top_opportunities if op.risk_level == 'MEDIUM']),
                    'high': len([op for op in top_opportunities if op.risk_level == 'HIGH'])
                },
                'profit_ranges': {
                    'under_25': len([op for op in top_opportunities if op.profit_after_fees < 25]),
                    '25_to_50': len([op for op in top_opportunities if 25 <= op.profit_after_fees < 50]),
                    '50_to_100': len([op for op in top_opportunities if 50 <= op.profit_after_fees < 100]),
                    'over_100': len([op for op in top_opportunities if op.profit_after_fees >= 100])
                }
            },
            'top_opportunities': [self.format_opportunity_for_api(op) for op in top_opportunities]
        }
    
    def format_opportunity_for_api(self, opportunity: ArbitrageOpportunity) -> Dict:
        """Format arbitrage opportunity for API response"""
        return {
            'opportunity_id': opportunity.opportunity_id,
            'similarity_score': round(opportunity.similarity_score, 3),
            'confidence_score': opportunity.confidence_score,
            'risk_level': opportunity.risk_level,
            'profit_analysis': {
                'gross_profit': round(opportunity.profit_before_fees, 2),
                'net_profit_after_fees': round(opportunity.profit_after_fees, 2),
                'roi_percentage': round(opportunity.roi_percentage, 1),
                'estimated_fees': round(opportunity.profit_before_fees - opportunity.profit_after_fees, 2)
            },
            'buy_listing': {
                'title': opportunity.lower_listing.title,
                'price': round(opportunity.lower_listing.price, 2),
                'shipping_cost': round(opportunity.lower_listing.shipping_cost, 2),
                'total_cost': round(opportunity.lower_listing.total_cost, 2),
                'condition': opportunity.lower_listing.condition,
                'seller_rating': opportunity.lower_listing.seller_rating,
                'seller_feedback': opportunity.lower_listing.seller_feedback_count,
                'location': opportunity.lower_listing.location,
                'image_url': opportunity.lower_listing.image_url,
                'ebay_link': opportunity.lower_listing.ebay_link,
                'item_id': opportunity.lower_listing.item_id
            },
            'sell_reference': {
                'title': opportunity.higher_listing.title,
                'price': round(opportunity.higher_listing.price, 2),
                'shipping_cost': round(opportunity.higher_listing.shipping_cost, 2),
                'total_cost': round(opportunity.higher_listing.total_cost, 2),
                'condition': opportunity.higher_listing.condition,
                'seller_rating': opportunity.higher_listing.seller_rating,
                'seller_feedback': opportunity.higher_listing.seller_feedback_count,
                'location': opportunity.higher_listing.location,
                'image_url': opportunity.higher_listing.image_url,
                'ebay_link': opportunity.higher_listing.ebay_link,
                'item_id': opportunity.higher_listing.item_id
            },
            'product_info': {
                'brand': opportunity.lower_listing.brand,
                'model': opportunity.lower_listing.model,
                'category': opportunity.lower_listing.category,
                'subcategory': opportunity.lower_listing.subcategory,
                'key_features': list(opportunity.lower_listing.key_features),
                'product_identifier': opportunity.lower_listing.product_identifier
            },
            'created_at': opportunity.created_at
        }
    
    def create_empty_result(self, start_time: datetime) -> Dict:
        """Create empty result structure when no opportunities found"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return {
            'scan_metadata': {
                'scan_id': hashlib.md5(str(start_time).encode()).hexdigest()[:8],
                'timestamp': end_time.isoformat(),
                'duration_seconds': round(duration, 2),
                'total_searches_performed': self.session_stats['total_searches'],
                'total_listings_analyzed': self.session_stats['total_listings_found'],
                'arbitrage_opportunities_found': 0,
                'scan_efficiency': 0.0,
                'keywords_used': [],
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


# Flask Integration Functions
def create_arbitrage_api_endpoints(scanner: EnhancedArbitrageScanner):
    """Create Flask-compatible API endpoint functions"""
    
    def scan_arbitrage_opportunities(request_data: Dict) -> Dict:
        """Main arbitrage scanning endpoint"""
        try:
            keywords = request_data.get('keywords', '')
            categories = request_data.get('categories', ['Tech', 'Gaming', 'Collectibles'])
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
    
    def quick_arbitrage_scan() -> Dict:
        """Quick scan with popular items"""
        try:
            trending_keywords = "airpods pro, nintendo switch, pokemon cards"
            
            results = scanner.scan_arbitrage_opportunities(
                keywords=trending_keywords,
                categories=['Tech', 'Gaming', 'Collectibles'],
                min_profit=20.0,
                max_results=15
            )
            
            return {
                'status': 'success',
                'data': results,
                'message': f'Quick scan found {results["opportunities_summary"]["total_opportunities"]} opportunities'
            }
            
        except Exception as e:
            logger.error(f"Quick arbitrage scan failed: {e}")
            return {
                'status': 'error',
                'message': f'Quick scan failed: {str(e)}',
                'data': None
            }
    
    def get_categories_endpoint() -> Dict:
        """Get available categories"""
        try:
            categories_data = {
                "Tech": {
                    'subcategories': ['Headphones', 'Smartphones', 'Laptops', 'Graphics Cards', 'Tablets'],
                    'description': 'Technology products and electronics'
                },
                "Gaming": {
                    'subcategories': ['Consoles', 'Video Games', 'Gaming Accessories'],
                    'description': 'Gaming consoles, games, and accessories'
                },
                "Collectibles": {
                    'subcategories': ['Trading Cards', 'Action Figures', 'Coins'],
                    'description': 'Collectible items and memorabilia'
                },
                "Fashion": {
                    'subcategories': ['Sneakers', 'Designer Clothing', 'Vintage Clothing'],
                    'description': 'Fashion items and streetwear'
                }
            }
            
            return {
                'status': 'success',
                'data': categories_data,
                'message': 'Categories retrieved successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to get categories: {e}")
            return {
                'status': 'error',
                'message': f'Failed to get categories: {str(e)}',
                'data': None
            }
    
    def get_session_stats_endpoint() -> Dict:
        """Get current session statistics"""
        try:
            stats = scanner.session_stats.copy()
            stats['uptime_seconds'] = (datetime.now() - stats['start_time']).total_seconds()
            
            return {
                'status': 'success',
                'data': stats,
                'message': 'Session stats retrieved successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {
                'status': 'error',
                'message': f'Failed to get session stats: {str(e)}',
                'data': None
            }
    
    return {
        'scan_arbitrage': scan_arbitrage_opportunities,
        'quick_scan': quick_arbitrage_scan,
        'get_categories': get_categories_endpoint,
        'get_session_stats': get_session_stats_endpoint
    }


# Demo function
def demo_arbitrage_scanner():
    """Demo the arbitrage scanner functionality"""
    scanner = EnhancedArbitrageScanner()
    
    print("🚀 Starting Arbitrage Scanner Demo...")
    print("=" * 60)
    
    # Test with a popular product
    test_keywords = "airpods pro"
    
    print(f"🔍 Testing Keywords: {test_keywords}")
    print(f"📂 Categories: Tech")
    print(f"💰 Min Profit: $20")
    print()
    
    results = scanner.scan_arbitrage_opportunities(
        keywords=test_keywords,
        categories=['Tech'],
        min_profit=20.0,
        max_results=5
    )
    
    # Display results
    metadata = results['scan_metadata']
    summary = results['opportunities_summary']
    
    print(f"📊 ARBITRAGE SCAN RESULTS:")
    print(f"⏱️  Duration: {metadata['duration_seconds']} seconds")
    print(f"🔍 Total searches: {metadata['total_searches_performed']}")
    print(f"📋 Listings analyzed: {metadata['total_listings_analyzed']}")
    print(f"🎯 Unique products: {metadata['unique_products_found']}")
    print(f"💡 Arbitrage opportunities: {summary['total_opportunities']}")
    print(f"💰 Average profit: ${summary['average_profit_after_fees']}")
    print(f"📈 Average ROI: {summary['average_roi']}%")
    print(f"🎯 Average confidence: {summary['average_confidence']}%")
    print()
    
    if results['top_opportunities']:
        print(f"🏆 TOP ARBITRAGE OPPORTUNITIES:")
        for i, opp in enumerate(results['top_opportunities'][:3], 1):
            print(f"\n{i}. ARBITRAGE OPPORTUNITY #{opp['opportunity_id']}")
            print(f"   📊 Confidence: {opp['confidence_score']}% | Risk: {opp['risk_level']}")
            print(f"   📈 ROI: {opp['profit_analysis']['roi_percentage']}%")
            print()
            
            # Buy listing
            buy = opp['buy_listing']
            print(f"   🛒 BUY FROM:")
            print(f"      Title: {buy['title'][:60]}...")
            print(f"      Price: ${buy['price']} + ${buy['shipping_cost']} shipping = ${buy['total_cost']}")
            print(f"      Condition: {buy['condition']}")
            print(f"      Seller: {buy['seller_rating']} ({buy['seller_feedback']} feedback)")
            print(f"      Location: {buy['location']}")
            print()
            
            # Sell reference
            sell = opp['sell_reference']
            print(f"   💰 SELL REFERENCE:")
            print(f"      Title: {sell['title'][:60]}...")
            print(f"      Price: ${sell['price']} + ${sell['shipping_cost']} shipping = ${sell['total_cost']}")
            print(f"      Condition: {sell['condition']}")
            print(f"      Seller: {sell['seller_rating']} ({sell['seller_feedback']} feedback)")
            print()
            
            # Profit analysis
            profit = opp['profit_analysis']
            print(f"   💵 PROFIT ANALYSIS:")
            print(f"      Gross Profit: ${profit['gross_profit']}")
            print(f"      Net Profit (after fees): ${profit['net_profit_after_fees']}")
            print(f"      Estimated Fees: ${profit['estimated_fees']}")
            print(f"      ROI: {profit['roi_percentage']}%")
    else:
        print("❌ No arbitrage opportunities found with current criteria")
    
    print("\n" + "=" * 60)
    print("✅ Demo completed successfully!")
    
    return results


if __name__ == "__main__":
    # Run demo
    try:
        demo_arbitrage_scanner()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        logger.exception("Demo failed")
