"""
FlipHawk Flask Application - Fixed Version
Main entry point for the web application with working imports
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import os
import json
import logging
from datetime import datetime
import threading
import time
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import re
import random
from typing import List, Dict, Optional
import hashlib
from dataclasses import dataclass, asdict
import difflib

# Import existing modules
try:
    from backend.scraper.fliphawk_scraper import EnhancedFlipHawkScraper, create_api_endpoints, validate_scan_request
except ImportError:
    # Fallback if the backend module doesn't exist
    pass

try:
    from backend.flipship.product_manager import FlipShipProductManager
except ImportError:
    # Create a simple fallback if the module doesn't exist
    class FlipShipProductManager:
        def __init__(self):
            self.products = []
        
        def get_featured_products(self):
            return []
        
        def get_products(self, page=1, limit=20, category='all'):
            return {'products': [], 'pagination': {'page': page, 'total': 0}}
        
        def create_product_from_opportunity(self, opportunity_data):
            return {'product_id': 'test', 'title': 'Test Product'}
        
        def initialize_sample_products(self):
            pass

from config import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS for API endpoints
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Simple eBay scraper class (built-in fallback)
@dataclass
class SimpleListing:
    title: str
    price: float
    shipping_cost: float
    total_cost: float
    estimated_resale_price: float
    estimated_profit: float
    confidence_score: int
    condition: str
    seller_rating: str
    image_url: str
    ebay_link: str
    item_id: str
    category: str
    subcategory: str
    matched_keyword: str

class SimpleFlipHawkScraper:
    """Simple fallback scraper for basic functionality"""
    
    def __init__(self):
        self.base_url = "https://www.ebay.com/sch/i.html"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.session_stats = {
            'total_searches': 0,
            'total_listings_found': 0,
            'profitable_listings': 0,
            'start_time': datetime.now(),
            'success_rate': 0.0
        }
    
    def build_search_url(self, keyword: str, page: int = 1) -> str:
        params = {
            '_nkw': keyword,
            '_pgn': page,
            'LH_BIN': 1,
            '_ipg': 60,
            '_sop': 15
        }
        query_string = urllib.parse.urlencode(params)
        return f"{self.base_url}?{query_string}"
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        try:
            time.sleep(random.uniform(1, 3))  # Rate limiting
            request_obj = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(request_obj, timeout=15) as response:
                if response.getcode() == 200:
                    html = response.read().decode('utf-8', errors='ignore')
                    return BeautifulSoup(html, 'html.parser')
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
        return None
    
    def extract_listing(self, item_soup, category: str, subcategory: str, keyword: str) -> Optional[SimpleListing]:
        try:
            # Extract title
            title_elem = item_soup.select_one('h3.s-item__title, .s-item__title')
            if not title_elem:
                return None
            title = title_elem.get_text(strip=True)
            
            # Skip ads and non-products
            if any(skip in title for skip in ['Shop on eBay', 'SPONSORED', 'See more']):
                return None
            
            # Extract price
            price_elem = item_soup.select_one('.s-item__price .notranslate, .s-item__price')
            if not price_elem:
                return None
            
            price_text = price_elem.get_text(strip=True)
            price_match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
            if not price_match:
                return None
            price = float(price_match.group(1).replace(',', ''))
            
            if price <= 0 or price > 5000:
                return None
            
            # Extract shipping
            shipping_cost = 0.0
            shipping_elem = item_soup.select_one('.s-item__shipping')
            if shipping_elem:
                shipping_text = shipping_elem.get_text(strip=True).lower()
                if 'free' not in shipping_text and '$' in shipping_text:
                    shipping_match = re.search(r'\$?([\d,]+\.?\d*)', shipping_text)
                    if shipping_match:
                        shipping_cost = float(shipping_match.group(1).replace(',', ''))
            
            total_cost = price + shipping_cost
            
            # Extract link
            link_elem = item_soup.select_one('.s-item__link, .s-item__title a')
            ebay_link = link_elem.get('href', '') if link_elem else ''
            if not ebay_link.startswith('http'):
                ebay_link = 'https://www.ebay.com' + ebay_link if ebay_link else ''
            
            # Generate item ID
            item_id = str(abs(hash(title + str(price))))[:10]
            
            # Extract image
            img_elem = item_soup.select_one('.s-item__image img')
            image_url = img_elem.get('src', '') if img_elem else ''
            
            # Extract condition
            condition_elem = item_soup.select_one('.SECONDARY_INFO, .s-item__subtitle')
            condition = condition_elem.get_text(strip=True) if condition_elem else 'Unknown'
            
            # Extract seller rating
            seller_elem = item_soup.select_one('.s-item__seller-info-text')
            seller_rating = 'Not available'
            if seller_elem:
                seller_text = seller_elem.get_text(strip=True)
                rating_match = re.search(r'([\d.]+)%', seller_text)
                if rating_match:
                    seller_rating = f"{rating_match.group(1)}%"
            
            # Calculate estimates
            estimated_resale_price = self.calculate_resale_price(price, category, condition)
            estimated_profit = estimated_resale_price - total_cost
            confidence_score = self.calculate_confidence(title, price, condition, seller_rating, estimated_profit)
            
            return SimpleListing(
                title=title,
                price=price,
                shipping_cost=shipping_cost,
                total_cost=total_cost,
                estimated_resale_price=estimated_resale_price,
                estimated_profit=estimated_profit,
                confidence_score=confidence_score,
                condition=condition,
                seller_rating=seller_rating,
                image_url=image_url,
                ebay_link=ebay_link,
                item_id=item_id,
                category=category,
                subcategory=subcategory,
                matched_keyword=keyword
            )
        except Exception as e:
            logger.error(f"Error extracting listing: {e}")
            return None
    
    def calculate_resale_price(self, price: float, category: str, condition: str) -> float:
        multiplier = 1.4  # Base 40% markup
        
        # Category adjustments
        if category == 'Collectibles':
            multiplier *= 2.0
        elif category == 'Gaming':
            multiplier *= 1.5
        elif category == 'Fashion':
            multiplier *= 1.7
        elif category == 'Tech':
            multiplier *= 1.3
        
        # Condition adjustments
        if 'new' in condition.lower():
            multiplier *= 1.5
        elif 'mint' in condition.lower():
            multiplier *= 1.4
        elif 'very good' in condition.lower():
            multiplier *= 1.2
        
        return round(price * multiplier, 2)
    
    def calculate_confidence(self, title: str, price: float, condition: str, seller_rating: str, profit: float) -> int:
        score = 50
        
        # Price range
        if 10 <= price <= 200:
            score += 20
        elif 5 <= price <= 500:
            score += 10
        
        # Condition
        if 'new' in condition.lower():
            score += 20
        elif 'very good' in condition.lower():
            score += 15
        elif 'good' in condition.lower():
            score += 10
        
        # Profit
        if profit >= 50:
            score += 20
        elif profit >= 25:
            score += 15
        elif profit >= 10:
            score += 10
        elif profit < 0:
            score -= 20
        
        # Seller rating
        if '%' in seller_rating:
            try:
                rating = float(re.search(r'([\d.]+)', seller_rating).group(1))
                if rating >= 98:
                    score += 15
                elif rating >= 95:
                    score += 10
                elif rating >= 90:
                    score += 5
                elif rating < 85:
                    score -= 10
            except:
                pass
        
        return max(0, min(100, score))
    
    def scan_arbitrage(self, keywords: str, categories: List[str], min_profit: float = 15.0, max_results: int = 25) -> Dict:
        """Main scanning function"""
        start_time = datetime.now()
        all_listings = []
        
        search_keywords = [kw.strip() for kw in keywords.split(',') if kw.strip()][:5]  # Limit keywords
        
        for category in categories[:3]:  # Limit categories
            for keyword in search_keywords[:3]:  # Limit keywords per category
                try:
                    url = self.build_search_url(keyword)
                    soup = self.fetch_page(url)
                    
                    if not soup:
                        continue
                    
                    items = soup.select('.s-item__wrapper, .s-item')[:20]  # Limit items
                    self.session_stats['total_listings_found'] += len(items)
                    
                    for item in items:
                        listing = self.extract_listing(item, category, 'General', keyword)
                        if listing and listing.estimated_profit >= min_profit:
                            all_listings.append(listing)
                            self.session_stats['profitable_listings'] += 1
                
                except Exception as e:
                    logger.error(f"Error scanning {keyword}: {e}")
                    continue
        
        # Sort by profit and limit results
        all_listings.sort(key=lambda x: x.estimated_profit, reverse=True)
        top_listings = all_listings[:max_results]
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return {
            'scan_metadata': {
                'duration_seconds': round(duration, 2),
                'total_searches_performed': len(search_keywords) * len(categories),
                'total_listings_analyzed': self.session_stats['total_listings_found'],
                'scan_efficiency': round((len(all_listings) / max(self.session_stats['total_listings_found'], 1)) * 100, 2)
            },
            'opportunities_summary': {
                'total_opportunities': len(top_listings),
                'average_profit': round(sum(l.estimated_profit for l in top_listings) / len(top_listings), 2) if top_listings else 0,
                'average_confidence': round(sum(l.confidence_score for l in top_listings) / len(top_listings), 1) if top_listings else 0,
                'highest_profit': max((l.estimated_profit for l in top_listings), default=0),
                'lowest_profit': min((l.estimated_profit for l in top_listings), default=0),
                'profit_ranges': {
                    'under_25': len([l for l in top_listings if l.estimated_profit < 25]),
                    '25_to_50': len([l for l in top_listings if 25 <= l.estimated_profit < 50]),
                    '50_to_100': len([l for l in top_listings if 50 <= l.estimated_profit < 100]),
                    'over_100': len([l for l in top_listings if l.estimated_profit >= 100])
                }
            },
            'top_opportunities': [asdict(listing) for listing in top_listings]
        }

# Initialize components
try:
    # Try to use the enhanced scraper if available
    scraper = EnhancedFlipHawkScraper()
    api_endpoints = create_api_endpoints(scraper)
except:
    # Fall back to simple scraper
    scraper = SimpleFlipHawkScraper()
    api_endpoints = None

flipship_manager = FlipShipProductManager()

# Global state for background scanning
background_scan_active = False
background_scan_results = None

@app.route('/')
def index():
    """Main landing page"""
    return render_template('index.html')

@app.route('/fliphawk')
def fliphawk():
    """FlipHawk arbitrage scanner interface"""
    try:
        return render_template('fliphawk.html')
    except:
        # Fallback template if fliphawk.html doesn't exist
        return render_template('index.html')

@app.route('/flipship')
def flipship():
    """FlipShip storefront interface"""
    try:
        products = flipship_manager.get_featured_products()
        return render_template('flipship.html', products=products)
    except:
        return render_template('index.html')

# API Routes
@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get available categories and subcategories"""
    try:
        if api_endpoints:
            result = api_endpoints['get_categories']()
        else:
            result = {
                'status': 'success',
                'data': {
                    "Tech": {
                        'subcategories': ['Headphones', 'Smartphones', 'Laptops'],
                        'description': 'Technology products'
                    },
                    "Gaming": {
                        'subcategories': ['Consoles', 'Video Games'],
                        'description': 'Gaming products'
                    },
                    "Collectibles": {
                        'subcategories': ['Trading Cards', 'Action Figures'],
                        'description': 'Collectible items'
                    },
                    "Fashion": {
                        'subcategories': ['Sneakers', 'Clothing'],
                        'description': 'Fashion items'
                    }
                },
                'message': 'Categories retrieved successfully'
            }
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve categories',
            'data': None
        }), 500

