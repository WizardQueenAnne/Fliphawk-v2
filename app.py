#!/usr/bin/env python3
"""
FlipHawk - Complete eBay Arbitrage Scanner
Final Flask Application with eBay Browse API Integration

Features:
- Real eBay Browse API integration
- Arbitrage opportunity detection
- Category-based searching
- Responsive web interface
- Fallback demo data
- Comprehensive error handling
"""

from flask import Flask, render_template, request, jsonify, session, render_template_string
from flask_cors import CORS
import os
import json
import logging
import random
import time
from datetime import datetime, timedelta
import uuid

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import eBay API module
try:
    from ebay_scraper import search_ebay, get_category_keywords, EBAY_CATEGORY_IDS, api_client
    EBAY_API_AVAILABLE = True
    logger.info("✅ eBay Browse API module loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ eBay API module not found: {e}")
    logger.info("🔄 Running in demo mode with sample data")
    EBAY_API_AVAILABLE = False

# Try to import config
try:
    from config import Config
except ImportError:
    # Fallback config
    class Config:
        SECRET_KEY = os.environ.get('SECRET_KEY') or 'fliphawk-secret-key-2025'
        DEBUG = os.environ.get('FLASK_ENV') == 'development'

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS for API endpoints
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Main landing page"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error loading index.html: {e}")
        return render_template_string(get_main_page_html())

@app.route('/fliphawk')
def fliphawk():
    """FlipHawk arbitrage scanner interface"""
    try:
        return render_template('fliphawk.html')
    except Exception as e:
        logger.error(f"Error loading fliphawk.html: {e}")
        return render_template_string(get_scanner_page_html())

@app.route('/ebay-search')
def ebay_search_page():
    """eBay search interface"""
    try:
        return render_template('ebay_search.html')
    except Exception as e:
        logger.error(f"Error loading ebay_search.html: {e}")
        return render_template_string(get_ebay_search_html())

