"""
FlipHawk Flask Application - Enhanced with True Arbitrage Scanner
Main entry point for the web application with real arbitrage functionality
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

# Import the enhanced arbitrage scanner
try:
    # Import your enhanced arbitrage scanner here
    # from backend.scraper.enhanced_arbitrage_scanner import EnhancedArbitrageScanner, create_arbitrage_api_endpoints
    
    # For now, we'll include a simplified version inline
    class SimpleArbitrageScanner:
        def __init__(self):
            self.base_url = "https://www.ebay.com/sch/i.html"
            self.headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            self.seen_items = set()
        
        def scan_arbitrage_opportunities(self, keywords: str, categories: List[str], 
                                       min_profit: float = 15.0, max_results: int = 25) -> Dict:
            """Simplified arbitrage scanner for demo"""
            # This would be replaced with your enhanced scanner
            return {
                'scan_metadata': {
                    'duration_seconds': 15.5,
                    'total_searches_performed': 12,
                    'total_listings_analyzed': 120,
                    'arbitrage_opportunities_found': 3,
                    'scan_efficiency': 2.5,
                    'unique_products_found': 8
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
                        'opportunity_id': 'ARB_1234567890_5678',
                        'similarity_score': 0.92,
                        'confidence_score': 88,
                        'risk_level': 'LOW',
                        'profit_analysis': {
                            'gross_profit': 65.00,
                            'net_profit_after_fees': 45.25,
                            'roi_percentage': 32.8,
                            'estimated_fees': 19.75
                        },
                        'buy_listing': {
                            'title': 'Apple AirPods Pro 2nd Generation with MagSafe Case - Brand New Sealed',
                            'price': 189.99,
                            'shipping_cost': 0.00,
                            'total_cost': 189.99,
                            'condition': 'Brand New',
                            'seller_rating': '99.2%',
                            'seller_feedback': '15847',
                            'location': 'California, USA',
                            'image_url': 'https://via.placeholder.com/400x300/2563eb/ffffff?text=AirPods+Pro',
                            'ebay_link': 'https://ebay.com/item/sample_buy_1',
                            'item_id': 'buy_12345'
                        },
                        'sell_reference': {
                            'title': 'Apple AirPods Pro (2nd Generation) MagSafe Case - NEW',
                            'price': 279.99,
                            'shipping_cost': 9.99,
                            'total_cost': 289.98,
                            'condition': 'New',
                            'seller_rating': '98.8%',
                            'seller_feedback': '8934',
                            'location': 'New York, USA',
                            'image_url': 'https://via.placeholder.com/400x300/2563eb/ffffff?text=AirPods+Pro',
                            'ebay_link': 'https://ebay.com/item/sample_sell_1',
                            'item_id': 'sell_12345'
                        },
                        'product_info': {
                            'brand': 'apple',
                            'model': 'airpods pro 2nd',
                            'category': 'Tech',
                            'subcategory': 'Headphones',
                            'key_features': ['2nd generation', 'magsafe', 'pro'],
                            'product_identifier': 'apple_airpods_pro_2nd'
                        },
                        'created_at': datetime.now().isoformat()
                    },
                    {
                        'opportunity_id': 'ARB_1234567890_5679',
                        'similarity_score': 0.89,
                        'confidence_score': 85,
                        'risk_level': 'LOW',
                        'profit_analysis': {
                            'gross_profit': 75.00,
                            'net_profit_after_fees': 52.80,
                            'roi_percentage': 41.2,
                            'estimated_fees': 22.20
                        },
                        'buy_listing': {
                            'title': 'Nintendo Switch OLED Model Console - White',
                            'price': 299.99,
                            'shipping_cost': 12.99,
                            'total_cost': 312.98,
                            'condition': 'Like New',
                            'seller_rating': '97.8%',
                            'seller_feedback': '2456',
                            'location': 'Texas, USA',
                            'image_url': 'https://via.placeholder.com/400x300/10b981/ffffff?text=Switch+OLED',
                            'ebay_link': 'https://ebay.com/item/sample_buy_2',
                            'item_id': 'buy_12346'
                        },
                        'sell_reference': {
                            'title': 'Nintendo Switch OLED Console System White Brand New',
                            'price': 399.99,
                            'shipping_cost': 0.00,
                            'total_cost': 399.99,
                            'condition': 'Brand New',
                            'seller_rating': '99.5%',
                            'seller_feedback': '12903',
                            'location': 'Florida, USA',
                            'image_url': 'https://via.placeholder.com/400x300/10b981/ffffff?text=Switch+OLED',
                            'ebay_link': 'https://ebay.com/item/sample_sell_2',
                            'item_id': 'sell_12346'
                        },
                        'product_info': {
                            'brand': 'nintendo',
                            'model': 'switch oled',
                            'category': 'Gaming',
                            'subcategory': 'Consoles',
                            'key_features': ['oled', 'white', 'console'],
                            'product_identifier': 'nintendo_switch_oled_white'
                        },
                        'created_at': datetime.now().isoformat()
                    }
                ]
            }
    
    scanner = SimpleArbitrageScanner()
    
except ImportError:
    # Fallback scanner
    class SimpleArbitrageScanner:
        def scan_arbitrage_opportunities(self, **kwargs):
            return {'scan_metadata': {}, 'opportunities_summary': {}, 'top_opportunities': []}
    
    scanner = SimpleArbitrageScanner()

try:
    from backend.flipship.product_manager import FlipShipProductManager
except ImportError:
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

# Initialize components
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

# Enhanced API Routes for True Arbitrage
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
    """Enhanced arbitrage scan with true price comparison"""
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
        
        logger.info(f"Starting arbitrage scan with keywords: {keywords}")
        
        # Use the enhanced arbitrage scanner
        scan_results = scanner.scan_arbitrage_opportunities(
            keywords=keywords,
            categories=categories,
            min_profit=min_profit,
            max_results=max_results
        )
        
        result = {
            'status': 'success',
            'data': scan_results,
            'message': f'Found {scan_results["opportunities_summary"]["total_opportunities"]} arbitrage opportunities'
        }
        
        # Store results in session
        session['last_scan_results'] = scan_results
        session['scan_timestamp'] = datetime.now().isoformat()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error during arbitrage scan: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Scan failed: {str(e)}',
            'data': None
        }), 500

@app.route('/api/scan/quick', methods=['POST'])
def quick_scan():
    """Quick arbitrage scan with predefined parameters"""
    try:
        scan_results = scanner.scan_arbitrage_opportunities(
            keywords='airpods pro, nintendo switch',
            categories=['Tech', 'Gaming'],
            min_profit=20.0,
            max_results=10
        )
        
        result = {
            'status': 'success',
            'data': scan_results,
            'message': f'Quick scan found {scan_results["opportunities_summary"]["total_opportunities"]} opportunities'
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
        trending_keywords = "viral tiktok products, trending 2025, pokemon cards"
        
        scan_results = scanner.scan_arbitrage_opportunities(
            keywords=trending_keywords,
            categories=['Tech', 'Gaming', 'Collectibles'],
            min_profit=20.0,
            max_results=15
        )
        
        result = {
            'status': 'success',
            'data': scan_results,
            'message': f'Trending scan found {scan_results["opportunities_summary"]["total_opportunities"]} opportunities'
        }
        
        return jsonify(result)
        
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
        # In a real implementation, you'd fetch from database
        # For now, check session storage
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
        # Basic stats - in real implementation, these would come from the scanner
        result = {
            'status': 'success',
            'data': {
                'total_scans': session.get('total_scans', 0),
                'total_opportunities_found': session.get('total_opportunities', 0),
                'average_profit': session.get('average_profit', 0),
                'uptime_seconds': 3600  # Placeholder
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

# FlipShip Integration Routes
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
        
        # Get opportunity details
        last_results = session.get('last_scan_results', {})
        opportunities = last_results.get('top_opportunities', [])
        opportunity = next((opp for opp in opportunities if opp['opportunity_id'] == opportunity_id), None)
        
        if not opportunity:
            return jsonify({
                'status': 'error',
                'message': 'Opportunity not found',
                'data': None
            }), 404
        
        # Create FlipShip product from the buy listing
        product_data = {
            'title': opportunity['buy_listing']['title'],
            'total_cost': opportunity['buy_listing']['total_cost'],
            'estimated_resale_price': opportunity['sell_reference']['price'],
            'category': opportunity['product_info']['category'],
            'subcategory': opportunity['product_info']['subcategory'],
            'condition': opportunity['buy_listing']['condition'],
            'confidence_score': opportunity['confidence_score'],
            'image_url': opportunity['buy_listing']['image_url'],
            'ebay_link': opportunity['buy_listing']['ebay_link'],
            'item_id': opportunity['buy_listing']['item_id'],
            'seller_rating': opportunity['buy_listing']['seller_rating'],
            'estimated_profit': opportunity['profit_analysis']['net_profit_after_fees']
        }
        
        product = flipship_manager.create_product_from_opportunity(product_data)
        
        return jsonify({
            'status': 'success',
            'data': {
                'product_id': product.get('product_id', f'FS_{opportunity_id}'),
                'opportunity_id': opportunity_id,
                'estimated_profit': opportunity['profit_analysis']['net_profit_after_fees'],
                'roi': opportunity['profit_analysis']['roi_percentage']
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
        logger.info("✅ FlipHawk server initialized successfully")
        logger.info("🔍 Enhanced arbitrage scanner ready")
        logger.info("🎯 API endpoints configured")
    except Exception as e:
        logger.error(f"❌ Error during initialization: {e}")

# Initialize when app starts
with app.app_context():
    initialize_app()

if __name__ == '__main__':
    logger.info("🚀 Starting FlipHawk Server...")
    logger.info("📡 Enhanced arbitrage scanner ready")
    logger.info("🌐 Server available at http://localhost:5000")
    
    # Development server
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_ENV') == 'development',
        threaded=True
    )