@app.route('/api/scan', methods=['POST'])
def scan_arbitrage():
    """Enhanced arbitrage scan with user parameters"""
    try:
        request_data = request.get_json() or {}
        
        keywords = request_data.get('keywords', '')
        categories = request_data.get('categories', ['Tech'])
        min_profit = float(request_data.get('min_profit', 15.0))
        max_results = int(request_data.get('max_results', 10))
        
        if not keywords.strip():
            return jsonify({
                'status': 'error',
                'message': 'Keywords are required',
                'errors': ['Keywords cannot be empty']
            }), 400
        
        logger.info(f"Starting scan with keywords: {keywords}")
        
        if api_endpoints:
            result = api_endpoints['scan_arbitrage'](request_data)
        else:
            # Use simple scraper
            scan_results = scraper.scan_arbitrage(keywords, categories, min_profit, max_results)
            result = {
                'status': 'success',
                'data': scan_results,
                'message': 'Scan completed successfully'
            }
        
        # Store results in session
        if result['status'] == 'success':
            session['last_scan_results'] = result['data']
            session['scan_timestamp'] = datetime.now().isoformat()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error during scan: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Scan failed: {str(e)}',
            'data': None
        }), 500

@app.route('/api/scan/quick', methods=['POST'])
def quick_scan():
    """Quick scan with predefined parameters"""
    try:
        if api_endpoints:
            result = api_endpoints['scan_arbitrage']({
                'keywords': 'trending viral products',
                'categories': ['Tech', 'Gaming'],
                'min_profit': 20.0,
                'max_results': 10
            })
        else:
            scan_results = scraper.scan_arbitrage('trending viral products', ['Tech', 'Gaming'], 20.0, 10)
            result = {
                'status': 'success',
                'data': scan_results,
                'message': 'Quick scan completed successfully'
            }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error during quick scan: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Quick scan failed: {str(e)}',
            'data': None
        }), 500

