"""
Debug version of the arbitrage scanner to see exactly what eBay is returning
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
    
    def calculate_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two product titles"""
        norm1 = self.normalize_title(title1)
        norm2 = self.normalize_title(title2)
        return difflib.SequenceMatcher(None, norm1, norm2).ratio()

class DebugArbitrageScanner:
    """Debug scanner to see exactly what eBay returns"""
    
    def __init__(self):
        self.base_url = "https://www.ebay.com/sch/i.html"
        self.product_matcher = ProductMatcher()
        self.seen_items = set()
        
        # More realistic headers
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
    
    def get_realistic_headers(self) -> Dict[str, str]:
        """Generate realistic browser headers"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
    
    def build_search_url(self, keyword: str, page: int = 1) -> str:
        """Build eBay search URL"""
        params = {
            '_nkw': keyword,
            '_pgn': page,
            'LH_BIN': 1,
            'LH_Complete': 0,
            'LH_Sold': 0,
            '_sop': 15,
            '_ipg': 60,
            'rt': 'nc',
            '_sacat': 0
        }
        
        query_string = urllib.parse.urlencode(params)
        return f"{self.base_url}?{query_string}"
    
    def fetch_and_debug_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch page and debug what we get back"""
        try:
            logger.info(f"🌐 Fetching URL: {url}")
            
            headers = self.get_realistic_headers()
            logger.info(f"📤 Using User-Agent: {headers['User-Agent'][:50]}...")
            
            time.sleep(random.uniform(2.0, 4.0))
            
            request = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(request, timeout=15) as response:
                status_code = response.getcode()
                logger.info(f"📥 Response status: {status_code}")
                
                if status_code == 200:
                    content = response.read()
                    logger.info(f"📊 Content length: {len(content)} bytes")
                    
                    # Check encoding
                    encoding = response.info().get_content_charset() or 'utf-8'
                    logger.info(f"🔤 Encoding: {encoding}")
                    
                    try:
                        html = content.decode(encoding)
                    except UnicodeDecodeError:
                        html = content.decode('utf-8', errors='ignore')
                        logger.warning("⚠️ Had to use error-ignore decoding")
                    
                    logger.info(f"📄 HTML length: {len(html)} characters")
                    
                    # Debug: Check what's in the HTML
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Check for blocking indicators
                    title = soup.find('title')
                    if title:
                        page_title = title.get_text().strip()
                        logger.info(f"📋 Page title: '{page_title}'")
                        
                        if any(block_word in page_title.lower() for block_word in [
                            'blocked', 'captcha', 'robot', 'security', 'verify'
                        ]):
                            logger.error(f"🚫 BLOCKED! Page title indicates blocking: {page_title}")
                            return None
                    
                    # Check for common eBay elements
                    search_results = soup.find('div', {'id': 'srp-river-results'})
                    if search_results:
                        logger.info("✅ Found main search results container")
                    else:
                        logger.warning("❌ Main search results container not found")
                    
                    # Check for items with multiple selectors
                    selectors_to_try = [
                        '.s-item__wrapper',
                        '.s-item',
                        '.srp-results .s-item',
                        '[data-testid="item"]',
                        '.item',
                        '.it'
                    ]
                    
                    total_items_found = 0
                    for selector in selectors_to_try:
                        items = soup.select(selector)
                        logger.info(f"🔍 Selector '{selector}': {len(items)} items")
                        total_items_found = max(total_items_found, len(items))
                    
                    # Check for "no results" messages
                    no_results_selectors = [
                        '.srp-save-null-search',
                        '.notfound',
                        '.s-answer-region',
                        '.no-results'
                    ]
                    
                    for selector in no_results_selectors:
                        no_results = soup.select_one(selector)
                        if no_results:
                            logger.warning(f"📭 Found 'no results' element: {selector}")
                            logger.warning(f"📭 Text: {no_results.get_text().strip()[:100]}")
                    
                    # Debug: Save a snippet of HTML for analysis
                    html_snippet = html[:2000] + "..." if len(html) > 2000 else html
                    logger.info(f"📄 HTML snippet (first 2000 chars):")
                    logger.info("=" * 50)
                    logger.info(html_snippet)
                    logger.info("=" * 50)
                    
                    if total_items_found > 0:
                        logger.info(f"✅ Found {total_items_found} total items using various selectors")
                        return soup
                    else:
                        logger.error("❌ No items found with any selector")
                        
                        # Check if this looks like eBay's actual search page
                        if 'ebay' in html.lower() and 'search' in html.lower():
                            logger.error("🤔 This looks like eBay's search page but with no items")
                            logger.error("🔍 Possible causes:")
                            logger.error("   - No search results for this keyword")
                            logger.error("   - eBay changed their HTML structure")
                            logger.error("   - Search results are loaded via JavaScript")
                            logger.error("   - Region-specific blocking")
                        else:
                            logger.error("🚫 This doesn't look like eBay's normal search page")
                            logger.error("   - Possible CAPTCHA or blocking page")
                            logger.error("   - Redirected to different page")
                        
                        return None
                
                else:
                    logger.error(f"❌ HTTP error: {status_code}")
                    return None
                    
        except urllib.error.HTTPError as e:
            logger.error(f"❌ HTTP Error: {e.code} - {e.reason}")
            return None
        except urllib.error.URLError as e:
            logger.error(f"❌ URL Error: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return None
    
    def scan_arbitrage_opportunities(self, keywords: str, categories: List[str],
                                   min_profit: float = 15.0, max_results: int = 25) -> Dict:
        """Debug scan to see what's happening"""
        logger.info(f"🚀 Starting DEBUG arbitrage scan for: '{keywords}'")
        start_time = datetime.now()
        
        # Try just the first keyword for debugging
        keyword = keywords.split(',')[0].strip()
        logger.info(f"🔍 DEBUG: Testing with single keyword: '{keyword}'")
        
        # Build URL
        url = self.build_search_url(keyword, 1)
        logger.info(f"🔗 Built URL: {url}")
        
        # Fetch and debug
        soup = self.fetch_and_debug_page(url)
        
        if soup is None:
            logger.error("❌ Failed to get valid page content")
            return {
                'scan_metadata': {
                    'duration_seconds': (datetime.now() - start_time).total_seconds(),
                    'total_searches_performed': 1,
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
                    'profit_ranges': {'under_25': 0, '25_to_50': 0, '50_to_100': 0, 'over_100': 0}
                },
                'top_opportunities': []
            }
        
        # If we got here, we have some content but no items
        # This suggests eBay is serving us a page but with no search results
        logger.info("✅ Got valid page content but no items found")
        logger.info("🔍 This suggests:")
        logger.info("   1. The keyword has no results")
        logger.info("   2. eBay changed their HTML structure") 
        logger.info("   3. Results are loaded via JavaScript (not accessible to basic scraping)")
        logger.info("   4. Geographic restrictions")
        
        # Return empty results
        return {
            'scan_metadata': {
                'duration_seconds': (datetime.now() - start_time).total_seconds(),
                'total_searches_performed': 1,
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
                'profit_ranges': {'under_25': 0, '25_to_50': 0, '50_to_100': 0, 'over_100': 0}
            },
            'top_opportunities': []
        }


# Create the alias for app.py compatibility
TrueArbitrageScanner = DebugArbitrageScanner

def create_arbitrage_api_endpoints(scanner):
    """Create Flask-compatible API endpoint functions"""
    
    def scan_arbitrage_opportunities(request_data: Dict) -> Dict:
        """Debug arbitrage scanning endpoint"""
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
                'message': 'Debug scan completed - check logs for details'
            }
            
        except Exception as e:
            logger.error(f"Debug scan failed: {e}")
            return {
                'status': 'error',
                'message': f'Debug scan failed: {str(e)}',
                'data': None
            }
    
    def quick_scan_endpoint() -> Dict:
        """Quick debug scan"""
        try:
            results = scanner.scan_arbitrage_opportunities(
                keywords="iphone",  # Simple keyword for testing
                categories=['General'],
                min_profit=20.0,
                max_results=15
            )
            
            return {
                'status': 'success',
                'data': results,
                'message': 'Debug quick scan completed - check logs'
            }
            
        except Exception as e:
            logger.error(f"Debug quick scan failed: {e}")
            return {
                'status': 'error',
                'message': f'Debug quick scan failed: {str(e)}',
                'data': None
            }
    
    def trending_scan_endpoint() -> Dict:
        """Trending debug scan"""
        try:
            results = scanner.scan_arbitrage_opportunities(
                keywords="nintendo",  # Simple keyword for testing
                categories=['General'],
                min_profit=25.0,
                max_results=20
            )
            
            return {
                'status': 'success',
                'data': results,
                'message': 'Debug trending scan completed - check logs'
            }
            
        except Exception as e:
            logger.error(f"Debug trending scan failed: {e}")
            return {
                'status': 'error',
                'message': f'Debug trending scan failed: {str(e)}',
                'data': None
            }
    
    return {
        'scan_arbitrage': scan_arbitrage_opportunities,
        'quick_scan': quick_scan_endpoint,
        'trending_scan': trending_scan_endpoint
    }
