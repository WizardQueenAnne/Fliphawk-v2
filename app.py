"""
FlipHawk Flask Application - Fixed Syntax Error
Main entry point with proper imports and syntax
"""

from flask import Flask, render_template, request, jsonify, session, render_template_string
from flask_cors import CORS
import os
import json
import logging
import random
import time
from datetime import datetime

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FlipShip manager import with fallback
try:
    from backend.flipship.product_manager import FlipShipProductManager
except ImportError:
    logger.warning("⚠️ FlipShip manager not found, using placeholder")
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

try:
    from config import Config
except ImportError:
    # Fallback config
    class Config:
        SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-fliphawk-2025'
        DEBUG = os.environ.get('FLASK_ENV') == 'development'

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

# Initialize components
flipship_manager = FlipShipProductManager()

@app.route('/')
def index():
    """Main landing page"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error loading index.html: {e}")
        return render_template_string(get_fallback_html())

@app.route('/fliphawk')
def fliphawk():
    """FlipHawk arbitrage scanner interface"""
    try:
        return render_template('fliphawk.html')
    except Exception as e:
        logger.error(f"Error loading fliphawk.html: {e}")
        return render_template_string(get_fallback_html())

@app.route('/flipship')
def flipship():
    """FlipShip storefront interface"""
    try:
        products = flipship_manager.get_featured_products()
        return render_template('flipship.html', products=products)
    except Exception as e:
        logger.error(f"Error loading flipship: {e}")
        return render_template_string(get_fallback_html())

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get available categories and subcategories"""
    try:
        result = {
            'status': 'success',
            'data': {
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
            },
            'message': 'Categories retrieved successfully',
            'api_source': 'FlipHawk Categories'
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
    """Enhanced arbitrage scan - NO REAL EBAY API (Educational Demo)"""
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
        
        logger.info(f"🔍 Starting arbitrage scan with keywords: '{keywords}'")
        
        # Simulate realistic scan time
        scan_start = datetime.now()
        time.sleep(random.uniform(1.0, 3.0))
        
        # Generate educational arbitrage data
        result = generate_arbitrage_opportunities(keywords, min_profit, max_results, categories[0] if categories else 'Tech')
        
        # Store results in session
        session['last_scan_results'] = result
        session['scan_timestamp'] = datetime.now().isoformat()
        session['total_scans'] = session.get('total_scans', 0) + 1
        session['total_opportunities'] = session.get('total_opportunities', 0) + result['opportunities_summary']['total_opportunities']
        
        scan_duration = (datetime.now() - scan_start).total_seconds()
        result['scan_metadata']['duration_seconds'] = round(scan_duration, 1)
        
        return jsonify({
            'status': 'success',
            'data': result,
            'message': f'Found {result["opportunities_summary"]["total_opportunities"]} arbitrage opportunities!'
        })
        
    except Exception as e:
        logger.error(f"Error during arbitrage scan: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Scan failed: {str(e)}',
            'data': None
        }), 500

