"""
FlipHawk Flask Application
Main entry point for the web application
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import os
import json
import logging
from datetime import datetime
import threading
import time

# Import our custom modules
from backend.scraper.fliphawk_scraper import EnhancedFlipHawkScraper, create_api_endpoints, validate_scan_request
from backend.flipship.product_manager import FlipShipProductManager
from config import Config

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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize scraper and API endpoints
scraper = EnhancedFlipHawkScraper()
api_endpoints = create_api_endpoints(scraper)
flipship_manager = FlipShipProductManager()

# Global state for background scanning
background_scan_active = False
background_scan_results = None

@app.route('/')
def index():
    """Main landing page - redirect to FlipHawk"""
    return render_template('fliphawk.html')

@app.route('/fliphawk')
def fliphawk():
    """FlipHawk arbitrage scanner interface"""
    return render_template('fliphawk.html')

@app.route('/flipship')
def flipship():
    """FlipShip storefront interface"""
    products = flipship_manager.get_featured_products()
    return render_template('flipship.html', products=products)

# =============================================================================
# API ROUTES
# =============================================================================

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get available categories and subcategories"""
    try:
        result = api_endpoints['get_categories']()
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
    """Start arbitrage scan with user parameters"""
    try:
        request_data = request.get_json() or {}
        
        # Validate request data
        validation = validate_scan_request(request_data)
        if not validation['valid']:
            return jsonify({
                'status': 'error',
                'message': 'Invalid request parameters',
                'errors': validation['errors']
            }), 400
        
        # Start scan
        logger.info(f"Starting scan with params: {request_data}")
        result = api_endpoints['scan_arbitrage'](request_data)
        
        # Store results in session for potential FlipShip integration
        if result['status'] == 'success':
            session['last_scan_results'] = result['data']
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error during scan: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Scan failed due to server error',
            'data': None
        }), 500

@app.route('/api/scan/quick', methods=['POST'])
def quick_scan():
    """Quick scan with predefined parameters"""
    try:
        quick_params = {
            'categories': ['Tech', 'Gaming'],
            'subcategories': {
                'Tech': ['Headphones', 'Smartphones'],
                'Gaming': ['Consoles', 'Video Games']
            },
            'min_profit': 20.0,
            'max_results': 10
        }
        
        logger.info("Starting quick scan")
        result = api_endpoints['scan_arbitrage'](quick_params)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error during quick scan: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Quick scan failed',
            'data': None
        }), 500

@app.route('/api/trending', methods=['POST'])
def add_trending_keywords():
    """Add trending keywords to the system"""
    try:
        request_data = request.get_json() or {}
        keywords = request_data.get('keywords', [])
        
        if not keywords:
            return jsonify({
                'status': 'error',
                'message': 'No keywords provided',
                'data': None
            }), 400
        
        result = api_endpoints['add_trending'](request_data)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error adding trending keywords: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to add trending keywords',
            'data': None
        }), 500

@app.route('/api/trending', methods=['GET'])
def get_trending_keywords():
    """Get current trending keywords"""
    try:
        trending = scraper.keyword_db.get_trending_keywords(20)
        return jsonify({
            'status': 'success',
            'data': {
                'keywords': trending,
                'count': len(trending),
                'last_updated': datetime.now().isoformat()
            },
            'message': 'Trending keywords retrieved successfully'
        })
    except Exception as e:
        logger.error(f"Error getting trending keywords: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve trending keywords',
            'data': None
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_session_stats():
    """Get current session statistics"""
    try:
        result = api_endpoints['get_session_stats']()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting session stats: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve session stats',
            'data': None
        }), 500

# =============================================================================
# FLIPSHIP API ROUTES
# =============================================================================

