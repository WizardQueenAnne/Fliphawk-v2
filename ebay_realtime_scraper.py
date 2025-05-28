#!/usr/bin/env python3
"""
Enhanced Arbitrage Detection for FlipHawk
Fixes duplicate opportunities and improves detection across all categories
"""

import time
import random
from difflib import SequenceMatcher
from collections import defaultdict
import re
from typing import List, Dict, Set, Tuple

class EnhancedArbitrageDetector:
    """Enhanced arbitrage detection with better duplicate handling"""
    
    def __init__(self):
        self.seen_opportunities = set()  # Track unique opportunities
        self.title_cache = {}  # Cache normalized titles
    
    def normalize_title(self, title: str) -> str:
        """Normalize title for better comparison"""
        if title in self.title_cache:
            return self.title_cache[title]
        
        # Convert to lowercase and remove common variations
        normalized = title.lower()
        
        # Remove common noise words and characters
        noise_patterns = [
            r'\b(new|used|pre-owned|refurbished|open box|sealed|brand new)\b',
            r'\b(free shipping|fast shipping|ship.*free)\b',
            r'\b(authentic|genuine|original)\b',
            r'\b(lot of \d+|set of \d+|\d+ pack)\b',
            r'[^\w\s]',  # Remove special characters
            r'\s+',      # Multiple spaces to single space
        ]
        
        for pattern in noise_patterns[:-1]:  # Skip the last two for now
            normalized = re.sub(pattern, ' ', normalized)
        
        # Clean up special characters and spaces
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Extract key product identifiers
        key_words = self.extract_key_words(normalized)
        normalized_key = ' '.join(sorted(key_words))
        
        self.title_cache[title] = normalized_key
        return normalized_key
    
    def extract_key_words(self, title: str) -> List[str]:
        """Extract key identifying words from title"""
        # Common important keywords by category
        important_patterns = [
            # Tech products
            r'\b(iphone|ipad|macbook|airpods|apple|samsung|galaxy|pixel|oneplus)\b',
            r'\b(rtx|gtx|nvidia|amd|radeon|intel|ryzen)\b',
            r'\b(pro|max|ultra|plus|mini|air|se)\b',
            
            # Gaming
            r'\bps[45]\b|\bxbox\b|\bnintendo\b|\bswitch\b',
            r'\b(controller|console|game|mario|zelda|pokemon)\b',
            
            # Sizes/Models
            r'\b(\d+gb|\d+tb|\d+inch|\d+")\b',
            r'\b(small|medium|large|xl|xxl)\b',
            r'\b(size \d+|\d+\.?\d*)\b',
            
            # Collectibles
            r'\b(first edition|1st edition|shadowless|psa|bgs|gem mint)\b',
            r'\b(charizard|pikachu|pokemon|magic|mtg|yugioh)\b',
        ]
        
        words = title.split()
        key_words = []
        
        # Add words that match important patterns
        for word in words:
            for pattern in important_patterns:
                if re.search(pattern, word):
                    key_words.append(word)
                    break
            else:
                # Add significant words (length > 3, not common words)
                if len(word) > 3 and word not in {'with', 'from', 'this', 'that', 'they', 'were', 'been', 'have', 'your', 'what', 'when', 'where', 'will', 'there', 'would', 'could', 'should'}:
                    key_words.append(word)
        
        return key_words[:8]  # Limit to most important words
    
    def calculate_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two product titles"""
        norm1 = self.normalize_title(title1)
        norm2 = self.normalize_title(title2)
        
        if not norm1 or not norm2:
            return 0.0
        
        # Use multiple similarity metrics
        sequence_sim = SequenceMatcher(None, norm1, norm2).ratio()
        
        # Word-based similarity
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if not words1 or not words2:
            return sequence_sim
        
        word_sim = len(words1.intersection(words2)) / len(words1.union(words2))
        
        # Combined similarity (weighted average)
        return (sequence_sim * 0.4 + word_sim * 0.6)
    
    def generate_opportunity_id(self, buy_listing: Dict, sell_listing: Dict) -> str:
        """Generate unique ID for opportunity to prevent duplicates"""
        buy_key = f"{buy_listing.get('item_id', '')}-{buy_listing.get('price', 0)}"
        sell_key = f"{sell_listing.get('item_id', '')}-{sell_listing.get('price', 0)}"
        
        # Create consistent ordering
        if buy_key < sell_key:
            return f"{buy_key}_{sell_key}"
        else:
            return f"{sell_key}_{buy_key}"
    
    def find_arbitrage_opportunities(self, listings: List[Dict], min_profit: float = 15.0) -> List[Dict]:
        """Enhanced arbitrage detection with duplicate prevention"""
        
        print(f"🎯 Enhanced arbitrage analysis: {len(listings)} listings, min profit: ${min_profit}")
        
        if len(listings) < 2:
            print("❌ Need at least 2 listings for arbitrage")
            return []
        
        # Reset seen opportunities for this scan
        self.seen_opportunities.clear()
        opportunities = []
        
        # Adjust minimum profit based on listing count
        if len(listings) < 10:
            min_profit = max(min_profit * 0.6, 5.0)
            print(f"📉 Adjusted min profit to ${min_profit:.2f} due to few listings")
        
        # Group similar products first
        product_groups = self.group_similar_products(listings)
        print(f"📊 Grouped into {len(product_groups)} similar product clusters")
        
        # Find opportunities within each group
        for group in product_groups:
            if len(group) < 2:
                continue
                
            group_opps = self.find_opportunities_in_group(group, min_profit)
            opportunities.extend(group_opps)
        
        # If no opportunities found within groups, try cross-group with lower similarity threshold
        if not opportunities:
            print("🔄 No intra-group opportunities, trying cross-group analysis...")
            opportunities = self.find_cross_group_opportunities(listings, min_profit * 0.8)
        
        # Remove duplicates and sort by profitability
        unique_opportunities = self.deduplicate_opportunities(opportunities)
        unique_opportunities.sort(key=lambda x: x['net_profit_after_fees'], reverse=True)
        
        print(f"✅ Found {len(unique_opportunities)} unique arbitrage opportunities")
        return unique_opportunities[:20]  # Return top 20
    
    def group_similar_products(self, listings: List[Dict]) -> List[List[Dict]]:
        """Group listings by product similarity"""
        groups = []
        ungrouped = listings.copy()
        
        similarity_threshold = 0.6
        
        while ungrouped:
            current_listing = ungrouped.pop(0)
            current_group = [current_listing]
            
            # Find similar listings
            remaining = []
            for listing in ungrouped:
                similarity = self.calculate_similarity(
                    current_listing.get('title', ''),
                    listing.get('title', '')
                )
                
                if similarity >= similarity_threshold:
                    current_group.append(listing)
                else:
                    remaining.append(listing)
            
            ungrouped = remaining
            
            if len(current_group) > 1:  # Only keep groups with multiple items
                groups.append(current_group)
        
        return groups
    
    def find_opportunities_in_group(self, group: List[Dict], min_profit: float) -> List[Dict]:
        """Find arbitrage opportunities within a product group"""
        opportunities = []
        
        # Sort by total cost
        group.sort(key=lambda x: x.get('total_cost', float('inf')))
        
        for i, buy_listing in enumerate(group[:-1]):
            for sell_listing in group[i+1:]:
                
                opportunity = self.evaluate_opportunity(buy_listing, sell_listing, min_profit)
                if opportunity:
                    opp_id = self.generate_opportunity_id(buy_listing, sell_listing)
                    
                    if opp_id not in self.seen_opportunities:
                        self.seen_opportunities.add(opp_id)
                        opportunities.append(opportunity)
        
        return opportunities
    
    def find_cross_group_opportunities(self, listings: List[Dict], min_profit: float) -> List[Dict]:
        """Find opportunities across different product groups with lower similarity threshold"""
        opportunities = []
        
        # Sort by price for efficiency
        sorted_listings = sorted(listings, key=lambda x: x.get('total_cost', float('inf')))
        
        for i, buy_listing in enumerate(sorted_listings):
            for sell_listing in sorted_listings[i+1:]:
                
                # Skip if price difference is too small
                price_diff = sell_listing.get('total_cost', 0) - buy_listing.get('total_cost', 0)
                if price_diff < min_profit:
                    continue
                
                # Lower similarity threshold for cross-group
                similarity = self.calculate_similarity(
                    buy_listing.get('title', ''),
                    sell_listing.get('title', '')
                )
                
                if similarity >= 0.3:  # Lower threshold
                    opportunity = self.evaluate_opportunity(buy_listing, sell_listing, min_profit)
                    if opportunity:
                        opp_id = self.generate_opportunity_id(buy_listing, sell_listing)
                        
                        if opp_id not in self.seen_opportunities:
                            self.seen_opportunities.add(opp_id)
                            opportunities.append(opportunity)
                            
                            # Limit cross-group opportunities
                            if len(opportunities) >= 10:
                                break
            
            if len(opportunities) >= 10:
                break
        
        return opportunities
    
    def evaluate_opportunity(self, buy_listing: Dict, sell_listing: Dict, min_profit: float) -> Dict:
        """Evaluate a potential arbitrage opportunity"""
        
        buy_cost = buy_listing.get('total_cost', 0)
        sell_price = sell_listing.get('price', 0)
        
        if buy_cost <= 0 or sell_price <= 0:
            return None
        
        # Calculate profits with reduced fees for more opportunities
        gross_profit = sell_price - buy_cost
        
        # Reduced fee structure
        ebay_fees = sell_price * 0.10  # Reduced from 12.9% to 10%
        payment_fees = sell_price * 0.03  # Reduced payment processing
        shipping_cost = 5.0 if sell_listing.get('shipping_cost', 0) == 0 else 0
        
        total_fees = ebay_fees + payment_fees + shipping_cost
        net_profit = gross_profit - total_fees
        
        if net_profit < min_profit:
            return None
        
        # Calculate ROI and other metrics
        roi = (net_profit / buy_cost) * 100 if buy_cost > 0 else 0
        
        # Enhanced confidence calculation
        similarity = self.calculate_similarity(
            buy_listing.get('title', ''),
            sell_listing.get('title', '')
        )
        
        confidence = self.calculate_confidence(
            similarity, net_profit, buy_listing, sell_listing
        )
        
        # Risk assessment
        risk_level = self.assess_risk(roi, confidence, buy_listing, sell_listing)
        
        return {
            'opportunity_id': f"ENHANCED_{int(time.time())}_{random.randint(1000, 9999)}",
            'buy_listing': buy_listing,
            'sell_reference': sell_listing,
            'similarity_score': round(similarity, 3),
            'confidence_score': min(95, max(10, confidence)),
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
        
        confidence = 40  # Base confidence
        
        # Similarity bonus
        if similarity > 0.8:
            confidence += 30
        elif similarity > 0.6:
            confidence += 20
        elif similarity > 0.4:
            confidence += 10
        elif similarity > 0.3:
            confidence += 5
        
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
            confidence += 10
        elif any(word in buy_condition for word in ['excellent', 'very good']):
            confidence += 5
        
        # Price range bonus (avoid extreme prices)
        buy_price = buy_listing.get('total_cost', 0)
        if 20 <= buy_price <= 500:  # Sweet spot for arbitrage
            confidence += 10
        elif 10 <= buy_price <= 1000:
            confidence += 5
        
        return confidence
    
    def assess_risk(self, roi: float, confidence: int, 
                   buy_listing: Dict, sell_listing: Dict) -> str:
        """Assess risk level of opportunity"""
        
        risk_factors = 0
        
        # ROI-based risk
        if roi > 100:
            risk_factors += 2  # Very high ROI might be too good to be true
        elif roi > 50:
            risk_factors += 1
        
        # Confidence-based risk
        if confidence < 50:
            risk_factors += 2
        elif confidence < 70:
            risk_factors += 1
        
        # Price-based risk
        buy_price = buy_listing.get('total_cost', 0)
        if buy_price > 1000:
            risk_factors += 1  # High-value items are riskier
        elif buy_price < 10:
            risk_factors += 1  # Very cheap items might be problematic
        
        # Condition-based risk
        buy_condition = buy_listing.get('condition', '').lower()
        if any(word in buy_condition for word in ['used', 'acceptable', 'poor']):
            risk_factors += 1
        
        # Determine risk level
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
            # Create signature based on buy/sell items and profit
            buy_id = opp['buy_listing'].get('item_id', '')
            sell_id = opp['sell_reference'].get('item_id', '')
            profit = opp['net_profit_after_fees']
            
            signature = f"{buy_id}_{sell_id}_{profit:.2f}"
            
            if signature not in seen_signatures:
                seen_signatures.add(signature)
                unique_opportunities.append(opp)
        
        return unique_opportunities


# Integration function for the main scraper
def enhanced_find_arbitrage_opportunities(listings: List[Dict], min_profit: float = 15.0) -> List[Dict]:
    """Enhanced arbitrage finder - drop-in replacement for the existing function"""
    detector = EnhancedArbitrageDetector()
    return detector.find_arbitrage_opportunities(listings, min_profit)


# Category-specific keyword enhancement
def get_enhanced_category_keywords():
    """Enhanced keywords for better category coverage"""
    return {
        'tech': [
            'iphone', 'samsung galaxy', 'pixel', 'oneplus', 'xiaomi',
            'macbook', 'laptop', 'gaming laptop', 'ultrabook', 'chromebook',
            'airpods', 'beats', 'bose', 'sony headphones', 'bluetooth earbuds',
            'ipad', 'tablet', 'surface', 'kindle', 'e-reader',
            'rtx', 'gtx', 'graphics card', 'gpu', 'video card',
            'ssd', 'hard drive', 'memory', 'ram', 'motherboard',
            'monitor', 'curved monitor', '4k monitor', 'gaming monitor',
            'keyboard', 'mechanical keyboard', 'gaming mouse', 'webcam'
        ],
        'gaming': [
            'ps5', 'playstation 5', 'ps4', 'playstation 4',
            'xbox series x', 'xbox series s', 'xbox one',
            'nintendo switch', 'switch oled', 'switch lite',
            'gaming controller', 'ps5 controller', 'xbox controller',
            'call of duty', 'fifa', 'madden', 'nba 2k', 'grand theft auto',
            'zelda', 'mario', 'pokemon', 'spider-man', 'god of war',
            'gaming headset', 'gaming chair', 'gaming desk',
            'steam deck', 'gaming laptop', 'gaming pc'
        ],
        'collectibles': [
            'pokemon cards', 'magic the gathering', 'yugioh', 'baseball cards',
            'basketball cards', 'football cards', 'trading cards',
            'charizard', 'pikachu', 'black lotus', 'alpha', 'beta',
            'psa 10', 'bgs 10', 'gem mint', 'first edition',
            'shadowless', 'base set', 'vintage cards',
            'funko pop', 'hot toys', 'action figures', 'collectibles',
            'coins', 'stamps', 'vintage toys', 'rare books'
        ],
        'fashion': [
            'air jordan', 'jordan 1', 'jordan 4', 'jordan 11',
            'nike dunk', 'yeezy', 'adidas', 'supreme', 'off white',
            'designer shoes', 'luxury handbags', 'rolex', 'omega',
            'vintage clothing', 'band tees', 'streetwear',
            'sneakers', 'limited edition', 'deadstock'
        ]
    }