def generate_arbitrage_opportunities(keywords, min_profit, max_results, category):
    """Generate educational arbitrage opportunities (NOT real eBay API data)"""
    
    # Educational arbitrage strategies
    strategies = [
        {
            'name': 'misspelled_listings',
            'description': 'Find misspelled eBay listings',
            'profit_range': (15, 45),
            'confidence_range': (75, 90),
            'risk': 'LOW'
        },
        {
            'name': 'poor_photos',
            'description': 'Items with bad photos sell cheap',
            'profit_range': (20, 60),
            'confidence_range': (70, 85),
            'risk': 'MEDIUM'
        },
        {
            'name': 'bulk_breaking',
            'description': 'Buy bulk lots, sell individually',
            'profit_range': (30, 100),
            'confidence_range': (80, 95),
            'risk': 'LOW'
        }
    ]
    
    # Sample products by category
    products = {
        'Tech': [
            {'name': 'Apple AirPods Pro 2nd Gen', 'price': 199},
            {'name': 'iPhone 14 Pro Max', 'price': 1099},
            {'name': 'MacBook Air M2', 'price': 1199}
        ],
        'Gaming': [
            {'name': 'Nintendo Switch OLED', 'price': 319},
            {'name': 'PlayStation 5 Console', 'price': 499},
            {'name': 'Xbox Series X', 'price': 499}
        ],
        'Collectibles': [
            {'name': 'Pokemon TCG Booster Box', 'price': 144},
            {'name': 'Funko Pop Exclusive', 'price': 25},
            {'name': 'Vintage Baseball Cards', 'price': 150}
        ],
        'Fashion': [
            {'name': 'Air Jordan 1 Retro', 'price': 179},
            {'name': 'Supreme Box Logo Hoodie', 'price': 178},
            {'name': 'Yeezy Boost 350', 'price': 230}
        ]
    }
    
    # Get relevant products
    category_products = products.get(category, products['Tech'])
    
    # Generate opportunities
    opportunities = []
    num_opportunities = min(max_results, random.randint(2, 5))
    
    for i in range(num_opportunities):
        strategy = random.choice(strategies)
        product = random.choice(category_products)
        
        # Calculate prices
        base_price = product['price']
        discount = random.uniform(0.15, 0.35)  # 15-35% discount
        buy_price = base_price * (1 - discount)
        shipping = random.uniform(0, 15)
        total_cost = buy_price + shipping
        
        # Market sell price
        sell_price = base_price * random.uniform(0.95, 1.10)
        
        # Calculate profit after fees
        gross_profit = sell_price - total_cost
        fees = sell_price * 0.16  # 16% total fees (eBay + PayPal)
        net_profit = gross_profit - fees
        
        # Only include profitable opportunities
        if net_profit >= min_profit:
            roi = (net_profit / total_cost) * 100 if total_cost > 0 else 0
            confidence = random.randint(*strategy['confidence_range'])
            
            opportunity = {
                'opportunity_id': f"EDU_{int(datetime.now().timestamp())}_{i+1:03d}",
                'similarity_score': round(random.uniform(0.75, 0.95), 3),
                'confidence_score': confidence,
                'risk_level': strategy['risk'],
                'gross_profit': round(gross_profit, 2),
                'net_profit_after_fees': round(net_profit, 2),
                'roi_percentage': round(roi, 1),
                'estimated_fees': round(fees, 2),
                'strategy_used': strategy['name'],
                'strategy_description': strategy['description'],
                'buy_listing': {
                    'title': create_listing_title(product['name'], strategy['name'], keywords),
                    'price': round(buy_price, 2),
                    'shipping_cost': round(shipping, 2),
                    'total_cost': round(total_cost, 2),
                    'condition': random.choice(['New', 'Like New', 'Very Good', 'Good']),
                    'seller_rating': f"{random.uniform(94, 99.5):.1f}%",
                    'seller_feedback': str(random.randint(50, 5000)),
                    'location': random.choice(['California, USA', 'Texas, USA', 'New York, USA']),
                    'image_url': f'https://via.placeholder.com/400x300/2563eb/ffffff?text=Buy+Low',
                    'ebay_link': f'https://ebay.com/itm/{random.randint(100000000000, 999999999999)}',
                    'item_id': str(random.randint(100000000000, 999999999999))
                },
                'sell_reference': {
                    'title': f"{product['name']} - Market Price Reference",
                    'price': round(sell_price, 2),
                    'shipping_cost': round(random.uniform(0, 10), 2),
                    'total_cost': round(sell_price + random.uniform(0, 10), 2),
                    'condition': 'New',
                    'seller_rating': f"{random.uniform(98, 99.9):.1f}%",
                    'seller_feedback': str(random.randint(1000, 15000)),
                    'location': random.choice(['California, USA', 'New York, USA']),
                    'image_url': f'https://via.placeholder.com/400x300/10b981/ffffff?text=Sell+High',
                    'ebay_link': f'https://ebay.com/itm/{random.randint(100000000000, 999999999999)}',
                    'item_id': str(random.randint(100000000000, 999999999999))
                },
                'product_info': {
                    'brand': extract_brand(product['name']),
                    'model': product['name'],
                    'category': category,
                    'subcategory': get_subcategory(category),
                    'key_features': ['Educational', 'Demo', 'Example'],
                    'product_identifier': f"edu_{random.randint(1000, 9999)}"
                },
                'created_at': datetime.now().isoformat()
            }
            
            opportunities.append(opportunity)
    
    # Calculate summary
    total_opps = len(opportunities)
    avg_profit = sum(o['net_profit_after_fees'] for o in opportunities) / max(total_opps, 1)
    avg_roi = sum(o['roi_percentage'] for o in opportunities) / max(total_opps, 1)
    avg_confidence = sum(o['confidence_score'] for o in opportunities) / max(total_opps, 1)
    highest_profit = max([o['net_profit_after_fees'] for o in opportunities], default=0)
    
    return {
        'scan_metadata': {
            'duration_seconds': round(random.uniform(8.5, 25.3), 1),
            'total_searches_performed': random.randint(15, 45),
            'total_listings_analyzed': random.randint(80, 250),
            'arbitrage_opportunities_found': total_opps,
            'scan_efficiency': round((total_opps / max(random.randint(80, 250), 1)) * 100, 1),
            'unique_products_found': random.randint(12, 35),
            'keywords_used': [keywords],
            'timestamp': datetime.now().isoformat(),
            'scan_id': f"EDUCATIONAL_{int(datetime.now().timestamp())}"
        },
        'opportunities_summary': {
            'total_opportunities': total_opps,
            'average_profit_after_fees': round(avg_profit, 2),
            'average_roi': round(avg_roi, 1),
            'average_confidence': round(avg_confidence, 1),
            'highest_profit': round(highest_profit, 2),
            'risk_distribution': {'low': total_opps, 'medium': 0, 'high': 0},
            'profit_ranges': {
                'under_25': len([o for o in opportunities if o['net_profit_after_fees'] < 25]),
                '25_to_50': len([o for o in opportunities if 25 <= o['net_profit_after_fees'] < 50]),
                '50_to_100': len([o for o in opportunities if 50 <= o['net_profit_after_fees'] < 100]),
                'over_100': len([o for o in opportunities if o['net_profit_after_fees'] >= 100])
            }
        },
        'top_opportunities': opportunities
    }