@app.route('/api/flipship/products', methods=['GET'])
def get_flipship_products():
    """Get FlipShip product catalog"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        category = request.args.get('category', 'all')
        
        products = flipship_manager.get_products(
            page=page, 
            limit=limit, 
            category=category
        )
        
        return jsonify({
            'status': 'success',
            'data': products,
            'message': 'Products retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting FlipShip products: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve products',
            'data': None
        }), 500

@app.route('/api/flipship/create', methods=['POST'])
def create_flipship_product():
    """Create new FlipShip product from scan results"""
    try:
        request_data = request.get_json() or {}
        opportunity_data = request_data.get('opportunity')
        
        if not opportunity_data:
            return jsonify({
                'status': 'error',
                'message': 'No opportunity data provided',
                'data': None
            }), 400
        
        product = flipship_manager.create_product_from_opportunity(opportunity_data)
        
        return jsonify({
            'status': 'success',
            'data': product,
            'message': 'Product created successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating FlipShip product: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to create product',
            'data': None
        }), 500

@app.route('/api/flipship/cart', methods=['POST'])
def add_to_cart():
    """Add product to shopping cart"""
    try:
        request_data = request.get_json() or {}
        product_id = request_data.get('product_id')
        quantity = int(request_data.get('quantity', 1))
        
        if not product_id:
            return jsonify({
                'status': 'error',
                'message': 'Product ID required',
                'data': None
            }), 400
        
        # Initialize cart in session if not exists
        if 'cart' not in session:
            session['cart'] = []
        
        # Add to cart
        cart_item = {
            'product_id': product_id,
            'quantity': quantity,
            'added_at': datetime.now().isoformat()
        }
        
        session['cart'].append(cart_item)
        session.modified = True
        
        return jsonify({
            'status': 'success',
            'data': {
                'cart_items': len(session['cart']),
                'item_added': cart_item
            },
            'message': 'Product added to cart'
        })
        
    except Exception as e:
        logger.error(f"Error adding to cart: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to add to cart',
            'data': None
        }), 500

@app.route('/api/flipship/cart', methods=['GET'])
def get_cart():
    """Get current shopping cart contents"""
    try:
        cart = session.get('cart', [])
        
        # Get product details for cart items
        cart_details = []
        for item in cart:
            product = flipship_manager.get_product_by_id(item['product_id'])
            if product:
                cart_details.append({
                    **item,
                    'product': product
                })
        
        total_value = sum(
            item['product']['price'] * item['quantity'] 
            for item in cart_details
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'items': cart_details,
                'total_items': len(cart_details),
                'total_value': total_value
            },
            'message': 'Cart retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting cart: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve cart',
            'data': None
        }), 500

# =============================================================================
# BACKGROUND SCANNING (Optional Feature)
# =============================================================================

@app.route('/api/scan/background/start', methods=['POST'])
def start_background_scan():
    """Start continuous background scanning"""
    global background_scan_active
    
    if background_scan_active:
        return jsonify({
            'status': 'info',
            'message': 'Background scan already running',
            'data': {'active': True}
        })
    
    def background_scan_worker():
        global background_scan_active, background_scan_results
        background_scan_active = True
        
        while background_scan_active:
            try:
                scan_params = {
                    'categories': ['Tech', 'Gaming', 'Collectibles'],
                    'min_profit': 25.0,
                    'max_results': 15
                }
                
                logger.info("Running background scan...")
                result = api_endpoints['scan_arbitrage'](scan_params)
                background_scan_results = result
                
                # Wait 5 minutes before next scan
                for _ in range(300):  # 300 seconds = 5 minutes
                    if not background_scan_active:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Background scan error: {e}")
                time.sleep(60)  # Wait 1 minute on error
    
    # Start background thread
    thread = threading.Thread(target=background_scan_worker, daemon=True)
    thread.start()
    
    return jsonify({
        'status': 'success',
        'message': 'Background scan started',
        'data': {'active': True}
    })

@app.route('/api/scan/background/stop', methods=['POST'])
def stop_background_scan():
    """Stop background scanning"""
    global background_scan_active
    background_scan_active = False
    
    return jsonify({
        'status': 'success',
        'message': 'Background scan stopped',
        'data': {'active': False}
    })

@app.route('/api/scan/background/status', methods=['GET'])
def get_background_scan_status():
    """Get background scan status and latest results"""
    return jsonify({
        'status': 'success',
        'data': {
            'active': background_scan_active,
            'latest_results': background_scan_results
        },
        'message': 'Background scan status retrieved'
    })

# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error',
            'message': 'API endpoint not found',
            'data': None
        }), 404
    return render_template('404.html'), 404

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
    return render_template('500.html'), 500

@app.errorhandler(429)
def rate_limit_error(error):
    """Handle rate limiting errors"""
    return jsonify({
        'status': 'error',
        'message': 'Rate limit exceeded. Please try again later.',
        'data': None
    }), 429

# =============================================================================
# INITIALIZATION
# =============================================================================

def initialize_app():
    """Initialize application with default data"""
    try:
        # Add some default trending keywords
        default_trending = [
            "airpods pro 2", "nintendo switch oled", "pokemon cards",
            "iphone 15 pro", "ps5 console", "nike dunk low",
            "supreme hoodie", "rolex watch", "gibson les paul",
            "vintage t-shirt", "jordan 1 chicago", "macbook pro m3"
        ]
        
        scraper.keyword_db.add_trending_keywords(default_trending, priority=1)
        logger.info("✅ App initialized with default trending keywords")
        
        # Initialize FlipShip with sample products
        flipship_manager.initialize_sample_products()
        logger.info("✅ FlipShip initialized with sample products")
        
    except Exception as e:
        logger.error(f"❌ Error during app initialization: {e}")

# Initialize when app starts
with app.app_context():
    initialize_app()

if __name__ == '__main__':
    # Development server
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_ENV') == 'development'
    )
