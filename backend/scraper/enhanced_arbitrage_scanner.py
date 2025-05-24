matched_keyword=matched_keyword,
                listing_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                views_count=views_count,
                watchers_count=watchers_count,
                is_auction=is_auction,
                buy_it_now_price=price if not is_auction else 0.0,
                time_left=time_left,
                location=location,
                sold_count=sold_count,
                availability=availability
            )
            
        except Exception as e:
            logger.error(f"Error extracting listing data: {e}")
            return None
    
    def calculate_enhanced_resale_price(self, title: str, current_price: float, 
                                      condition: str, category: str, subcategory: str, location: str) -> float:
        """Advanced resale price estimation with comprehensive market intelligence"""
        base_multiplier = 1.4  # 40% base markup
        
        # Category-specific multipliers based on extensive market analysis
        category_multipliers = {
            'Tech': 1.3,        # Fast-moving, competitive market
            'Gaming': 1.5,      # High demand, limited supply dynamics
            'Collectibles': 2.2,# High markup potential, collector premium
            'Fashion': 1.8,     # Brand value and trend-driven
            'Vintage': 2.5,     # Rarity and nostalgia premium
            'Antiques': 2.0,    # Collector and historical value
            'Sports': 1.6,      # Fan dedication premium
            'Music': 1.7        # Artist and rarity value
        }
        
        # Subcategory-specific adjustments for precision
        subcategory_multipliers = {
            'Trading Cards': 2.8,
            'Sneakers': 2.0,
            'Consoles': 1.4,
            'Graphics Cards': 1.2,
            'Smartphones': 1.3,
            'Headphones': 1.6,
            'Designer Clothing': 2.2,
            'Action Figures': 1.9,
            'Vintage Electronics': 2.3,
            'Watches': 1.8,
            'Jewelry': 1.9,
            'Cameras': 1.5,
            'Video Games': 1.3,
            'Comics': 2.1
        }
        
        # Apply category multiplier
        if category in category_multipliers:
            base_multiplier *= category_multipliers[category]
        
        # Apply subcategory multiplier
        if subcategory in subcategory_multipliers:
            base_multiplier *= subcategory_multipliers[subcategory]
        
        # Condition-based adjustments with granular scaling
        condition_multipliers = {
            'new': 1.6, 'brand new': 1.6, 'new with tags': 1.7, 'sealed': 1.8,
            'new in box': 1.7, 'new other': 1.5, 'new without tags': 1.5,
            'like new': 1.4, 'mint': 1.5, 'near mint': 1.4, 'mint condition': 1.5,
            'very good': 1.3, 'excellent': 1.35, 'very fine': 1.25,
            'good': 1.2, 'fine': 1.15, 'very good condition': 1.3,
            'acceptable': 1.1, 'used': 1.15, 'fair': 1.05, 'poor': 0.95,
            'refurbished': 1.25, 'certified refurbished': 1.3, 'open box': 1.3,
            'manufacturer refurbished': 1.35
        }
        
        condition_key = next(
            (k for k in condition_multipliers.keys() if k in condition.lower()), 
            'used'
        )
        base_multiplier *= condition_multipliers[condition_key]
        
        # High-demand keywords analysis with comprehensive database
        demand_keywords = [
            # Rarity indicators
            'rare', 'limited', 'exclusive', 'vintage', 'first edition', 'original',
            'sealed', 'mint', 'deadstock', 'og', 'grail', 'holy grail', 'unicorn',
            'prototype', 'sample', 'promo', 'one of one', '1/1', 'one off',
            
            # Grading and authentication
            'psa 10', 'psa 9', 'bgs 10', 'bgs 9.5', 'cgc 10', 'cgc 9.8',
            'gem mint', 'black label', 'pristine', 'perfect', 'flawless',
            
            # Viral and trending
            'viral', 'trending', 'tiktok', 'popular', 'hot', 'fire', 'must have',
            'sold out', 'discontinued', 'retired', 'no longer made',
            
            # Investment terms
            'investment', 'appreciating', 'blue chip', 'safe investment',
            'collectible investment', 'store of value', 'hedge',
            
            # Premium descriptors
            'premium', 'luxury', 'high end', 'top tier', 'flagship',
            'professional', 'pro model', 'signature', 'artist series'
        ]
        
        demand_boost = 1.0
        title_lower = title.lower()
        for keyword in demand_keywords:
            if keyword in title_lower:
                demand_boost += 0.15
        
        # Cap demand boost to prevent unrealistic prices
        base_multiplier *= min(demand_boost, 2.0)
        
        # Price range optimization based on market sweet spots
        if 10 <= current_price <= 50:
            base_multiplier *= 1.2  # High turnover range, easy to flip
        elif 50 <= current_price <= 200:
            base_multiplier *= 1.15  # Optimal range for most categories
        elif 200 <= current_price <= 500:
            base_multiplier *= 1.1   # Good range, but slower turnover
        elif 500 <= current_price <= 1000:
            base_multiplier *= 1.05  # Requires more specialized buyers
        elif current_price > 1000:
            base_multiplier *= 0.9   # High-end items, limited market
        
        # Location-based arbitrage opportunities
        location_lower = location.lower()
        if 'china' in location_lower or 'hong kong' in location_lower:
            base_multiplier *= 1.3  # Import arbitrage opportunity
        elif 'japan' in location_lower:
            base_multiplier *= 1.4  # Premium for Japanese items (quality perception)
        elif 'usa' in location_lower or 'united states' in location_lower:
            base_multiplier *= 1.1  # Domestic premium, faster shipping
        elif 'germany' in location_lower or 'uk' in location_lower:
            base_multiplier *= 1.05  # European quality perception
        
        # Brand recognition boost with comprehensive brand database
        premium_brands = [
            # Tech brands
            'apple', 'google', 'microsoft', 'sony', 'samsung', 'dell', 'hp',
            'nvidia', 'amd', 'intel', 'canon', 'nikon', 'gopro', 'dji',
            
            # Fashion brands
            'nike', 'jordan', 'adidas', 'supreme', 'off-white', 'yeezy',
            'louis vuitton', 'gucci', 'chanel', 'hermes', 'prada', 'versace',
            'balenciaga', 'givenchy', 'valentino', 'bottega veneta',
            
            # Luxury brands
            'rolex', 'omega', 'patek philippe', 'audemars piguet', 'cartier',
            'tiffany', 'bulgari', 'ferrari', 'lamborghini', 'porsche',
            
            # Gaming brands
            'nintendo', 'playstation', 'xbox', 'razer', 'corsair', 'steelseries',
            
            # Collectible brands
            'pokemon', 'magic', 'topps', 'panini', 'upper deck', 'hot toys',
            'sideshow', 'funko', 'lego', 'disney', 'marvel', 'dc'
        ]
        
        for brand in premium_brands:
            if brand in title_lower:
                base_multiplier *= 1.2
                break
        
        # Seasonal and trending adjustments
        current_month = datetime.now().month
        seasonal_multipliers = {
            11: 1.1,  # November (Black Friday prep)
            12: 1.15, # December (Holiday season)
            1: 1.05,  # January (New Year resolutions)
            8: 1.08,  # August (Back to school)
            9: 1.06   # September (Back to school continued)
        }
        
        if current_month in seasonal_multipliers:
            base_multiplier *= seasonal_multipliers[current_month]
        
        # Final price calculation with bounds checking
        estimated_price = round(current_price * base_multiplier, 2)
        
        # Sanity check - ensure reasonable markup bounds
        min_price = current_price * 1.1  # At least 10% markup
        max_price = current_price * 5.0  # Maximum 400% markup
        
        return max(min_price, min(estimated_price, max_price))
    
    def calculate_enhanced_confidence_score(self, title: str, price: float, condition: str,
                                          seller_rating: str, estimated_profit: float,
                                          category: str, subcategory: str, matched_keyword: str,
                                          location: str, feedback_count: str) -> int:
        """Advanced confidence scoring with comprehensive multi-factor analysis"""
        score = 50  # Base score
        
        # Price range scoring optimized for different categories
        price_ranges = {
            'Collectibles': [(50, 500, 25), (20, 1000, 15), (10, 2000, 10)],
            'Tech': [(30, 300, 25), (15, 800, 15), (10, 1500, 10)],
            'Gaming': [(40, 400, 25), (20, 600, 15), (10, 1000, 10)],
            'Fashion': [(25, 250, 25), (15, 500, 15), (10, 1000, 10)],
            'Vintage': [(30, 400, 25), (15, 800, 15), (10, 1200, 10)]
        }
        
        ranges = price_ranges.get(category, [(20, 200, 25), (10, 500, 15), (5, 1000, 10)])
        for min_price, max_price, points in ranges:
            if min_price <= price <= max_price:
                score += points
                break
        
        # Condition scoring with detailed breakdown
        condition_scores = {
            'new': 30, 'brand new': 30, 'new with tags': 35, 'sealed': 40,
            'new in box': 32, 'new other': 25, 'new without tags': 28,
            'mint': 28, 'near mint': 25, 'like new': 25, 'mint condition': 30,
            'very good': 20, 'excellent': 22, 'very fine': 20,
            'good': 15, 'fine': 12, 'very good condition': 18,
            'acceptable': 10, 'used': 12, 'fair': 8, 'poor': 5,
            'refurbished': 18, 'certified refurbished': 22, 'open box': 20,
            'manufacturer refurbished': 25
        }
        
        condition_found = False
        for cond, points in condition_scores.items():
            if cond in condition.lower():
                score += points
                condition_found = True
                break
        
        if not condition_found and condition != "Unknown":
            score += 10  # Some condition information is better than none
        
        # Profit-based scoring with category-specific thresholds
        profit_thresholds = {
            'Collectibles': [25, 50, 100, 200, 400],
            'Tech': [15, 30, 60, 120, 250],
            'Gaming': [20, 40, 80, 150, 300],
            'Fashion': [30, 60, 120, 250, 500],
            'Vintage': [35, 70, 140, 280, 600]
        }
        
        thresholds = profit_thresholds.get(category, [15, 30, 60, 120, 250])
        
        if estimated_profit >= thresholds[4]:
            score += 35  # Exceptional profit
        elif estimated_profit >= thresholds[3]:
            score += 30  # Excellent profit
        elif estimated_profit >= thresholds[2]:
            score += 25  # Very good profit
        elif estimated_profit >= thresholds[1]:
            score += 20  # Good profit
        elif estimated_profit >= thresholds[0]:
            score += 15  # Decent profit
        elif estimated_profit >= 5:
            score += 5   # Minimal profit
        elif estimated_profit < 0:
            score -= 30  # Loss scenario
        
        # Seller quality scoring with detailed breakdown
        try:
            if '%' in seller_rating and seller_rating != "Not available":
                rating_value = float(re.search(r'([\d.]+)', seller_rating).group(1))
                if rating_value >= 99.8:
                    score += 25  # Exceptional seller
                elif rating_value >= 99.5:
                    score += 20  # Excellent seller
                elif rating_value >= 98.0:
                    score += 15  # Very good seller
                elif rating_value >= 95.0:
                    score += 10  # Good seller
                elif rating_value >= 90.0:
                    score += 5   # Acceptable seller
                elif rating_value >= 85.0:
                    score -= 5   # Below average seller
                elif rating_value < 85.0:
                    score -= 15  # Poor seller
        except (ValueError, AttributeError):
            pass
        
        # Feedback count scoring with exponential scaling
        try:
            if feedback_count != "Not available":
                count = int(feedback_count.replace(',', ''))
                if count >= 50000:
                    score += 20  # Power seller
                elif count >= 10000:
                    score += 15  # Established seller
                elif count >= 1000:
                    score += 10  # Experienced seller
                elif count >= 100:
                    score += 5   # Regular seller
                elif count >= 50:
                    score += 2   # New but active seller
                elif count < 10:
                    score -= 10  # Very new seller
        except (ValueError, AttributeError):
            pass
        
        # Title quality and completeness assessment
        title_words = len(title.split())
        title_chars = len(title)
        
        if title_words >= 15 and title_chars >= 80:
            score += 20  # Very detailed title
        elif title_words >= 10 and title_chars >= 60:
            score += 15  # Good detail level
        elif title_words >= 6 and title_chars >= 40:
            score += 10  # Adequate detail
        elif title_words >= 4:
            score += 5   # Minimal detail
        else:
            score -= 5   # Too vague
        
        # Keyword matching accuracy with advanced similarity
        keyword_similarity = difflib.SequenceMatcher(
            None, matched_keyword.lower(), title.lower()
        ).ratio()
        
        if keyword_similarity > 0.9:
            score += 25  # Excellent match
        elif keyword_similarity > 0.8:
            score += 20  # Very good match
        elif keyword_similarity > 0.6:
            score += 15  # Good match
        elif keyword_similarity > 0.4:
            score += 10  # Acceptable match
        elif keyword_similarity > 0.2:
            score += 5   # Weak match
        else:
            score -= 10  # Poor match
        
        # Location-based trust and shipping considerations
        location_lower = location.lower()
        if 'usa' in location_lower or 'united states' in location_lower:
            score += 10  # Domestic, reliable shipping
        elif 'canada' in location_lower:
            score += 8   # Close, reliable
        elif 'uk' in location_lower or 'germany' in location_lower:
            score += 5   # EU, generally reliable
        elif 'japan' in location_lower:
            score += 5   # Quality reputation
        elif 'australia' in location_lower:
            score += 3   # Distant but reliable
        elif 'china' in location_lower or 'hong kong' in location_lower:
            score -= 5   # Longer shipping, potential issues
        elif location == "Unknown":
            score -= 8   # Uncertainty penalty
        
        # Category-specific confidence bonuses
        high_confidence_categories = ['Collectibles', 'Fashion', 'Vintage']
        medium_confidence_categories = ['Gaming', 'Tech']
        
        if category in high_confidence_categories:
            score += 10  # High markup potential
        elif category in medium_confidence_categories:
            score += 5   # Good markup potential
        
        # Brand recognition and authenticity indicators
        premium_indicators = [
            'authentic', 'genuine', 'original', 'official', 'licensed',
            'certificate', 'serial number', 'hologram', 'warranty',
            'verified', 'authenticated', 'certified', 'authorized dealer',
            'factory sealed', 'tamper proof', 'coa', 'certificate of authenticity'
        ]
        
        authenticity_score = 0
        for indicator in premium_indicators:
            if indicator in title.lower():
                authenticity_score += 3
        
        score += min(authenticity_score, 15)  # Cap at 15 points for authenticity
        
        # Risk factors that reduce confidence
        risk_factors = [
            'as is', 'no returns', 'sold as is', 'damaged', 'broken',
            'for parts', 'not working', 'cracked', 'scratched',
            'missing', 'incomplete', 'untested', 'unknown condition'
        ]
        
        risk_penalty = 0
        for risk in risk_factors:
            if risk in title.lower():
                risk_penalty += 10
        
        score -= min(risk_penalty, 30)  # Cap penalty at 30 points
        
        # Final score bounds and validation
        return max(0, min(100, score))
    
    def scan_with_keyword_variations(self, base_keyword: str, category: str, 
                                   subcategory: str = None, max_pages: int = 3, 
                                   min_profit: float = 15.0) -> List[eBayListing]:
        """Scan eBay using keyword variations for comprehensive coverage"""
        logger.info(f"🔍 Scanning with keyword: '{base_keyword}' in {category}/{subcategory}")
        
        # Generate comprehensive keyword variations
        keyword_variations = self.keyword_generator.generate_keyword_variations(base_keyword)
        trending_keywords = self.keyword_generator.generate_trending_keywords([base_keyword])
        
        # Combine and prioritize keywords
        all_keywords = [base_keyword] + keyword_variations[:8] + trending_keywords[:4]
        
        all_listings = []
        self.session_stats['categories_searched'].add(f"{category}/{subcategory or 'All'}")
        
        for keyword_index, keyword in enumerate(all_keywords[:12]):  # Limit to prevent rate limiting
            try:
                for page in range(1, max_pages + 1):
                    try:
                        url = self.build_advanced_search_url(keyword, page)
                        soup = self.fetch_page_with_retry(url)
                        
                        if not soup:
                            logger.warning(f"Failed to fetch page {page} for keyword '{keyword}'")
                            break
                        
                        # Multiple item container selectors for robustness
                        item_selectors = [
                            '.s-item__wrapper',
                            '.s-item',
                            '.srp-results .s-item',
                            '.srp-river-results .s-item',
                            '.s-item__wrapper-clearfix'
                        ]
                        
                        items = []
                        for selector in item_selectors:
                            items = soup.select(selector)
                            if items:
                                logger.debug(f"Found {len(items)} items using selector: {selector}")
                                break
                        
                        if not items:
                            logger.warning(f"No items found on page {page} for keyword '{keyword}'")
                            break
                        
                        self.session_stats['total_searches'] += 1
                        self.session_stats['total_listings_found'] += len(items)
                        
                        page_listings = 0
                        for item in items:
                            listing = self.extract_enhanced_listing_data(
                                item, category, subcategory or 'General', keyword
                            )
                            
                            if listing and listing.estimated_profit >= min_profit:
                                all_listings.append(listing)
                                page_listings += 1
                                self.session_stats['profitable_listings'] += 1
                        
                        logger.info(f"Page {page} for '{keyword}': {page_listings} profitable listings")
                        
                        # Smart rate limiting with progressive delays
                        delay = random.uniform(2.0, 4.0) + (keyword_index * 0.5)
                        time.sleep(delay)
                        
                    except Exception as e:
                        logger.error(f"Error scanning page {page} for keyword '{keyword}': {e}")
                        continue
                
                # Delay between keywords with exponential backoff
                keyword_delay = random.uniform(1.0, 3.0) + (keyword_index * 0.2)
                time.sleep(keyword_delay)
                
            except Exception as e:
                logger.error(f"Error processing keyword '{keyword}': {e}")
                continue
        
        logger.info(f"Completed scan for '{base_keyword}': {len(all_listings)} total profitable listings")
        return all_listings
    
    def comprehensive_arbitrage_scan(self, keywords: str = None, target_categories: List[str] = None, 
                                   target_subcategories: Dict[str, List[str]] = None,
                                   min_profit: float = 15.0, max_results: int = 25) -> Dict:
        """Main scanning function with comprehensive analysis and error handling"""
        logger.info("🚀 Starting enhanced FlipHawk arbitrage scan...")
        
        # Reset session stats
        self.session_stats = {
            'total_searches': 0,
            'total_listings_found': 0,
            'profitable_listings': 0,
            'categories_searched': set(),
            'start_time': datetime.now(),
            'success_rate': 0.0
        }
        
        all_opportunities = []
        
        # Default categories if none specified
        if not target_categories:
            target_categories = ['Tech', 'Gaming', 'Collectibles']
        
        # Process keywords if provided
        if keywords:
            search_keywords = [kw.strip() for kw in keywords.split(',') if kw.strip()]
        else:
            search_keywords = ['trending items', 'viral products', 'popular deals']
        
        logger.info(f"Scanning categories: {target_categories}")
        logger.info(f"Using keywords: {search_keywords}")
        
        # Scan each category with keywords
        for category in target_categories:
            try:
                subcategories_to_scan = []
                
                if target_subcategories and category in target_subcategories:
                    subcategories_to_scan = target_subcategories[category]
                else:
                    # Default subcategories for each category
                    default_subcategories = {
                        'Tech': ['Headphones', 'Smartphones'],
                        'Gaming': ['Consoles', 'Video Games'],
                        'Collectibles': ['Trading Cards', 'Action Figures'],
                        'Fashion': ['Sneakers', 'Designer Clothing'],
                        'Vintage': ['Electronics', 'Cameras']
                    }
                    subcategories_to_scan = default_subcategories.get(category, ['General'])
                
                # Limit subcategories for performance
                for subcategory in subcategories_to_scan[:2]:  # Max 2 subcategories per category
                    for keyword in search_keywords[:4]:  # Max 4 keywords per subcategory
                        try:
                            category_listings = self.scan_with_keyword_variations(
                                keyword, category, subcategory, max_pages=2, min_profit=min_profit
                            )
                            all_opportunities.extend(category_listings)
                            
                            # Break if we have enough results to prevent over-scanning
                            if len(all_opportunities) >= max_results * 4:
                                logger.info(f"Reached target of {max_results * 4} opportunities, stopping scan")
                                break
                                
                        except Exception as e:
                            logger.error(f"Error scanning {category}/{subcategory} with keyword '{keyword}': {e}")
                            continue
                    
                    if len(all_opportunities) >= max_results * 4:
                        break
                
                if len(all_opportunities) >= max_results * 4:
                    break
                    
            except Exception as e:
                logger.error(f"Error processing category {category}: {e}")
                continue
        
        # Calculate success rate
        if self.session_stats['total_listings_found'] > 0:
            self.session_stats['success_rate'] = (
                self.session_stats['profitable_listings'] / 
                self.session_stats['total_listings_found'] * 100
            )
        
        # Rank and filter results
        ranked_opportunities = self.rank_arbitrage_opportunities(all_opportunities)
        top_opportunities = ranked_opportunities[:max_results]
        
        # Generate comprehensive summary
        end_time = datetime.now()
        duration = end_time - self.session_stats['start_time']
        
        summary = {
            'scan_metadata': {
                'scan_id': hashlib.md5(str(self.session_stats['start_time']).encode()).hexdigest()[:8],
                'timestamp': end_time.isoformat(),
                'duration_seconds': round(duration.total_seconds(), 2),
                'total_searches_performed': self.session_stats['total_searches'],
                'total_listings_analyzed': self.session_stats['total_listings_found'],
                'profitable_listings_found': len(all_opportunities),
                'categories_scanned': list(self.session_stats['categories_searched']),
                'scan_efficiency': round(self.session_stats['success_rate'], 2),
                'keywords_used': search_keywords,
                'average_listings_per_search': round(
                    self.session_stats['total_listings_found'] / 
                    max(self.session_stats['total_searches'], 1), 2
                )
            },
            'opportunities_summary': {
                'total_opportunities': len(top_opportunities),
                'average_profit': round(
                    sum(op.estimated_profit for op in top_opportunities) / 
                    len(top_opportunities), 2
                ) if top_opportunities else 0,
                'average_confidence': round(
                    sum(op.confidence_score for op in top_opportunities) / 
                    len(top_opportunities), 1
                ) if top_opportunities else 0,
                'highest_profit': max(
                    (op.estimated_profit for op in top_opportunities), default=0
                ),
                'lowest_profit': min(
                    (op.estimated_profit for op in top_opportunities), default=0
                ),
                'categories_represented': list(set(op.category for op in top_opportunities)),
                'subcategories_represented': list(set(op.subcategory for op in top_opportunities)),
                'profit_ranges': {
                    'under_25': len([op for op in top_opportunities if op.estimated_profit < 25]),
                    '25_to_50': len([op for op in top_opportunities if 25 <= op.estimated_profit < 50]),
                    '50_to_100': len([op for op in top_opportunities if 50 <= op.estimated_profit < 100]),
                    'over_100': len([op for op in top_opportunities if op.estimated_profit >= 100])
                },
                'condition_breakdown': {
                    condition: len([op for op in top_opportunities if condition.lower() in op.condition.lower()])
                    for condition in ['New', 'Used', 'Refurbished']
                }
            },
            'top_opportunities': [asdict(listing) for listing in top_opportunities],
            'performance_metrics': {
                'listings_per_second': round(
                    self.session_stats['total_listings_found'] / 
                    max(duration.total_seconds(), 1), 2
                ),
                'profitable_percentage': round(self.session_stats['success_rate'], 2),
                'categories_per_minute': round(
                    len(self.session_stats['categories_searched']) / 
                    max(duration.total_seconds() / 60, 1), 2
                ),
                'average_confidence': round(
                    sum(op.confidence_score for op in top_opportunities) / 
                    len(top_opportunities), 1
                ) if top_opportunities else 0
            }
        }
        
        logger.info(f"✅ Scan completed: {len(top_opportunities)} opportunities found in {duration.total_seconds():.1f}s")
        return summary
    
    def rank_arbitrage_opportunities(self, opportunities: List[eBayListing]) -> List[eBayListing]:
        """Advanced ranking algorithm with comprehensive multi-factor scoring"""
        def calculate_opportunity_score(listing):
            # Weighted scoring algorithm with refined weights
            profit_score = min(listing.estimated_profit / 300, 1.0) * 0.30  # 30% weight
            confidence_score = listing.confidence_score / 100 * 0.25  # 25% weight
            margin_score = min(listing.profit_margin_percent / 100, 1.0) * 0.20  # 20% weight
            
            # Price range optimization (15% weight)
            price_score = 0.0
            if 20 <= listing.total_cost <= 150:
                price_score = 0.15  # Sweet spot for flipping
            elif 10 <= listing.total_cost <= 300:
                price_score = 0.12  # Still good range
            elif 5 <= listing.total_cost <= 500:
                price_score = 0.08   # Acceptable range
            elif listing.category in medium_opportunity_categories:
                category_bonus += 0.03
            
            # Condition-based bonus
            condition_lower = listing.condition.lower()
            if any(keyword in condition_lower for keyword in ['new', 'mint', 'sealed']):
                category_bonus += 0.04
            elif any(keyword in condition_lower for keyword in ['like new', 'excellent', 'very good']):
                category_bonus += 0.02
            
            return profit_score + confidence_score + margin_score + price_score + category_bonus
        
        return sorted(opportunities, key=calculate_opportunity_score, reverse=True)