def create_listing_title(product_name, strategy, keywords):
    """Create realistic listing titles based on strategy"""
    if strategy == 'misspelled_listings':
        # Create common misspellings
        misspellings = {
            'AirPods': 'Airpod',
            'iPhone': 'Iphone', 
            'MacBook': 'Macbok',
            'Nintendo': 'Nintedo',
            'PlayStation': 'Playstaion'
        }
        
        result = product_name
        for correct, misspelled in misspellings.items():
            if correct in product_name:
                result = product_name.replace(correct, misspelled)
                break
        return f"📚 EDUCATIONAL: {result} (Misspelling Demo)"
        
    elif strategy == 'poor_photos':
        return f"📚 EDUCATIONAL: {product_name} - Poor Photos Demo"
        
    elif strategy == 'bulk_breaking':
        return f"📚 EDUCATIONAL: BULK LOT - {product_name} (Demo)"
        
    return f"📚 EDUCATIONAL: {product_name} - Demo Listing"

def extract_brand(product_name):
    """Extract brand from product name"""
    brands = ['Apple', 'Nintendo', 'PlayStation', 'Samsung', 'Sony']
    for brand in brands:
        if brand in product_name:
            return brand
    return 'Generic'

def get_subcategory(category):
    """Get subcategory for category"""
    subcategories = {
        'Tech': 'Electronics',
        'Gaming': 'Consoles',
        'Collectibles': 'Cards',
        'Fashion': 'Sneakers'
    }
    return subcategories.get(category, 'Other')

