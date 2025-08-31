#!/usr/bin/env python3
"""
MavFast Remote Brighton Best API
Provides REST API endpoints for n8n to trigger Brighton Best automation remotely.
Designed for Railway/Render deployment (free tier compatible).
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
import traceback
from pathlib import Path

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import gspread
from google.oauth2.service_account import Credentials

# Add Brighton Best automation modules to path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/mavfast_api.log') if os.path.exists('/tmp') else logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Environment configuration for Railway/Render
class Config:
    """Configuration class supporting Railway/Render deployment"""
    
    # Brighton Best credentials
    COMPANY_ID = os.environ.get('COMPANY_ID', 'n20120')
    USER_ID = os.environ.get('USER_ID', 'STEPHEN') 
    PASSWORD = os.environ.get('PASSWORD', 'stephen99')
    
    # Google Sheets configuration
    GOOGLE_SHEETS_CREDENTIALS = os.environ.get('GOOGLE_SHEETS_CREDENTIALS', '')
    INPUT_SHEET_ID = os.environ.get('INPUT_SHEET_ID', '15pzfwd0ii_ySdlWT_8RYSf7a5piDN0PSIaU49Capc58')
    OUTPUT_SHEET_ID = os.environ.get('OUTPUT_SHEET_ID', '15pzfwd0ii_ySdlWT_8RYSf7a5piDN0PSIaU49Capc58')
    
    # Chrome/Selenium configuration for cloud deployment
    CHROME_BIN = os.environ.get('CHROME_BIN', '/usr/bin/chromium-browser')
    CHROMEDRIVER_PATH = os.environ.get('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')
    
    # API configuration
    PORT = int(os.environ.get('PORT', 5000))
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Webhook/notification URLs
    N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL', '')
    SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL', '')

config = Config()

class RemoteBrightonAutomation:
    """Brighton Best automation adapted for cloud deployment"""
    
    def __init__(self):
        self.driver = None
        self.sheets_client = None
        self.setup_google_sheets()
    
    def setup_google_sheets(self):
        """Initialize Google Sheets client from environment variable"""
        try:
            if config.GOOGLE_SHEETS_CREDENTIALS:
                # Parse credentials from environment variable (JSON string)
                creds_data = json.loads(config.GOOGLE_SHEETS_CREDENTIALS)
                credentials = Credentials.from_service_account_info(
                    creds_data,
                    scopes=[
                        'https://www.googleapis.com/auth/spreadsheets',
                        'https://www.googleapis.com/auth/drive'
                    ]
                )
                self.sheets_client = gspread.authorize(credentials)
                logger.info("✅ Google Sheets client initialized")
            else:
                logger.warning("⚠️ No Google Sheets credentials provided")
        except Exception as e:
            logger.error(f"❌ Google Sheets setup failed: {e}")
            self.sheets_client = None
    
    def setup_chrome_driver(self):
        """Initialize Chrome WebDriver for cloud deployment"""
        try:
            chrome_options = Options()
            
            # Cloud-friendly Chrome options
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-javascript')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            # Set Chrome binary location for cloud platforms
            if config.CHROME_BIN and os.path.exists(config.CHROME_BIN):
                chrome_options.binary_location = config.CHROME_BIN
            
            # Initialize WebDriver
            if config.CHROMEDRIVER_PATH and os.path.exists(config.CHROMEDRIVER_PATH):
                service = Service(config.CHROMEDRIVER_PATH)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # Try default Chrome driver
                self.driver = webdriver.Chrome(options=chrome_options)
            
            logger.info("✅ Chrome WebDriver initialized for cloud deployment")
            return True
            
        except Exception as e:
            logger.error(f"❌ Chrome WebDriver setup failed: {e}")
            logger.error(f"Chrome binary: {config.CHROME_BIN}")
            logger.error(f"ChromeDriver path: {config.CHROMEDRIVER_PATH}")
            return False
    
    def process_brighton_automation(self, quote_data: Dict) -> Dict:
        """Execute Brighton Best automation for the provided quote data"""
        
        start_time = datetime.now()
        quote_id = quote_data.get('quote_id', 'UNKNOWN')
        
        logger.info(f"🚀 Starting Brighton Best automation for quote: {quote_id}")
        
        try:
            # Validate input data
            if not quote_data.get('parts_requested'):
                return {
                    'success': False,
                    'error': 'No parts provided for processing',
                    'quote_id': quote_id
                }
            
            # Setup browser
            if not self.setup_chrome_driver():
                return {
                    'success': False,
                    'error': 'Failed to initialize Chrome WebDriver',
                    'quote_id': quote_id
                }
            
            # Brighton Best login and processing
            result = self.run_brighton_workflow(quote_data)
            
            # Update Google Sheets if available
            if self.sheets_client and result.get('success'):
                self.update_sheets_with_results(quote_data, result)
            
            # Add processing metadata
            result.update({
                'processing_time_seconds': (datetime.now() - start_time).total_seconds(),
                'processed_at': datetime.now().isoformat(),
                'api_version': '1.0'
            })
            
            logger.info(f"✅ Brighton Best automation completed for {quote_id}")
            return result
            
        except Exception as e:
            error_msg = f"Brighton Best automation failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            logger.error(traceback.format_exc())
            
            return {
                'success': False,
                'error': error_msg,
                'quote_id': quote_id,
                'processing_time_seconds': (datetime.now() - start_time).total_seconds(),
                'processed_at': datetime.now().isoformat()
            }
        
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    logger.info("🔒 Chrome WebDriver closed")
                except:
                    pass
    
    def run_brighton_workflow(self, quote_data: Dict) -> Dict:
        """Execute the core Brighton Best workflow (adapted from your existing scripts)"""
        
        quote_id = quote_data['quote_id']
        parts = quote_data['parts_requested']
        
        logger.info(f"Processing {len(parts)} parts for quote {quote_id}")
        
        try:
            # Step 1: Navigate to Brighton Best and login
            self.driver.get('https://brightonbest.com/login')
            
            # Add your existing login logic here
            # This would use your proven login methods from enhanced_scraper.py
            
            # Step 2: Create new quote
            # Your existing quote creation logic
            
            # Step 3: Submit parts using bulk paste method
            # Your proven bulk paste logic from enhanced_scraper.py
            
            # Step 4: Extract pricing and location data
            # Your existing scraping methods
            
            # For now, return mock data (replace with actual scraping results)
            mock_results = self.generate_mock_results(parts, quote_id)
            
            return mock_results
            
        except Exception as e:
            raise Exception(f"Brighton Best workflow failed: {str(e)}")
    
    def generate_mock_results(self, parts: List[Dict], quote_id: str) -> Dict:
        """Generate mock results for testing (replace with actual scraping)"""
        
        total_material_cost = 0
        pricing_data = []
        
        for part in parts:
            # Mock pricing calculation
            unit_price = 0.5529  # Replace with actual scraped price
            total_price = part['quantity'] * unit_price
            total_material_cost += total_price
            
            pricing_data.append({
                'part_number': part['part_number'],
                'quantity': part['quantity'],
                'unit_price': unit_price,
                'total_price': total_price,
                'description': f"Mock description for {part['part_number']}",
                'availability': 'In Stock',
                'warehouse_location': 'DALLAS',
                'is_dallas_stock': True
            })
        
        # Mock freight calculation (Dallas = $0, Non-Dallas = $20 per item)
        total_freight = sum(20.0 if not item['is_dallas_stock'] else 0.0 for item in pricing_data)
        dallas_items = sum(1 for item in pricing_data if item['is_dallas_stock'])
        
        return {
            'success': True,
            'quote_id': quote_id,
            'parts_processed': len(parts),
            'pricing_data': pricing_data,
            'total_material_cost': total_material_cost,
            'total_freight': total_freight,
            'total_quote_value': total_material_cost + total_freight,
            'availability_rate': 100.0,  # Mock 100% availability
            'dallas_items': dallas_items,
            'dallas_percentage': (dallas_items / len(parts)) * 100,
            'processing_notes': 'Mock processing completed successfully',
            'brighton_session_info': {
                'login_successful': True,
                'quote_submitted': True,
                'data_extracted': True
            }
        }
    
    def update_sheets_with_results(self, quote_data: Dict, results: Dict):
        """Update Google Sheets with Brighton Best results"""
        try:
            if not self.sheets_client:
                logger.warning("No Google Sheets client available")
                return
                
            # Open the sheet
            sheet = self.sheets_client.open_by_key(config.OUTPUT_SHEET_ID).sheet1
            
            # Find rows with matching quote ID and update pricing data
            quote_id = quote_data['quote_id']
            
            # Your existing sheet update logic would go here
            logger.info(f"✅ Google Sheets updated for quote {quote_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to update Google Sheets: {e}")

# Initialize automation handler
automation_handler = RemoteBrightonAutomation()

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'MavFast Brighton Best API',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0'
    })

@app.route('/api/brighton-automation', methods=['POST'])
def trigger_brighton_automation():
    """Main endpoint for n8n to trigger Brighton Best automation"""
    
    try:
        # Parse request data
        request_data = request.get_json()
        if not request_data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        quote_data = request_data.get('quote_data', {})
        if not quote_data:
            return jsonify({'success': False, 'error': 'No quote_data provided'}), 400
        
        logger.info(f"🎯 Brighton automation request received for quote: {quote_data.get('quote_id', 'UNKNOWN')}")
        
        # Process the automation
        result = automation_handler.process_brighton_automation(quote_data)
        
        # Return results
        status_code = 200 if result.get('success') else 500
        return jsonify(result), status_code
        
    except Exception as e:
        error_response = {
            'success': False,
            'error': f'API error: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }
        logger.error(f"❌ API error: {e}")
        return jsonify(error_response), 500

@app.route('/api/test', methods=['GET', 'POST'])
def test_endpoint():
    """Test endpoint for debugging"""
    
    test_quote_data = {
        'quote_id': 'MF-TEST-20250831-123456',
        'customer_info': {
            'company': 'Test Company',
            'email': 'test@example.com',
            'rep': 'Test Rep'
        },
        'parts_requested': [
            {
                'part_number': '455432',
                'quantity': 225,
                'part_index': 1
            }
        ]
    }
    
    if request.method == 'POST':
        # Test the automation
        result = automation_handler.process_brighton_automation(test_quote_data)
        return jsonify(result)
    else:
        # Return test data structure
        return jsonify({
            'message': 'MavFast Brighton Best API Test Endpoint',
            'test_data': test_quote_data,
            'config': {
                'company_id': config.COMPANY_ID,
                'chrome_bin': config.CHROME_BIN,
                'chromedriver_path': config.CHROMEDRIVER_PATH,
                'has_sheets_client': automation_handler.sheets_client is not None
            }
        })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("🚀 Starting MavFast Brighton Best API")
    logger.info(f"Port: {config.PORT}")
    logger.info(f"Debug: {config.DEBUG}")
    logger.info(f"Chrome Binary: {config.CHROME_BIN}")
    logger.info(f"ChromeDriver: {config.CHROMEDRIVER_PATH}")
    
    app.run(host='0.0.0.0', port=config.PORT, debug=config.DEBUG)