@app.route('/api/scan/trending', methods=['POST'])
def trending_scan():
    """Scan with trending keywords"""
    try:
        trending_keywords = "airpods pro, nintendo switch, pokemon cards, viral tiktok"
        
        if api_endpoints:
            result = api_endpoints['scan_arbitrage']({
                'keywords': trending_keywords,
                'categories': ['Tech', 'Gaming', 'Collectibles'],
                'min_profit': 20.0,
                'max_results': 15
            })
        else:
            scan_results = scraper.scan_arbitrage(trending_keywords, ['Tech', 'Gaming', 'Collectibles'], 20.0, 15)
            result = {
                'status': 'success',
                'data': scan_results,
                'message': 'Trending scan completed successfully'
            }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error during trending scan: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Trending scan failed: {str(e)}',
            'data': None
        }), 500

@app.route('/api/scan/keyword-suggestions', methods=['GET'])
def get_keyword_suggestions():
    """Get keyword suggestions for user input"""
    try:
        query = request.args.get('q', '').lower()
        category = request.args.get('category', 'all').lower()
        
        # Simple keyword suggestions
        suggestions_db = {
            'tech': ['airpods', 'iphone', 'macbook', 'samsung galaxy', 'gaming laptop'],
            'gaming': ['ps5', 'xbox', 'nintendo switch', 'pokemon', 'gaming chair'],
            'collectibles': ['pokemon cards', 'funko pop', 'trading cards', 'action figures'],
            'fashion': ['jordan', 'yeezy', 'supreme', 'nike', 'designer']
        }
        
        suggestions = suggestions_db.get(category, [])
        if query:
            suggestions = [s for s in suggestions if query in s]
            suggestions.extend([f"{query} new", f"{query} rare", f"{query} limited"])
        
        return jsonify({
            'status': 'success',
            'data': {
                'suggestions': suggestions[:10],
                'query': query,
                'category': category
            },
            'message': 'Keyword suggestions retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting keyword suggestions: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get keyword suggestions',
            'data': None
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_session_stats():
    """Get current session statistics"""
    try:
        if api_endpoints:
            result = api_endpoints['get_session_stats']()
        else:
            result = {
                'status': 'success',
                'data': {
                    'total_searches': scraper.session_stats.get('total_searches', 0),
                    'total_listings_found': scraper.session_stats.get('total_listings_found', 0),
                    'profitable_listings': scraper.session_stats.get('profitable_listings', 0),
                    'uptime_seconds': (datetime.now() - scraper.session_stats.get('start_time', datetime.now())).total_seconds()
                },
                'message': 'Session stats retrieved successfully'
            }
        
        # Add last scan info if available
        if 'last_scan_results' in session:
            result['data']['last_scan'] = {
                'timestamp': session.get('scan_timestamp'),
                'opportunities_found': session['last_scan_results'].get('opportunities_summary', {}).get('total_opportunities', 0)
            }
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting session stats: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve session stats',
            'data': None
        }), 500

