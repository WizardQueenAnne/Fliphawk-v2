#!/usr/bin/env python3
"""
FIXED FlipHawk Real-Time eBay Scraper
- Fixes price calculation issues
- Adds proper keywords for all categories  
- Gets real current prices from listings
- Calculates accurate profit margins
"""

import requests
import json
import time
import re
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from urllib.parse import urlencode
from bs4 import BeautifulSoup
import random
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher

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

class FixedArbitrageDetector:
    """Fixed arbitrage detector with proper profit calculations"""
    
    def __init__(self):
        self.seen_pairs = set()
        
    def get_category_keywords(self, keyword: str) -> List[str]:
        """Get expanded keywords based on search term"""
        
        keyword_lower = keyword.lower()
        
        # Tech keywords
        if any(term in keyword_lower for term in ['tech', 'iphone', 'samsung', 'apple', 'laptop', 'macbook', 'airpods', 'ipad']):
            return [
                'iphone 15', 'iphone 14', 'iphone 13', 'iphone 12',
                'samsung galaxy s24', 'samsung galaxy s23', 'pixel 8', 'pixel 7',
                'macbook pro', 'macbook air', 'dell xps', 'lenovo thinkpad',
                'airpods pro', 'airpods max', 'sony wh-1000xm5', 'bose quietcomfort',
                'ipad pro', 'ipad air', 'surface pro', 'galaxy tab s9',
                'apple watch', 'samsung watch', 'gaming laptop', 'ultrabook'
            ]
        
        # Gaming keywords    
        elif any(term in keyword_lower for term in ['gaming', 'ps5', 'xbox', 'nintendo', 'switch', 'playstation']):
            return [
                'playstation 5', 'ps5 console', 'ps5 digital edition',
                'xbox series x', 'xbox series s', 'xbox one x',
                'nintendo switch oled', 'nintendo switch lite', 'nintendo switch console',
                'ps5 controller', 'xbox controller', 'nintendo pro controller',
                'gaming headset', 'gaming monitor', 'gaming keyboard', 'gaming mouse',
                'call of duty', 'fifa 24', 'spider-man 2', 'god of war',
                'zelda tears of the kingdom', 'mario wonder', 'pokemon scarlet violet',
                'steam deck', 'rog ally', 'gaming chair', 'corsair', 'razer'
            ]
        
        # Collectibles keywords
        elif any(term in keyword_lower for term in ['pokemon', 'cards', 'collectibles', 'vintage', 'magic', 'yugioh']):
            return [
                'pokemon cards', 'pokemon booster box', 'charizard card', 'pikachu card',
                'pokemon tcg', 'pokemon 151', 'pokemon paradox rift', 'pokemon obsidian flames',
                'magic the gathering', 'mtg cards', 'black lotus', 'magic booster box',
                'yugioh cards', 'blue eyes white dragon', 'yugioh booster box',
                'baseball cards', 'basketball cards', 'football cards', 'topps chrome',
                'psa 10', 'bgs 10', 'gem mint', 'first edition', 'shadowless',
                'funko pop', 'hot toys', 'vintage toys', 'action figures',
                'coin collection', 'vintage comics', 'rare books'
            ]
        
        # Fashion keywords
        elif any(term in keyword_lower for term in ['fashion', 'jordan', 'yeezy', 'nike', 'supreme', 'sneakers']):
            return [
                'air jordan 1', 'air jordan 4', 'air jordan 11', 'jordan retro',
                'nike dunk low', 'nike dunk high', 'sb dunk', 'panda dunk',
                'yeezy 350', 'yeezy 700', 'yeezy slides', 'adidas yeezy',
                'supreme hoodie', 'supreme box logo', 'off white nike', 'travis scott jordan',
                'rolex watch', 'omega watch', 'ap watch', 'patek philippe',
                'louis vuitton bag', 'gucci bag', 'chanel bag', 'designer handbag',
                'vintage band tee', 'vintage nike', 'streetwear', 'hypebeast',
                'new balance 550', 'new balance 2002r', 'asics gel'
            ]
        
        # Default: return variations of the original keyword
        else:
            return [
                keyword,
                f"{keyword} new",
                f"{keyword} used", 
                f"{keyword} sealed",
                f"vintage {keyword}",
                f"{keyword} collection",
                f"{keyword} lot"
            ]
    
    def find_arbitrage_opportunities(self, listings: List[eBayListing], min_profit: float = 15.0) -> List[Dict]:
        """Find arbitrage opportunities with accurate profit calculations"""
        
        logger.info(f"🎯 Analyzing {len(listings)} listings for arbitrage (min profit: ${min_profit})")
        
        if len(listings) < 2:
            return []
        
        opportunities = []
        self.seen_pairs.clear()
        
        # Sort listings by price for efficiency
        sorted_listings = sorted(listings, key=lambda x: x.total_cost)
        
        for i, buy_listing in enumerate(sorted_listings):
            for sell_listing in sorted_listings[i+1:]:
                
                # Skip if price difference is too small
                price_diff = sell_listing.total_cost - buy_listing.total_cost
                if price_diff < min_profit * 0.7:
                    continue
                
                # Calculate similarity
                similarity = self.calculate_similarity(buy_listing.title, sell_listing.title)
                
                # Lower similarity threshold for more opportunities
                if similarity < 0.25:
                    continue
                
                # Check for duplicate pairs
                pair_id = f"{buy_listing.item_id}_{sell_listing.item_id}"
                if pair_id in self.seen_pairs:
                    continue
                self.seen_pairs.add(pair_id)
                    
                # Calculate accurate profit
                opportunity = self.calculate_accurate_profit(
                    buy_listing, sell_listing, similarity, min_profit
                )
                
                if opportunity:
                    opportunities.append(opportunity)
                    
                    # Limit opportunities to prevent too many results
                    if len(opportunities) >= 25:
                        break
            
            if len(opportunities) >= 25:
                break
        
        # Sort by net profit
        opportunities.sort(key=lambda x: x['net_profit_after_fees'], reverse=True)
        
        logger.info(f"✅ Found {len(opportunities)} arbitrage opportunities")
        return opportunities
    
    def calculate_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between product titles"""
        
        # Normalize titles
        norm1 = self.normalize_title(title1)
        norm2 = self.normalize_title(title2)
        
        if not norm1 or not norm2:
            return 0.0
        
        # Use sequence matcher for basic similarity
        seq_sim = SequenceMatcher(None, norm1, norm2).ratio()
        
        # Word-based similarity
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if words1 and words2:
            word_sim = len(words1 & words2) / len(words1 | words2)
            return (seq_sim * 0.4 + word_sim * 0.6)
        
        return seq_sim
    
    def normalize_title(self, title: str) -> str:
        """Normalize title for comparison"""
        
        # Convert to lowercase
        normalized = title.lower()
        
        # Remove common noise words
        noise_words = [
            'new', 'used', 'brand new', 'sealed', 'mint', 'excellent',
            'free shipping', 'fast shipping', 'authentic', 'genuine',
            'original', 'oem', 'refurbished', 'open box'
        ]
        
        for noise in noise_words:
            normalized = normalized.replace(noise, ' ')
        
        # Remove special characters and extra spaces
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def calculate_accurate_profit(self, buy_listing: eBayListing, sell_listing: eBayListing, 
                                similarity: float, min_profit: float) -> Optional[Dict]:
        """Calculate accurate profit with real eBay fees and costs"""
        
        buy_cost = buy_listing.total_cost
        sell_price = sell_listing.price  # Use the price they're asking, not total cost
        
        if buy_cost <= 0 or sell_price <= buy_cost:
            return None
        
        # ACCURATE eBay fee calculation
        # eBay Final Value Fee: 13.25% for most categories
        ebay_final_value_fee = sell_price * 0.1325
        
        # PayPal/Payment processing: ~2.9% + $0.30
        payment_processing_fee = (sell_price * 0.029) + 0.30
        
        # Shipping cost to buyer (if you need to ship)
        estimated_shipping_out = 8.50  # Average shipping cost
        
        # Total fees and costs
        total_fees = ebay_final_value_fee + payment_processing_fee + estimated_shipping_out
        
        # Calculate profits
        gross_profit = sell_price - buy_cost
        net_profit = gross_profit - total_fees
        
        # Check if profitable enough
        if net_profit < min_profit:
            return None
        
        # Calculate ROI
        roi = (net_profit / buy_cost) * 100 if buy_cost > 0 else 0
        
        # Calculate confidence score
        confidence = self.calculate_confidence(similarity, net_profit, buy_listing, sell_listing)
        
        # Assess risk
        risk_level = self.assess_risk(roi, confidence, buy_cost)
        
        return {
            'opportunity_id': f"FIXED_{int(time.time())}_{random.randint(1000, 9999)}",
            'buy_listing': asdict(buy_listing),
            'sell_reference': asdict(sell_listing),
            'similarity_score': round(similarity, 3),
            'confidence_score': min(95, max(20, confidence)),
            'risk_level': risk_level,
            'gross_profit': round(gross_profit, 2),
            'net_profit_after_fees': round(net_profit, 2),
            'roi_percentage': round(roi, 1),
            'estimated_fees': round(total_fees, 2),
            'profit_analysis': {
                'buy_price': buy_cost,
                'sell_price': sell_price,
                'gross_profit': gross_profit,
                'net_profit_after_fees': net_profit,
                'roi_percentage': roi,
                'estimated_fees': total_fees,
                'fee_breakdown': {
                    'ebay_final_value_fee': round(ebay_final_value_fee, 2),
                    'payment_processing_fee': round(payment_processing_fee, 2),
                    'estimated_shipping_cost': estimated_shipping_out
                }
            },
            'created_at': datetime.now().isoformat()
        }
    
    def calculate_confidence(self, similarity: float, net_profit: float, 
                           buy_listing: eBayListing, sell_listing: eBayListing) -> int:
        """Calculate confidence score"""
        
        confidence = 30  # Base confidence
        
        # Similarity bonus
        if similarity > 0.7:
            confidence += 40
        elif similarity > 0.5:
            confidence += 25
        elif similarity > 0.3:
            confidence += 15
        elif similarity > 0.25:
            confidence += 8
        
        # Profit bonus
        if net_profit >= 50:
            confidence += 25
        elif net_profit >= 30:
            confidence += 15
        elif net_profit >= 20:
            confidence += 10
        
        # Condition bonus
        if 'new' in buy_listing.condition.lower():
            confidence += 15
        elif 'excellent' in buy_listing.condition.lower():
            confidence += 8
        
        # Price range bonus (sweet spot for arbitrage)
        if 20 <= buy_listing.total_cost <= 300:
            confidence += 10
        elif 10 <= buy_listing.total_cost <= 500:
            confidence += 5
        
        return confidence
    
    def assess_risk(self, roi: float, confidence: int, buy_cost: float) -> str:
        """Assess risk level"""
        
        risk_score = 0
        
        # ROI risk
        if roi > 200:
            risk_score += 2  # Too good to be true
        elif roi > 100:
            risk_score += 1
        
        # Confidence risk
        if confidence < 50:
            risk_score += 2
        elif confidence < 70:
            risk_score += 1
        
        # Price risk
        if buy_cost > 500:
            risk_score += 1  # High value = higher risk
        elif buy_cost < 10:
            risk_score += 1  # Too cheap might be problematic
        
        if risk_score >= 3:
            return 'HIGH'
        elif risk_score >= 1:
            return 'MEDIUM'
        else:
            return 'LOW'

class RealTimeeBayScraper:
    """Fixed eBay scraper with accurate price extraction"""
    
    def __init__(self):
        self.base_url = "https://www.ebay.com"
        self.search_url = f"{self.base_url}/sch/i.html"
        
        # Better user agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]
        
        self.session = requests.Session()
        self.last_request_time = 0
        self.min_delay = 1.5
        self.seen_items = set()
        
        # Initialize arbitrage detector
        self.arbitrage_detector = FixedArbitrageDetector()
    
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
        }
    
    def rate_limit(self):
        """Rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            sleep_time = self.min_delay - time_since_last + random.uniform(0.3, 0.8)
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def build_search_url(self, keyword: str, page: int = 1, sort_order: str = "price") -> str:
        """Build eBay search URL"""
        params = {
            '_nkw': keyword,
            '_pgn': page,
            '_ipg': 200,  # Max results per page
            'LH_BIN': 1,  # Buy It Now only
            'LH_Complete': 0,  # Active listings only
            'LH_Sold': 0,  # Not sold
            'rt': 'nc',
            '_sacat': 0,
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
    
    def search_ebay(self, keyword: str, limit: int = 50, sort_order: str = "price", 
                   max_pages: int = 4) -> List[eBayListing]:
        """Search eBay with better keyword expansion"""
        
        logger.info(f"🔍 Searching eBay for: '{keyword}' (limit: {limit})")
        
        # Get expanded keywords for better coverage
        expanded_keywords = self.arbitrage_detector.get_category_keywords(keyword)
        
        # Use the original keyword plus 2-3 expanded ones
        search_terms = [keyword] + expanded_keywords[:3]
        
        all_listings = []
        
        for search_term in search_terms:
            logger.info(f"  🔎 Searching: {search_term}")
            
            for page in range(1, max_pages + 1):
                try:
                    url = self.build_search_url(search_term, page, sort_order)
                    soup = self.get_page(url)
                    
                    if not soup:
                        break
                    
                    # Find item containers
                    items = soup.select('.s-item__wrapper, .s-item')
                    
                    if not items:
                        break
                    
                    page_listings = []
                    for item in items:
                        listing = self.extract_listing_data(item, search_term)
                        if listing and listing.item_id not in self.seen_items:
                            self.seen_items.add(listing.item_id)
                            page_listings.append(listing)
                    
                    all_listings.extend(page_listings)
                    logger.info(f"    Page {page}: {len(page_listings)} listings")
                    
                    # Stop if we have enough listings
                    if len(all_listings) >= limit:
                        break
                    
                    # Rate limiting between pages
                    time.sleep(random.uniform(2.0, 4.0))
                    
                except Exception as e:
                    logger.error(f"Error searching page {page} for '{search_term}': {e}")
                    continue
            
            # Rate limiting between search terms
            time.sleep(random.uniform(3.0, 5.0))
            
            # Stop if we have enough total listings
            if len(all_listings) >= limit:
                break
        
        # Remove duplicates and sort
        unique_listings = {listing.item_id: listing for listing in all_listings}.values()
        final_listings = list(unique_listings)
        
        if sort_order == "price":
            final_listings.sort(key=lambda x: x.total_cost)
        
        logger.info(f"✅ Found {len(final_listings)} unique listings total")
        return final_listings[:limit]
    
    def get_page(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """Fetch and parse eBay page"""
        for attempt in range(retries):
            try:
                self.rate_limit()
                
                headers = self.get_headers()
                response = self.session.get(url, headers=headers, timeout=20)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    if soup.find('title') and 'eBay' in soup.get_text():
                        return soup
                    else:
                        logger.warning(f"Invalid eBay page content")
                        return None
                
                elif response.status_code == 429:
                    wait_time = (2 ** attempt) + random.uniform(8, 15)
                    logger.warning(f"Rate limited, waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    
                else:
                    logger.warning(f"HTTP {response.status_code} for {url}")
                    if attempt < retries - 1:
                        time.sleep(random.uniform(5, 10))
                        
            except Exception as e:
                logger.error(f"Error fetching page (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    time.sleep(random.uniform(8, 15))
        
        return None
    
    def extract_listing_data(self, item_soup: BeautifulSoup, keyword: str) -> Optional[eBayListing]:
        """Extract listing data with accurate price extraction"""
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
            
            # FIXED: Extract current price more accurately
            price = 0.0
            price_selectors = [
                '.s-item__price .notranslate',
                '.s-item__price span.POSITIVE',
                '.s-item__price span',
                '.s-item__price'
            ]
            
            for selector in price_selectors:
                price_elem = item_soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    
                    # Handle price ranges (take the first/lowest price)
                    if 'to' in price_text.lower() or ' - ' in price_text:
                        prices = re.findall(r'\$?([\d,]+\.?\d*)', price_text)
                        if prices:
                            try:
                                price = float(prices[0].replace(',', ''))
                                break
                            except ValueError:
                                continue
                    else:
                        # Extract single price
                        price_match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
                        if price_match:
                            try:
                                price = float(price_match.group(1).replace(',', ''))
                                break
                            except ValueError:
                                continue
            
            if price <= 0 or price > 20000:  # Reasonable price range
                return None
            
            # FIXED: Extract shipping cost more accurately
            shipping_cost = 0.0
            shipping_selectors = [
                '.s-item__shipping .vi-price .notranslate',
                '.s-item__shipping span',
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
                                shipping_cost = min(shipping_cost, price * 0.3)  # Cap shipping at 30% of price
                                break
                            except ValueError:
                                continue
            
            total_cost = price + shipping_cost
            
            # Extract eBay link with cleaning
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
                        # Clean the URL
                        if href.startswith('//'):
                            ebay_link = 'https:' + href
                        elif href.startswith('/'):
                            ebay_link = 'https://www.ebay.com' + href
                        elif href.startswith('http'):
                            ebay_link = href
                        
                        # Remove tracking parameters but keep essential ones
                        if '?' in ebay_link:
                            base_url = ebay_link.split('?')[0]
                            ebay_link = base_url
                        
                        if 'ebay.com' in ebay_link:
                            break
            
            if not ebay_link:
                return None
            
            # Extract item ID
            item_id = self.extract_item_id(ebay_link)
            
            # Other data extraction...
            condition = self.extract_condition(item_soup)
            image_url = self.extract_image_url(item_soup)
            location = self.extract_location(item_soup)
            
            return eBayListing(
                item_id=item_id,
                title=title,
                price=price,
                shipping_cost=shipping_cost,
                total_cost=total_cost,
                condition=condition,
                seller_username="Unknown",
                seller_rating="Not available",
                seller_feedback="Not available",
                image_url=image_url,
                ebay_link=ebay_link,
                location=location,
                listing_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                watchers="Not available",
                bids="0",
                time_left="Buy It Now",
                is_auction=False,
                buy_it_now_available=True
            )
            
        except Exception as e:
            logger.error(f"Error extracting listing data: {e}")
            return None
    
    def extract_item_id(self, url: str) -> str:
        """Extract eBay item ID from URL"""
        try:
            patterns = [
                r'/itm/([^/]+/)?(\d{12,})',
                r'/(\d{12,})',
                r'item/(\d{12,})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    groups = match.groups()
                    item_id = groups[-1] if groups else None
                    if item_id and item_id.isdigit() and len(item_id) >= 12:
                        return item_id
            
            # Fallback
            return f"item_{int(time.time())}_{random.randint(100, 999)}"
            
        except:
            return f"item_{int(time.time())}_{random.randint(100, 999)}"
    
    def extract_condition(self, item_soup: BeautifulSoup) -> str:
        """Extract item condition"""
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
                    'brand new', 'new', 'sealed', 'mint',
                    'open box', 'like new', 'excellent', 'very good', 'good',
                    'acceptable', 'used', 'pre-owned', 'refurbished'
                ]
                
                condition_lower = condition_text.lower()
                for keyword in condition_keywords:
                    if keyword in condition_lower:
                        return condition_text.title()
                
                if condition_text:
                    return condition_text
        
        return "Used"
    
    def extract_image_url(self, item_soup: BeautifulSoup) -> str:
        """Extract item image URL"""
        image_selectors = [
            '.s-item__image img',
            '.s-item__wrapper img'
        ]
        
        for selector in image_selectors:
            img_elem = item_soup.select_one(selector)
            if img_elem:
                src = img_elem.get('src') or img_elem.get('data-src')
                if src:
                    if src.startswith('//'):
                        return 'https:' + src
                    elif src.startswith('/'):
                        return 'https://www.ebay.com' + src
                    else:
                        return src
        
        return ""
    
    def extract_location(self, item_soup: BeautifulSoup) -> str:
        """Extract item location"""
        location_selectors = [
            '.s-item__location',
            '.s-item__shipping .s-item__location'
        ]
        
        for selector in location_selectors:
            location_elem = item_soup.select_one(selector)
            if location_elem:
                location_text = location_elem.get_text(strip=True)
                if location_text and 'from' not in location_text.lower():
                    return location_text
        
        return "Unknown"
    
    def find_arbitrage_opportunities(self, listings: List[eBayListing], min_profit: float = 15.0) -> List[Dict]:
        """Find arbitrage opportunities using the fixed detector"""
        return self.arbitrage_detector.find_arbitrage_opportunities(listings, min_profit)


# REQUIRED FUNCTIONS FOR FLASK APP - FIXED VERSIONS
def search_ebay_real(keyword: str, limit: int = 50, sort: str = "price") -> List[Dict]:
    """FIXED: Main function to search eBay for real listings"""
    try:
        logger.info(f"🔍 Real eBay search: '{keyword}' (limit: {limit})")
        
        scraper = RealTimeeBayScraper()
        listings = scraper.search_ebay(keyword, limit, sort)
        
        # Convert to dict format for JSON serialization
        listings_dict = []
        for listing in listings:
            try:
                listing_dict = asdict(listing)
                # Ensure all fields are properly formatted
                listing_dict['price'] = round(listing_dict['price'], 2)
                listing_dict['shipping_cost'] = round(listing_dict['shipping_cost'], 2) 
                listing_dict['total_cost'] = round(listing_dict['total_cost'], 2)
                listings_dict.append(listing_dict)
            except Exception as e:
                logger.error(f"Error converting listing to dict: {e}")
                continue
        
        logger.info(f"✅ Returning {len(listings_dict)} formatted listings")
        return listings_dict
        
    except Exception as e:
        logger.error(f"❌ Real eBay search failed: {e}")
        return []

def find_arbitrage_real(keyword: str, min_profit: float = 15.0, limit: int = 50) -> Dict:
    """FIXED: Find real arbitrage opportunities with accurate calculations"""
    try:
        start_time = datetime.now()
        logger.info(f"🎯 Starting arbitrage analysis for '{keyword}' (min profit: ${min_profit})")
        
        # Use the fixed scraper
        scraper = RealTimeeBayScraper()
        
        # Search with expanded limit for better arbitrage detection
        search_limit = min(limit * 3, 150)  # Search more to find better arbitrage
        listings = scraper.search_ebay(keyword, search_limit, "price")
        
        if not listings:
            logger.warning(f"No listings found for '{keyword}'")
            return {
                'scan_metadata': {
                    'scan_id': f"FIXED_{int(time.time())}",
                    'timestamp': datetime.now().isoformat(),
                    'duration_seconds': 0,
                    'total_searches_performed': 1,
                    'total_listings_analyzed': 0,
                    'arbitrage_opportunities_found': 0,
                    'scan_efficiency': 0,
                    'keywords_used': [keyword],
                    'unique_products_found': 0,
                    'status': 'no_listings_found'
                },
                'opportunities_summary': {
                    'total_opportunities': 0,
                    'average_profit_after_fees': 0,
                    'average_roi': 0,
                    'highest_profit': 0,
                    'risk_distribution': {'low': 0, 'medium': 0, 'high': 0}
                },
                'top_opportunities': []
            }
        
        logger.info(f"📊 Analyzing {len(listings)} listings for arbitrage...")
        
        # Find arbitrage opportunities using fixed detector
        opportunities = scraper.find_arbitrage_opportunities(listings, min_profit)
        
        # Calculate metrics
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        total_opportunities = len(opportunities)
        
        if total_opportunities > 0:
            profits = [opp['net_profit_after_fees'] for opp in opportunities]
            rois = [opp['roi_percentage'] for opp in opportunities]
            
            avg_profit = sum(profits) / len(profits)
            avg_roi = sum(rois) / len(rois)
            highest_profit = max(profits)
            
            # Risk distribution
            risk_counts = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0}
            for opp in opportunities:
                risk_level = opp.get('risk_level', 'MEDIUM')
                risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
        else:
            avg_profit = avg_roi = highest_profit = 0
            risk_counts = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0}
        
        # Calculate scan efficiency
        scan_efficiency = (total_opportunities / len(listings)) * 100 if listings else 0
        
        # Get expanded keywords used
        expanded_keywords = scraper.arbitrage_detector.get_category_keywords(keyword)
        keywords_used = [keyword] + expanded_keywords[:3]
        
        result = {
            'scan_metadata': {
                'scan_id': f"FIXED_{int(time.time())}_{random.randint(100, 999)}",
                'timestamp': end_time.isoformat(),
                'duration_seconds': round(duration, 2),
                'total_searches_performed': len(keywords_used),
                'total_listings_analyzed': len(listings),
                'arbitrage_opportunities_found': total_opportunities,
                'scan_efficiency': round(scan_efficiency, 2),
                'keywords_used': keywords_used,
                'unique_products_found': len(listings),
                'status': 'success' if total_opportunities > 0 else 'no_opportunities_found',
                'min_profit_threshold': min_profit,
                'average_similarity_threshold': 0.25
            },
            'opportunities_summary': {
                'total_opportunities': total_opportunities,
                'average_profit_after_fees': round(avg_profit, 2),
                'average_roi': round(avg_roi, 1),
                'highest_profit': round(highest_profit, 2),
                'risk_distribution': {
                    'low': risk_counts.get('LOW', 0),
                    'medium': risk_counts.get('MEDIUM', 0), 
                    'high': risk_counts.get('HIGH', 0)
                }
            },
            'top_opportunities': opportunities[:limit]  # Return requested limit
        }
        
        logger.info(f"✅ Arbitrage analysis complete: {total_opportunities} opportunities found in {duration:.2f}s")
        return result
        
    except Exception as e:
        logger.error(f"❌ Arbitrage analysis failed for '{keyword}': {e}")
        return {
            'scan_metadata': {
                'scan_id': f"ERROR_{int(time.time())}",
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': 0,
                'error': str(e),
                'status': 'error'
            },
            'opportunities_summary': {
                'total_opportunities': 0,
                'average_profit_after_fees': 0,
                'average_roi': 0,
                'highest_profit': 0,
                'risk_distribution': {'low': 0, 'medium': 0, 'high': 0}
            },
            'top_opportunities': []
        }

# Demo function for testing
def demo_fixed_scraper():
    """Demo the fixed scraper functionality"""
    
    test_categories = {
        'tech': 'iphone 13',
        'gaming': 'nintendo switch',
        'collectibles': 'pokemon cards',
        'fashion': 'air jordan'
    }
    
    print("🎯 TESTING FIXED FLIPHAWK SCRAPER")
    print("=" * 50)
    
    for category, keyword in test_categories.items():
        print(f"\n🔍 Testing {category.upper()}: '{keyword}'")
        print("-" * 30)
        
        try:
            # Test arbitrage finding
            result = find_arbitrage_real(keyword, min_profit=12.0, limit=10)
            
            opportunities = result['top_opportunities']
            metadata = result['scan_metadata']
            summary = result['opportunities_summary']
            
            print(f"📊 Scanned {metadata['total_listings_analyzed']} listings in {metadata['duration_seconds']:.1f}s")
            print(f"✅ Found {len(opportunities)} arbitrage opportunities")
            
            if opportunities:
                print(f"💰 Average profit: ${summary['average_profit_after_fees']:.2f}")
                print(f"📈 Average ROI: {summary['average_roi']:.1f}%")
                print(f"🎯 Highest profit: ${summary['highest_profit']:.2f}")
                
                print(f"\nTop 3 Opportunities:")
                for i, opp in enumerate(opportunities[:3], 1):
                    buy_listing = opp['buy_listing']
                    sell_ref = opp['sell_reference']
                    
                    print(f"{i}. {buy_listing['title'][:50]}...")
                    print(f"   💵 Buy: ${buy_listing['total_cost']:.2f} → Sell: ${sell_ref['price']:.2f}")
                    print(f"   💰 Net Profit: ${opp['net_profit_after_fees']:.2f} (ROI: {opp['roi_percentage']:.1f}%)")
                    print(f"   🔄 Similarity: {opp['similarity_score']:.3f} | Confidence: {opp['confidence_score']}%")
                    print(f"   🔗 Buy Link: {buy_listing['ebay_link']}")
                    print()
            else:
                print("❌ No profitable opportunities found")
                
        except Exception as e:
            print(f"❌ Error testing {category}: {e}")
        
        print("-" * 50)
        time.sleep(2)  # Rate limiting between tests

if __name__ == "__main__":
    demo_fixed_scraper()