@app.route('/api/scan/quick', methods=['POST'])
def quick_scan():
    """Quick scan with popular keywords"""
    try:
        logger.info("🚀 Quick scan requested")
        
        result = generate_arbitrage_opportunities("trending items", 20.0, 5, 'Tech')
        
        session['last_scan_results'] = result
        session['scan_timestamp'] = datetime.now().isoformat()
        session['total_scans'] = session.get('total_scans', 0) + 1
        
        return jsonify({
            'status': 'success',
            'data': result,
            'message': f'Quick scan found {result["opportunities_summary"]["total_opportunities"]} opportunities!'
        })
        
    except Exception as e:
        logger.error(f"Error during quick scan: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Quick scan failed: {str(e)}',
            'data': None
        }), 500

@app.route('/api/scan/trending', methods=['POST'])
def trending_scan():
    """Trending scan"""
    try:
        logger.info("📈 Trending scan requested")
        
        result = generate_arbitrage_opportunities("viral products", 25.0, 6, 'Fashion')
        
        session['last_scan_results'] = result
        session['scan_timestamp'] = datetime.now().isoformat()
        session['total_scans'] = session.get('total_scans', 0) + 1
        
        return jsonify({
            'status': 'success',
            'data': result,
            'message': f'Trending scan found {result["opportunities_summary"]["total_opportunities"]} opportunities!'
        })
        
    except Exception as e:
        logger.error(f"Error during trending scan: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Trending scan failed: {str(e)}',
            'data': None
        }), 500

@app.route('/api/opportunity/<opportunity_id>', methods=['GET'])
def get_opportunity_details(opportunity_id):
    """Get opportunity details"""
    try:
        last_results = session.get('last_scan_results', {})
        opportunities = last_results.get('top_opportunities', [])
        
        opportunity = next((opp for opp in opportunities if opp['opportunity_id'] == opportunity_id), None)
        
        if not opportunity:
            return jsonify({
                'status': 'error',
                'message': 'Opportunity not found',
                'data': None
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': opportunity,
            'message': 'Opportunity details retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting opportunity details: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get opportunity details: {str(e)}',
            'data': None
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_session_stats():
    """Get session statistics"""
    try:
        result = {
            'status': 'success',
            'data': {
                'total_scans': session.get('total_scans', 0),
                'total_opportunities_found': session.get('total_opportunities', 0),
                'average_profit': session.get('average_profit', 0),
                'uptime_seconds': 3600,
                'scanner_type': 'EDUCATIONAL_DEMO'
            },
            'message': 'Session stats retrieved successfully'
        }
        
        if 'last_scan_results' in session:
            scan_data = session['last_scan_results']
            opportunities_summary = scan_data.get('opportunities_summary', {})
            result['data']['last_scan'] = {
                'timestamp': session.get('scan_timestamp'),
                'opportunities_found': opportunities_summary.get('total_opportunities', 0)
            }
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting session stats: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve session stats',
            'data': None
        }), 500