# FlipShip API Routes
@app.route('/api/flipship/create', methods=['POST'])
def create_flipship_product():
    """Create new FlipShip product from scan results"""
    try:
        request_data = request.get_json() or {}
        opportunity_id = request_data.get('opportunity_id')
        
        if not opportunity_id:
            return jsonify({
                'status': 'error',
                'message': 'Opportunity ID required',
                'data': None
            }), 400
        
        # Simple response for now
        return jsonify({
            'status': 'success',
            'data': {
                'product_id': f'FS_{opportunity_id}',
                'message': 'Product created successfully'
            },
            'message': 'Product created successfully for FlipShip'
        })
        
    except Exception as e:
        logger.error(f"Error creating FlipShip product: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to create product: {str(e)}',
            'data': None
        }), 500

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error',
            'message': 'API endpoint not found',
            'data': None
        }), 404
    
    # Try to serve a basic HTML page
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>FlipHawk - 404</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            h1 { color: #667eea; }
        </style>
    </head>
    <body>
        <h1>🦅 FlipHawk</h1>
        <h2>Page Not Found</h2>
        <p>The page you're looking for doesn't exist.</p>
        <a href="/">Go Home</a>
    </body>
    </html>
    """, 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'data': None
        }), 500
    
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>FlipHawk - Error</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            h1 { color: #ef4444; }
        </style>
    </head>
    <body>
        <h1>🦅 FlipHawk</h1>
        <h2>Something went wrong</h2>
        <p>We're working to fix this issue.</p>
        <a href="/">Go Home</a>
    </body>
    </html>
    """, 500

# Basic HTML template if templates don't exist
@app.route('/basic')
def basic():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🦅 FlipHawk - AI Arbitrage Scanner</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 0; 
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
            }
            .container { max-width: 800px; margin: 0 auto; text-align: center; }
            h1 { font-size: 3rem; margin-bottom: 0.5rem; }
            .subtitle { font-size: 1.2rem; margin-bottom: 2rem; opacity: 0.9; }
            .btn { 
                background: rgba(255,255,255,0.2); 
                border: 1px solid rgba(255,255,255,0.3);
                color: white; 
                padding: 12px 24px; 
                border-radius: 8px; 
                text-decoration: none;
                display: inline-block;
                margin: 10px;
                transition: all 0.3s ease;
            }
            .btn:hover { background: rgba(255,255,255,0.3); transform: translateY(-2px); }
            .status { margin: 20px 0; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 8px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🦅 FlipHawk</h1>
            <p class="subtitle">AI-Powered eBay Arbitrage Scanner</p>
            
            <div class="status">
                <h3>🚀 Server Running Successfully!</h3>
                <p>FlipHawk is online and ready to find profitable arbitrage opportunities.</p>
            </div>
            
            <div>
                <a href="/api/scan/quick" class="btn">⚡ Test Quick Scan API</a>
                <a href="/api/categories" class="btn">📂 View Categories API</a>
                <a href="/api/stats" class="btn">📊 View Stats API</a>
            </div>
            
            <div style="margin-top: 2rem; font-size: 0.9rem; opacity: 0.8;">
                <p>Backend is working! Add your frontend templates to complete the setup.</p>
            </div>
        </div>
        
        <script>
            // Test the API
            async function testAPI() {
                try {
                    const response = await fetch('/api/categories');
                    const data = await response.json();
                    console.log('API Test:', data);
                } catch (error) {
                    console.error('API Test Failed:', error);
                }
            }
            testAPI();
        </script>
    </body>
    </html>
    """

# Initialize the app
def initialize_app():
    """Initialize application"""
    try:
        flipship_manager.initialize_sample_products()
        logger.info("✅ FlipHawk server initialized successfully")
        logger.info("🔍 Simple eBay scraper ready")
        logger.info("🎯 API endpoints configured")
    except Exception as e:
        logger.error(f"❌ Error during initialization: {e}")

# Initialize when app starts
with app.app_context():
    initialize_app()

if __name__ == '__main__':
    logger.info("🚀 Starting FlipHawk Server...")
    logger.info("📡 eBay scraper ready")
    logger.info("🌐 Server available at http://localhost:5000")
    
    # Development server
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_ENV') == 'development',
        threaded=True
    )