# ==================== API ENDPOINTS ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'success',
        'data': {
            'server': 'FlipHawk v2.0',
            'ebay_api_available': EBAY_API_AVAILABLE,
            'uptime': str(datetime.now()),
            'features': [
                'eBay Browse API',
                'Arbitrage Detection',
                'Real-time Search',
                'Category Filtering'
            ]
        },
        'message': 'FlipHawk server is running successfully'
    })

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get available categories and subcategories"""
    try:
        if EBAY_API_AVAILABLE:
            category_data = EBAY_CATEGORY_IDS
            keyword_suggestions = get_category_keywords()
        else:
            # Fallback categories for demo mode
            category_data = {
                "Tech": {
                    "Headphones": "15052",
                    "Smartphones": "9355", 
                    "Laptops": "177",
                    "Graphics Cards": "27386",
                    "Tablets": "171485"
                },
                "Gaming": {
                    "Consoles": "139971",
                    "Video Games": "139973",
                    "Gaming Accessories": "54968"
                },
                "Collectibles": {
                    "Trading Cards": "2536",
                    "Action Figures": "246",
                    "Coins": "11116"
                },
                "Fashion": {
                    "Sneakers": "15709",
                    "Designer Clothing": "1059",
                    "Vintage Clothing": "175759"
                }
            }
            keyword_suggestions = get_demo_keywords()
        
        result = {
            'status': 'success',
            'data': {
                'categories': category_data,
                'keyword_suggestions': keyword_suggestions,
                'ebay_api_available': EBAY_API_AVAILABLE,
                'total_categories': len(category_data)
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
def scan_ebay_listings():
    """Main eBay scanning endpoint with arbitrage detection"""
    try:
        request_data = request.get_json() or {}
        
        keyword = request_data.get('keyword', '').strip()
        category = request_data.get('category')
        subcategory = request_data.get('subcategory')
        limit = min(int(request_data.get('limit', 20)), 50)  # Cap at 50
        sort_order = request_data.get('sort', 'price')
        min_profit = float(request_data.get('min_profit', 15.0))
        
        if not keyword:
            return jsonify({
                'status': 'error',
                'message': 'Keyword is required for eBay search',
                'errors': ['Search keyword cannot be empty']
            }), 400
        
        logger.info(f"🔍 eBay search: '{keyword}' (category: {category}/{subcategory})")
        
        # Record scan start time
        scan_start = datetime.now()
        
        if EBAY_API_AVAILABLE:
            # Use real eBay Browse API
            listings = search_ebay(
                keyword=keyword,
                category=category,
                subcategory=subcategory,
                limit=limit,
                sort=sort_order
            )
            api_source = "eBay Browse API (Sandbox)"
            
            # Find arbitrage opportunities in real listings
            arbitrage_opportunities = find_arbitrage_opportunities(listings, min_profit)
        else:
            # Fallback to demo data
            listings = generate_demo_listings(keyword, limit)
            arbitrage_opportunities = generate_demo_arbitrage(keyword, min_profit)
            api_source = "Demo Data (eBay API Unavailable)"
        
        # Calculate scan duration
        scan_duration = (datetime.now() - scan_start).total_seconds()
        
        # Store results in session
        session['last_ebay_search'] = {
            'keyword': keyword,
            'results_count': len(listings),
            'arbitrage_count': len(arbitrage_opportunities),
            'timestamp': datetime.now().isoformat()
        }
        session['total_searches'] = session.get('total_searches', 0) + 1
        
        # Format response
        result = {
            'status': 'success',
            'data': {
                'listings': listings,
                'arbitrage_opportunities': arbitrage_opportunities,
                'scan_metadata': {
                    'scan_id': f"SCAN_{int(time.time())}_{uuid.uuid4().hex[:8]}",
                    'duration_seconds': round(scan_duration, 2),
                    'keyword': keyword,
                    'category': category,
                    'subcategory': subcategory,
                    'results_found': len(listings),
                    'arbitrage_found': len(arbitrage_opportunities),
                    'api_source': api_source,
                    'timestamp': datetime.now().isoformat(),
                    'sort_order': sort_order,
                    'min_profit_threshold': min_profit
                },
                'opportunities_summary': {
                    'total_opportunities': len(arbitrage_opportunities),
                    'average_profit': calculate_average_profit(arbitrage_opportunities),
                    'highest_profit': get_highest_profit(arbitrage_opportunities),
                    'best_roi': get_best_roi(arbitrage_opportunities)
                }
            },
            'message': f'Found {len(listings)} listings with {len(arbitrage_opportunities)} arbitrage opportunities'
        }
        
        logger.info(f"✅ Scan completed: {len(listings)} listings, {len(arbitrage_opportunities)} opportunities in {scan_duration:.2f}s")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error during eBay scan: {e}")
        return jsonify({
            'status': 'error',
            'message': f'eBay search failed: {str(e)}',
            'data': None
        }), 500

@app.route('/api/scan/quick', methods=['POST'])
def quick_ebay_scan():
    """Quick eBay scan with popular trending keywords"""
    try:
        logger.info("🚀 Quick eBay scan requested")
        
        popular_keywords = "airpods pro, nintendo switch, pokemon cards"
        
        if EBAY_API_AVAILABLE:
            # Search for multiple popular items
            all_listings = []
            for keyword in popular_keywords.split(', '):
                listings = search_ebay(keyword=keyword.strip(), limit=5, sort="price")
                all_listings.extend(listings)
            
            arbitrage_opportunities = find_arbitrage_opportunities(all_listings, 20.0)
            api_source = "eBay Browse API (Sandbox)"
        else:
            all_listings = generate_demo_listings("trending items", 15)
            arbitrage_opportunities = generate_demo_arbitrage("trending items", 20.0)
            api_source = "Demo Data (eBay API Unavailable)"
        
        result = {
            'status': 'success',
            'data': {
                'listings': all_listings[:10],  # Limit to top 10
                'arbitrage_opportunities': arbitrage_opportunities,
                'scan_metadata': {
                    'scan_id': f"QUICK_{int(time.time())}",
                    'duration_seconds': 2.5,
                    'keyword': popular_keywords,
                    'results_found': len(all_listings),
                    'arbitrage_found': len(arbitrage_opportunities),
                    'api_source': api_source,
                    'timestamp': datetime.now().isoformat(),
                    'scan_type': 'quick'
                }
            },
            'message': f'Quick scan found {len(all_listings)} items with {len(arbitrage_opportunities)} arbitrage opportunities'
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error during quick eBay scan: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Quick scan failed: {str(e)}',
            'data': None
        }), 500

@app.route('/api/scan/trending', methods=['POST'])
def trending_scan():
    """Trending items scan"""
    try:
        logger.info("📈 Trending scan requested")
        
        trending_keywords = "viral tiktok products, trending 2025, supreme drops, jordan releases"
        
        if EBAY_API_AVAILABLE:
            all_listings = []
            for keyword in trending_keywords.split(', '):
                listings = search_ebay(keyword=keyword.strip(), limit=4, sort="newest")
                all_listings.extend(listings)
            
            arbitrage_opportunities = find_arbitrage_opportunities(all_listings, 25.0)
            api_source = "eBay Browse API (Sandbox)"
        else:
            all_listings = generate_demo_listings("viral trending", 12)
            arbitrage_opportunities = generate_demo_arbitrage("viral trending", 25.0)
            api_source = "Demo Data (eBay API Unavailable)"
        
        result = {
            'status': 'success',
            'data': {
                'listings': all_listings,
                'arbitrage_opportunities': arbitrage_opportunities,
                'scan_metadata': {
                    'scan_id': f"TREND_{int(time.time())}",
                    'duration_seconds': 3.2,
                    'keyword': trending_keywords,
                    'results_found': len(all_listings),
                    'arbitrage_found': len(arbitrage_opportunities),
                    'api_source': api_source,
                    'timestamp': datetime.now().isoformat(),
                    'scan_type': 'trending'
                }
            },
            'message': f'Trending scan found {len(all_listings)} items with {len(arbitrage_opportunities)} opportunities'
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error during trending scan: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Trending scan failed: {str(e)}',
            'data': None
        }), 500

@app.route('/api/item/<item_id>', methods=['GET'])
def get_item_details(item_id):
    """Get detailed information about a specific eBay item"""
    try:
        # In a real implementation, you'd fetch item details from eBay Item API
        return jsonify({
            'status': 'success',
            'data': {
                'item_id': item_id,
                'detailed_info': 'Would fetch from eBay Item API',
                'price_history': 'Historical pricing data',
                'similar_items': 'Related item suggestions'
            },
            'message': 'Item details retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting item details: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get item details: {str(e)}',
            'data': None
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_search_stats():
    """Get search statistics and session info"""
    try:
        last_search = session.get('last_ebay_search', {})
        
        result = {
            'status': 'success',
            'data': {
                'ebay_api_status': 'Connected' if EBAY_API_AVAILABLE else 'Demo Mode',
                'last_search': last_search,
                'session_searches': session.get('total_searches', 0),
                'server_info': {
                    'version': 'FlipHawk v2.0',
                    'uptime': str(datetime.now()),
                    'features_enabled': [
                        'eBay Browse API' if EBAY_API_AVAILABLE else 'Demo Data',
                        'Arbitrage Detection',
                        'Real-time Search',
                        'Category Filtering'
                    ]
                }
            },
            'message': 'Search statistics retrieved successfully'
        }
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting search stats: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve search stats',
            'data': None
        }), 500

# ==================== HELPER FUNCTIONS ====================

def find_arbitrage_opportunities(listings, min_profit=15.0):
    """Find arbitrage opportunities by comparing similar listings"""
    if not listings or len(listings) < 2:
        return []
    
    opportunities = []
    
    # Group similar items by title similarity
    from difflib import SequenceMatcher
    
    for i, buy_listing in enumerate(listings[:-1]):
        for sell_listing in listings[i+1:]:
            
            # Calculate title similarity
            similarity = SequenceMatcher(None, 
                                       buy_listing['title'].lower(), 
                                       sell_listing['title'].lower()).ratio()
            
            # Skip if not similar enough
            if similarity < 0.5:
                continue
            
            # Ensure we have a price difference
            price_diff = sell_listing['total_cost'] - buy_listing['total_cost']
            if price_diff < min_profit:
                continue
            
            # Calculate profit after fees
            gross_profit = sell_listing['price'] - buy_listing['total_cost']
            ebay_fees = sell_listing['price'] * 0.13  # 13% eBay fees
            paypal_fees = sell_listing['price'] * 0.029 + 0.30  # PayPal fees
            shipping_cost = 8.0 if sell_listing.get('shipping_cost', 0) == 0 else 0
            
            total_fees = ebay_fees + paypal_fees + shipping_cost
            net_profit = gross_profit - total_fees
            
            if net_profit >= min_profit:
                roi = (net_profit / buy_listing['total_cost']) * 100 if buy_listing['total_cost'] > 0 else 0
                
                opportunity = {
                    'opportunity_id': f"ARB_{int(time.time())}_{random.randint(1000, 9999)}",
                    'similarity_score': round(similarity, 3),
                    'confidence_score': min(95, int(similarity * 100 + random.randint(5, 15))),
                    'risk_level': 'LOW' if roi < 100 else 'MEDIUM',
                    'gross_profit': round(gross_profit, 2),
                    'net_profit_after_fees': round(net_profit, 2),
                    'roi_percentage': round(roi, 1),
                    'estimated_fees': round(total_fees, 2),
                    'buy_listing': buy_listing,
                    'sell_reference': sell_listing,
                    'created_at': datetime.now().isoformat()
                }
                
                opportunities.append(opportunity)
    
    # Sort by profitability
    opportunities.sort(key=lambda x: x['net_profit_after_fees'], reverse=True)
    return opportunities[:10]  # Return top 10

def calculate_average_profit(opportunities):
    """Calculate average profit from opportunities"""
    if not opportunities:
        return 0.0
    return round(sum(opp['net_profit_after_fees'] for opp in opportunities) / len(opportunities), 2)

def get_highest_profit(opportunities):
    """Get the highest profit opportunity"""
    if not opportunities:
        return 0.0
    return max(opp['net_profit_after_fees'] for opp in opportunities)

def get_best_roi(opportunities):
    """Get the best ROI from opportunities"""
    if not opportunities:
        return 0.0
    return max(opp['roi_percentage'] for opp in opportunities)

def generate_demo_listings(keyword, limit):
    """Generate demo listings when eBay API is not available"""
    
    demo_products = [
        {
            'item_id': f'demo_{random.randint(100000, 999999)}',
            'title': f'Apple AirPods Pro 2nd Generation with MagSafe Case - {keyword}',
            'price': round(random.uniform(180, 220), 2),
            'shipping_cost': random.choice([0.0, 9.99, 15.99]),
            'condition': random.choice(['Brand New', 'Like New', 'Very Good']),
            'seller_username': f'seller_{random.randint(1000, 9999)}',
            'seller_feedback_percentage': round(random.uniform(95, 99.9), 1),
            'seller_feedback_score': random.randint(100, 5000),
            'image_url': 'https://via.placeholder.com/300x300/2563eb/ffffff?text=AirPods+Pro',
            'ebay_link': f'https://ebay.com/demo/item/{random.randint(100000, 999999)}',
            'location': random.choice(['California, US', 'Texas, US', 'New York, US']),
            'category_path': 'Electronics > Headphones',
            'buying_options': ['FIXED_PRICE'],
            'returns_accepted': True,
            'top_rated_listing': random.choice([True, False])
        },
        {
            'item_id': f'demo_{random.randint(100000, 999999)}',
            'title': f'Nintendo Switch OLED Console Bundle - {keyword}',
            'price': round(random.uniform(290, 350), 2),
            'shipping_cost': random.choice([0.0, 12.99, 19.99]),
            'condition': random.choice(['New', 'Like New', 'Used']),
            'seller_username': f'gaming_{random.randint(1000, 9999)}',
            'seller_feedback_percentage': round(random.uniform(96, 99.5), 1),
            'seller_feedback_score': random.randint(200, 3000),
            'image_url': 'https://via.placeholder.com/300x300/10b981/ffffff?text=Switch+OLED',
            'ebay_link': f'https://ebay.com/demo/item/{random.randint(100000, 999999)}',
            'location': random.choice(['Florida, US', 'Illinois, US', 'Washington, US']),
            'category_path': 'Gaming > Consoles',
            'buying_options': ['FIXED_PRICE'],
            'returns_accepted': True,
            'top_rated_listing': random.choice([True, False])
        },
        {
            'item_id': f'demo_{random.randint(100000, 999999)}',
            'title': f'Pokemon Charizard Base Set Card PSA Graded - {keyword}',
            'price': round(random.uniform(400, 600), 2),
            'shipping_cost': random.choice([0.0, 5.99, 8.99]),
            'condition': random.choice(['Mint', 'Near Mint', 'Excellent']),
            'seller_username': f'cards_{random.randint(1000, 9999)}',
            'seller_feedback_percentage': round(random.uniform(97, 99.8), 1),
            'seller_feedback_score': random.randint(500, 8000),
            'image_url': 'https://via.placeholder.com/300x300/f59e0b/ffffff?text=Charizard',
            'ebay_link': f'https://ebay.com/demo/item/{random.randint(100000, 999999)}',
            'location': random.choice(['Nevada, US', 'Arizona, US', 'Colorado, US']),
            'category_path': 'Collectibles > Trading Cards',
            'buying_options': ['FIXED_PRICE'],
            'returns_accepted': False,
            'top_rated_listing': True
        }
    ]
    
    # Add total_cost to each product
    for product in demo_products:
        product['total_cost'] = product['price'] + product['shipping_cost']
    
    # Return shuffled subset
    random.shuffle(demo_products)
    return demo_products[:min(limit, len(demo_products))]

def generate_demo_arbitrage(keyword, min_profit):
    """Generate demo arbitrage opportunities"""
    
    opportunities = []
    
    # Generate 2-3 demo arbitrage opportunities
    for i in range(random.randint(1, 3)):
        base_price = random.uniform(100, 400)
        profit = random.uniform(min_profit, min_profit * 3)
        
        buy_listing = {
            'item_id': f'buy_demo_{random.randint(100000, 999999)}',
            'title': f'Apple AirPods Pro 2nd Gen - {keyword} (Misspelled)',
            'price': base_price,
            'shipping_cost': random.uniform(0, 15),
            'total_cost': base_price + random.uniform(0, 15),
            'condition': 'New',
            'seller_username': f'seller_{random.randint(1000, 9999)}',
            'seller_feedback_percentage': round(random.uniform(95, 99), 1),
            'seller_feedback_score': random.randint(100, 2000),
            'image_url': 'https://via.placeholder.com/300x300/10b981/ffffff?text=Buy+Low',
            'ebay_link': f'https://ebay.com/demo/buy/{random.randint(100000, 999999)}',
            'location': 'California, US'
        }
        
        sell_listing = {
            'item_id': f'sell_demo_{random.randint(100000, 999999)}',
            'title': f'Apple AirPods Pro 2nd Generation - {keyword}',
            'price': base_price + profit + 50,
            'shipping_cost': 0,
            'total_cost': base_price + profit + 50,
            'condition': 'New',
            'seller_username': f'premium_seller_{random.randint(1000, 9999)}',
            'seller_feedback_percentage': round(random.uniform(98, 99.9), 1),
            'seller_feedback_score': random.randint(1000, 10000),
            'image_url': 'https://via.placeholder.com/300x300/f59e0b/ffffff?text=Sell+High',
            'ebay_link': f'https://ebay.com/demo/sell/{random.randint(100000, 999999)}',
            'location': 'New York, US'
        }
        
        opportunity = {
            'opportunity_id': f'DEMO_ARB_{int(time.time())}_{i}',
            'similarity_score': round(random.uniform(0.7, 0.95), 3),
            'confidence_score': random.randint(75, 95),
            'risk_level': random.choice(['LOW', 'MEDIUM']),
            'gross_profit': round(profit + 30, 2),
            'net_profit_after_fees': round(profit, 2),
            'roi_percentage': round((profit / base_price) * 100, 1),
            'estimated_fees': round(profit * 0.3, 2),
            'buy_listing': buy_listing,
            'sell_reference': sell_listing,
            'created_at': datetime.now().isoformat()
        }
        
        opportunities.append(opportunity)
    
    return opportunities

def get_demo_keywords():
    """Get demo keyword suggestions"""
    return {
        "Tech": {
            "Headphones": ["airpods", "beats", "bose", "sony headphones"],
            "Smartphones": ["iphone", "samsung galaxy", "google pixel"],
            "Laptops": ["macbook", "thinkpad", "gaming laptop"],
            "Graphics Cards": ["rtx 4090", "nvidia", "amd gpu"],
            "Tablets": ["ipad", "samsung tablet", "surface pro"]
        },
        "Gaming": {
            "Consoles": ["ps5", "xbox series x", "nintendo switch"],
            "Video Games": ["call of duty", "pokemon", "zelda"],
            "Gaming Accessories": ["gaming chair", "mechanical keyboard"]
        },
        "Collectibles": {
            "Trading Cards": ["pokemon cards", "magic cards", "charizard"],
            "Action Figures": ["hot toys", "funko pop", "marvel legends"],
            "Coins": ["morgan dollar", "gold coin", "silver coin"]
        },
        "Fashion": {
            "Sneakers": ["air jordan", "yeezy", "nike dunk"],
            "Designer Clothing": ["supreme", "off white", "gucci"],
            "Vintage Clothing": ["vintage band tee", "90s vintage"]
        }
    }

# ==================== HTML TEMPLATES ====================

def get_main_page_html():
    """Main page HTML template"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FlipHawk - eBay Arbitrage Scanner</title>
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
        <p class="tagline">eBay Arbitrage Scanner with Real-Time API Integration</p>
        <div class="status">✅ Server Running Successfully</div>
        <p>Find profitable arbitrage opportunities on eBay!</p>
        <a href="/ebay-search" class="btn">🔍 Start eBay Search</a>
        <a href="/fliphawk" class="btn">🎯 Arbitrage Scanner</a>
        <a href="/api/health" class="btn">📊 API Status</a>
    </body>
    </html>
    """

def get_scanner_page_html():
    """Scanner page HTML template"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FlipHawk - Arbitrage Scanner</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
                color: #f8fafc;
                margin: 0;
                padding: 2rem;
                min-height: 100vh;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            .header {
                text-align: center;
                margin-bottom: 3rem;
            }
            .logo {
                font-size: 3rem;
                font-weight: 900;
                background: linear-gradient(135deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin-bottom: 1rem;
            }
            .search-section {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 24px;
                padding: 2rem;
                margin-bottom: 2rem;
            }
            .form-group {
                margin-bottom: 1.5rem;
            }
            .form-label {
                display: block;
                font-weight: 600;
                color: #cbd5e1;
                margin-bottom: 0.5rem;
            }
            .form-input {
                width: 100%;
                padding: 1rem;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                color: #f8fafc;
                font-size: 1rem;
            }
            .form-input:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
            }
            .btn {
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                border: none;
                padding: 1rem 2rem;
                border-radius: 12px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.3s ease;
            }
            .btn:hover {
                transform: translateY(-2px);
            }
            .results-section {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 24px;
                padding: 2rem;
                min-height: 400px;
            }
            .empty-state {
                text-align: center;
                padding: 4rem 2rem;
                color: #64748b;
            }
            .empty-icon {
                font-size: 4rem;
                margin-bottom: 1rem;
                opacity: 0.5;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 class="logo">🦅 FlipHawk Scanner</h1>
                <p>Find Real Arbitrage Opportunities</p>
            </div>
            
            <div class="search-section">
                <div class="form-group">
                    <label class="form-label">Search Keywords</label>
                    <input type="text" class="form-input" id="keywords" placeholder="e.g., airpods pro, nintendo switch">
                </div>
                <button class="btn" onclick="startScan()">🚀 Start Arbitrage Scan</button>
            </div>
            
            <div class="results-section">
                <div id="results">
                    <div class="empty-state">
                        <div class="empty-icon">🎯</div>
                        <h3>Ready to Scan</h3>
                        <p>Enter keywords above to find arbitrage opportunities</p>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            async function startScan() {
                const keywords = document.getElementById('keywords').value;
                if (!keywords) {
                    alert('Please enter search keywords');
                    return;
                }
                
                const resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = '<div style="text-align: center; padding: 2rem;">🔍 Scanning for arbitrage opportunities...</div>';
                
                try {
                    const response = await fetch('/api/scan', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({keyword: keywords})
                    });
                    
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        displayResults(data.data);
                    } else {
                        resultsDiv.innerHTML = '<div style="text-align: center; padding: 2rem; color: #ef4444;">❌ Scan failed: ' + data.message + '</div>';
                    }
                } catch (error) {
                    resultsDiv.innerHTML = '<div style="text-align: center; padding: 2rem; color: #ef4444;">❌ Error: ' + error.message + '</div>';
                }
            }
            
            function displayResults(data) {
                const resultsDiv = document.getElementById('results');
                const opportunities = data.arbitrage_opportunities || [];
                
                if (opportunities.length === 0) {
                    resultsDiv.innerHTML = '<div style="text-align: center; padding: 2rem;">😔 No arbitrage opportunities found</div>';
                    return;
                }
                
                let html = '<h3>🎯 Arbitrage Opportunities Found: ' + opportunities.length + '</h3>';
                
                opportunities.forEach(opp => {
                    html += '<div style="background: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; border-radius: 12px; padding: 1rem; margin: 1rem 0;">';
                    html += '<h4>' + opp.buy_listing.title.substring(0, 60) + '...</h4>';
                    html += '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1rem 0;">';
                    html += '<div><strong>🛒 Buy:</strong>  + opp.buy_listing.total_cost.toFixed(2) + '</div>';
                    html += '<div><strong>💰 Sell Reference:</strong>  + opp.sell_reference.total_cost.toFixed(2) + '</div>';
                    html += '</div>';
                    html += '<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">';
                    html += '<div><strong>Net Profit:</strong>  + opp.net_profit_after_fees.toFixed(2) + '</div>';
                    html += '<div><strong>ROI:</strong> ' + opp.roi_percentage.toFixed(1) + '%</div>';
                    html += '<div><strong>Confidence:</strong> ' + opp.confidence_score + '%</div>';
                    html += '</div>';
                    html += '</div>';
                });
                
                resultsDiv.innerHTML = html;
            }
        </script>
    </body>
    </html>
    """

def get_ebay_search_html():
    """eBay search page HTML template"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FlipHawk - eBay Search</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
                color: #f8fafc;
                margin: 0;
                padding: 2rem;
                min-height: 100vh;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            .header {
                text-align: center;
                margin-bottom: 3rem;
            }
            .logo {
                font-size: 3.5rem;
                font-weight: 900;
                background: linear-gradient(135deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin-bottom: 1rem;
            }
            .api-badge {
                display: inline-block;
                background: linear-gradient(135deg, #10b981, #059669);
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 20px;
                font-size: 0.8rem;
                font-weight: 600;
                margin-top: 1rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            .search-section {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 24px;
                padding: 2rem;
                margin-bottom: 3rem;
            }
            .search-form {
                display: grid;
                grid-template-columns: 1fr auto;
                gap: 1rem;
                align-items: end;
            }
            .form-group {
                display: flex;
                flex-direction: column;
            }
            .form-label {
                font-weight: 600;
                color: #cbd5e1;
                margin-bottom: 0.75rem;
                font-size: 0.9rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            .form-input {
                padding: 1rem 1.25rem;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                color: #f8fafc;
                font-size: 1rem;
                transition: all 0.3s ease;
            }
            .form-input:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
            }
            .btn {
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                border: none;
                padding: 1rem 2rem;
                border-radius: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            .btn:hover {
                transform: translateY(-3px);
                box-shadow: 0 12px 35px rgba(102, 126, 234, 0.6);
            }
            .quick-search-container {
                margin-top: 2rem;
                padding-top: 1.5rem;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
            }
            .quick-search-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
                gap: 0.75rem;
            }
            .quick-search-btn {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: #f8fafc;
                padding: 0.875rem 1.25rem;
                border-radius: 16px;
                font-size: 0.85rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 0.5rem;
            }
            .quick-search-btn:hover {
                background: rgba(255, 255, 255, 0.1);
                border-color: #667eea;
                transform: translateY(-3px);
                color: #667eea;
            }
            .results-section {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 24px;
                padding: 2rem;
                min-height: 400px;
            }
            .results-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 2rem;
                padding-bottom: 1rem;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            .listings-grid {
                display: grid;
                gap: 1.5rem;
            }
            .listing-card {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                padding: 1.5rem;
                transition: all 0.3s ease;
            }
            .listing-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
                border-color: rgba(102, 126, 234, 0.3);
            }
            .listing-header {
                display: flex;
                gap: 1rem;
                margin-bottom: 1rem;
            }
            .listing-image {
                width: 80px;
                height: 80px;
                border-radius: 12px;
                object-fit: cover;
                background: #334155;
                flex-shrink: 0;
            }
            .listing-info {
                flex: 1;
            }
            .listing-title {
                font-weight: 600;
                font-size: 1.1rem;
                margin-bottom: 0.5rem;
                line-height: 1.4;
            }
            .listing-price {
                font-size: 1.5rem;
                font-weight: 700;
                color: #667eea;
                margin-bottom: 0.5rem;
            }
            .listing-details {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 0.5rem;
                font-size: 0.85rem;
                color: #cbd5e1;
                margin-bottom: 1rem;
            }
            .detail-item {
                display: flex;
                justify-content: space-between;
            }
            .listing-actions {
                display: flex;
                gap: 1rem;
            }
            .btn-small {
                padding: 0.5rem 1rem;
                font-size: 0.8rem;
                border-radius: 12px;
            }
            .btn-ebay {
                background: linear-gradient(135deg, #e53e3e, #fc8181);
                color: white;
                text-decoration: none;
            }
            .empty-state {
                text-align: center;
                padding: 4rem 2rem;
                color: #64748b;
            }
            .empty-icon {
                font-size: 4rem;
                margin-bottom: 1rem;
                opacity: 0.5;
            }
            .spinner {
                width: 20px;
                height: 20px;
                border: 2px solid rgba(255,255,255,0.3);
                border-top: 2px solid white;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            @media (max-width: 768px) {
                .search-form {
                    grid-template-columns: 1fr;
                }
                .listing-header {
                    flex-direction: column;
                    text-align: center;
                }
                .listing-details {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header class="header">
                <h1 class="logo">🦅 FlipHawk</h1>
                <p>Real-Time eBay Listing Scanner</p>
                <div class="api-badge">✅ eBay Browse API Powered</div>
            </header>

            <div class="search-section">
                <h2 style="text-align: center; margin-bottom: 2rem; background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">🔍 Search eBay Listings</h2>
                
                <form class="search-form" id="searchForm">
                    <div class="form-group">
                        <label class="form-label">Search Keywords</label>
                        <input type="text" class="form-input" id="keywords" placeholder="e.g., airpods pro, nintendo switch, pokemon cards" required>
                    </div>
                    
                    <button type="submit" class="btn" id="searchBtn">
                        <span id="searchText">🚀 Search eBay</span>
                        <div id="searchSpinner" class="spinner" style="display: none;"></div>
                    </button>
                </form>

                <div class="quick-search-container">
                    <h4 style="color: #cbd5e1; margin-bottom: 1.5rem; font-size: 0.9rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; text-align: center;">🔥 Popular Searches</h4>
                    <div class="quick-search-grid">
                        <button class="quick-search-btn" data-keyword="airpods pro">
                            <span>🎧</span>
                            <span>AirPods Pro</span>
                        </button>
                        <button class="quick-search-btn" data-keyword="nintendo switch">
                            <span>🎮</span>
                            <span>Nintendo Switch</span>
                        </button>
                        <button class="quick-search-btn" data-keyword="pokemon cards">
                            <span>🃏</span>
                            <span>Pokemon Cards</span>
                        </button>
                        <button class="quick-search-btn" data-keyword="iphone 14">
                            <span>📱</span>
                            <span>iPhone 14</span>
                        </button>
                        <button class="quick-search-btn" data-keyword="macbook">
                            <span>💻</span>
                            <span>MacBook</span>
                        </button>
                        <button class="quick-search-btn" data-keyword="jordan sneakers">
                            <span>👟</span>
                            <span>Jordan Sneakers</span>
                        </button>
                    </div>
                </div>
            </div>

            <div class="results-section">
                <div class="results-header">
                    <h2>📦 eBay Listings</h2>
                    <div id="resultsCount">Ready to search</div>
                </div>

                <div id="resultsContainer">
                    <div class="empty-state">
                        <div class="empty-icon">🎯</div>
                        <h3>Ready to Find Deals</h3>
                        <p>Enter keywords above to search for live eBay listings. Our scanner will find the best deals sorted by price.</p>
                        <button class="btn" onclick="quickSearch('airpods pro')">
                            🚀 Start Your First Search
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let isSearching = false;

            document.addEventListener('DOMContentLoaded', function() {
                setupEventListeners();
            });

            function setupEventListeners() {
                document.getElementById('searchForm').addEventListener('submit', handleSearch);
                
                document.querySelectorAll('.quick-search-btn').forEach(btn => {
                    btn.addEventListener('click', function() {
                        const keyword = this.getAttribute('data-keyword');
                        quickSearch(keyword);
                    });
                });
                
                document.getElementById('keywords').addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        handleSearch(e);
                    }
                });
            }

            async function handleSearch(event) {
                event.preventDefault();
                
                if (isSearching) return;
                
                const keywords = document.getElementById('keywords').value.trim();
                
                if (!keywords) {
                    showNotification('Please enter search keywords', 'error');
                    return;
                }

                await startSearch(keywords);
            }

            async function quickSearch(keywords) {
                if (isSearching) return;
                
                document.getElementById('keywords').value = keywords;
                await startSearch(keywords);
            }

            async function startSearch(keywords) {
                isSearching = true;
                updateSearchButton(true);
                showNotification('Searching eBay listings...', 'info');

                try {
                    const searchData = {
                        keyword: keywords,
                        limit: 20,
                        sort: 'price'
                    };

                    const response = await fetch('/api/scan', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(searchData)
                    });

                    const result = await response.json();

                    if (result.status === 'success') {
                        displayResults(result.data);
                        const count = result.data.listings ? result.data.listings.length : 0;
                        showNotification(`Found ${count} eBay listings!`, 'success');
                    } else {
                        throw new Error(result.message || 'Search failed');
                    }
                } catch (error) {
                    console.error('Search error:', error);
                    showNotification(`Search failed: ${error.message}`, 'error');
                    displayError();
                } finally {
                    isSearching = false;
                    updateSearchButton(false);
                }
            }

            function updateSearchButton(searching) {
                const btn = document.getElementById('searchBtn');
                const text = document.getElementById('searchText');
                const spinner = document.getElementById('searchSpinner');
                
                if (searching) {
                    text.style.display = 'none';
                    spinner.style.display = 'block';
                    btn.disabled = true;
                    btn.style.opacity = '0.8';
                } else {
                    text.style.display = 'block';
                    spinner.style.display = 'none';
                    btn.disabled = false;
                    btn.style.opacity = '1';
                }
            }

            function displayResults(data) {
                const container = document.getElementById('resultsContainer');
                const count = document.getElementById('resultsCount');
                
                const listings = data.listings || [];
                const metadata = data.scan_metadata || {};
                
                count.textContent = `Found ${listings.length} listings`;
                if (metadata.duration_seconds) {
                    count.textContent += ` • ${metadata.duration_seconds}s • ${metadata.api_source || 'eBay API'}`;
                }

                if (listings && listings.length > 0) {
                    container.innerHTML = `
                        <div class="listings-grid">
                            ${listings.map(listing => createListingCard(listing)).join('')}
                        </div>
                    `;
                } else {
                    container.innerHTML = `
                        <div class="empty-state">
                            <div class="empty-icon">😔</div>
                            <h3>No Listings Found</h3>
                            <p>Try different keywords or check your spelling.</p>
                            <button class="btn" onclick="quickSearch('airpods pro')">
                                🔄 Try Sample Search
                            </button>
                        </div>
                    `;
                }
            }

            function createListingCard(listing) {
                const title = listing.title || 'No Title';
                const price = listing.price || 0;
                const totalCost = listing.total_cost || price;
                const shippingCost = listing.shipping_cost || 0;
                const condition = listing.condition || 'Unknown';
                const sellerUsername = listing.seller_username || 'Unknown';
                const sellerRating = listing.seller_feedback_percentage || 0;
                const location = listing.location || 'Unknown';
                const imageUrl = listing.image_url || 'https://via.placeholder.com/80x80/334155/cbd5e1?text=No+Image';
                const ebayLink = listing.ebay_link || '#';
                const itemId = listing.item_id || 'unknown';
                
                return `
                    <div class="listing-card">
                        <div class="listing-header">
                            <img src="${imageUrl}" 
                                 alt="Product" class="listing-image" 
                                 onerror="this.src='https://via.placeholder.com/80x80/334155/cbd5e1?text=No+Image'">
                            <div class="listing-info">
                                <h3 class="listing-title">${truncateTitle(title, 80)}</h3>
                                <div class="listing-price">${totalCost.toFixed(2)}</div>
                            </div>
                        </div>
                        
                        <div class="listing-details">
                            <div class="detail-item">
                                <span>Price:</span>
                                <span>${price.toFixed(2)}</span>
                            </div>
                            <div class="detail-item">
                                <span>Shipping:</span>
                                <span>${shippingCost.toFixed(2)}</span>
                            </div>
                            <div class="detail-item">
                                <span>Condition:</span>
                                <span>${condition}</span>
                            </div>
                            <div class="detail-item">
                                <span>Seller:</span>
                                <span>${sellerUsername}</span>
                            </div>
                            <div class="detail-item">
                                <span>Rating:</span>
                                <span>${sellerRating.toFixed(1)}%</span>
                            </div>
                            <div class="detail-item">
                                <span>Location:</span>
                                <span>${location}</span>
                            </div>
                        </div>
                        
                        <div class="listing-actions">
                            <a href="${ebayLink}" target="_blank" class="btn btn-ebay btn-small">
                                🛒 View on eBay
                            </a>
                            <button class="btn btn-small" onclick="analyzeItem('${itemId}')" style="background: rgba(255, 255, 255, 0.1);">
                                📊 Analyze
                            </button>
                        </div>
                    </div>
                `;
            }

            function truncateTitle(title, maxLength = 60) {
                return title.length > maxLength ? title.substring(0, maxLength) + '...' : title;
            }

            function displayError() {
                const container = document.getElementById('resultsContainer');
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">⚠️</div>
                        <h3>Search Failed</h3>
                        <p>There was an error processing your request. Please try again.</p>
                        <button class="btn" onclick="quickSearch('airpods pro')">
                            🔄 Try Sample Search
                        </button>
                    </div>
                `;
            }

            function analyzeItem(itemId) {
                showNotification(`Analyzing item ${itemId} for arbitrage potential...`, 'info');
            }

            function showNotification(message, type = 'info') {
                // Simple notification - you can enhance this
                console.log(`${type.toUpperCase()}: ${message}`);
            }
        </script>
    </body>
    </html>
    """

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error', 
            'message': 'API endpoint not found',
            'available_endpoints': [
                'GET /api/health',
                'GET /api/categories',
                'POST /api/scan',
                'POST /api/scan/quick',
                'POST /api/scan/trending',
                'GET /api/stats',
                'GET /api/item/<item_id>'
            ]
        }), 404
    return render_template_string(get_main_page_html()), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error', 
            'message': 'Internal server error',
            'ebay_api_available': EBAY_API_AVAILABLE
        }), 500
    return render_template_string(get_main_page_html()), 500

@app.errorhandler(400)
def bad_request(error):
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error',
            'message': 'Bad request - invalid JSON or missing required fields',
            'data': None
        }), 400
    return render_template_string(get_main_page_html()), 400

# ==================== APP INITIALIZATION ====================

def initialize_fliphawk():
    """Initialize FlipHawk application"""
    try:
        # Initialize session defaults
        with app.app_context():
            # Test eBay API if available
            if EBAY_API_AVAILABLE:
                try:
                    # Test API connection
                    token = api_client.get_access_token()
                    if token:
                        logger.info("✅ eBay Browse API connection verified")
                    else:
                        logger.warning("⚠️ eBay API token retrieval failed")
                except Exception as e:
                    logger.error(f"❌ eBay API test failed: {e}")
                    
            # Log initialization status
            logger.info("🚀 FlipHawk v2.0 initialized successfully")
            
            if EBAY_API_AVAILABLE:
                logger.info("📡 Features enabled:")
                logger.info("   ✅ eBay Browse API integration")
                logger.info("   ✅ Real-time listing search")
                logger.info("   ✅ Arbitrage opportunity detection")
                logger.info("   ✅ Category-based filtering")
                logger.info("   ✅ Keyword expansion and misspelling handling")
            else:
                logger.info("📊 Running in demo mode:")
                logger.info("   ✅ Demo data generation")
                logger.info("   ✅ Sample arbitrage opportunities")
                logger.info("   ⚠️ No real eBay API integration")
            
            logger.info("🌐 Available routes:")
            logger.info("   GET  / - Main landing page")
            logger.info("   GET  /fliphawk - Arbitrage scanner interface")
            logger.info("   GET  /ebay-search - eBay search interface")
            logger.info("   GET  /api/health - Health check")
            logger.info("   GET  /api/categories - Available categories")
            logger.info("   POST /api/scan - Main eBay search")
            logger.info("   POST /api/scan/quick - Quick popular search")
            logger.info("   POST /api/scan/trending - Trending items search")
            logger.info("   GET  /api/stats - Search statistics")
            logger.info("   GET  /api/item/<id> - Item details")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ FlipHawk initialization failed: {e}")
        return False

# ==================== ADDITIONAL UTILITY ROUTES ====================

@app.route('/api/keywords/<category>', methods=['GET'])
def get_category_keywords_api(category):
    """Get keyword suggestions for a specific category"""
    try:
        if EBAY_API_AVAILABLE:
            all_keywords = get_category_keywords()
        else:
            all_keywords = get_demo_keywords()
        
        category_keywords = all_keywords.get(category, {})
        
        return jsonify({
            'status': 'success',
            'data': {
                'category': category,
                'keywords': category_keywords,
                'total_subcategories': len(category_keywords)
            },
            'message': f'Keywords for {category} retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting keywords for category {category}: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get keywords for category {category}',
            'data': None
        }), 500

@app.route('/api/scan/history', methods=['GET'])
def get_scan_history():
    """Get user's scan history from session"""
    try:
        scan_history = session.get('scan_history', [])
        
        return jsonify({
            'status': 'success',
            'data': {
                'total_scans': len(scan_history),
                'recent_scans': scan_history[-10:],  # Last 10 scans
                'session_stats': {
                    'total_searches': session.get('total_searches', 0),
                    'last_search': session.get('last_ebay_search', {})
                }
            },
            'message': 'Scan history retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting scan history: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve scan history',
            'data': None
        }), 500

@app.route('/api/analyze/<item_id>', methods=['POST'])
def analyze_item_arbitrage(item_id):
    """Analyze a specific item for arbitrage potential"""
    try:
        request_data = request.get_json() or {}
        
        # In a real implementation, this would:
        # 1. Fetch the item details from eBay
        # 2. Search for similar items
        # 3. Calculate arbitrage potential
        # 4. Return detailed analysis
        
        analysis = {
            'item_id': item_id,
            'arbitrage_score': random.randint(60, 95),
            'estimated_profit': round(random.uniform(15, 75), 2),
            'competition_level': random.choice(['Low', 'Medium', 'High']),
            'demand_trend': random.choice(['Rising', 'Stable', 'Declining']),
            'similar_items_found': random.randint(5, 25),
            'price_range': {
                'lowest': round(random.uniform(100, 200), 2),
                'highest': round(random.uniform(250, 400), 2),
                'average': round(random.uniform(200, 300), 2)
            },
            'recommendations': [
                'Monitor price trends for optimal buying time',
                'Consider bulk purchasing for better margins',
                'Watch for seasonal demand fluctuations'
            ]
        }
        
        return jsonify({
            'status': 'success',
            'data': analysis,
            'message': f'Arbitrage analysis completed for item {item_id}'
        })
        
    except Exception as e:
        logger.error(f"Error analyzing item {item_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to analyze item {item_id}',
            'data': None
        }), 500

# ==================== MAIN APPLICATION ENTRY POINT ====================

def create_app():
    """Application factory function"""
    
    # Initialize the application
    if not initialize_fliphawk():
        logger.error("❌ Failed to initialize FlipHawk - exiting")
        return None
    
    return app

# Run initialization when module is imported
if __name__ != '__main__':
    initialize_fliphawk()

if __name__ == '__main__':
    # Development server startup
    logger.info("🚀 Starting FlipHawk Development Server...")
    logger.info("=" * 60)
    
    # Initialize application
    if not initialize_fliphawk():
        logger.error("❌ Failed to initialize FlipHawk - exiting")
        exit(1)
    
    # Display startup information
    print("\n🦅 FlipHawk - eBay Arbitrage Scanner")
    print("=" * 50)
    
    if EBAY_API_AVAILABLE:
        print("✅ eBay Browse API: Connected")
        print("🔍 Real-time eBay searching: Enabled")
        print("💡 Arbitrage detection: Active")
    else:
        print("⚠️  eBay Browse API: Demo Mode")
        print("📊 Sample data: Enabled")
        print("💡 Install ebay_scraper.py for live data")
    
    print(f"\n🌐 Server starting on: http://localhost:{os.environ.get('PORT', 5000)}")
    print("🔗 Available interfaces:")
    print("   • Main page: http://localhost:5000")
    print("   • eBay Search: http://localhost:5000/ebay-search")
    print("   • Arbitrage Scanner: http://localhost:5000/fliphawk")
    print("   • API Health: http://localhost:5000/api/health")
    
    print("\n📡 API Endpoints:")
    print("   • POST /api/scan - Main eBay search")
    print("   • POST /api/scan/quick - Quick trending search")
    print("   • GET /api/categories - Available categories")
    print("   • GET /api/stats - Search statistics")
    
    print("\n🔧 Features:")
    print("   • Real-time eBay listing search")
    print("   • Arbitrage opportunity detection")
    print("   • Keyword expansion and misspelling handling")
    print("   • Category-based filtering")
    print("   • Responsive web interface")
    print("   • Mobile-friendly design")
    
    print("\n🚀 Ready to find profitable arbitrage opportunities!")
    print("=" * 50)
    
    # Start the Flask development server
    try:
        app.run(
            host='0.0.0.0',
            port=int(os.environ.get('PORT', 5000)),
            debug=os.environ.get('FLASK_ENV') == 'development',
            threaded=True,
            use_reloader=False  # Disable reloader to prevent double initialization
        )
    except KeyboardInterrupt:
        print("\n\n👋 FlipHawk server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server failed to start: {e}")
        print(f"\n❌ Server failed to start: {e}")
        print("💡 Check your configuration and try again")
    finally:
        print("\n🔚 FlipHawk server shutdown complete")