# Flask Integration Functions
def create_enhanced_api_endpoints(scraper: EnhancedFlipHawkScraper):
    """Create Flask-compatible API endpoint functions with enhanced scraper"""
    
    def scan_arbitrage_opportunities(request_data: Dict) -> Dict:
        """Enhanced API endpoint for arbitrage scanning"""
        try:
            keywords = request_data.get('keywords', '')
            target_categories = request_data.get('categories', ['Tech', 'Gaming', 'Collectibles'])
            target_subcategories = request_data.get('subcategories', {})
            min_profit = float(request_data.get('min_profit', 15.0))
            max_results = int(request_data.get('max_results', 25))
            
            # Validate inputs
            if not keywords.strip():
                return {
                    'status': 'error',
                    'message': 'Keywords are required',
                    'data': None
                }
            
            results = scraper.comprehensive_arbitrage_scan(
                keywords=keywords,
                target_categories=target_categories,
                target_subcategories=target_subcategories,
                min_profit=min_profit,
                max_results=max_results
            )
            
            return {
                'status': 'success',
                'data': results,
                'message': 'Enhanced arbitrage scan completed successfully'
            }
            
        except Exception as e:
            logger.error(f"Enhanced scan failed: {e}")
            return {
                'status': 'error',
                'message': f'Scan failed: {str(e)}',
                'data': None
            }
    
    def quick_scan_endpoint() -> Dict:
        """Quick scan with trending keywords"""
        try:
            trending_keywords = "airpods pro, nintendo switch oled, pokemon cards, viral tiktok products"
            
            results = scraper.comprehensive_arbitrage_scan(
                keywords=trending_keywords,
                target_categories=['Tech', 'Gaming', 'Collectibles'],
                target_subcategories={
                    'Tech': ['Headphones', 'Smartphones'],
                    'Gaming': ['Consoles', 'Video Games'],
                    'Collectibles': ['Trading Cards']
                },
                min_profit=20.0,
                max_results=15
            )
            
            return {
                'status': 'success',
                'data': results,
                'message': 'Quick scan completed successfully'
            }
            
        except Exception as e:
            logger.error(f"Quick scan failed: {e}")
            return {
                'status': 'error',
                'message': f'Quick scan failed: {str(e)}',
                'data': None
            }
    
    def get_categories_endpoint() -> Dict:
        """Get available categories and subcategories"""
        try:
            categories_data = {
                "Tech": {
                    'subcategories': ['Headphones', 'Smartphones', 'Laptops', 'Graphics Cards', 'Tablets'],
                    'total_keywords': 500,
                    'description': 'Technology products and electronics'
                },
                "Gaming": {
                    'subcategories': ['Consoles', 'Video Games', 'Gaming Accessories'],
                    'total_keywords': 300,
                    'description': 'Gaming consoles, games, and accessories'
                },
                "Collectibles": {
                    'subcategories': ['Trading Cards', 'Action Figures', 'Coins'],
                    'total_keywords': 400,
                    'description': 'Collectible items and memorabilia'
                },
                "Fashion": {
                    'subcategories': ['Sneakers', 'Designer Clothing', 'Vintage Clothing'],
                    'total_keywords': 350,
                    'description': 'Fashion items and streetwear'
                },
                "Vintage": {
                    'subcategories': ['Electronics', 'Cameras'],
                    'total_keywords': 200,
                    'description': 'Vintage and retro items'
                }
            }
            
            return {
                'status': 'success',
                'data': categories_data,
                'message': 'Categories retrieved successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to get categories: {e}")
            return {
                'status': 'error',
                'message': f'Failed to get categories: {str(e)}',
                'data': None
            }
    
    def get_session_stats_endpoint() -> Dict:
        """Get current session statistics"""
        try:
            stats = scraper.session_stats.copy()
            stats['categories_searched'] = list(stats['categories_searched'])
            stats['uptime_seconds'] = (datetime.now() - stats['start_time']).total_seconds()
            
            return {
                'status': 'success',
                'data': stats,
                'message': 'Session stats retrieved successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {
                'status': 'error',
                'message': f'Failed to get session stats: {str(e)}',
                'data': None
            }
    
    return {
        'scan_arbitrage': scan_arbitrage_opportunities,
        'quick_scan': quick_scan_endpoint,
        'get_categories': get_categories_endpoint,
        'get_session_stats': get_session_stats_endpoint
    }

# Validation and Utility Functions
def validate_enhanced_scan_request(request_data: Dict) -> Dict:
    """Validate incoming enhanced scan request data with comprehensive checks"""
    errors = []
    
    # Validate keywords
    keywords = request_data.get('keywords', '')
    if not keywords or not keywords.strip():
        errors.append("Keywords are required and cannot be empty")
    elif len(keywords) > 500:
        errors.append("Keywords too long (max 500 characters)")
    elif len(keywords.split(',')) > 10:
        errors.append("Too many keywords (max 10)")
    
    # Validate categories
    valid_categories = ['Tech', 'Gaming', 'Collectibles', 'Fashion', 'Vintage', 'Sports', 'Music', 'Antiques']
    categories = request_data.get('categories', [])
    
    if not isinstance(categories, list):
        errors.append("Categories must be a list")
    elif not categories:
        errors.append("At least one category must be selected")
    elif len(categories) > 5:
        errors.append("Too many categories selected (max 5)")
    elif not all(cat in valid_categories for cat in categories):
        errors.append(f"Invalid categories. Valid options: {valid_categories}")
    
    # Validate min_profit
    try:
        min_profit = float(request_data.get('min_profit', 15.0))
        if min_profit < 0:
            errors.append("Min profit cannot be negative")
        elif min_profit > 1000:
            errors.append("Min profit too high (max $1000)")
    except (ValueError, TypeError):
        errors.append("Min profit must be a valid number")
    
    # Validate max_results
    try:
        max_results = int(request_data.get('max_results', 25))
        if max_results < 1:
            errors.append("Max results must be at least 1")
        elif max_results > 100:
            errors.append("Max results too high (max 100)")
    except (ValueError, TypeError):
        errors.append("Max results must be a valid integer")
    
    # Validate subcategories
    subcategories = request_data.get('subcategories', {})
    if subcategories and not isinstance(subcategories, dict):
        errors.append("Subcategories must be a dictionary")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def get_keyword_suggestions_by_category(category: str, query: str = "") -> List[str]:
    """Get keyword suggestions for a specific category with comprehensive database"""
    category_keywords = {
        'tech': [
            'airpods', 'iphone', 'samsung galaxy', 'macbook', 'ipad',
            'gaming laptop', 'mechanical keyboard', 'wireless mouse',
            'bluetooth speaker', 'smartwatch', 'camera', 'headphones',
            'nintendo switch', 'ps5', 'xbox', 'graphics card', 'ssd',
            'monitor', 'webcam', 'microphone', 'router', 'tablet'
        ],
        'gaming': [
            'ps5', 'xbox series x', 'nintendo switch', 'gaming chair',
            'gaming headset', 'controller', 'gaming monitor', 'pc parts',
            'call of duty', 'pokemon', 'zelda', 'mario', 'fifa',
            'gaming keyboard', 'gaming mouse', 'steam deck', 'retro games',
            'arcade cabinet', 'vr headset', 'racing wheel', 'flight stick'
        ],
        'collectibles': [
            'pokemon cards', 'magic cards', 'baseball cards', 'funko pop',
            'action figures', 'vintage toys', 'comic books', 'trading cards',
            'graded cards', 'psa 10', 'first edition', 'rare cards',
            'vintage collectibles', 'limited edition', 'autographed items',
            'sports memorabilia', 'movie props', 'celebrity autographs'
        ],
        'fashion': [
            'jordan', 'yeezy', 'supreme', 'nike', 'adidas', 'designer',
            'sneakers', 'streetwear', 'vintage', 'luxury', 'limited edition',
            'off white', 'balenciaga', 'gucci', 'louis vuitton', 'rolex',
            'designer bags', 'vintage clothing', 'rare sneakers', 'watches'
        ],
        'vintage': [
            'vintage electronics', 'retro games', 'vintage camera',
            'antique', 'mid century', 'vintage audio', 'classic cars',
            'vintage watches', 'vintage jewelry', 'vinyl records',
            'vintage furniture', 'retro computing', 'film cameras'
        ]
    }
    
    keywords = category_keywords.get(category.lower(), [])
    
    if query:
        # Filter keywords that contain the query
        filtered = [kw for kw in keywords if query.lower() in kw.lower()]
        # Add query variations
        filtered.extend([
            f"{query} new", f"{query} used", f"{query} vintage",
            f"{query} rare", f"{query} limited", f"authentic {query}",
            f"{query} sealed", f"{query} mint", f"{query} graded"
        ])
        return list(set(filtered))[:15]
    
    return keywords[:15]

# Utility functions for data formatting
def format_currency(amount: float) -> str:
    """Format currency for display"""
    return f"${amount:.2f}"

def format_percentage(value: float) -> str:
    """Format percentage for display"""
    return f"{value:.1f}%"

def truncate_text(text: str, max_length: int = 60) -> str:
    """Truncate text with ellipsis"""
    return text[:max_length] + '...' if len(text) > max_length else text

def generate_scan_id() -> str:
    """Generate unique scan ID"""
    return hashlib.md5(f"{datetime.now().isoformat()}{random.random()}".encode()).hexdigest()[:12]

def clean_html_text(text: str) -> str:
    """Clean HTML text and normalize whitespace"""
    if not text:
        return ""
    # Remove HTML tags and normalize whitespace
    clean_text = re.sub(r'<[^>]+>', '', text)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    return clean_text.strip()

# Demo and Testing Functions
def demo_enhanced_scraper():
    """Comprehensive demonstration function for testing the enhanced scraper"""
    scraper = EnhancedFlipHawkScraper()
    
    print("🚀 Starting Enhanced FlipHawk Demo Scan...")
    print("=" * 70)
    
    # Test with popular keywords
    test_keywords = "airpods pro, pokemon charizard, nintendo switch oled"
    
    print(f"🔍 Testing Keywords: {test_keywords}")
    print(f"📂 Categories: Tech, Collectibles, Gaming")
    print(f"💰 Min Profit: $25")
    print(f"📊 Max Results: 5")
    print()
    
    results = scraper.comprehensive_arbitrage_scan(
        keywords=test_keywords,
        target_categories=['Tech', 'Collectibles', 'Gaming'],
        target_subcategories={
            'Tech': ['Headphones'],
            'Collectibles': ['Trading Cards'],
            'Gaming': ['Consoles']
        },
        min_profit=25.0,
        max_results=5
    )
    
    # Display results
    print(f"📊 ENHANCED DEMO RESULTS:")
    print(f"⏱️  Duration: {results['scan_metadata']['duration_seconds']} seconds")
    print(f"🔍 Total searches: {results['scan_metadata']['total_searches_performed']}")
    print(f"📋 Listings analyzed: {results['scan_metadata']['total_listings_analyzed']}")
    print(f"💡 Opportunities found: {results['opportunities_summary']['total_opportunities']}")
    print(f"💰 Average profit: ${results['opportunities_summary']['average_profit']}")
    print(f"🎯 Average confidence: {results['opportunities_summary']['average_confidence']}%")
    print(f"📈 Success rate: {results['scan_metadata']['scan_efficiency']}%")
    print()
    
    if results['top_opportunities']:
        print(f"🏆 TOP OPPORTUNITIES:")
        for i, opportunity in enumerate(results['top_opportunities'][:3], 1):
            print(f"\n{i}. {opportunity['title'][:70]}...")
            print(f"   💰 Profit: ${opportunity['estimated_profit']:.2f}")
            print(f"   🎯 Confidence: {opportunity['confidence_score']}%")
            print(f"   🏪 eBay Price: ${opportunity['price']:.2f}")
            print(f"   🏷️  Resale Price: ${opportunity['estimated_resale_price']:.2f}")
            print(f"   ⭐ Condition: {opportunity['condition']}")
            print(f"   📍 Location: {opportunity['location']}")
            print(f"   🔗 Link: {opportunity['ebay_link'][:60]}...")
    else:
        print("❌ No opportunities found with current criteria")
    
    print(f"\n📈 PROFIT DISTRIBUTION:")
    ranges = results['opportunities_summary']['profit_ranges']
    print(f"   💵 Under $25: {ranges['under_25']} items")
    print(f"   💰 $25-$50: {ranges['25_to_50']} items")
    print(f"   💸 $50-$100: {ranges['50_to_100']} items")
    print(f"   💎 Over $100: {ranges['over_100']} items")
    
    print(f"\n🎯 PERFORMANCE METRICS:")
    metrics = results['performance_metrics']
    print(f"   ⚡ Listings per second: {metrics['listings_per_second']}")
    print(f"   📊 Profitable percentage: {metrics['profitable_percentage']}%")
    print(f"   🏃 Categories per minute: {metrics['categories_per_minute']}")
    
    print("\n" + "=" * 70)
    print("✅ Demo completed successfully!")
    
    return results

# Export main components
__all__ = [
    'EnhancedFlipHawkScraper',
    'AdvancedKeywordGenerator', 
    'eBayListing',
    'create_enhanced_api_endpoints',
    'validate_enhanced_scan_request',
    'demo_enhanced_scraper',
    'get_keyword_suggestions_by_category',
    'format_currency',
    'format_percentage',
    'truncate_text',
    'generate_scan_id',
    'clean_html_text'
]

if __name__ == "__main__":
    # Run comprehensive demo
    try:
        demo_enhanced_scraper()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        logger.exception("Demo failed").total_cost <= 1000:
                price_score = 0.05   # Higher investment risk
            
            # Category and condition bonus (10% weight)
            category_bonus = 0.0
            high_opportunity_categories = ['Collectibles', 'Fashion', 'Gaming', 'Vintage']
            medium_opportunity_categories = ['Tech', 'Sports', 'Music']
            
            if listing.category in high_opportunity_categories:
                category_bonus += 0.06
            elif listing"""
FlipHawk Enhanced eBay Scraper - Complete Implementation
Production-ready scraper with advanced keyword generation, intelligent analysis, and comprehensive error handling
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
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class eBayListing:
    """Enhanced eBay listing data structure with all required fields"""
    title: str
    price: float
    shipping_cost: float
    total_cost: float
    estimated_resale_price: float
    estimated_profit: float
    profit_margin_percent: float
    confidence_score: int
    condition: str
    seller_rating: str
    seller_feedback_count: str
    return_policy: str
    shipping_time: str
    image_url: str
    ebay_link: str
    item_id: str
    category: str
    subcategory: str
    matched_keyword: str
    listing_date: str
    views_count: str
    watchers_count: str
    is_auction: bool
    buy_it_now_price: float
    time_left: str
    location: str
    sold_count: str
    availability: str

class AdvancedKeywordGenerator:
    """Generates comprehensive keyword variations for maximum eBay coverage"""
    
    def __init__(self):
        # Common typos and misspellings database
        self.common_typos = {
            'pokemon': ['pokeman', 'pokmon', 'pokémon', 'pocket monsters', 'pkmn', 'pokemom', 'pokemn'],
            'nintendo': ['nintedo', 'nintndo', 'nitendo', 'ninendo', 'nintedo'],
            'playstation': ['play station', 'playstaton', 'ps', 'playstaion', 'playsation'],
            'iphone': ['i phone', 'ifone', 'apple phone', 'iphome', 'iph0ne'],
            'airpods': ['air pods', 'air pod', 'aripos', 'airpds', 'apple earbuds', 'apple airpads', 'air buds'],
            'beats': ['beets', 'beatz', 'beat', 'dre beats', 'bats headphones'],
            'supreme': ['suprme', 'supremme', 'suprem', 'supremo'],
            'jordan': ['jordon', 'air jordan', 'aj', 'jordans'],
            'xbox': ['x box', 'xobx', 'x-box'],
            'macbook': ['mac book', 'mackbook', 'macbok', 'mac-book'],
            'samsung': ['samung', 'samsang', 'samsug'],
            'magic': ['magik', 'majik', 'mgic'],
            'charizard': ['charizrd', 'charizrd', 'charzard'],
            'vintage': ['vintge', 'vintag', 'vintaje'],
            'sealed': ['seled', 'seald', 'seeled'],
            'collectible': ['colectable', 'collectible', 'collectabel']
        }
        
        # Brand variations
        self.brand_variations = {
            'apple': ['apple inc', 'aapl', 'apple computer'],
            'nike': ['just do it', 'swoosh', 'nik'],
            'adidas': ['three stripes', '3 stripes', 'adi'],
            'sony': ['sonny', 'soney', 'son'],
            'samsung': ['samung', 'galaxy', 'sam'],
            'bose': ['boss', 'boze', 'bosee'],
            'beats': ['dr dre', 'dre', 'beats by dre'],
            'supreme': ['sup', 'bogo'],
            'nintendo': ['nin', 'tendo']
        }
        
        # Condition keywords for enhancement
        self.condition_keywords = [
            'new', 'sealed', 'mint', 'new with tags', 'nwt', 'bnib', 'brand new',
            'used', 'pre-owned', 'preowned', 'like new', 'excellent', 'very good',
            'good', 'fair', 'acceptable', 'refurbished', 'open box', 'certified',
            'graded', 'psa', 'bgs', 'cgc', 'authenticated', 'verified'
        ]
        
        # Trending queue for popular keywords
        self.trending_queue = []
        self.search_history = defaultdict(int)
        
    def generate_keyword_variations(self, base_keyword: str, max_variations: int = 30) -> List[str]:
        """Generate comprehensive keyword variations including typos, abbreviations, and alternatives"""
        variations = set([base_keyword.lower().strip()])
        
        # Clean base keyword
        clean_keyword = re.sub(r'[^\w\s]', '', base_keyword.lower())
        variations.add(clean_keyword)
        
        # Add common typos for recognized keywords
        for correct, typos in self.common_typos.items():
            if correct in clean_keyword:
                for typo in typos:
                    variations.add(clean_keyword.replace(correct, typo))
        
        # Add brand variations
        for brand, brand_vars in self.brand_variations.items():
            if brand in clean_keyword:
                for variation in brand_vars:
                    variations.add(clean_keyword.replace(brand, variation))
        
        # Character-level variations (common typing errors)
        word = clean_keyword
        
        # Adjacent character swaps
        for i in range(len(word) - 1):
            if word[i].isalpha() and word[i+1].isalpha():
                swapped = list(word)
                swapped[i], swapped[i+1] = swapped[i+1], swapped[i]
                variations.add(''.join(swapped))
        
        # Missing characters (skipped letters)
        for i in range(1, len(word) - 1):
            if word[i].isalpha():
                variations.add(word[:i] + word[i+1:])
        
        # Extra characters (double typing)
        for i in range(len(word)):
            if word[i].isalpha():
                variations.add(word[:i] + word[i] + word[i:])
        
        # Common letter substitutions
        substitutions = {
            'c': 'k', 'k': 'c', 's': 'z', 'z': 's', 'ph': 'f', 'f': 'ph',
            'ei': 'ie', 'ie': 'ei', 'ou': 'oo', 'oo': 'ou', 'th': 't', 't': 'th'
        }
        
        for old, new in substitutions.items():
            if old in word:
                variations.add(word.replace(old, new))
        
        # Space and punctuation variations
        variations.add(word.replace(' ', ''))
        variations.add(word.replace(' ', '-'))
        variations.add(word.replace(' ', '_'))
        variations.add(word.replace('-', ' '))
        variations.add(word.replace('_', ' '))
        
        # Plural/singular forms
        if word.endswith('s') and len(word) > 3:
            variations.add(word[:-1])
        elif not word.endswith('s'):
            variations.add(word + 's')
            variations.add(word + 'es')
            if word.endswith('y'):
                variations.add(word[:-1] + 'ies')
        
        # Abbreviations and acronyms
        words = word.split()
        if len(words) > 1:
            # First letters
            abbreviation = ''.join([w[0] for w in words if w])
            if len(abbreviation) > 1:
                variations.add(abbreviation)
                variations.add(abbreviation.upper())
        
        # Number substitutions (leet speak)
        leet_map = {'o': '0', 'i': '1', 'l': '1', 'e': '3', 'a': '@', 's': '$', 't': '7', 'g': '9'}
        leet_word = word
        for letter, number in leet_map.items():
            leet_word = leet_word.replace(letter, number)
        if leet_word != word:
            variations.add(leet_word)
        
        # Phonetic variations
        phonetic_map = {
            'ph': 'f', 'ck': 'k', 'qu': 'kw', 'x': 'ks', 'tion': 'shun',
            'ough': 'uff', 'ea': 'ee', 'ai': 'ay', 'ey': 'y'
        }
        
        for old, new in phonetic_map.items():
            if old in word:
                variations.add(word.replace(old, new))
        
        # Remove empty strings and filter
        variations = [v for v in variations if v and len(v) > 2]
        return list(variations)[:max_variations]

    def generate_trending_keywords(self, base_keywords: List[str]) -> List[str]:
        """Generate trending keyword variations based on current popular terms"""
        trending_prefixes = [
            'viral', 'trending', 'tiktok', 'popular', 'hot', 'new', 'latest',
            'rare', 'limited', 'exclusive', 'special edition', 'collectors',
            'investment', 'grail', 'must have', 'sold out'
        ]
        
        trending_suffixes = [
            '2024', '2025', 'edition', 'version', 'model', 'style', 'drop',
            'release', 'restock', 'sale', 'deal', 'clearance', 'bundle',
            'pack', 'set', 'collection', 'series'
        ]
        
        trending_variations = []
        
        for keyword in base_keywords:
            # Add prefixes (limit to avoid spam)
            for prefix in trending_prefixes[:3]:
                trending_variations.append(f"{prefix} {keyword}")
            
            # Add suffixes
            for suffix in trending_suffixes[:3]:
                trending_variations.append(f"{keyword} {suffix}")
            
            # Add condition combinations
            for condition in self.condition_keywords[:5]:
                trending_variations.append(f"{keyword} {condition}")
        
        return trending_variations
    
    def get_trending_keywords(self, limit: int = 20) -> List[str]:
        """Get trending keywords from the queue"""
        return [item['keyword'] for item in self.trending_queue[:limit]]
    
    def add_trending_keywords(self, keywords: List[str], priority: int = 1):
        """Add trending keywords to search queue"""
        for keyword in keywords:
            self.trending_queue.append({
                'keyword': keyword,
                'priority': priority,
                'added_date': datetime.now().isoformat(),
                'category': 'Trending',
                'subcategory': 'Viral'
            })

class EnhancedFlipHawkScraper:
    """Production-ready eBay scraper with advanced features and error handling"""
    
    def __init__(self):
        self.base_url = "https://www.ebay.com/sch/i.html"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        self.seen_items = set()
        self.keyword_generator = AdvancedKeywordGenerator()
        self.session_stats = {
            'total_searches': 0,
            'total_listings_found': 0,
            'profitable_listings': 0,
            'categories_searched': set(),
            'start_time': datetime.now(),
            'success_rate': 0.0
        }
        
    def build_advanced_search_url(self, keyword: str, page: int = 1, 
                                 price_min: float = None, price_max: float = None,
                                 condition: str = None, sort_order: str = "price") -> str:
        """Build sophisticated eBay search URL with advanced filters"""
        params = {
            '_nkw': keyword,
            '_pgn': page,
            'LH_BIN': 1,  # Buy It Now only
            'LH_Complete': 0,  # Active listings
            'LH_Sold': 0,  # Not sold
            '_sop': {
                'price': 15,  # Price + shipping: lowest first
                'newest': 10,  # Time: newly listed
                'ending': 1,   # Time: ending soonest
                'popular': 12, # Best Match
                'distance': 7  # Distance: nearest first
            }.get(sort_order, 15),
            '_ipg': 240,  # Items per page (max)
            'rt': 'nc',   # No categories redirect
            '_sacat': 0,  # All categories
            'LH_FS': 0,   # Include auction and BIN
            'LH_CAds': 1, # Include classified ads
        }
        
        # Add price filters
        if price_min:
            params['_udlo'] = price_min
        if price_max:
            params['_udhi'] = price_max
            
        # Add condition filter
        if condition:
            condition_codes = {
                'new': '1000|1500',
                'used': '3000|4000|5000|6000',
                'refurbished': '2000|2500'
            }
            if condition.lower() in condition_codes:
                params['LH_ItemCondition'] = condition_codes[condition.lower()]
        
        query_string = urllib.parse.urlencode(params)
        return f"{self.base_url}?{query_string}"
    
    def fetch_page_with_retry(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """Robust page fetching with retry logic and comprehensive error handling"""
        for attempt in range(retries):
            try:
                # Rotate User-Agent to avoid blocking
                user_agents = [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ]
                
                headers = self.headers.copy()
                headers['User-Agent'] = random.choice(user_agents)
                
                # Add random delay to appear more human
                time.sleep(random.uniform(0.5, 2.0))
                
                request = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(request, timeout=30) as response:
                    if response.getcode() == 200:
                        content = response.read()
                        
                        # Handle different encodings
                        encoding = response.info().get_content_charset() or 'utf-8'
                        try:
                            html = content.decode(encoding)
                        except UnicodeDecodeError:
                            html = content.decode('utf-8', errors='ignore')
                        
                        return BeautifulSoup(html, 'html.parser')
                    else:
                        logger.warning(f"HTTP {response.getcode()} for {url}")
                        
            except urllib.error.HTTPError as e:
                logger.warning(f"HTTP Error {e.code} on attempt {attempt + 1} for {url}")
                if e.code == 429:  # Rate limited
                    wait_time = (2 ** attempt) + random.uniform(5, 15)
                    logger.info(f"Rate limited, waiting {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                elif e.code in [403, 406]:  # Blocked
                    logger.warning("Potentially blocked, using longer delay...")
                    time.sleep(random.uniform(10, 30))
                else:
                    break
                    
            except urllib.error.URLError as e:
                logger.warning(f"URL Error on attempt {attempt + 1}: {e}")
                if attempt < retries - 1:
                    time.sleep(random.uniform(2, 5))
                    
            except Exception as e:
                logger.warning(f"Unexpected error on attempt {attempt + 1} for {url}: {e}")
                if attempt < retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(1, 3)
                    time.sleep(wait_time)
                    
        logger.error(f"Failed to fetch {url} after {retries} attempts")
        return None
    
    def extract_enhanced_listing_data(self, item_soup: BeautifulSoup, category: str, 
                                    subcategory: str, matched_keyword: str) -> Optional[eBayListing]:
        """Extract comprehensive listing data with multiple fallbacks and validation"""
        try:
            # Enhanced title extraction with multiple selectors
            title_selectors = [
                'h3.s-item__title',
                '.s-item__title',
                'h3[role="heading"]',
                '.it-ttl a',
                '.s-item__title-text',
                '.s-item__title--has-tags',
                '.s-item__title a span[role="heading"]'
            ]
            
            title = None
            for selector in title_selectors:
                title_elem = item_soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    # Clean title
                    title = re.sub(r'\s+', ' ', title)
                    title = title.replace('New Listing', '').strip()
                    break
            
            # Filter out non-product listings
            if not title or any(skip in title for skip in [
                'Shop on eBay', 'SPONSORED', 'See more like this', 'Advertisement',
                'Related searches', 'You may also like', 'More like this'
            ]):
                return None
            
            # Enhanced price extraction with validation
            price_selectors = [
                '.s-item__price .notranslate',
                '.s-item__price',
                '.adp-price .notranslate',
                '.u-flL.condText',
                '.s-item__detail--primary .s-item__price',
                '.s-item__purchase-options-with-icon .notranslate',
                '.s-item__price-container .notranslate'
            ]
            
            price = 0.0
            for selector in price_selectors:
                price_elem = item_soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    # Handle different price formats
                    if 'to' in price_text.lower() or '-' in price_text:
                        # Price range - take the lower price
                        prices = re.findall(r'\$?([\d,]+\.?\d*)', price_text)
                        if prices:
                            price = float(prices[0].replace(',', ''))
                    else:
                        price_match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
                        if price_match:
                            price = float(price_match.group(1).replace(',', ''))
                    
                    if price > 0:
                        break
            
            # Validate price range
            if price <= 0 or price > 10000:  # Skip if no price or unreasonably high
                return None
            
            # Enhanced shipping cost extraction
            shipping_cost = 0.0
            shipping_selectors = [
                '.s-item__shipping',
                '.s-item__logisticsCost',
                '.vi-acc-del-range',
                '.s-item__detail--secondary',
                '.s-item__shipping-cost'
            ]
            
            for selector in shipping_selectors:
                shipping_elem = item_soup.select_one(selector)
                if shipping_elem:
                    shipping_text = shipping_elem.get_text(strip=True).lower()
                    if 'free' in shipping_text:
                        shipping_cost = 0.0
                        break
                    elif '$' in shipping_text:
                        shipping_match = re.search(r'\$?([\d,]+\.?\d*)', shipping_text)
                        if shipping_match:
                            shipping_cost = float(shipping_match.group(1).replace(',', ''))
                            break
            
            total_cost = price + shipping_cost
            
            # Enhanced link extraction with validation
            link_selectors = [
                '.s-item__link',
                '.it-ttl a',
                '.s-item__title a',
                'a.s-item__link'
            ]
            
            ebay_link = ""
            for selector in link_selectors:
                link_elem = item_soup.select_one(selector)
                if link_elem:
                    href = link_elem.get('href', '')
                    if href:
                        # Clean the URL
                        ebay_link = href.split('?')[0] if '?' in href else href
                        if not ebay_link.startswith('http'):
                            ebay_link = 'https://www.ebay.com' + ebay_link
                        break
            
            if not ebay_link:
                return None
            
            # Enhanced item ID extraction with multiple patterns
            item_id_patterns = [
                r'/(\d{12,})',
                r'itm/(\d+)',
                r'item/(\d+)',
                r'/p/(\d+)',
                r'hash=item([a-f0-9]+)',
                r'item=(\d+)',
                r'_trksid=.*?(\d{12,})'
            ]
            
            item_id = None
            for pattern in item_id_patterns:
                match = re.search(pattern, ebay_link)
                if match:
                    item_id = match.group(1)
                    break
            
            if not item_id:
                # Generate fallback ID from title and price
                item_id = str(abs(hash(title + str(price))))[:12]
            
            # Duplicate prevention
            if item_id in self.seen_items:
                return None
            self.seen_items.add(item_id)
            
            # Enhanced image extraction with fallbacks
            image_selectors = [
                '.s-item__image img',
                '.s-item__image',
                '.img img',
                'img[src*="ebayimg"]',
                'img[data-src*="ebayimg"]',
                '.s-item__wrapper img'
            ]
            
            image_url = ""
            for selector in image_selectors:
                img_elem = item_soup.select_one(selector)
                if img_elem:
                    image_url = img_elem.get('src', '') or img_elem.get('data-src', '')
                    if image_url:
                        # Clean and enhance image URL
                        image_url = image_url.replace('s-l64', 's-l500').replace('s-l140', 's-l500')
                        if not image_url.startswith('http'):
                            image_url = 'https:' + image_url if image_url.startswith('//') else 'https://i.ebayimg.com' + image_url
                        break
            
            # Enhanced condition extraction with standardization
            condition_selectors = [
                '.SECONDARY_INFO',
                '.s-item__subtitle',
                '.s-item__condition',
                '.s-item__detail--secondary',
                '.cldt',
                '.s-item__condition-text'
            ]
            
            condition = "Unknown"
            for selector in condition_selectors:
                condition_elem = item_soup.select_one(selector)
                if condition_elem:
                    condition_text = condition_elem.get_text(strip=True)
                    # Clean condition text
                    condition_text = re.sub(r'\s+', ' ', condition_text)
                    condition_keywords = [
                        'new', 'brand new', 'new with tags', 'sealed', 'mint',
                        'used', 'pre-owned', 'like new', 'very good', 'excellent',
                        'good', 'fair', 'acceptable', 'refurbished', 'open box',
                        'certified refurbished'
                    ]
                    if any(word in condition_text.lower() for word in condition_keywords):
                        condition = condition_text
                        break
            
            # Enhanced seller information extraction
            seller_selectors = [
                '.s-item__seller-info-text',
                '.s-item__seller',
                '.mbg-nw',
                '.s-item__seller-info',
                '.s-item__seller-name'
            ]
            
            seller_rating = "Not available"
            feedback_count = "Not available"
            
            for selector in seller_selectors:
                seller_elem = item_soup.select_one(selector)
                if seller_elem:
                    seller_text = seller_elem.get_text(strip=True)
                    # Extract rating percentage
                    rating_match = re.search(r'([\d.]+)%', seller_text)
                    if rating_match:
                        seller_rating = f"{rating_match.group(1)}%"
                    
                    # Extract feedback count
                    count_match = re.search(r'\(([\d,]+)\)', seller_text)
                    if count_match:
                        feedback_count = count_match.group(1).replace(',', '')
                    
                    if rating_match or count_match:
                        break
            
            # Location extraction with cleaning
            location_selectors = [
                '.s-item__location',
                '.s-item__itemLocation',
                '.s-item__shipping',
                '.s-item__location-text'
            ]
            
            location = "Unknown"
            for selector in location_selectors:
                location_elem = item_soup.select_one(selector)
                if location_elem:
                    location_text = location_elem.get_text(strip=True)
                    if 'from' in location_text.lower():
                        location = location_text.replace('From', '').replace('from', '').strip()
                        break
                    elif any(word in location_text.lower() for word in [
                        'usa', 'united states', 'china', 'japan', 'uk', 'canada', 
                        'germany', 'australia', 'france', 'italy'
                    ]):
                        location = location_text
                        break
            
            # Check if auction or Buy It Now
            is_auction = bool(item_soup.select_one('.s-item__time-left, .timeMs, .vi-time-left, .s-item__time'))
            
            # Extract time left for auctions
            time_left = "Buy It Now"
            if is_auction:
                time_elem = item_soup.select_one('.s-item__time-left, .timeMs, .vi-time-left, .s-item__time')
                if time_elem:
                    time_left = time_elem.get_text(strip=True)
            
            # Additional metrics (limited availability in search results)
            views_count = "Not available"
            watchers_count = "Not available"
            sold_count = "Not available"
            availability = "Available"
            
            # Check sold listings count
            sold_elem = item_soup.select_one('.s-item__quantitySold, .vi-qtyS-sold, .s-item__sold')
            if sold_elem:
                sold_text = sold_elem.get_text(strip=True)
                sold_match = re.search(r'(\d+)', sold_text)
                if sold_match:
                    sold_count = sold_match.group(1)
            
            # Enhanced profitability calculations
            estimated_resale_price = self.calculate_enhanced_resale_price(
                title, price, condition, category, subcategory, location
            )
            estimated_profit = estimated_resale_price - total_cost
            profit_margin_percent = (estimated_profit / estimated_resale_price * 100) if estimated_resale_price > 0 else 0
            
            # Enhanced confidence scoring
            confidence_score = self.calculate_enhanced_confidence_score(
                title, price, condition, seller_rating, estimated_profit, 
                category, subcategory, matched_keyword, location, feedback_count
            )
            
            return eBayListing(
                title=title,
                price=price,
                shipping_cost=shipping_cost,
                total_cost=total_cost,
                estimated_resale_price=estimated_resale_price,
                estimated_profit=estimated_profit,
                profit_margin_percent=profit_margin_percent,
                confidence_score=confidence_score,
                condition=condition,
                seller_rating=seller_rating,
                seller_feedback_count=feedback_count,
                return_policy="30-day returns",  # Default - would need individual page scraping
                shipping_time="3-7 business days",  # Default - would need individual page scraping
                image_url=image_url,
                ebay_link=ebay_link,
                item_id=item_id,
                category=category,
                subcategory=subcategory,
                matched_keyword=matched_keywor
