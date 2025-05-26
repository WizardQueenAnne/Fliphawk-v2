"""
FlipHawk Flask Application - Fixed Scan Error
Main entry point for the web application with corrected data structure
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import os
import json
import logging
from datetime import datetime
import threading
import time

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import eBay API integration
EBAY_API_AVAILABLE = False  # Set to False for now to use fallback

# Fallback to enhanced arbitrage scanner
scanner = None
api_endpoints = None

try:
    logger.info("🔄 Loading fallback arbitrage scanner...")
    from backend.scraper.enhanced_arbitrage_scanner import TrueArbitrageScanner, create_arbitrage_api_endpoints
    
    logger.info("✅ Fallback scanner loaded successfully!")
    scanner = TrueArbitrageScanner()
    api_endpoints = create_arbitrage_api_endpoints(scanner)
    
except ImportError as e:
    logger.error(f"❌ ImportError when loading fallback scanner: {e}")
    scanner = None
    api_endpoints = None

# FlipShip manager import
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

# Initialize components
flipship_manager = FlipShipProductManager()

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
        return render_template('index.html')

@app.route('/flipship')
def flipship():
    """FlipShip storefront interface"""
    try:
        products = flipship_manager.get_featured_products()
        return render_template('flipship.html', products=products)
    except:
        return render_template('index.html')

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
            'api_source': 'Fallback'
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
    """Enhanced arbitrage scan with proper error handling"""
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
        
        logger.info(f"🔍 Starting arbitrage scan with keywords: {keywords}")
        
        # Use the scanner (real or fallback)
        if api_endpoints:
            result = api_endpoints['scan_arbitrage']({
                'keywords': keywords,
                'categories': categories,
                'min_profit': min_profit,
                'max_results': max_results
            })
            
            # Store results in session
            if result['status'] == 'success' and 'data' in result:
                session['last_scan_results'] = result['data']
                session['scan_timestamp'] = datetime.now().isoformat()
            
            return jsonify(result)
        else:
            # Ultimate fallback - return structured demo data
            demo_result = get_demo_scan_data(keywords, max_results)
            
            # Store results in session
            session['last_scan_results'] = demo_result
            session['scan_timestamp'] = datetime.now().isoformat()
            
            return jsonify({
                'status': 'success',
                'data': demo_result,
                'message': '⚠️ Demo data - Scanner not available'
            })
        
    except Exception as e:
        logger.error(f"Error during arbitrage scan: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Scan failed: {str(e)}',
            'data': None
        }), 500

def get_demo_scan_data(keywords, max_results):
    """Generate properly structured demo data that matches frontend expectations"""
    return {
        'scan_metadata': {
            'duration_seconds': 15.5,
            'total_searches_performed': 12,
            'total_listings_analyzed': 120,
            'arbitrage_opportunities_found': 3,
            'scan_efficiency': 78.5,
            'unique_products_found': 8,
            'keywords_used': [keywords],
            'timestamp': datetime.now().isoformat(),
            'scan_id': f"DEMO_{int(datetime.now().timestamp())}"
        },
        'opportunities_summary': {
            'total_opportunities': 3,
            'average_profit_after_fees': 45.25,
            'average_roi': 35.7,
            'average_confidence': 82,
            'highest_profit': 89.50,
            'risk_distribution': {'low': 2, 'medium': 1, 'high': 0},
            'profit_ranges': {
                'under_25': 0, '25_to_50': 2, '50_to_100': 1, 'over_100': 0
            }
        },
        'top_opportunities': [
            {
                'opportunity_id': 'DEMO_ARB_001',
                'similarity_score': 0.92,
                'confidence_score': 88,
                'risk_level': 'LOW',
                'gross_profit': 65.00,
                'net_profit_after_fees': 45.25,
                'roi_percentage': 32.8,
                'estimated_fees': 19.75,
                'buy_listing': {
                    'title': f'⚠️ DEMO DATA - {keywords} - Apple AirPods Pro 2nd Generation',
                    'price': 189.99,
                    'shipping_cost': 0.00,
                    'total_cost': 189.99,
                    'condition': 'Brand New',
                    'seller_rating': '99.2%',
                    'seller_feedback': '15847',
                    'location': 'California, USA',
                    'image_url': 'https://via.placeholder.com/400x300/ff6b6b/ffffff?text=DEMO+DATA',
                    'ebay_link': 'https://ebay.com/item/demo_data',
                    'item_id': 'demo_001'
                },
                'sell_reference': {
                    'title': f'⚠️ DEMO DATA - {keywords} - Reference Listing',
                    'price': 279.99,
                    'shipping_cost': 9.99,
                    'total_cost': 289.98,
                    'condition': 'New',
                    'seller_rating': '98.8%',
                    'seller_feedback': '8934',
                    'location': 'New York, USA',
                    'image_url': 'https://via.placeholder.com/400x300/10b981/ffffff?text=DEMO+DATA',
                    'ebay_link': 'https://ebay.com/item/demo_data_ref',
                    'item_id': 'demo_002'
                },
                'product_info': {
                    'brand': 'demo',
                    'model': 'sample',
                    'category': 'Tech',
                    'subcategory': 'Headphones',
                    'key_features': ['demo', 'data', 'only'],
                    'product_identifier': 'demo_product'
                },
                'created_at': datetime.now().isoformat()
            },
            {
                'opportunity_id': 'DEMO_ARB_002',
                'similarity_score': 0.85,
                'confidence_score': 79,
                'risk_level': 'MEDIUM',
                'gross_profit': 35.00,
                'net_profit_after_fees': 25.50,
                'roi_percentage': 18.2,
                'estimated_fees': 9.50,
                'buy_listing': {
                    'title': f'⚠️ DEMO DATA - {keywords} - Sample Product 2',
                    'price': 129.99,
                    'shipping_cost': 10.00,
                    'total_cost': 139.99,
                    'condition': 'Like New',
                    'seller_rating': '97.8%',
                    'seller_feedback': '3421',
                    'location': 'Texas, USA',
                    'image_url': 'https://via.placeholder.com/400x300/3b82f6/ffffff?text=DEMO+2',
                    'ebay_link': 'https://ebay.com/item/demo_2',
                    'item_id': 'demo_003'
                },
                'sell_reference': {
                    'title': f'⚠️ DEMO DATA - {keywords} - Reference 2',
                    'price': 174.99,
                    'shipping_cost': 0.00,
                    'total_cost': 174.99,
                    'condition': 'New',
                    'seller_rating': '99.1%',
                    'seller_feedback': '12456',
                    'location': 'Florida, USA',
                    'image_url': 'https://via.placeholder.com/400x300/8b5cf6/ffffff?text=DEMO+REF+2',
                    'ebay_link': 'https://ebay.com/item/demo_ref_2',
                    'item_id': 'demo_004'
                },
                'product_info': {
                    'brand': 'demo',
                    'model': 'sample2',
                    'category': 'Tech',
                    'subcategory': 'Electronics',
                    'key_features': ['demo', 'sample', 'test'],
                    'product_identifier': 'demo_product_2'
                },
                'created_at': datetime.now().isoformat()
            }
        ]
    }

@app.route('/api/scan/quick', methods=['POST'])
def quick_scan():
    """Quick arbitrage scan with predefined parameters"""
    try:
        logger.info("🚀 Quick scan requested")
        
        if api_endpoints:
            result = api_endpoints['quick_scan']()
            
            # Store results in session
            if result['status'] == 'success' and 'data' in result:
                session['last_scan_results'] = result['data']
                session['scan_timestamp'] = datetime.now().isoformat()
            
            return jsonify(result)
        else:
            # Fallback demo data
            demo_result = get_demo_scan_data("trending viral products", 10)
            
            session['last_scan_results'] = demo_result
            session['scan_timestamp'] = datetime.now().isoformat()
            
            return jsonify({
                'status': 'success',
                'data': demo_result,
                'message': '⚠️ Demo quick scan data'
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
    """Scan with trending keywords"""
    try:
        logger.info("📈 Trending scan requested")
        
        if api_endpoints:
            result = api_endpoints['trending_scan']()
            
            # Store results in session
            if result['status'] == 'success' and 'data' in result:
                session['last_scan_results'] = result['data']
                session['scan_timestamp'] = datetime.now().isoformat()
            
            return jsonify(result)
        else:
            # Fallback demo data
            demo_result = get_demo_scan_data("trending viral products", 15)
            
            session['last_scan_results'] = demo_result
            session['scan_timestamp'] = datetime.now().isoformat()
            
            return jsonify({
                'status': 'success',
                'data': demo_result,
                'message': '⚠️ Demo trending scan data'
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
    """Get detailed information about a specific arbitrage opportunity"""
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
    """Get current session statistics"""
    try:
        result = {
            'status': 'success',
            'data': {
                'total_scans': session.get('total_scans', 0),
                'total_opportunities_found': session.get('total_opportunities', 0),
                'average_profit': session.get('average_profit', 0),
                'uptime_seconds': 3600,
                'scanner_type': 'DEMO' if not api_endpoints else 'REAL'
            },
            'message': 'Session stats retrieved successfully'
        }
        
        # Add last scan info if available
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
    """Create new FlipShip product from arbitrage opportunity"""
    try:
        request_data = request.get_json() or {}
        opportunity_id = request_data.get('opportunity_id')
        
        if not opportunity_id:
            return jsonify({
                'status': 'error',
                'message': 'Opportunity ID required',
                'data': None
            }), 400
        
        # Get opportunity details from session
        last_results = session.get('last_scan_results', {})
        opportunities = last_results.get('top_opportunities', [])
        opportunity = next((opp for opp in opportunities if opp['opportunity_id'] == opportunity_id), None)
        
        if not opportunity:
            return jsonify({
                'status': 'error',
                'message': 'Opportunity not found',
                'data': None
            }), 404
        
        # Create FlipShip product
        buy_listing = opportunity.get('buy_listing', {})
        product_data = {
            'title': buy_listing.get('title', 'Unknown Product'),
            'total_cost': buy_listing.get('total_cost', 0),
            'estimated_resale_price': opportunity.get('sell_reference', {}).get('price', 0),
            'category': opportunity.get('product_info', {}).get('category', 'General'),
            'subcategory': opportunity.get('product_info', {}).get('subcategory', 'All'),
            'condition': buy_listing.get('condition', 'Unknown'),
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
    
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>FlipHawk - 404</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                text-align: center; 
                padding: 50px; 
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                color: #f8fafc;
                min-height: 100vh;
                margin: 0;
            }
            h1 { color: #667eea; font-size: 3rem; margin-bottom: 1rem; }
            h2 { color: #cbd5e1; margin-bottom: 1rem; }
            p { color: #94a3b8; margin-bottom: 2rem; }
            a { 
                color: #667eea; 
                text-decoration: none; 
                padding: 0.75rem 1.5rem;
                border: 1px solid #667eea;
                border-radius: 8px;
                transition: all 0.3s ease;
            }
            a:hover { 
                background: #667eea; 
                color: white; 
                transform: translateY(-2px);
            }
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
            body { 
                font-family: Arial, sans-serif; 
                text-align: center; 
                padding: 50px; 
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                color: #f8fafc;
                min-height: 100vh;
                margin: 0;
            }
            h1 { color: #ef4444; font-size: 3rem; margin-bottom: 1rem; }
            h2 { color: #cbd5e1; margin-bottom: 1rem; }
            p { color: #94a3b8; margin-bottom: 2rem; }
            a { 
                color: #667eea; 
                text-decoration: none; 
                padding: 0.75rem 1.5rem;
                border: 1px solid #667eea;
                border-radius: 8px;
                transition: all 0.3s ease;
            }
            a:hover { 
                background: #667eea; 
                color: white; 
                transform: translateY(-2px);
            }
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

# Initialize the app
def initialize_app():
    """Initialize application"""
    try:
        flipship_manager.initialize_sample_products()
        
        # Log scanner status
        if api_endpoints:
            logger.info("✅ FlipHawk using arbitrage scanner")
        else:
            logger.warning("⚠️ FlipHawk using demo data only")
        
        logger.info("🚀 FlipHawk server initialized")
        
    except Exception as e:
        logger.error(f"❌ Error during initialization: {e}")

# Initialize when app starts
with app.app_context():
    initialize_app()

if __name__ == '__main__':
    logger.info("🚀 Starting FlipHawk Server...")
    
    # Log final scanner status
    if api_endpoints:
        logger.info("✅ Arbitrage scanner loaded successfully")
    else:
        logger.warning("⚠️ Using demo data - scanner not available")
    
    logger.info("🌐 Server available at http://localhost:5000")
    
    # Development server
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_ENV') == 'development',
        threaded=True
    )
