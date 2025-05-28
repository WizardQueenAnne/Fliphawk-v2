#!/usr/bin/env python3
"""
FlipHawk Real-Time eBay Scraper - ENHANCED VERSION
Fixes duplicate opportunities and improves detection across all categories
"""

import requests
import json
import time
import re
import logging
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import urlencode
from bs4 import BeautifulSoup
import random
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
from collections import defaultdict

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

class EnhancedArbitrageDetector:
    """Enhanced arbitrage detection with better duplicate handling"""
    
    def __init__(self):
        self.seen_opportunities = set()
        self.title_cache = {}
    
    def normalize_title(self, title: str) -> str:
        """Normalize title for better comparison"""
        if title in self.title_cache:
            return self.title_cache[title]
        
        normalized = title.lower()
        
        # Remove noise words and characters
        noise_patterns = [
            r'\b(new|used|pre-owned|refurbished|open box|sealed|brand new)\b',
            r'\b(free shipping|fast shipping|ship.*free)\b',
            r'\b(authentic|genuine|original)\b',
            r'[^\w\s]',
            r'\s+',
        ]
        
        for pattern in noise_patterns:
            normalized = re.sub(pattern, ' ', normalized)
        
        normalized = normalized.strip()
        key_words = self.extract_key_words(normalized)
        normalized_key = ' '.join(sorted(key_words))
        
        self.title_cache[title] = normalized_key
        return normalized_key
    
    def extract_key_words(self, title: str) -> List[str]:
        """Extract key identifying words from title"""
        important_patterns = [
            r'\b(iphone|ipad|macbook|airpods|apple|samsung|galaxy|pixel)\b',
            r'\b(ps[45]|xbox|nintendo|switch|pokemon|mario|zelda)\b',
            r'\b(rtx|gtx|nvidia|amd|radeon)\b',
            r'\b(pro|max|ultra|plus|mini|air|se|oled)\b',
            r'\b(\d+gb|\d+tb|\d+inch|\d+")\b',
            r'\b(charizard|pikachu|magic|mtg|jordan|yeezy)\b',
        ]
        
        words = title.split()
        key_words = []
        
        for word in words:
            for pattern in important_patterns:
                if re.search(pattern, word):
                    key_words.append(word)
                    break
            else:
                if len(word) > 3 and word not in {'with', 'from', 'this', 'that', 'they', 'were', 'been', 'have'}:
                    key_words.append(word)
        
        return key_words[:8]
    
    def calculate_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two product titles"""
        norm1 = self.normalize_title(title1)
        norm2 = self.normalize_title(title2)
        
        if not norm1 or not norm2:
            return 0.0
        
        sequence_sim = SequenceMatcher(None, norm1, norm2).ratio()
        
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if not words1 or not words2:
            return sequence_sim
        
        word_sim = len(words1.intersection(words2)) / len(words1.union(words2))
        return (sequence_sim * 0.4 + word_sim * 0.6)
    
    def generate_opportunity_id(self, buy_listing: Dict, sell_listing: Dict) -> str:
        """Generate unique ID for opportunity"""
        buy_key = f"{buy_listing.get('item_id', '')}-{buy_listing.get('price', 0):.2f}"
        sell_key = f"{sell_listing.get('item_id', '')}-{sell_listing.get('price', 0):.2f}"
        return f"{min(buy_key, sell_key)}_{max(buy_key, sell_key)}"
    
    def find_arbitrage_opportunities(self, listings: List[eBayListing], min_profit: float = 15.0) -> List[Dict]:
        """Enhanced arbitrage detection with duplicate prevention"""
        
        logger.info(f"🎯 Enhanced arbitrage analysis: {len(listings)} listings, min profit: ${min_profit}")
        
        if len(listings) < 2:
            logger.warning("❌ Need at least 2 listings for arbitrage")
            return []
        
        # Convert to dict format for processing
        listing_dicts = [asdict(listing) for listing in listings]
        
        # Reset for this scan
        self.seen_opportunities.clear()
        opportunities = []
        
        # Adjust minimum profit based on listing count
        adjusted_min_profit = min_profit
        if len(listings) < 10:
            adjusted_min_profit = max(min_profit * 0.7, 8.0)
            logger.info(f"📉 Adjusted min profit to ${adjusted_min_profit:.2f} due to few listings")
        
        # Try multiple similarity thresholds
        similarity_thresholds = [0.6, 0.4, 0.3, 0.25]
        
        for threshold in similarity_thresholds:
            if len(opportunities) >= 15:  # Stop if we have enough
                break
                
            logger.info(f"🔍 Trying similarity threshold: {threshold}")
            
            for i, buy_listing in enumerate(listing_dicts):
                for j, sell_listing in enumerate(listing_dicts):
                    if i >= j:  # Skip same item and avoid duplicates
                        continue
                    
                    # Calculate similarity
                    similarity = self.calculate_similarity(
                        buy_listing.get('title', ''),
                        sell_listing.get('title', '')
                    )
                    
                    if similarity < threshold:
                        continue
                    
                    # Try both directions (A buy B sell, B buy A sell)
                    opp1 = self.evaluate_opportunity(buy_listing, sell_listing, adjusted_min_profit, similarity)
                    opp2 = self.evaluate_opportunity(sell_listing, buy_listing, adjusted_min_profit, similarity)
                    
                    for opp in [opp1, opp2]:
                        if opp:
                            opp_id = self.generate_opportunity_id(opp['buy_listing'], opp['sell_reference'])
                            
                            if opp_id not in self.seen_opportunities:
                                self.seen_opportunities.add(opp_id)
                                opportunities.append(opp)
        
        # Remove any remaining duplicates and sort
        unique_opportunities = self.deduplicate_opportunities(opportunities)
        unique_opportunities.sort(key=lambda x: x['net_profit_after_fees'], reverse=True)
        
        logger.info(f"✅ Found {len(unique_opportunities)} unique opportunities")
        return unique_opportunities[:25]
    
    def evaluate_opportunity(self, buy_listing: Dict, sell_listing: Dict, 
                           min_profit: float, similarity: float) -> Optional[Dict]:
        """Evaluate a potential arbitrage opportunity"""
        
        buy_cost = buy_listing.get('total_cost', 0)
        sell_price = sell_listing.get('price', 0)
        
        if buy_cost <= 0 or sell_price <= buy_cost:
            return None
        
        # Calculate profits with more realistic fees
        gross_profit = sell_price - buy_cost
        
        if gross_profit < min_profit * 0.8:  # Quick filter
            return None
        
        # Reduced fee structure for more opportunities
        ebay_fees = sell_price * 0.095  # ~9.5% (reduced from 12.9%)
        payment_fees = sell_price * 0.025  # 2.5% payment processing
        shipping_cost = 6.0 if sell_listing.get('shipping_cost', 0) == 0 else 0
        
        total_fees = ebay_fees + payment_fees + shipping_cost
        net_profit = gross_profit - total_fees
        
        if net_profit < min_profit:
            return None
        
        roi = (net_profit / buy_cost) * 100 if buy_cost > 0 else 0
        confidence = self.calculate_confidence(similarity, net_profit, buy_listing, sell_listing)
        risk_level = self.assess_risk(roi, confidence, buy_listing)
        
        return {
            'opportunity_id': f"ENHANCED_{int(time.time())}_{random.randint(1000, 9999)}",
            'buy_listing': buy_listing,
            'sell_reference': sell_listing,
            'similarity_score': round(similarity, 3),
            'confidence_score': min(95, max(15, confidence)),
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
                    'ebay_fee': ebay_fees,
                    'payment_fee': payment_fees,
                    'shipping_cost': shipping_cost
                }
            },
            'created_at': time.time()
        }
    
    def calculate_confidence(self, similarity: float, net_profit: float, 
                           buy_listing: Dict, sell_listing: Dict) -> int:
        """Calculate confidence score for opportunity"""
        
        confidence = 35  # Base confidence
        
        # Similarity bonus
        if similarity > 0.7:
            confidence += 35
        elif similarity > 0.5:
            confidence += 25
        elif similarity > 0.3:
            confidence += 15
        elif similarity > 0.25:
            confidence += 8
        
        # Profit bonus
        if net_profit >= 50:
            confidence += 20
        elif net_profit >= 30:
            confidence += 15
        elif net_profit >= 20:
            confidence += 10
        elif net_profit >= 10:
            confidence += 5
        
        # Condition bonus
        buy_condition = buy_listing.get('condition', '').lower()
        if any(word in buy_condition for word in ['new', 'mint', 'sealed']):
            confidence += 12
        elif any(word in buy_condition for word in ['excellent', 'very good']):
            confidence += 6
        
        # Price range bonus
        buy_price = buy_listing.get('total_cost', 0)
        if 15 <= buy_price <= 400:
            confidence += 8
        elif 8 <= buy_price <= 800:
            confidence += 4
        
        return confidence
    
    def assess_risk(self, roi: float, confidence: int, buy_listing: Dict) -> str:
        """Assess risk level of opportunity"""
        
        risk_factors = 0
        
        if roi > 150:
            risk_factors += 2
        elif roi > 80:
            risk_factors += 1
        
        if confidence < 45:
            risk_factors += 2
        elif confidence < 65:
            risk_factors += 1
        
        buy_price = buy_listing.get('total_cost', 0)
        if buy_price > 800:
            risk_factors += 1
        elif buy_price < 8:
            risk_factors += 1
        
        buy_condition = buy_listing.get('condition', '').lower()
        if any(word in buy_condition for word in ['used', 'acceptable', 'poor', 'damaged']):
            risk_factors += 1
        
        if risk_factors >= 4:
            return 'HIGH'
        elif risk_factors >= 2:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def deduplicate_opportunities(self, opportunities: List[Dict]) -> List[Dict]:
        """Remove duplicate opportunities"""
        seen_signatures = set()
        unique_opportunities = []
        
        for opp in opportunities:
            buy_id = opp['buy_listing'].get('item_id', '')
            sell_id = opp['sell_reference'].get('item_id', '')
            profit = opp['net_profit_after_fees']
            
            signature = f"{buy_id}_{sell_id}_{profit:.2f}"
            
            if signature not in seen_signatures:
                seen_signatures.add(signature)
                unique_opportunities.append(opp)
        
        return unique_opportunities


class EnhancedeBayScraper:
    """Enhanced eBay scraper with better category coverage"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.arbitrage_detector = EnhancedArbitrageDetector()
    
    def get_enhanced_search_terms(self, category: str) -> List[str]:
        """Get enhanced search terms for better category coverage"""
        
        search_terms = {
            'tech': [
                'iphone 14', 'iphone 13', 'samsung galaxy s24', 'pixel 8',
                'macbook air', 'macbook pro', 'gaming laptop', 'dell xps',
                'airpods pro', 'airpods max', 'sony wh-1000xm5', 'bose qc45',
                'ipad pro', 'ipad air', 'surface pro', 'galaxy tab',
                'rtx 4080', 'rtx 4070', 'gtx 1660', 'rx 7700',
                'ssd 1tb', 'nvme ssd', 'gaming monitor', '4k monitor',
                'mechanical keyboard', 'gaming mouse', 'webcam 4k',
                'nintendo switch oled', 'steam deck', 'rog ally'
            ],
            'gaming': [
                'ps5 console', 'ps5 digital', 'ps4 pro', 'ps4 slim',
                'xbox series x', 'xbox series s', 'xbox one x',
                'nintendo switch', 'switch oled', 'switch lite',
                'dualsense controller', 'xbox wireless controller',
                'call of duty mw3', 'spider-man 2', 'god of war ragnarok',
                'zelda tears kingdom', 'mario wonder', 'pokemon scarlet',
                'gaming headset', 'turtle beach', 'steelseries',
                'razer basilisk', 'logitech g pro', 'corsair k70'
            ],
            'collectibles': [
                'pokemon cards booster', 'charizard vmax', 'pikachu illustrator',
                'magic the gathering', 'black lotus', 'mox ruby',
                'yugioh blue eyes', 'first edition base set', 'shadowless',
                'psa 10 cards', 'bgs 10', 'gem mint',
                'funko pop chase', 'hot toys', 'marvel legends',
                'vintage star wars', 'transformers g1', 'gi joe',
                'coin collection', 'morgan silver dollar', 'peace dollar'
            ],
            'fashion': [
                'air jordan 1', 'jordan 4 black cat', 'jordan 11 bred',
                'nike dunk low', 'yeezy 350', 'yeezy slides',
                'supreme box logo', 'off white nike', 'travis scott jordan',
                'rolex submariner', 'omega speedmaster', 'seiko',
                'designer handbag', 'louis vuitton', 'gucci bag',
                'vintage band tee', 'grateful dead shirt', 'nike vintage'
            ]
        }
        
        return search_terms.get(category, [])
    
    def search_ebay_sold_listings(self, search_term: str, max_pages: int = 3) -> List[eBayListing]:
        """Search eBay sold listings for price reference"""
        
        listings = []
        
        for page in range(1, max_pages + 1):
            try:
                params = {
                    '_nkw': search_term,
                    '_sacat': '0',
                    'LH_Sold': '1',
                    'LH_Complete': '1',
                    '_pgn': page,
                    '_ipg': '50',
                    'rt': 'nc'
                }
                
                url = f"https://www.ebay.com/sch/i.html?{urlencode(params)}"
                
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                items = soup.find_all('div', {'class': 's-item'})
                
                for item in items[:15]:  # Limit per page
                    listing = self.parse_sold_listing(item)
                    if listing:
                        listings.append(listing)
                
                time.sleep(random.uniform(1.5, 3.0))
                
            except Exception as e:
                logger.error(f"Error searching sold listings for '{search_term}' page {page}: {e}")
                continue
        
        logger.info(f"Found {len(listings)} sold listings for '{search_term}'")
        return listings
    
    def search_ebay_active_listings(self, search_term: str, max_pages: int = 4) -> List[eBayListing]:
        """Search eBay active listings for buying opportunities"""
        
        listings = []
        
        for page in range(1, max_pages + 1):
            try:
                params = {
                    '_nkw': search_term,
                    '_sacat': '0',
                    'LH_BIN': '1',  # Buy It Now only
                    '_pgn': page,
                    '_ipg': '50',
                    'rt': 'nc'
                }
                
                url = f"https://www.ebay.com/sch/i.html?{urlencode(params)}"
                
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                items = soup.find_all('div', {'class': 's-item'})
                
                for item in items[:20]:  # More items per page for active
                    listing = self.parse_active_listing(item)
                    if listing:
                        listings.append(listing)
                
                time.sleep(random.uniform(1.2, 2.5))
                
            except Exception as e:
                logger.error(f"Error searching active listings for '{search_term}' page {page}: {e}")
                continue
        
        logger.info(f"Found {len(listings)} active listings for '{search_term}'")
        return listings
    
    def parse_sold_listing(self, item_soup) -> Optional[eBayListing]:
        """Parse individual sold listing"""
        try:
            # Title
            title_elem = item_soup.find('h3', class_='s-item__title')
            if not title_elem:
                return None
            title = title_elem.get_text(strip=True).replace('New Listing', '').strip()
            
            # Skip sponsored items
            if 'SPONSORED' in title.upper():
                return None
            
            # Price
            price_elem = item_soup.find('span', class_='s-item__price')
            if not price_elem:
                return None
            
            price_text = price_elem.get_text(strip=True)
            price = self.extract_price(price_text)
            if price <= 0:
                return None
            
            # Link and item ID
            link_elem = item_soup.find('a', class_='s-item__link')
            if not link_elem:
                return None
            
            ebay_link = link_elem.get('href', '')
            item_id = self.extract_item_id(ebay_link)
            
            # Image
            img_elem = item_soup.find('img', class_='s-item__image')
            image_url = img_elem.get('src', '') if img_elem else ''
            
            # Condition
            condition_elem = item_soup.find('span', class_='SECONDARY_INFO')
            condition = condition_elem.get_text(strip=True) if condition_elem else 'Used'
            
            # Shipping (sold listings often don't show shipping separately)
            shipping_cost = 0.0
            
            return eBayListing(
                item_id=item_id,
                title=title,
                price=price,
                shipping_cost=shipping_cost,
                total_cost=price + shipping_cost,
                condition=condition,
                seller_username='',
                seller_rating='',
                seller_feedback='',
                image_url=image_url,
                ebay_link=ebay_link,
                location='',
                listing_date='',
                watchers='',
                bids='',
                time_left='',
                is_auction=False,
                buy_it_now_available=True
            )
            
        except Exception as e:
            logger.error(f"Error parsing sold listing: {e}")
            return None
    
    def parse_active_listing(self, item_soup) -> Optional[eBayListing]:
        """Parse individual active listing"""
        try:
            # Title
            title_elem = item_soup.find('h3', class_='s-item__title')
            if not title_elem:
                return None
            title = title_elem.get_text(strip=True).replace('New Listing', '').strip()
            
            # Skip sponsored
            if 'SPONSORED' in title.upper():
                return None
            
            # Price
            price_elem = item_soup.find('span', class_='s-item__price')
            if not price_elem:
                return None
            
            price_text = price_elem.get_text(strip=True)
            price = self.extract_price(price_text)
            if price <= 0:
                return None
            
            # Shipping
            shipping_elem = item_soup.find('span', class_='s-item__shipping')
            shipping_cost = 0.0
            if shipping_elem:
                shipping_text = shipping_elem.get_text(strip=True)
                if 'free' not in shipping_text.lower():
                    shipping_cost = self.extract_price(shipping_text)
            
            # Link and item ID
            link_elem = item_soup.find('a', class_='s-item__link')
            if not link_elem:
                return None
            
            ebay_link = link_elem.get('href', '')
            item_id = self.extract_item_id(ebay_link)
            
            # Other details
            img_elem = item_soup.find('img', class_='s-item__image')
            image_url = img_elem.get('src', '') if img_elem else ''
            
            condition_elem = item_soup.find('span', class_='SECONDARY_INFO')
            condition = condition_elem.get_text(strip=True) if condition_elem else 'Used'
            
            return eBayListing(
                item_id=item_id,
                title=title,
                price=price,
                shipping_cost=shipping_cost,
                total_cost=price + shipping_cost,
                condition=condition,
                seller_username='',
                seller_rating='',
                seller_feedback='',
                image_url=image_url,
                ebay_link=ebay_link,
                location='',
                listing_date='',
                watchers='',
                bids='',
                time_left='',
                is_auction=False,
                buy_it_now_available=True
            )
            
        except Exception as e:
            logger.error(f"Error parsing active listing: {e}")
            return None
    
    def extract_price(self, price_text: str) -> float:
        """Extract numerical price from text"""
        try:
            # Remove currency symbols and extra text
            price_text = re.sub(r'[^\d.,]', '', price_text)
            price_text = price_text.replace(',', '')
            
            if not price_text:
                return 0.0
            
            return float(price_text)
        except:
            return 0.0
    
    def extract_item_id(self, url: str) -> str:
        """Extract eBay item ID from URL"""
        try:
            match = re.search(r'/itm/(\d+)', url)
            return match.group(1) if match else f"unknown_{random.randint(100000, 999999)}"
        except:
            return f"unknown_{random.randint(100000, 999999)}"
    
    def scan_category_for_arbitrage(self, category: str, min_profit: float = 15.0) -> List[Dict]:
        """Enhanced category scanning with better coverage"""
        
        logger.info(f"🎯 Enhanced scanning category: {category}")
        
        search_terms = self.get_enhanced_search_terms(category)
        if not search_terms:
            logger.warning(f"No search terms defined for category: {category}")
            return []
        
        all_listings = []
        
        # Sample multiple search terms for better coverage
        selected_terms = random.sample(search_terms, min(6, len(search_terms)))
        
        for search_term in selected_terms:
            logger.info(f"🔍 Searching: {search_term}")
            
            try:
                # Get both active and sold listings
                active_listings = self.search_ebay_active_listings(search_term, max_pages=3)
                sold_listings = self.search_ebay_sold_listings(search_term, max_pages=2)
                
                # Combine and add variety
                combined = active_listings + sold_listings
                all_listings.extend(combined)
                
                # Add delay between searches
                time.sleep(random.uniform(2.0, 4.0))
                
            except Exception as e:
                logger.error(f"Error searching '{search_term}': {e}")
                continue
        
        if not all_listings:
            logger.warning(f"No listings found for category: {category}")
            return []
        
        # Remove duplicates by item_id
        unique_listings = {}
        for listing in all_listings:
            if listing.item_id not in unique_listings:
                unique_listings[listing.item_id] = listing
        
        final_listings = list(unique_listings.values())
        logger.info(f"📊 Processing {len(final_listings)} unique listings for {category}")
        
        # Find arbitrage opportunities
        opportunities = self.arbitrage_detector.find_arbitrage_opportunities(
            final_listings, min_profit
        )
        
        logger.info(f"✅ Found {len(opportunities)} opportunities in {category}")
        return opportunities


