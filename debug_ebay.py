#!/usr/bin/env python3
"""
eBay API Debug Script
Diagnose exactly why the eBay API isn't working
"""

import requests
import base64
import json
import time

def test_oauth_token():
    """Test OAuth token generation step by step"""
    
    print("🔍 DEBUGGING EBAY OAUTH TOKEN")
    print("=" * 50)
    
    # Your credentials
    app_id = "JackDail-FlipHawk-SBX-bf00e7bcf-34d63630"
    cert_id = "SBX-f00e7bcfbabb-98f9-4d3a-bd03-5ff9"
    dev_id = "f20a1274-fea2-4041-a8dc-721ecf5f38e9"
    
    print(f"App ID: {app_id}")
    print(f"Cert ID: {cert_id[:15]}...")
    print(f"Dev ID: {dev_id}")
    
    # Step 1: Encode credentials
    print(f"\n📝 Step 1: Encoding credentials...")
    credentials = f"{app_id}:{cert_id}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    print(f"✅ Encoded credentials: {encoded_credentials[:30]}...")
    
    # Step 2: OAuth request
    print(f"\n🔑 Step 2: Making OAuth request...")
    oauth_url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {encoded_credentials}'
    }
    
    data = {
        'grant_type': 'client_credentials',
        'scope': 'https://api.ebay.com/oauth/api_scope'
    }
    
    print(f"URL: {oauth_url}")
    print(f"Headers: {headers}")
    print(f"Data: {data}")
    
    try:
        response = requests.post(oauth_url, headers=headers, data=data, timeout=30)
        
        print(f"\n📊 Step 3: OAuth Response...")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ SUCCESS! Token received:")
            print(f"   Access Token: {token_data['access_token'][:30]}...")
            print(f"   Token Type: {token_data.get('token_type')}")
            print(f"   Expires In: {token_data.get('expires_in')} seconds")
            return token_data['access_token']
        else:
            print(f"❌ OAUTH FAILED!")
            print(f"Response Text: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ OAuth Exception: {e}")
        return None

def test_browse_api_call(access_token):
    """Test actual Browse API call"""
    
    print(f"\n🔍 TESTING BROWSE API CALL")
    print("=" * 50)
    
    if not access_token:
        print("❌ No access token available - skipping API test")
        return False
    
    # Browse API call
    browse_url = "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US',
        'X-EBAY-C-ENDUSERCTX': 'contextualLocation=country=US,zip=10001',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    params = {
        'q': 'airpods',
        'limit': 3,
        'sort': 'price',
        'filter': 'buyingOptions:{FIXED_PRICE}|itemLocationCountry:US'
    }
    
    print(f"URL: {browse_url}")
    print(f"Headers: {headers}")
    print(f"Params: {params}")
    
    try:
        response = requests.get(browse_url, headers=headers, params=params, timeout=30)
        
        print(f"\n📊 Browse API Response...")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('itemSummaries', [])
            print(f"✅ SUCCESS! Found {len(items)} items")
            
            if items:
                item = items[0]
                print(f"\n📦 Sample Item:")
                print(f"   Title: {item.get('title', 'N/A')[:60]}...")
                print(f"   Price: ${item.get('price', {}).get('value', 0)}")
                print(f"   Item ID: {item.get('itemId', 'N/A')}")
                return True
            else:
                print(f"⚠️ No items in response")
                return False
        else:
            print(f"❌ BROWSE API FAILED!")
            print(f"Response Text: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Browse API Exception: {e}")
        return False

def test_your_current_code():
    """Test if your current ebay_scraper.py works"""
    
    print(f"\n🔍 TESTING YOUR CURRENT CODE")
    print("=" * 50)
    
    try:
        # Try to import your current code
        from ebay_scraper import search_ebay, api_client
        
        print("✅ Successfully imported ebay_scraper")
        
        # Test token
        print("\n🔑 Testing token with your code...")
        token = api_client.get_access_token()
        
        if token:
            print(f"✅ Your code got token: {token[:30]}...")
        else:
            print("❌ Your code failed to get token")
            return False
        
        # Test search
        print("\n🔍 Testing search with your code...")
        results = search_ebay("airpods", limit=3)
        
        if results:
            print(f"✅ Your code found {len(results)} results")
            return True
        else:
            print("❌ Your code returned no results")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import ebay_scraper: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing your code: {e}")
        return False

def main():
    """Run all diagnostic tests"""
    
    print("🚀 FLIPHAWK EBAY API DIAGNOSTICS")
    print("=" * 60)
    print("This will test your eBay API connection step by step")
    print("=" * 60)
    
    # Test 1: OAuth
    access_token = test_oauth_token()
    
    # Test 2: Browse API
    if access_token:
        browse_success = test_browse_api_call(access_token)
    else:
        browse_success = False
    
    # Test 3: Your current code
    code_success = test_your_current_code()
    
    # Summary
    print(f"\n🏁 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    print(f"OAuth Token:      {'✅ SUCCESS' if access_token else '❌ FAILED'}")
    print(f"Browse API Call:  {'✅ SUCCESS' if browse_success else '❌ FAILED'}")
    print(f"Your Code:        {'✅ SUCCESS' if code_success else '❌ FAILED'}")
    
    if access_token and browse_success:
        print(f"\n🎉 GOOD NEWS: eBay API is working!")
        print(f"The issue is likely in your Flask app import or logic.")
        print(f"\n🔧 NEXT STEPS:")
        print(f"1. Check that your app.py imports ebay_scraper correctly")
        print(f"2. Make sure EBAY_API_AVAILABLE = True in your app")
        print(f"3. Check the Flask logs for import errors")
    elif access_token and not browse_success:
        print(f"\n⚠️ TOKEN WORKS BUT BROWSE API FAILS")
        print(f"This usually means sandbox data limitations or API endpoint issues")
    elif not access_token:
        print(f"\n❌ OAUTH FAILED - CHECK YOUR CREDENTIALS")
        print(f"1. Verify your App ID, Cert ID, and Dev ID are correct")
        print(f"2. Make sure you're using sandbox credentials")
        print(f"3. Check eBay developer account status")
    
    if not code_success:
        print(f"\n🔧 YOUR CODE ISSUES:")
        print(f"1. Make sure ebay_scraper.py has the updated code")
        print(f"2. Check for any import errors in the console")
        print(f"3. Verify all required packages are installed: pip install requests")

if __name__ == "__main__":
    main()