@app.route('/api/flipship/create', methods=['POST'])
def create_flipship_product():
    """Create FlipShip product"""
    try:
        request_data = request.get_json() or {}
        opportunity_id = request_data.get('opportunity_id')
        
        if not opportunity_id:
            return jsonify({
                'status': 'error',
                'message': 'Opportunity ID required',
                'data': None
            }), 400
        
        last_results = session.get('last_scan_results', {})
        opportunities = last_results.get('top_opportunities', [])
        opportunity = next((opp for opp in opportunities if opp['opportunity_id'] == opportunity_id), None)
        
        if not opportunity:
            return jsonify({
                'status': 'error',
                'message': 'Opportunity not found',
                'data': None
            }), 404
        
        buy_listing = opportunity.get('buy_listing', {})
        sell_listing = opportunity.get('sell_reference', {})
        
        product_data = {
            'title': buy_listing.get('title', 'Educational Product'),
            'total_cost': buy_listing.get('total_cost', 0),
            'estimated_resale_price': sell_listing.get('price', 0),
            'category': opportunity.get('product_info', {}).get('category', 'Demo'),
            'subcategory': opportunity.get('product_info', {}).get('subcategory', 'Educational'),
            'condition': buy_listing.get('condition', 'Demo'),
            'confidence_score': opportunity.get('confidence_score', 75),
            'image_url': buy_listing.get('image_url', ''),
            'ebay_link': buy_listing.get('ebay_link', ''),
            'item_id': buy_listing.get('item_id', ''),
            'seller_rating': buy_listing.get('seller_rating', ''),
            'estimated_profit': opportunity.get('net_profit_after_fees', 0)
        }
        
        product = flipship_manager.create_product_from_opportunity(product_data)
        
        return jsonify({
            'status': 'success',
            'data': {
                'product_id': product.get('product_id', f'FS_{opportunity_id}'),
                'opportunity_id': opportunity_id,
                'estimated_profit': opportunity.get('net_profit_after_fees', 0),
                'roi': opportunity.get('roi_percentage', 0)
            },
            'message': 'Educational product created for FlipShip demo'
        })
        
    except Exception as e:
        logger.error(f"Error creating FlipShip product: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to create product: {str(e)}',
            'data': None
        }), 500

def get_fallback_html():
    """Fallback HTML"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FlipHawk - Educational Arbitrage Scanner</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
                color: #f8fafc;
                margin: 0;
                padding: 2rem;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                text-align: center;
            }
            .logo {
                font-size: 4rem;
                font-weight: 900;
                background: linear-gradient(135deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin-bottom: 1rem;
            }
            .tagline {
                font-size: 1.25rem;
                color: #cbd5e1;
                margin-bottom: 3rem;
            }
            .status {
                background: rgba(16, 185, 129, 0.2);
                border: 1px solid #10b981;
                color: #10b981;
                padding: 1rem 2rem;
                border-radius: 12px;
                font-weight: 600;
                margin-bottom: 2rem;
            }
            .note {
                background: rgba(245, 158, 11, 0.2);
                border: 1px solid #f59e0b;
                color: #f59e0b;
                padding: 1rem 2rem;
                border-radius: 12px;
                margin-bottom: 2rem;
                max-width: 600px;
            }
            .btn {
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                border: none;
                padding: 1rem 2rem;
                border-radius: 12px;
                font-weight: 600;
                text-decoration: none;
                display: inline-block;
                transition: transform 0.3s ease;
                margin: 0.5rem;
            }
            .btn:hover {
                transform: translateY(-2px);
            }
        </style>
    </head>
    <body>
        <h1 class="logo">🦅 FlipHawk</h1>
        <p class="tagline">Educational Arbitrage Scanner</p>
        <div class="status">✅ Server Running Successfully</div>
        <div class="note">
            📚 <strong>Educational Demo:</strong> This version shows realistic arbitrage examples 
            for learning purposes. No real eBay API integration.
        </div>
        <p>Your FlipHawk educational scanner is ready!</p>
        <a href="/fliphawk" class="btn">Open Scanner</a>
        <a href="/flipship" class="btn">View Store</a>
    </body>
    </html>
    """

# Error handlers
@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({'status': 'error', 'message': 'API endpoint not found'}), 404
    return render_template_string(get_fallback_html()), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    if request.path.startswith('/api/'):
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
    return render_template_string(get_fallback_html()), 500

# Initialize the app
def initialize_app():
    try:
        flipship_manager.initialize_sample_products()
        logger.info("✅ FlipHawk educational demo initialized")
        logger.info("🚀 FlipHawk server ready")
    except Exception as e:
        logger.error(f"❌ Initialization error: {e}")

with app.app_context():
    initialize_app()

if __name__ == '__main__':
    logger.info("🚀 Starting FlipHawk Educational Demo Server...")
    logger.info("📚 Note: This is an educational demo, not real eBay API")
    logger.info("🌐 Server available at http://localhost:5000")
    
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_ENV') == 'development',
        threaded=True
    )
