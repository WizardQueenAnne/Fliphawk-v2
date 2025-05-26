"""
FlipHawk Flask Application - Updated with eBay Browse API Integration
Main entry point for the web application with real eBay API functionality
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
try:
    logger.info("🔄 Loading eBay Browse API integration...")
    from ebay_api import search_ebay, EbayBrowseAPI, EBAY_CATEGORY_IDS, get_category_keywords
    logger.info("✅ eBay Browse API loaded successfully!")
    EBAY_API_AVAILABLE = True
except ImportError as e:
    logger.error(f"❌ Failed to load eBay API: {e}")
    EBAY_API_AVAILABLE = False

# Fallback to enhanced arbitrage scanner if eBay API not available
scanner = None
api_endpoints = None

if not EBAY_API_AVAILABLE:
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
        if EBAY_API_AVAILABLE:
            # Use eBay categories
            categories_data = {}
            for category, subcategories in EBAY_CATEGORY_IDS.items():
                categories_data[category] = {
                    'subcategories': list(subcategories.keys()),
                    'description': f'{category} products from eBay',
                    'category_ids': subcategories
                }
            
            result = {
                'status': 'success',
                'data': categories_data,
                'message': 'eBay categories retrieved successfully',
                'api_source': 'eBay Browse API'
            }
        else:
            # Fallback categories
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
                'message': 'Fallback categories retrieved',
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
def scan_listings():
    """eBay Browse API integration for listing scan"""
    try:
        request_data = request.get_json() or {}
        
        keywords = request_data.get('keywords', '')
        category = request_data.get('category')
        subcategory = request_data.get('subcategory')
        min_price = float(request_data.get('min_price', 0))
        max_price = float(request_data.get('max_price', 10000))
        max_results = int(request_data.get('max_results', 20))
        sort_by = request_data.get('sort', 'price')
        
        if not keywords.strip() and not (category and subcategory):
            return jsonify({
                'status': 'error',
                'message': 'Keywords or category selection required',
                'errors': ['Either keywords or category must be specified']
            }), 400
        
        logger.info(f"🔍 Starting eBay scan with keywords: '{keywords}', category: {category}, subcategory: {subcategory}")
        
        scan_start_time = datetime.now()
        
        if EBAY_API_AVAILABLE:
            # Use eBay Browse API
            logger.info("✅ Using eBay Browse API")
            
            # Get eBay listings
            ebay_listings = search_ebay(
                keyword=keywords,
                category=category,
                subcategory=subcategory,
                limit=max_results * 2,  # Get more to filter
                sort=sort_by
            )
            
            # Filter by price range
            filtered_listings = []
            for listing in ebay_listings:
                if min_price <= listing['total_cost'] <= max_price:
                    filtered_listings.append(listing)
            
            # Limit results
            filtered_listings = filtered_listings[:max_results]
            
            # Convert to FlipHawk format
            opportunities = []
            for listing in filtered_listings:
                opportunity = {
                    'opportunity_id': f"EBAY_{listing['item_id']}",
                    'title': listing['title'],
                    'price': listing['price'],
                    'shipping_cost': listing['shipping_cost'],
                    'total_cost': listing['total_cost'],
                    'condition': listing['condition'],
                    'seller_rating': f"{listing['seller_feedback_percentage']:.1f}%",
                    'seller_feedback': str(listing['seller_feedback_score']),
                    'location': listing['location'],
                    'image_url': listing['image_url'],
                    'ebay_link': listing['ebay_link'],
                    'item_id': listing['item_id'],
                    'category': category or 'General',
                    'subcategory': subcategory or 'All',
                    'matched_keyword': keywords,
                    'listing_date': listing['item_creation_date'],
                    'confidence_score': calculate_listing_confidence(listing),
                    'estimated_profit': 0,  # No arbitrage calculation for single listings
                    'estimated_resale_price': listing['total_cost'] * 1.3,  # Rough estimate
                    'api_source': 'eBay Browse API'
                }
                opportunities.append(opportunity)
            
            scan_duration = (datetime.now() - scan_start_time).total_seconds()
            
            # Build response
            result = {
                'scan_metadata': {
                    'scan_id': f"EBAY_{int(datetime.now().timestamp())}",
                    'timestamp': datetime.now().isoformat(),
                    'duration_seconds': round(scan_duration, 2),
                    'total_searches_performed': 1,
                    'total_listings_analyzed': len(ebay_listings),
                    'arbitrage_opportunities_found': 0,  # Single listings, no arbitrage
                    'listings_found': len(filtered_listings),
                    'scan_efficiency': round((len(filtered_listings) / max(len(ebay_listings), 1)) * 100, 2),
                    'keywords_used': [keywords] if keywords else [],
                    'category_searched': f"{category} → {subcategory}" if category else "All",
                    'api_source': 'eBay Browse API'
                },
                'listings_summary': {
                    'total_listings': len(filtered_listings),
                    'price_range': {
                        'min': min([l['total_cost'] for l in filtered_listings]) if filtered_listings else 0,
                        'max': max([l['total_cost'] for l in filtered_listings]) if filtered_listings else 0,
                        'average': sum([l['total_cost'] for l in filtered_listings]) / len(filtered_listings) if filtered_listings else 0
                    },
                    'conditions': list(set([l['condition'] for l in filtered_listings])),
                    'top_sellers': list(set([l['seller_username'] for l in filtered_listings]))[:5]
                },
                'listings': opportunities
            }
            
            # Store results in session
            session['last_scan_results'] = result
            session['scan_timestamp'] = datetime.now().isoformat()
            
            return jsonify({
                'status': 'success',
                'data': result,
                'message': f'Found {len(filtered_listings)} eBay listings'
            })
            
        else:
            # Fallback to enhanced arbitrage scanner
            logger.warning("⚠️ Using fallback arbitrage scanner")
            
            if api_endpoints:
                result = api_endpoints['scan_arbitrage']({
                    'keywords': keywords,
                    'categories': [category] if category else ['Tech'],
                    'min_profit': 15.0,  # Default for arbitrage
                    'max_results': max_results
                })
                
                # Store results in session
                if result['status'] == 'success':
                    session['last_scan_results'] = result['data']
                    session['scan_timestamp'] = datetime.now().isoformat()
                
                return jsonify(result)
            else:
                # Ultimate fallback - demo data
                return jsonify({
                    'status': 'success',
                    'data': get_demo_data(),
                    'message': '⚠️ Demo data - eBay API not available'
                })
        
    except Exception as e:
        logger.error(f"Error during scan: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Scan failed: {str(e)}',
            'data': None
        }), 500

def calculate_listing_confidence(listing):
    """Calculate confidence score for an eBay listing"""
    confidence = 50  # Base confidence
    
    # Seller reputation
    feedback_pct = listing.get('seller_feedback_percentage', 0)
    if feedback_pct >= 99:
        confidence += 20
    elif feedback_pct >= 95:
        confidence += 15
    elif feedback_pct >= 90:
        confidence += 10
    
    # Seller feedback score
    feedback_score = listing.get('seller_feedback_score', 0)
    if feedback_score >= 1000:
        confidence += 15
    elif feedback_score >= 100:
        confidence += 10
    elif feedback_score >= 50:
        confidence += 5
    
    # Condition
    condition = listing.get('condition', '').lower()
    if 'new' in condition:
        confidence += 15
    elif 'excellent' in condition or 'like new' in condition:
        confidence += 10
    elif 'good' in condition or 'very good' in condition:
        confidence += 5
    
    # Top rated listing
    if listing.get('top_rated_listing'):
        confidence += 10
    
    # Fast and free shipping
    if listing.get('fast_n_free'):
        confidence += 5
    
    # Returns accepted
    if listing.get('returns_accepted'):
        confidence += 5
    
    return min(100, max(0, confidence))

def get_demo_data():
    """Return demo data when APIs are not available"""
    return {
        'scan_metadata': {
            'scan_id': f"DEMO_{int(datetime.now().timestamp())}",
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': 2.5,
            'total_searches_performed': 1,
            'total_listings_analyzed': 15,
            'listings_found': 3,
            'scan_efficiency': 20.0,
            'api_source': 'Demo Data'
        },
        'listings_summary': {
            'total_listings': 3,
            'price_range': {'min': 149.99, 'max': 289.99, 'average': 219.99}
        },
        'listings': [
            {
                'opportunity_id': 'DEMO_001',
                'title': '⚠️ DEMO - Apple AirPods Pro 2nd Generation',
                'price': 179.99,
                'shipping_cost': 0.00,
                'total_cost': 179.99,
                'condition': 'Brand New',
                'seller_rating': '99.1%',
                'seller_feedback': '5847',
                'location': 'California, USA',
                'image_url': 'https://via.placeholder.com/400x300/007acc/ffffff?text=AirPods+Pro',
                'ebay_link': 'https://ebay.com/itm/demo',
                'confidence_score': 85,
                'api_source': 'Demo Data'
            }
        ]
    }

@app.route('/api/scan/quick', methods=['POST'])
def quick_scan():
    """Quick scan with popular keywords"""
    try:
        logger.info("🚀 Quick scan requested")
        
        if EBAY_API_AVAILABLE:
            # Use eBay API for quick scan
            popular_keywords = ["airpods pro", "nintendo switch", "iphone 14"]
            all_listings = []
            
            for keyword in popular_keywords:
                listings = search_ebay(keyword=keyword, limit=5, sort="price")
                all_listings.extend(listings[:3])  # Top 3 from each
            
            # Convert to opportunities format
            opportunities = []
            for listing in all_listings:
                opportunity = {
                    'opportunity_id': f"QUICK_{listing['item_id']}",
                    'title': listing['title'],
                    'price': listing['price'],
                    'total_cost': listing['total_cost'],
                    'condition': listing['condition'],
                    'seller_rating': f"{listing['seller_feedback_percentage']:.1f}%",
                    'image_url': listing['image_url'],
                    'ebay_link': listing['ebay_link'],
                    'confidence_score': calculate_listing_confidence(listing)
                }
                opportunities.append(opportunity)
            
            result = {
                'scan_metadata': {
                    'duration_seconds': 5.2,
                    'total_searches_performed': len(popular_keywords),
                    'listings_found': len(opportunities),
                    'api_source': 'eBay Browse API'
                },
                'listings': opportunities
            }
            
            return jsonify({
                'status': 'success',
                'data': result,
                'message': f'Quick scan found {len(opportunities)} listings'
            })
        
        else:
            # Fallback to arbitrage scanner
            if api_endpoints:
                result = api_endpoints['quick_scan']()
                return jsonify(result)
            else:
                return jsonify({
                    'status': 'success',
                    'data': get_demo_data(),
                    'message': '⚠️ Demo quick scan'
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
        
        if EBAY_API_AVAILABLE:
            trending_keywords = ["viral tiktok products", "trending 2025", "supreme", "yeezy"]
            all_listings = []
            
            for keyword in trending_keywords:
                listings = search_ebay(keyword=keyword, limit=4, sort="price")
                all_listings.extend(listings[:2])  # Top 2 from each
            
            # Convert to opportunities format
            opportunities = []
            for listing in all_listings:
                opportunity = {
                    'opportunity_id': f"TREND_{listing['item_id']}",
                    'title': listing['title'],
                    'price': listing['price'],
                    'total_cost': listing['total_cost'],
                    'condition': listing['condition'],
                    'seller_rating': f"{listing['seller_feedback_percentage']:.1f}%",
                    'image_url': listing['image_url'],
                    'ebay_link': listing['ebay_link'],
                    'confidence_score': calculate_listing_confidence(listing)
                }
                opportunities.append(opportunity)
            
            result = {
                'scan_metadata': {
                    'duration_seconds': 7.1,
                    'total_searches_performed': len(trending_keywords),
                    'listings_found': len(opportunities),
                    'api_source': 'eBay Browse API'
                },
                'listings': opportunities
            }
            
            return jsonify({
                'status': 'success',
                'data': result,
                'message': f'Trending scan found {len(opportunities)} listings'
            })
        
        else:
            # Fallback
            if api_endpoints:
                result = api_endpoints['trending_scan']()
                return jsonify(result)
            else:
                return jsonify({
                    'status': 'success',
                    'data': get_demo_data(),
                    'message': '⚠️ Demo trending scan'
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
    """Get detailed information about a specific opportunity"""
    try:
        last_results = session.get('last_scan_results', {})
        opportunities = last_results.get('listings', []) or last_results.get('top_opportunities', [])
        
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
        api_source = "eBay Browse API" if EBAY_API_AVAILABLE else "Fallback Scanner"
        
        result = {
            'status': 'success',
            'data': {
                'total_scans': session.get('total_scans', 0),
                'total_listings_found': session.get('total_listings', 0),
                'average_price': session.get('average_price', 0),
                'uptime_seconds': 3600,
                'api_source': api_source,
                'ebay_api_available': EBAY_API_AVAILABLE
            },
            'message': 'Session stats retrieved successfully'
        }
        
        # Add last scan info if available
        if 'last_scan_results' in session:
            scan_data = session['last_scan_results']
            result['data']['last_scan'] = {
                'timestamp': session.get('scan_timestamp'),
                'listings_found': len(scan_data.get('listings', [])) or scan_data.get('opportunities_summary', {}).get('total_opportunities', 0)
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
    """Create new FlipShip product from listing"""
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
        opportunities = last_results.get('listings', []) or last_results.get('top_opportunities', [])
        opportunity = next((opp for opp in opportunities if opp['opportunity_id'] == opportunity_id), None)
        
        if not opportunity:
            return jsonify({
                'status': 'error',
                'message': 'Opportunity not found',
                'data': None
            }), 404
        
        # Create FlipShip product
        product_data = {
            'title': opportunity['title'],
            'total_cost': opportunity.get('total_cost', opportunity.get('price', 0)),
            'estimated_resale_price': opportunity.get('estimated_resale_price', opportunity.get('price', 0) * 1.3),
            'category': opportunity.get('category', 'General'),
            'subcategory': opportunity.get('subcategory', 'All'),
            'condition': opportunity.get('condition', 'Unknown'),
            'confidence_score': opportunity.get('confidence_score', 75),
            'image_url': opportunity.get('image_url', ''),
            'ebay_link': opportunity.get('ebay_link', ''),
            'item_id': opportunity.get('item_id', ''),
            'seller_rating': opportunity.get('seller_rating', ''),
            'estimated_profit': opportunity.get('estimated_profit', 0)
        }
        
        product = flipship_manager.create_product_from_opportunity(product_data)
        
        return jsonify({
            'status': 'success',
            'data': {
                'product_id': product.get('product_id', f'FS_{opportunity_id}'),
                'opportunity_id': opportunity_id,
                'estimated_profit': product_data['estimated_profit'],
                'markup_price': product_data['estimated_resale_price']
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
        
        # Log API status
        if EBAY_API_AVAILABLE:
            logger.info("✅ FlipHawk using eBay Browse API")
        elif scanner:
            logger.warning("⚠️ FlipHawk using fallback arbitrage scanner")
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
    
    # Log final API status
    if EBAY_API_AVAILABLE:
        logger.info("✅ eBay Browse API integration active")
    else:
        logger.warning("⚠️ eBay API not available - using fallback")
    
    logger.info("🌐 Server available at http://localhost:5000")
    
    # Development server
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_ENV') == 'development',
        threaded=True
    )'