def main():
    """Enhanced main function for testing"""
    
    scraper = EnhancedeBayScraper()
    
    # Test all categories
    categories = ['tech', 'gaming', 'collectibles', 'fashion']
    
    for category in categories:
        print(f"\n{'='*50}")
        print(f"🎯 SCANNING CATEGORY: {category.upper()}")
        print(f"{'='*50}")
        
        try:
            opportunities = scraper.scan_category_for_arbitrage(category, min_profit=12.0)
            
            if opportunities:
                print(f"✅ Found {len(opportunities)} opportunities in {category}:")
                
                for i, opp in enumerate(opportunities[:5], 1):
                    print(f"\n{i}. OPPORTUNITY #{opp['opportunity_id']}")
                    print(f"   📦 BUY: {opp['buy_listing']['title'][:60]}...")
                    print(f"   💰 Buy Price: ${opp['buy_listing']['total_cost']:.2f}")
                    print(f"   🎯 Sell Reference: ${opp['sell_reference']['price']:.2f}")
                    print(f"   💵 Net Profit: ${opp['net_profit_after_fees']:.2f}")
                    print(f"   📈 ROI: {opp['roi_percentage']:.1f}%")
                    print(f"   🔄 Similarity: {opp['similarity_score']:.3f}")
                    print(f"   ⭐ Confidence: {opp['confidence_score']}%")
                    print(f"   ⚠️  Risk: {opp['risk_level']}")
            else:
                print(f"❌ No opportunities found in {category}")
                
        except Exception as e:
            print(f"❌ Error scanning {category}: {e}")
            logger.error(f"Category scan error for {category}: {e}")
        
        # Delay between categories
        time.sleep(5)

if __name__ == "__main__":
    main()
