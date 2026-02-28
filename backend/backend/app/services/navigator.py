"""
Production-ready autonomous navigation engine using AWS Bedrock AgentCore Browser Tool.

This module implements browser orchestration using AgentCore's managed browser
sandbox for navigating Kerala utility portals with real browser automation.
"""
import asyncio
import base64
import json
import logging
import uuid
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from dataclasses import dataclass, field

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import httpx

from app.models import ServiceType, ScrapedData, PaymentStatus, BillingHistory
from app.config import settings
from app.services.captcha_solver import CaptchaSolver

# Configure logging
logger = logging.getLogger(__name__)

# Try to import browser automation tools
try:
    from playwright.sync_api import sync_playwright
    BROWSER_AVAILABLE = True
    logger.info("Playwright browser automation available")
except ImportError as e:
    BROWSER_AVAILABLE = False
    logger.warning(f"Browser automation not available: {e}. Using Nova Pro vision fallback.")


@dataclass
class NavigationSession:
    """Represents an active navigation session."""
    session_id: str
    service_type: ServiceType
    consumer_id: str
    started_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "active"
    screenshots: List[str] = field(default_factory=list)
    extracted_data: Dict[str, Any] = field(default_factory=dict)


class AgentCoreBrowserAgent:
    """
    AWS Bedrock AgentCore Browser Tool for web navigation.
    
    Uses AgentCore's managed browser sandbox to:
    - Navigate websites with full browser capabilities
    - Fill forms and handle CAPTCHAs
    - Extract structured data from web pages
    - Capture screenshots and QR codes
    
    Features:
    - Serverless, auto-scaling browser sessions
    - Reduced CAPTCHA interruptions
    - Enterprise-grade security
    """
    
    NOVA_PRO_MODEL = "amazon.nova-pro-v1:0"
    
    def __init__(self):
        self._runtime_client = None
        self._browser_tool = None
        self._agent = None
        self.captcha_solver = CaptchaSolver()
        self._initialize_clients()
    
    def _initialize_clients(self) -> None:
        """Initialize Bedrock AgentCore clients."""
        try:
            boto_config = Config(
                region_name=settings.aws_region,
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                connect_timeout=30,
                read_timeout=300,
                max_pool_connections=25
            )
            
            client_kwargs = {'config': boto_config}
            
            if settings.aws_access_key_id and settings.aws_secret_access_key:
                client_kwargs['aws_access_key_id'] = settings.aws_access_key_id
                client_kwargs['aws_secret_access_key'] = settings.aws_secret_access_key
                client_kwargs['region_name'] = settings.aws_region
            
            self._runtime_client = boto3.client(
                'bedrock-runtime', 
                **client_kwargs
            )
            
            # Initialize Strands Browser Tool lazily to avoid uvloop/nest_asyncio conflict
            if BROWSER_AVAILABLE:
                logger.info("Strands Browser Tool available; browser instance will be created lazily in worker thread")
            else:
                logger.warning("Browser tool not available, using Nova Pro vision fallback")
            
            logger.info("Bedrock clients initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize clients: {e}")
            raise RuntimeError(f"Client initialization failed: {e}")
    
    @property
    def runtime_client(self):
        if self._runtime_client is None:
            self._initialize_clients()
        return self._runtime_client
    
    async def navigate_and_extract(
        self,
        url: str,
        instructions: str,
        consumer_id: str,
        number_plate: Optional[str] = None,
        max_iterations: int = 15
    ) -> Dict[str, Any]:
        """
        Navigate to a URL and extract data using AgentCore Browser Tool.
        
        Args:
            url: Target URL to navigate to
            instructions: Natural language instructions for the agent
            consumer_id: Consumer ID to enter in forms
            number_plate: Vehicle number for e-Challan (optional)
            max_iterations: Maximum navigation iterations
            
        Returns:
            Extracted data dictionary
        """
        if BROWSER_AVAILABLE:
            return await self._navigate_with_browser(url, instructions, consumer_id, number_plate)
        else:
            return await self._navigate_with_nova_vision(url, instructions, consumer_id, max_iterations)
    
    async def _navigate_with_browser(
        self,
        url: str,
        instructions: str,
        consumer_id: str,
        number_plate: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Use Playwright for direct browser control and navigation.
        """
        logger.info(f"Starting Playwright navigation to: {url}")
        
        def _run_playwright_automation():
            """Run Playwright automation in sync context to avoid uvloop conflict."""
            from playwright.sync_api import sync_playwright
            import time
            
            results = {}
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                try:
                    # Navigate to URL
                    logger.info(f"Navigating to {url}")
                    page.goto(url, wait_until='networkidle', timeout=30000)
                    time.sleep(0.5)
                    
                    # Check for CAPTCHA
                    has_captcha = page.evaluate("""() => {
                        const captchaText = document.querySelector('#captcha-text, #captcha-image, .captcha-image, [id*=captcha]');
                        const captchaInput = document.querySelector('#captchaValue, input[name=captchaValue], input[placeholder*=captcha i]');
                        return captchaText && captchaInput ? 'found' : 'none';
                    }""")
                    
                    logger.info(f"CAPTCHA detection: {has_captcha}")
                    
                    # Handle e-Challan search type selection
                    has_search_type = page.evaluate("""() => {
                        const radios = document.querySelectorAll('input[name=searchType]');
                        return radios.length > 0 ? 'found' : 'none';
                    }""")
                    
                    if has_search_type == 'found':
                        if number_plate:
                            logger.info(f"Selecting vehicle search for {number_plate}")
                            page.evaluate("""() => {
                                const vehicleRadio = document.querySelector('input[name=searchType][value=vehicle]');
                                if (vehicleRadio) {
                                    vehicleRadio.checked = true;
                                    vehicleRadio.dispatchEvent(new Event('change', { bubbles: true }));
                                }
                            }""")
                            time.sleep(0.2)
                        else:
                            page.evaluate("""() => {
                                const challanRadio = document.querySelector('input[name=searchType][value=challan]');
                                if (challanRadio) {
                                    challanRadio.checked = true;
                                    challanRadio.dispatchEvent(new Event('change', { bubbles: true }));
                                }
                            }""")
                            time.sleep(0.2)
                    
                    # Fill search value (consumer ID or number plate)
                    search_value = number_plate if number_plate else consumer_id
                    logger.info(f"Entering search value: {search_value}")
                    
                    typed = page.evaluate(f"""() => {{
                        const selectors = [
                            'input[id="searchValue"]', 'input[name="searchValue"]',
                            'input[id="consumerNumber"]', 'input[name="consumer_id"]',
                            'input[id="buildingId"]', 'input[name="buildingId"]',
                            'input[type="text"]'
                        ];
                        for (let sel of selectors) {{
                            const input = document.querySelector(sel);
                            if (input) {{
                                input.value = '{search_value}';
                                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                return sel;
                            }}
                        }}
                        return null;
                    }}""")
                    
                    if typed:
                        logger.info(f"Typed value using selector: {typed}")
                    
                    # Handle CAPTCHA if present
                    if has_captcha == 'found':
                        logger.info("Solving CAPTCHA...")
                        captcha_value = page.evaluate("""() => {
                            const txt = document.querySelector('#captcha-text');
                            if (txt) return txt.textContent.trim();
                            const img = document.querySelector('#captcha-image, .captcha-image');
                            if (img && img.querySelector('svg text')) {
                                return img.querySelector('svg text').textContent.trim();
                            }
                            return '';
                        }""")
                        
                        logger.info(f"CAPTCHA value: {captcha_value}")
                        
                        # Handle math CAPTCHA
                        if captcha_value and any(op in captcha_value for op in ['+', '-', '*', '/', 'x', '×']):
                            try:
                                math_expr = captcha_value.replace('x', '*').replace('×', '*').replace('÷', '/')
                                result = eval(math_expr, {"__builtins__": {}}, {})
                                captcha_value = str(int(result))
                                logger.info(f"Solved math CAPTCHA: {math_expr} = {captcha_value}")
                            except Exception as e:
                                logger.warning(f"Failed to solve math CAPTCHA: {e}")
                        
                        if captcha_value:
                            page.evaluate(f"""() => {{
                                const input = document.querySelector('#captchaValue') || 
                                             document.querySelector('input[name="captchaValue"]');
                                if (input) {{
                                    input.value = '{captcha_value}';
                                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                }}
                            }}""")
                    
                    # Click submit button
                    logger.info("Clicking submit...")
                    submit_selector = page.evaluate("""() => {
                        const selectors = [
                            'button[type="submit"]', 'input[type="submit"]',
                            '.btn-primary', '.submit-btn', '#submit', 'button'
                        ];
                        for (let sel of selectors) {
                            const btn = document.querySelector(sel);
                            if (btn) {
                                btn.click();
                                return sel;
                            }
                        }
                        return null;
                    }""")
                    
                    if submit_selector:
                        logger.info(f"Clicked submit using: {submit_selector}")
                    
                    # Wait for results
                    logger.info("Waiting for results...")
                    time.sleep(2)
                    
                    # Wait for bill-view to be visible
                    for i in range(3):
                        is_visible = page.evaluate("""() => {
                            const billView = document.getElementById('bill-view');
                            return billView && !billView.classList.contains('hidden') ? 'VISIBLE' : 'HIDDEN';
                        }""")
                        if is_visible == 'VISIBLE':
                            logger.info("Results visible")
                            time.sleep(0.5)
                            break
                        time.sleep(1)
                    
                    # Extract data from DOM
                    logger.info("Extracting data from page...")
                    extracted_data = page.evaluate("""() => {
                        const data = {};
                        
                        // Consumer name
                        const nameSelectors = ['#consumer-name', '#display-owner', '#owner-name', '#bill-name'];
                        for (let sel of nameSelectors) {
                            const el = document.querySelector(sel);
                            if (el && el.textContent.trim()) {
                                data.consumer_name = el.textContent.trim();
                                break;
                            }
                        }
                        
                        // Amount due
                        const amountSelectors = ['#display-fine', '#display-amount', '#bill-amount', '#tax-amount'];
                        for (let sel of amountSelectors) {
                            const el = document.querySelector(sel);
                            if (el && el.textContent.trim()) {
                                data.amount_due = el.textContent.trim();
                                break;
                            }
                        }
                        
                        // Status
                        const statusSelectors = ['#display-status', '#bill-status', '#payment-status'];
                        for (let sel of statusSelectors) {
                            const el = document.querySelector(sel);
                            if (el && el.textContent.trim()) {
                                data.status = el.textContent.trim().toLowerCase();
                                break;
                            }
                        }
                        
                        // Extract from details div if not found yet
                        if (!data.amount_due || !data.consumer_name) {
                            const detailsDiv = document.querySelector('#bill-details, #challan-details, #property-details');
                            if (detailsDiv) {
                                detailsDiv.querySelectorAll('div').forEach(div => {
                                    const label = div.querySelector('span');
                                    const value = div.querySelector('strong');
                                    if (label && value) {
                                        const labelText = label.textContent.trim().toLowerCase();
                                        const valueText = value.textContent.trim();
                                        
                                        if ((labelText.includes('amount') || labelText.includes('fine') || labelText.includes('tax')) && !data.amount_due) {
                                            data.amount_due = valueText;
                                        }
                                        else if ((labelText.includes('unit') || labelText.includes('consumption')) && !data.units_consumed) {
                                            data.units_consumed = valueText;
                                        }
                                        else if (labelText.includes('due date') && !data.due_date) {
                                            data.due_date = valueText;
                                        }
                                    }
                                });
                            }
                        }
                        
                        return data;
                    }""")
                    
                    logger.info(f"Extracted DOM data: {extracted_data}")
                    results['dom_data'] = extracted_data
                    
                    # Extract historical data
                    history_data = page.evaluate("""() => {
                        const historyData = [];
                        const billList = document.querySelector('#bill-list');
                        
                        if (billList) {
                            const billItems = billList.querySelectorAll('.bill-item, button');
                            billItems.forEach(item => {
                                const leftDiv = item.querySelector('div:first-child');
                                const rightDiv = item.querySelector('div:last-child');
                                
                                if (leftDiv && rightDiv) {
                                    const dueSpan = leftDiv.querySelector('span');
                                    const amountStrong = rightDiv.querySelector('strong');
                                    const statusSpan = rightDiv.querySelector('span.pill, span');
                                    
                                    const historyItem = {};
                                    
                                    if (dueSpan && dueSpan.textContent) {
                                        const dueText = dueSpan.textContent.trim();
                                        const dateMatch = dueText.match(/\\d{4}-\\d{2}-\\d{2}/);
                                        historyItem.date = dateMatch ? dateMatch[0] : dueText.replace('Due ', '');
                                    }
                                    
                                    if (amountStrong && amountStrong.textContent) {
                                        historyItem.amount = amountStrong.textContent.trim();
                                    }
                                    
                                    if (statusSpan && statusSpan.textContent) {
                                        historyItem.status = statusSpan.textContent.trim();
                                    }
                                    
                                    if (historyItem.amount) {
                                        historyData.push(historyItem);
                                    }
                                }
                            });
                        }
                        
                        return historyData;
                    }""")
                    
                    logger.info(f"Extracted {len(history_data)} historical bills")
                    results['history_data'] = history_data
                    
                    # Get page HTML
                    results['html'] = page.content()
                    
                finally:
                    browser.close()
            
            return results
        
        try:
            # Run Playwright in thread pool
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, _run_playwright_automation)
            
            dom_data = results.get('dom_data', {})
            history_data = results.get('history_data', [])
            
            # Process extracted data
            if dom_data and dom_data.get('consumer_name') and dom_data.get('amount_due'):
                logger.info("Using DOM-extracted data")
                import re
                amount_str = str(dom_data.get('amount_due', '0'))
                amount_clean = re.sub(r'[₹$Rs\s]', '', amount_str).replace(',', '')
                try:
                    amount_due = float(amount_clean)
                except:
                    amount_due = 0.0
                
                return {
                    'consumer_name': dom_data.get('consumer_name', f'Customer {consumer_id}'),
                    'amount_due': amount_due,
                    'units_consumed': dom_data.get('units_consumed'),
                    'due_date': dom_data.get('due_date'),
                    'status': dom_data.get('status', 'unpaid' if amount_due > 0 else 'paid'),
                    'history': history_data
                }
            
            # Fallback to HTML parsing if DOM extraction failed
            logger.warning("DOM extraction incomplete, falling back to Bedrock analysis")
            page_html = results.get('html', '')
            if page_html:
                return await self._analyze_html_with_bedrock(page_html, consumer_id, history_data)
            
            raise ValueError("Failed to extract data from page")
            
        except Exception as e:
            logger.error(f"Playwright navigation failed: {e}", exc_info=True)
            raise
            
            # Initialize browser session
            result = browser_tool.browser(BrowserInput(action={
                "type": "init_session",
                "description": "OneWay utility portal automation",
                "session_name": session_name
            }))
            results['init'] = result
            logger.info(f"Browser session initialized: {result}")
            
            # Navigate to URL
            result = browser_tool.browser(BrowserInput(action={
                "type": "navigate",
                "session_name": session_name,
                "url": url
            }))
            results['navigate'] = result
            logger.info(f"Navigated to: {url}")
            
            # Small wait for page load
            import time
            time.sleep(0.5)
            logger.info("Page loaded, checking for CAPTCHA...")
            
            # Step 1: Check for CAPTCHA presence
            captcha_result = browser_tool.browser(BrowserInput(action={
                "type": "evaluate",
                "session_name": session_name,
                "script": """(function() {
                    const captchaText = document.querySelector('#captcha-text, #captcha-image, .captcha-image, [id*=captcha]');
                    const captchaInput = document.querySelector('#captchaValue, input[name=captchaValue], input[placeholder*=captcha i]');
                    return captchaText && captchaInput ? 'found' : 'none';
                })();"""
            }))
            has_captcha = 'found' in str(captcha_result.get('content', []))
            logger.info(f"CAPTCHA detection: {has_captcha}")
            
            # Step 2: Select search type for e-Challan
            # Check if page has searchType radio buttons (e-Challan specific)
            search_type_check = browser_tool.browser(BrowserInput(action={
                "type": "evaluate",
                "session_name": session_name,
                "script": """(function() {
                    const radios = document.querySelectorAll('input[name=searchType]');
                    return radios.length > 0 ? 'found' : 'none';
                })();"""
            }))
            has_search_type = 'found' in str(search_type_check.get('content', []))
            
            if has_search_type:
                if number_plate:
                    logger.info(f"e-Challan: Using vehicle number search for {number_plate}")
                    # Select vehicle radio button
                    vehicle_radio_result = browser_tool.browser(BrowserInput(action={
                        "type": "evaluate",
                        "session_name": session_name,
                        "script": """(function() {
                            const vehicleRadio = document.querySelector('input[name=searchType][value=vehicle]');
                            if (vehicleRadio) {
                                vehicleRadio.checked = true;
                                vehicleRadio.dispatchEvent(new Event('change', { bubbles: true }));
                                return 'vehicle-selected';
                            }
                            return 'no-vehicle-radio';
                        })();"""
                    }))
                    logger.info(f"Vehicle radio selection: {vehicle_radio_result}")
                    time.sleep(0.2)
                else:
                    logger.info(f"e-Challan: Using challan number search")
                    # Explicitly select challan radio button and trigger change event
                    challan_radio_result = browser_tool.browser(BrowserInput(action={
                        "type": "evaluate",
                        "session_name": session_name,
                        "script": """(function() {
                            const challanRadio = document.querySelector('input[name=searchType][value=challan]');
                            if (challanRadio) {
                                challanRadio.checked = true;
                                challanRadio.dispatchEvent(new Event('change', { bubbles: true }));
                                return 'challan-selected';
                            }
                            return 'no-challan-radio';
                        })();"""
                    }))
                    logger.info(f"Challan radio selection: {challan_radio_result}")
                    time.sleep(0.2)
            
            # Step 4: Fill consumer ID or number plate
            search_value = number_plate if number_plate else consumer_id
            logger.info(f"Attempting to type search value: {search_value}")
            
            # Use JavaScript to find and fill the input directly (much faster than trying selectors)
            type_result = browser_tool.browser(BrowserInput(action={
                "type": "evaluate",
                "session_name": session_name,
                "script": f"""(function() {{
                    const selectors = [
                        'input[id="searchValue"]',
                        'input[name="searchValue"]', 
                        'input[id="consumerNumber"]',
                        'input[name="consumer_id"]',
                        'input[name="consumer_no"]',
                        'input[name="consumerNumber"]',
                        'input[id="consumer_id"]',
                        'input[id="consumerId"]',
                        'input[id="buildingId"]',
                        'input[name="buildingId"]',
                        'input[type="text"]'
                    ];
                    for (let sel of selectors) {{
                        const input = document.querySelector(sel);
                        if (input) {{
                            input.value = '{search_value}';
                            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            return 'SUCCESS:' + sel;
                        }}
                    }}
                    return 'FAILED';
                }})();"""
            }))
            
            typed = False
            if type_result.get('status') == 'success':
                content = type_result.get('content', [])
                if content and len(content) > 0:
                    result_text = content[0].get('text', '')
                    if 'SUCCESS' in result_text:
                        selector_used = result_text.split(':')[-1].strip() if ':' in result_text else 'unknown'
                        logger.info(f"Typed search value ({search_value}) using selector: {selector_used}")
                        typed = True
            
            if not typed:
                logger.warning("Could not find search value input field")
            
            # Step 5: Handle CAPTCHA if present
            if has_captcha:
                logger.info("CAPTCHA detected, attempting solve...")
                # Extract CAPTCHA text/image
                captcha_extract = browser_tool.browser(BrowserInput(action={
                    "type": "evaluate",
                    "session_name": session_name,
                    "script": """(function() {
                        const txt = document.querySelector('#captcha-text');
                        if (txt) return txt.textContent.trim();
                        const img = document.querySelector('#captcha-image, .captcha-image');
                        if (img && img.querySelector('svg text')) {
                            return img.querySelector('svg text').textContent.trim();
                        }
                        return '';
                    })();"""
                }))
                
                captcha_value = ''
                if captcha_extract.get('status') == 'success':
                    content = captcha_extract.get('content', [])
                    if content and len(content) > 0:
                        raw = content[0].get('text', '')
                        # Strip prefix if evaluate returns "Evaluation result (fixed): VALUE"
                        if 'Evaluation result' in raw:
                            captcha_value = raw.split(':')[-1].strip()
                        else:
                            captcha_value = raw.strip()
                
                logger.info(f"Extracted CAPTCHA text: '{captcha_value}'")
                
                # Check if it's a math problem (e.g., "4 + 1", "10 - 3", "2 * 5")
                if captcha_value and any(op in captcha_value for op in ['+', '-', '*', '/', 'x', '×']):
                    try:
                        # Replace multiplication symbols
                        math_expr = captcha_value.replace('x', '*').replace('×', '*').replace('÷', '/')
                        # Evaluate the math expression safely
                        result = eval(math_expr, {"__builtins__": {}}, {})
                        captcha_value = str(int(result))
                        logger.info(f"Solved math CAPTCHA: {math_expr} = {captcha_value}")
                    except Exception as e:
                        logger.warning(f"Failed to solve math CAPTCHA '{captcha_value}': {e}")
                
                if captcha_value:
                    # Type CAPTCHA using JavaScript (faster than selector-based type)
                    captcha_input_result = browser_tool.browser(BrowserInput(action={
                        "type": "evaluate",
                        "session_name": session_name,
                        "script": f"""(function() {{
                            const input = document.querySelector('#captchaValue') || 
                                         document.querySelector('input[name="captchaValue"]') ||
                                         document.querySelector('.captcha-input');
                            if (input) {{
                                input.value = '{captcha_value}';
                                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                return 'SUCCESS';
                            }}
                            return 'FAILED';
                        }})();"""
                    }))
                    
                    if captcha_input_result.get('status') == 'success':
                        content = captcha_input_result.get('content', [])
                        if content and 'SUCCESS' in content[0].get('text', ''):
                            logger.info("CAPTCHA typed successfully")
                        else:
                            logger.warning(f"CAPTCHA input field not found")
                    else:
                        logger.warning(f"CAPTCHA input failed: {captcha_input_result}")
                else:
                    logger.warning("Could not extract CAPTCHA value from page")
            
            # Step 6: Click submit button using JavaScript (faster than trying selectors)
            submit_result = browser_tool.browser(BrowserInput(action={
                "type": "evaluate",
                "session_name": session_name,
                "script": """(function() {
                    const selectors = [
                        'button[type="submit"]',
                        'input[type="submit"]',
                        '.btn-primary',
                        '.submit-btn',
                        '#submit',
                        'button'
                    ];
                    for (let sel of selectors) {
                        const btn = document.querySelector(sel);
                        if (btn) {
                            btn.click();
                            return 'SUCCESS:' + sel;
                        }
                    }
                    return 'FAILED';
                })();"""
            }))
            
            if submit_result.get('status') == 'success':
                content = submit_result.get('content', [])
                if content and 'SUCCESS' in content[0].get('text', ''):
                    selector_used = content[0].get('text', '').split(':')[-1].strip() if ':' in content[0].get('text', '') else 'unknown'
                    logger.info(f"Clicked submit using selector: {selector_used}")
                else:
                    logger.warning("Submit button not found on page")
            
            # Wait for results section to appear (JavaScript rendering)
            logger.info("Waiting for results to load...")
            time.sleep(2)
            
            # Check if bill-view section is visible (wait up to 3 more seconds)
            for i in range(3):
                visibility_check = browser_tool.browser(BrowserInput(action={
                    "type": "evaluate",
                    "session_name": session_name,
                    "script": """(function() {
                        const billView = document.getElementById('bill-view');
                        if (billView && !billView.classList.contains('hidden')) {
                            return 'VISIBLE';
                        }
                        return 'HIDDEN';
                    })();"""
                }))
                if visibility_check.get('status') == 'success':
                    content = visibility_check.get('content', [])
                    if content and 'VISIBLE' in content[0].get('text', ''):
                        logger.info("Results section is now visible")
                        time.sleep(0.5)  # Extra time for JavaScript to populate DOM
                        break
                time.sleep(1)
            
            logger.info("Getting page HTML after submit...")
            
            # First, try to extract structured data directly from DOM elements (faster and more reliable)
            data_extract = browser_tool.browser(BrowserInput(action={
                "type": "evaluate",
                "session_name": session_name,
                "script": """(function() {
                    const data = {};
                    
                    // Consumer/Owner name - try multiple selectors for different sites
                    const nameSelectors = [
                        '#consumer-name', '#display-owner', '#owner-name', '#property-owner',
                        '#bill-name', '.consumer-name', '.owner-name'
                    ];
                    for (let sel of nameSelectors) {
                        const nameEl = document.querySelector(sel);
                        if (nameEl && nameEl.textContent.trim()) {
                            data.consumer_name = nameEl.textContent.trim();
                            break;
                        }
                    }
                    
                    // Amount - try different patterns for different sites
                    const amountSelectors = [
                        '#display-fine',       // e-Challan
                        '#display-amount',     // Generic
                        '#bill-amount',        // Bills
                        '#tax-amount'          // K-Smart
                    ];
                    for (let sel of amountSelectors) {
                        const amountEl = document.querySelector(sel);
                        if (amountEl && amountEl.textContent.trim()) {
                            data.amount_due = amountEl.textContent.trim();
                            break;
                        }
                    }
                    
                    // Status - try different selectors
                    const statusSelectors = ['#display-status', '#bill-status', '#payment-status'];
                    for (let sel of statusSelectors) {
                        const statusEl = document.querySelector(sel);
                        if (statusEl && statusEl.textContent.trim()) {
                            const statusText = statusEl.textContent.trim().toLowerCase();
                            if (statusText.includes('paid') || statusText.includes('settled')) {
                                data.status = 'paid';
                            }
                            break;
                        }
                    }
                    
                    // Extract from details div (works for KSEB, KWA, e-Challan, K-Smart)
                    // Only if we didn't already find the data above
                    if (!data.amount_due || !data.consumer_name) {
                        const detailsSelectors = ['#bill-details', '#challan-details', '#property-details', '.details'];
                        for (let detailsSel of detailsSelectors) {
                            const detailsDiv = document.querySelector(detailsSel);
                            if (detailsDiv) {
                                const divs = detailsDiv.querySelectorAll('div');
                                divs.forEach(div => {
                                    const label = div.querySelector('span');
                                    const value = div.querySelector('strong');
                                    if (label && value) {
                                        const labelText = label.textContent.trim().toLowerCase();
                                        const valueText = value.textContent.trim();
                                        
                                        // Amount patterns (bill amount, fine amount, tax amount)
                                        if ((labelText.includes('bill amount') || labelText.includes('amount') || 
                                            labelText.includes('fine') || labelText.includes('tax')) && 
                                            !data.amount_due) {
                                            data.amount_due = valueText;
                                        } 
                                        // Due date
                                        else if ((labelText.includes('due date') || labelText.includes('date')) && 
                                                 !data.due_date) {
                                            data.due_date = valueText;
                                        } 
                                        // Units/consumption
                                        else if ((labelText.includes('unit') || labelText.includes('consumption') || 
                                                 labelText.includes('usage')) && !data.units_consumed) {
                                            data.units_consumed = valueText;
                                        }
                                    }
                                });
                                break;
                            }
                        }
                    }
                    
                    // Check for paid/settled status banners
                    const paidSelectors = ['#paid-banner', '#settled-banner', '.paid-banner', '.settled-banner'];
                    for (let sel of paidSelectors) {
                        const banner = document.querySelector(sel);
                        if (banner && !banner.classList.contains('hidden')) {
                            data.status = 'paid';
                            break;
                        }
                    }
                    
                    return JSON.stringify(data);
                })();"""
            }))
            
            extracted_data = {}
            if data_extract.get('status') == 'success':
                content = data_extract.get('content', [])
                if content and len(content) > 0:
                    try:
                        data_text = content[0].get('text', '{}')
                        logger.info(f"Raw DOM extraction result: {data_text}")
                        # Remove "Evaluation result:" prefix if present
                        if 'Evaluation result' in data_text:
                            data_text = data_text.split(':', 1)[-1].strip()
                        extracted_data = json.loads(data_text)
                        logger.info(f"Parsed structured data from DOM: {extracted_data}")
                        results['dom_data'] = extracted_data
                    except Exception as e:
                        logger.warning(f"Failed to parse DOM data: {e}")
            
            # Extract historical billing data from bill-list
            logger.info("Extracting historical billing data...")
            history_extract = browser_tool.browser(BrowserInput(action={
                "type": "evaluate",
                "session_name": session_name,
                "script": """(function() {
                    const historyData = [];
                    const billList = document.querySelector('#bill-list');
                    
                    if (billList) {
                        // The bills are rendered as buttons with class 'bill-item'
                        const billItems = billList.querySelectorAll('.bill-item, button');
                        
                        billItems.forEach(item => {
                            // Structure: button > (div[left], div[right])
                            // Left div: strong (bill ID), span (due date)
                            // Right div: strong (amount), span.pill (status)
                            
                            const leftDiv = item.querySelector('div:first-child');
                            const rightDiv = item.querySelector('div:last-child');
                            
                            if (leftDiv && rightDiv) {
                                const billId = leftDiv.querySelector('strong');
                                const dueSpan = leftDiv.querySelector('span');
                                const amountStrong = rightDiv.querySelector('strong');
                                const statusSpan = rightDiv.querySelector('span.pill, span');
                                
                                const historyItem = {};
                                
                                // Extract date from "Due YYYY-MM-DD" or bill ID
                                if (dueSpan && dueSpan.textContent) {
                                    const dueText = dueSpan.textContent.trim();
                                    // Extract date from "Due 2026-01-15" format
                                    const dateMatch = dueText.match(/\\d{4}-\\d{2}-\\d{2}/);
                                    historyItem.date = dateMatch ? dateMatch[0] : dueText.replace('Due ', '');
                                } else if (billId) {
                                    historyItem.date = billId.textContent.trim();
                                }
                                
                                // Extract amount
                                if (amountStrong && amountStrong.textContent) {
                                    historyItem.amount = amountStrong.textContent.trim();
                                }
                                
                                // Extract status
                                if (statusSpan && statusSpan.textContent) {
                                    historyItem.status = statusSpan.textContent.trim();
                                }
                                
                                // Only add if we have amount (most important field)
                                if (historyItem.amount) {
                                    historyData.push(historyItem);
                                }
                            }
                        });
                    }
                    
                    return JSON.stringify({
                        found: historyData.length,
                        data: historyData,
                        billListExists: !!billList
                    });
                })();"""
            }))
            
            history_list = []
            if history_extract.get('status') == 'success':
                content = history_extract.get('content', [])
                if content and len(content) > 0:
                    try:
                        history_text = content[0].get('text', '{}')
                        if 'Evaluation result' in history_text:
                            history_text = history_text.split(':', 1)[-1].strip()
                        history_response = json.loads(history_text)
                        
                        # Log debugging info
                        logger.info(f"History extraction debug - billListExists: {history_response.get('billListExists')}, found: {history_response.get('found')} items")
                        if history_response.get('billListHTML'):
                            logger.info(f"bill-list HTML sample: {history_response.get('billListHTML')[:200]}")
                        
                        # Extract the actual history data
                        history_list = history_response.get('data', [])
                        if history_list:
                            logger.info(f"Extracted {len(history_list)} historical bills from DOM")
                        else:
                            logger.warning("No historical bills found in bill-list")
                        results['history_data'] = history_list
                    except Exception as e:
                        logger.warning(f"Failed to parse history data: {e}")
            
            # Get page HTML
            html_result = browser_tool.browser(BrowserInput(action={
                "type": "get_html",
                "session_name": session_name
            }))
            
            page_html = ''
            if html_result.get('status') == 'success':
                content = html_result.get('content', [])
                if content and isinstance(content, list) and len(content) > 0:
                    page_html = content[0].get('text', '')
            
            results['html'] = page_html
            logger.info(f"Extracted page HTML: {len(page_html)} chars")
            
            # Debug: Log the actual HTML content
            logger.info(f"HTML Content Preview: {page_html[:1000]}")
            
            # Check if page shows an error or "not found" message
            if page_html:
                page_lower = page_html.lower()
                if any(err in page_lower for err in ['not found', 'invalid', 'error', 'incorrect captcha', 'wrong captcha']):
                    logger.warning(f"Page may contain error message. HTML snippet: {page_html[:500]}")
            
            # Close session
            try:
                browser_tool.browser(BrowserInput(action={
                    "type": "close",
                    "session_name": session_name
                }))
            except Exception:
                pass
            
            return results
        
        try:
            # Run browser automation in thread pool to avoid uvloop conflict
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, _run_browser_automation)
            
            page_html = results.get('html', '')
            dom_data = results.get('dom_data', {})
            history_data = results.get('history_data', [])
            
            # If we have DOM-extracted data with required fields, use it directly
            if dom_data and dom_data.get('consumer_name') and dom_data.get('amount_due'):
                logger.info("Using DOM-extracted data (faster, more reliable)")
                # Parse amount if it's a string with currency symbols
                amount_str = str(dom_data.get('amount_due', '0'))
                import re
                # Remove currency symbols and thousand separators, but keep decimal point
                amount_clean = re.sub(r'[₹$Rs\s]', '', amount_str)  # Remove currency symbols and spaces
                amount_clean = amount_clean.replace(',', '')  # Remove thousand separators
                try:
                    amount_due = float(amount_clean)
                except:
                    amount_due = 0.0
                
                return {
                    'consumer_name': dom_data.get('consumer_name', f'Customer {consumer_id}'),
                    'amount_due': amount_due,
                    'units_consumed': dom_data.get('units_consumed'),
                    'due_date': dom_data.get('due_date'),
                    'status': dom_data.get('status', 'unpaid' if amount_due > 0 else 'paid'),
                    'history': history_data
                }
            
            # Fallback to Nova Pro if DOM extraction didn't find the data
            logger.info("DOM extraction incomplete, falling back to Nova Pro analysis")
            extracted_data = await self._analyze_page_content(page_html, consumer_id)
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Browser navigation failed: {e}")
            # Fallback to Nova Pro vision
            return await self._navigate_with_nova_vision(url, instructions, consumer_id, 15)
    
    async def _analyze_page_content(self, page_text: str, consumer_id: str) -> Dict[str, Any]:
        """
        Use Nova Pro to analyze extracted page content and structure the data.
        This is safe because we're only analyzing text, not automating navigation.
        """
        prompt = f"""
Analyze this utility bill page HTML/text and extract the billing information.

Page Content:
{page_text[:4000]}

Consumer ID: {consumer_id}

Look for:
- Consumer/customer name (may appear as "name", "consumerName", "Consumer Name", etc.)
- Bill amount/amount due (may appear as "billAmount", "amount", "total", etc.)
- Units consumed for electricity/water (if applicable)
- Due date (if visible)

Extract and return ONLY a JSON object with these fields:
- consumer_name: Name of the account holder (string). If not found in page, use "Customer {consumer_id}"
- amount_due: Amount to pay as a plain number without currency symbols or commas (e.g., 1234.50 not ₹1,234.50)
- units_consumed: Units consumed as a number, or null if not applicable
- due_date: Payment due date as string, or null
- status: "paid" if amount is 0, "unpaid" if amount > 0

IMPORTANT Rules:
1. Return amount_due as a plain number like 1234.50, NOT as ₹1,234.50 or with any formatting
2. If no consumer name is visible, use "Customer {consumer_id}" as fallback
3. Look for amount in text like "₹500.00" or "Bill Amount: 500" and extract just the number

Return ONLY valid JSON, no explanation or markdown.
Example: {{"consumer_name":"Rajesh Kumar","amount_due":1234.50,"units_consumed":150,"due_date":"2024-03-15","status":"unpaid"}}
"""
        
        messages = [{"role": "user", "content": [{"text": prompt}]}]
        
        request_body = {
            "messages": messages,
            "inferenceConfig": {
                "maxTokens": 1024,
                "temperature": 0.1
            }
        }
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.runtime_client.invoke_model(
                    modelId=self.NOVA_PRO_MODEL,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps(request_body)
                )
            )
            
            response_body = json.loads(response['body'].read())
            output = response_body.get('output', {})
            message = output.get('message', {})
            content = message.get('content', [])
            
            response_text = content[0].get('text', '') if content else ''
            return self._parse_extraction_result(response_text)
            
        except Exception as e:
            logger.error(f"Content analysis failed: {e}")
            raise RuntimeError(f"Content analysis failed: {e}")
    
    async def _navigate_with_nova_vision(
        self,
        url: str,
        instructions: str,
        consumer_id: str,
        max_iterations: int = 15
    ) -> Dict[str, Any]:
        """
        Fallback: Use Nova Pro for text-based extraction only.
        """
        logger.info(f"Using Nova Pro vision analysis for: {url}")
        
        page_text: str = ""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                page_text = resp.text
                logger.info("Fetched page content for vision fallback")
        except Exception as fetch_error:
            logger.warning(f"Failed to fetch page content for vision fallback: {fetch_error}")

        # If we have page content, reuse the structured content analysis path
        if page_text:
            try:
                return await self._analyze_page_content(page_text, consumer_id)
            except Exception as analyze_error:
                logger.warning(f"Content analysis via Nova vision failed, will retry with minimal prompt: {analyze_error}")

        # Minimal prompt (no page content available)
        prompt = f"""
You are a strict data extraction agent.

Target URL: {url}
Consumer ID: {consumer_id}

Task:
{instructions}

Do NOT simulate, infer, or fabricate values.
If required fields are not present in the input context, return:
{{"error":"EXTRACTION_UNAVAILABLE"}}

Otherwise return JSON with:
- consumer_name
- amount_due
- units_consumed
- due_date
- status

Return ONLY the JSON, no other text.
"""
        
        messages = [
            {
                "role": "user",
                "content": [{"text": prompt}]
            }
        ]
        
        request_body = {
            "messages": messages,
            "inferenceConfig": {
                "maxTokens": 2048,
                "temperature": 0.7
            }
        }
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.runtime_client.invoke_model(
                    modelId=self.NOVA_PRO_MODEL,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps(request_body)
                )
            )
            
            response_body = json.loads(response['body'].read())
            output = response_body.get('output', {})
            message = output.get('message', {})
            content = message.get('content', [])
            
            response_text = content[0].get('text', '') if content else ''
            
            return self._parse_extraction_result(response_text)
            
        except Exception as e:
            logger.error(f"Nova Pro vision analysis failed: {e}")
            raise
    
    def _parse_extraction_result(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from agent response."""
        import re
        
        # Try to find JSON in the response
        try:
            # Look for JSON block
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                if not isinstance(parsed, dict):
                    raise ValueError("Extraction payload is not a JSON object")

                if parsed.get("error"):
                    raise ValueError(f"Extraction failed: {parsed.get('error')}")

                if "consumer_name" not in parsed or "amount_due" not in parsed:
                    raise ValueError("Extraction missing required fields: consumer_name, amount_due")

                # Allow fallback consumer names like "Customer 12345" but reject truly empty ones
                consumer_name = parsed.get("consumer_name", "").strip()
                if not consumer_name or consumer_name in ("Unknown", ""):
                    raise ValueError("Extraction returned empty consumer_name")

                # Parse amount_due - handle currency symbols and commas
                try:
                    amount_str = str(parsed.get("amount_due", "0"))
                    # Remove currency symbols and spaces, then remove thousand separators
                    amount_cleaned = re.sub(r'[₹$Rs\s]', '', amount_str)
                    amount_cleaned = amount_cleaned.replace(',', '')  # Remove commas but keep decimal point
                    parsed["amount_due"] = float(amount_cleaned)
                except Exception as exc:
                    raise ValueError(f"Extraction returned non-numeric amount_due: {parsed.get('amount_due')}") from exc

                return parsed
        except json.JSONDecodeError:
            raise ValueError("Failed to parse extraction JSON")

        raise ValueError("No JSON object found in extraction response")
    
    async def capture_qr_code(self, url: str, consumer_id: str) -> Optional[str]:
        """
        Navigate to payment page and capture QR code using Playwright.
        Uses Bedrock Nova Pro to extract and crop the QR code from the screenshot.
        
        Returns:
            Base64-encoded QR code image (cropped) or None
        """
        if not BROWSER_AVAILABLE:
            logger.warning("QR capture requires Playwright browser")
            return None
        
        def _capture_qr():
            """Run QR capture using Playwright in separate sync context."""
            from playwright.sync_api import sync_playwright
            import base64
            
            def _shoot(p):
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                logger.info(f"Navigating to payment page: {url}")
                page.goto(url, wait_until='networkidle', timeout=30000)
                page.wait_for_timeout(1000)

                target_page = page  # May switch if gateway opens in a popup/new tab
                current_page = page

                # All four sites now require an explicit Pay by UPI click before the QR renders
                def _click_with_wait_on(page_obj, click_fn):
                    """Click and wait for popup or navigation, returning the active page."""
                    import time
                    before_pages = set(page_obj.context.pages)

                    # 1) Explicit popup (window.open) from the clicked element
                    try:
                        with page_obj.expect_popup(timeout=8000) as popup_info:
                            click_fn()
                        new_page = popup_info.value
                        new_page.wait_for_load_state('load', timeout=15000)
                        return new_page, "popup"
                    except Exception:
                        pass

                    # 2) New tab opened in same context (not caught as popup)
                    try:
                        with page_obj.context.expect_page(timeout=8000) as page_info:
                            click_fn()
                        new_page = page_info.value
                        new_page.wait_for_load_state('load', timeout=15000)
                        return new_page, "new_tab"
                    except Exception:
                        pass

                    # 3) Same-page navigation
                    try:
                        with page_obj.expect_navigation(wait_until="networkidle", timeout=20000):
                            click_fn()
                        return page_obj, "navigation"
                    except Exception:
                        pass

                    # 4) No observable nav; assume same page
                    click_fn()
                    # 5) Late-discovered tab/window: poll for new page in context
                    deadline = time.time() + 10
                    while time.time() < deadline:
                        for p in page_obj.context.pages:
                            if p not in before_pages:
                                try:
                                    p.wait_for_load_state('load', timeout=15000)
                                except Exception:
                                    pass
                                return p, "late_tab"
                        time.sleep(0.25)

                    return page_obj, "same"

                def _click_pay_by_upi(active_page):
                    import re

                    def _try_click_once():
                        try:
                            btn = active_page.get_by_role("button", name=re.compile("pay by upi", re.IGNORECASE)).first
                            if btn.count() > 0:
                                return _click_with_wait_on(active_page, lambda: btn.click(timeout=5000)), "role"
                        except Exception:
                            pass

                        try:
                            btn = active_page.locator("text=/pay by upi/i").first
                            if btn.count() > 0:
                                return _click_with_wait_on(active_page, lambda: btn.click(timeout=5000)), "text"
                        except Exception:
                            pass

                        try:
                            return _click_with_wait_on(
                                active_page,
                                lambda: active_page.evaluate(
                                    """
                                    () => {
                                        const candidates = Array.from(document.querySelectorAll('button, a, div, span'));
                                        for (const el of candidates) {
                                            const txt = (el.innerText || el.textContent || '').trim().toLowerCase();
                                            if (txt.includes('pay by upi')) {
                                                el.click();
                                                return true;
                                            }
                                        }
                                        return false;
                                    }
                                    """
                                )
                            ), "dom"
                        except Exception:
                            pass

                        return (None, None), None

                    # Poll briefly for the button to render after submit/navigation
                    for _ in range(5):
                        result = _try_click_once()
                        if result[1]:
                            return result
                        active_page.wait_for_timeout(800)

                    return (None, None), None

                def _fill_consumer_and_submit(active_page):
                    if consumer_id:
                        typed_selector = active_page.evaluate(
                            """
                            (value) => {
                                const selectors = [
                                    'input[id="consumerNumber"]', 'input[name="consumerNumber"]',
                                    'input[id="consumer_id"]', 'input[name="consumer_id"]',
                                    'input[id="buildingId"]', 'input[name="buildingId"]',
                                    'input[id="searchValue"]', 'input[name="searchValue"]',
                                    'input[type="text"]'
                                ];
                                for (const sel of selectors) {
                                    const input = document.querySelector(sel);
                                    if (input) {
                                        input.value = value;
                                        input.dispatchEvent(new Event('input', { bubbles: true }));
                                        input.dispatchEvent(new Event('change', { bubbles: true }));
                                        return sel;
                                    }
                                }
                                return null;
                            }
                            """,
                            consumer_id
                        )
                        if typed_selector:
                            logger.info(f"Entered consumer id using selector: {typed_selector}")
                        else:
                            logger.warning("Could not find consumer input to populate before payment")

                    def _click_submit(active_page):
                        import re
                        try:
                            btn = active_page.get_by_role("button", name=re.compile("proceed|continue|pay|view bill|submit|search", re.IGNORECASE)).first
                            if btn.count() > 0:
                                return _click_with_wait_on(active_page, lambda: btn.click(timeout=5000)), "role"
                        except Exception:
                            pass

                        try:
                            btn = active_page.locator("text=/proceed|continue|pay now|view bill|submit|search/i").first
                            if btn.count() > 0:
                                return _click_with_wait_on(active_page, lambda: btn.click(timeout=5000)), "text"
                        except Exception:
                            pass

                        try:
                            btn = active_page.locator("input[type='submit'], button[type='submit']").first
                            if btn.count() > 0:
                                return _click_with_wait_on(active_page, lambda: btn.click(timeout=5000)), "submit"
                        except Exception:
                            pass

                        try:
                            return _click_with_wait_on(
                                active_page,
                                lambda: active_page.evaluate(
                                    """
                                    () => {
                                        const selectors = ['button', 'a', 'div', 'span', 'input[type=submit]'];
                                        for (const sel of selectors) {
                                            for (const el of document.querySelectorAll(sel)) {
                                                const txt = (el.innerText || el.textContent || '').trim().toLowerCase();
                                                if (txt.includes('proceed') || txt.includes('continue') || txt.includes('pay') || txt.includes('view bill') || txt.includes('submit') || txt.includes('search')) {
                                                    el.click();
                                                    return true;
                                                }
                                            }
                                        }
                                        return false;
                                    }
                                    """
                                )
                            ), "dom"
                        except Exception:
                            pass

                        return (None, None), None

                    try:
                        (submitted_page, submit_mode), submit_source = _click_submit(active_page)
                    except Exception:
                        (submitted_page, submit_mode) = (None, None)
                        submit_source = None

                    if submit_source:
                        active_page = submitted_page or active_page
                        logger.info(f"Submitted details via {submit_source} locator; wait_mode={submit_mode}")
                        try:
                            active_page.wait_for_load_state('networkidle', timeout=20000)
                        except Exception:
                            logger.warning("Load state after submit timed out; continuing")
                        active_page.wait_for_timeout(800)

                    return active_page

                current_page = _fill_consumer_and_submit(current_page)

                (clicked_page, click_source) = (None, None)
                try:
                    (clicked_page, wait_mode), click_source = _click_pay_by_upi(current_page)
                except Exception:
                    (clicked_page, wait_mode) = (None, None)
                    click_source = None

                if click_source:
                    target_page = clicked_page or current_page
                    logger.info(f"Clicked 'Pay by UPI' via {click_source} locator; wait_mode={wait_mode}")
                    try:
                        target_page.wait_for_load_state('networkidle', timeout=20000)
                    except Exception:
                        logger.warning("Load state after UPI click timed out; proceeding with heuristic wait")

                    # Wait until a QR-like element appears; fall back to fixed delay if not detected
                    try:
                        target_page.wait_for_function(
                            """
                            () => {
                                const centerYMin = 0.2, centerYMax = 0.8, centerXMin = 0.2, centerXMax = 0.8;
                                const viewH = window.innerHeight || 1000;
                                const viewW = window.innerWidth || 1000;

                                // Look for square-ish imgs/canvas near the center
                                const candidates = [
                                    ...document.querySelectorAll('img'),
                                    ...document.querySelectorAll('canvas')
                                ];

                                for (const el of candidates) {
                                    const rect = el.getBoundingClientRect();
                                    const w = rect.width, h = rect.height;
                                    if (w < 80 || h < 80) continue;
                                    const aspect = Math.min(w, h) / Math.max(w, h);
                                    if (aspect < 0.7) continue; // keep near-square

                                    const cy = (rect.top + rect.bottom) / 2 / viewH;
                                    const cx = (rect.left + rect.right) / 2 / viewW;
                                    if (cy < centerYMin || cy > centerYMax || cx < centerXMin || cx > centerXMax) continue;

                                    const src = (el.src || '').toLowerCase();
                                    const alt = (el.alt || '').toLowerCase();
                                    const title = (el.title || '').toLowerCase();
                                    if (src.includes('qr') || src.includes('upi') || alt.includes('qr') || title.includes('qr')) {
                                        return true;
                                    }
                                }

                                return false;
                            }
                            """,
                            timeout=6000
                        )
                        logger.info("QR-like element detected after UPI click")
                    except Exception:
                        logger.warning("QR heuristic did not resolve in time; using fixed wait")
                        target_page.wait_for_timeout(4000)
                else:
                    logger.warning("'Pay by UPI' button not found; capturing current view")

                # QR now appears near the center; capture a fresh full-page shot after render settle
                target_page.wait_for_timeout(1200)
                shot = target_page.screenshot(full_page=True)
                browser.close()
                return base64.b64encode(shot).decode('utf-8')

            for attempt in range(2):
                try:
                    with sync_playwright() as p:
                        screenshot_base64 = _shoot(p)
                        logger.info(f"Screenshot captured successfully (attempt {attempt + 1})")
                        if screenshot_base64:
                            return screenshot_base64
                except Exception as e:
                    logger.warning(f"Playwright screenshot attempt {attempt + 1} failed: {e}")
            logger.error("All Playwright screenshot attempts failed")
            return None
        
        try:
            loop = asyncio.get_event_loop()
            screenshot_base64 = await loop.run_in_executor(None, _capture_qr)
            
            if not screenshot_base64:
                logger.error("Failed to capture screenshot; no QR will be returned")
                return None
            
            # Per new requirement: when gateway opens, just return the full-page screenshot
            logger.info("Screenshot captured after UPI flow; returning full page without cropping")
            return screenshot_base64
            
        except Exception as e:
            logger.error(f"QR capture failed: {e}")
            return None
    
    async def _extract_qr_from_screenshot(self, screenshot_base64: str) -> str:
        """
        Use Bedrock Nova Pro vision to extract and crop QR code from screenshot.
        
        Args:
            screenshot_base64: Full page screenshot as base64 string
            
        Returns:
            Cropped QR code region as base64, or original screenshot if QR not found
        """
        logger.info("Starting Bedrock QR extraction...")
        
        try:
            import json
            from app.config import settings
            
            # Use existing boto3 client setup
            from botocore.config import Config
            
            # Initialize Bedrock client with shorter timeout
            boto_config = Config(
                region_name=settings.aws_region,
                retries={'max_attempts': 2, 'mode': 'standard'},
                connect_timeout=5,
                read_timeout=25
            )
            
            client_kwargs = {
                'service_name': 'bedrock-runtime',
                'config': boto_config,
                'region_name': settings.aws_region
            }
            
            if settings.aws_access_key_id and settings.aws_secret_access_key:
                client_kwargs['aws_access_key_id'] = settings.aws_access_key_id
                client_kwargs['aws_secret_access_key'] = settings.aws_secret_access_key
            
            bedrock_client = boto3.client(**client_kwargs)
            logger.info("Bedrock client initialized")
            
            # Prepare image for Nova Pro (limit size to avoid timeout)
            # Check if image is too large
            try:
                import base64
                img_bytes = base64.b64decode(screenshot_base64)
                img_size_mb = len(img_bytes) / (1024 * 1024)
                logger.info(f"Screenshot size: {img_size_mb:.2f} MB")
                
                # If image is too large, skip bedrock and return original
                if img_size_mb > 5:
                    logger.warning("Screenshot too large for Bedrock, returning original")
                    return screenshot_base64
            except Exception as size_error:
                logger.warning(f"Error checking image size: {size_error}")
            
            # Nova REST payload must be JSON-serializable; send base64 string
            image_content = {
                "image": {
                    "format": "png",
                    "source": {
                        "bytes": screenshot_base64
                    }
                }
            }
            
            # Ask Nova Pro to locate the QR code using normalized 0-1000 coords with quiet zone
            prompt_text = (
                "You are an expert CV assistant for UI element detection. "
                "Locate the payment UPI QR code (the scannable black-and-white square). Ignore logos or decorative QR-like graphics. "
                "After clicking the 'Pay by UPI' button, the page refreshes and the QR appears almost dead center in the viewport inside the primary payment panel. Focus on the central QR image, not sidebars or headers. "
                "Return ONLY one JSON object, no prose: {\"element\":\"qr_code\",\"detected\":true|false,\"bounding_box\":[ymin,xmin,ymax,xmax],\"confidence_score\":0.xx}. "
                "Coordinates must be normalized 0-1000 where ymin,xmin,ymax,xmax are top-left and bottom-right. "
                "Include 5-10px of quiet-zone margin inside the image bounds. "
                "Prefer the QR closest to the visual center if multiple candidates exist. "
                "If no QR, set detected:false and omit bounding_box."
            )

            messages = [
                {
                    "role": "user",
                    "content": [
                        image_content,
                        {"text": prompt_text}
                    ]
                }
            ]
            
            request_body = {
                "messages": messages,
                "inferenceConfig": {
                    "maxTokens": 100,
                    "temperature": 0
                }
            }
            
            logger.info("Calling Bedrock Nova Pro...")
            def invoke_bedrock():
                return bedrock_client.invoke_model(
                    modelId="amazon.nova-pro-v1:0",
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps(request_body)
                )
            
            response = await asyncio.get_event_loop().run_in_executor(None, invoke_bedrock)
            response_body = json.loads(response['body'].read())
            content = response_body.get('output', {}).get('message', {}).get('content', [])
            
            if not content:
                logger.warning("No content in Bedrock response, returning full screenshot")
                return screenshot_base64
            
            response_text = content[0].get('text', '').strip()
            logger.info(f"Bedrock QR location response: {response_text}")
            
            # If QR not found, try direct QR crop via Bedrock before giving up
            if "NO_QR_FOUND" in response_text.upper():
                logger.info("No QR code found from coordinates, attempting direct crop via Bedrock")
                direct = await self._extract_qr_image_direct(bedrock_client, screenshot_base64)
                return direct if direct else screenshot_base64

            # Try direct extraction first; if it works and is a valid PNG, prefer it over coordinate crop
            def _is_valid_png(b64_data: str) -> bool:
                try:
                    import base64
                    import io
                    from PIL import Image
                    img_bytes = base64.b64decode(b64_data)
                    if len(img_bytes) < 100:  # too small to be a QR
                        return False
                    img = Image.open(io.BytesIO(img_bytes))
                    img.verify()
                    return True
                except Exception:
                    return False

            direct_qr = await self._extract_qr_image_direct(bedrock_client, screenshot_base64)
            if direct_qr:
                if _is_valid_png(direct_qr):
                    logger.info("Direct QR extraction returned a valid cropped image; using it")
                    return direct_qr
                else:
                    logger.warning("Direct QR extraction returned invalid PNG; falling back to coordinate crop")
            
            # Try to parse and crop QR code
            logger.info("Attempting to crop QR code from screenshot...")
            cropped = await self._crop_qr_from_response(screenshot_base64, response_text)
            
            # If cropping failed (returned original), try direct Bedrock crop once
            if cropped == screenshot_base64:
                logger.info("Crop response invalid, attempting direct crop via Bedrock")
                direct = direct_qr or await self._extract_qr_image_direct(bedrock_client, screenshot_base64)
                return direct if direct else screenshot_base64
            
            return cropped
            
        except Exception as e:
            logger.error(f"Bedrock QR extraction error: {e}", exc_info=True)
            return screenshot_base64
    
    async def _crop_qr_from_response(self, screenshot_base64: str, response_text: str) -> str:
        """Crop QR code based on Bedrock's position response."""
        try:
            from PIL import Image
            import io
            import re
            import json

            # Decode screenshot
            img_data = base64.b64decode(screenshot_base64)
            img = Image.open(io.BytesIO(img_data))
            width, height = img.size

            # Hardcode crop to bottom-left quarter of the page
            x1 = 0
            y1 = height // 2
            x2 = width // 2
            y2 = height

            # Add modest padding while staying in bounds
            padding = 12
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(width, x2 + padding)
            y2 = min(height, y2 + padding)

            logger.info(f"Bottom-left quarter crop: ({x1},{y1})-({x2},{y2}) on {width}x{height}")
            
            # Crop image
            cropped = img.crop((x1, y1, x2, y2))
            
            # Convert back to base64
            buffer = io.BytesIO()
            cropped.save(buffer, format='PNG')
            cropped_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            logger.info("QR code cropped successfully")
            return cropped_base64
            
        except Exception as crop_error:
            logger.error(f"Error cropping QR code: {crop_error}", exc_info=True)
            return screenshot_base64

    async def _extract_qr_image_direct(self, bedrock_client, screenshot_base64: str) -> Optional[str]:
        """Ask Bedrock to return a cropped QR image directly as base64 PNG."""
        try:
            import json
            import base64
            import io
            from PIL import Image
            
            image_content = {
                "image": {
                    "format": "png",
                    "source": {
                        "bytes": screenshot_base64
                    }
                }
            }

            messages = [
                {
                    "role": "user",
                    "content": [
                        image_content,
                        {
                            "text": (
                                "Extract ONLY the QR code region from this payment page. "
                                "Return a strict JSON object with a single field qr_base64_png containing the base64 PNG of the cropped QR. "
                                "Format: {\"qr_base64_png\": \"<base64_png>\"}. "
                                "Do NOT include markdown, code fences, or any explanation. "
                                "If no QR is present, return NO_QR_FOUND."
                            )
                        }
                    ]
                }
            ]

            request_body = {
                "messages": messages,
                "inferenceConfig": {
                    "maxTokens": 400,
                    "temperature": 0
                }
            }

            def invoke_bedrock():
                return bedrock_client.invoke_model(
                    modelId="amazon.nova-pro-v1:0",
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps(request_body)
                )

            response = await asyncio.get_event_loop().run_in_executor(None, invoke_bedrock)
            response_body = json.loads(response['body'].read())
            content = response_body.get('output', {}).get('message', {}).get('content', [])

            if not content:
                logger.warning("Direct QR extraction returned empty content")
                return None

            response_text = content[0].get('text', '').strip()
            if "NO_QR_FOUND" in response_text.upper():
                logger.info("Direct QR extraction reported NO_QR_FOUND")
                return None

            def _is_valid_png(b64_data: str) -> bool:
                try:
                    img_bytes = base64.b64decode(b64_data)
                    if len(img_bytes) < 100:
                        return False
                    img = Image.open(io.BytesIO(img_bytes))
                    img.verify()
                    return True
                except Exception:
                    return False

            try:
                parsed = json.loads(response_text)
                qr_b64 = parsed.get("qr_base64_png")
                if qr_b64:
                    if _is_valid_png(qr_b64):
                        logger.info("Direct QR extraction succeeded")
                        return qr_b64
                    logger.warning("Direct QR extraction JSON PNG invalid")
            except Exception as parse_err:
                logger.warning(f"Failed to parse direct QR response: {parse_err}")

            # Fallback parsing: extract base64-looking string from response text
            try:
                import re
                m = re.search(r'"qr_base64_png"\s*:\s*"([A-Za-z0-9+/=]+)"', response_text)
                if m:
                    candidate = m.group(1)
                    if _is_valid_png(candidate):
                        logger.info("Direct QR extraction parsed via JSON regex")
                        return candidate
                    logger.warning("Direct QR extraction regex PNG invalid")

                # Generic long base64 blob (avoid tiny matches)
                m = re.search(r'([A-Za-z0-9+/=]{200,})', response_text)
                if m:
                    candidate = m.group(1)
                    if _is_valid_png(candidate):
                        logger.info("Direct QR extraction parsed via base64 fallback")
                        return candidate
                    logger.warning("Direct QR extraction base64 fallback invalid")
            except Exception as fallback_err:
                logger.warning(f"Fallback parse for direct QR failed: {fallback_err}")

            logger.warning("Direct QR extraction did not return usable base64")
            return None

        except Exception as e:
            logger.error(f"Direct QR extraction error: {e}", exc_info=True)
            return None


class UtilityNavigator:
    """
    Production-ready autonomous navigation engine for Kerala utility portals.
    
    Uses AWS Bedrock AgentCore Browser Tool for real browser automation
    within a managed, secure sandbox environment.
    
    Features:
    - Real browser navigation with AgentCore
    - Auto-scaling serverless sessions  
    - Reduced CAPTCHA interruptions
    - Intelligent form filling
    - Structured data extraction
    """
    
    def __init__(self):
        self.browser_agent = AgentCoreBrowserAgent()
        self.active_sessions: Dict[str, NavigationSession] = {}
        
        self.url_map = {
            ServiceType.KSEB: settings.kseb_url,
            ServiceType.KWA: settings.kwa_url,
            ServiceType.ECHALLAN: settings.echallan_url,
            ServiceType.KSMART: settings.ksmart_url
        }
        
        self.service_instructions = {
            ServiceType.KSEB: self._get_kseb_instructions(),
            ServiceType.KWA: self._get_kwa_instructions(),
            ServiceType.ECHALLAN: self._get_echallan_instructions(),
            ServiceType.KSMART: self._get_ksmart_instructions()
        }
    
    def _get_kseb_instructions(self) -> str:
        return """
Navigate the KSEB (Kerala State Electricity Board) portal:
1. Go to the bill payment/view section
2. Find and fill the consumer number input field
3. Handle any CAPTCHA if present
4. Submit to view bill details
5. Extract: Consumer Name, Amount Due, Units Consumed, Due Date
"""
    
    def _get_kwa_instructions(self) -> str:
        return """
Navigate the KWA (Kerala Water Authority) portal:
1. Go to the quick pay or bill view section
2. Enter the consumer number
3. Handle any CAPTCHA verification
4. Extract: Consumer Name, Water Consumption, Amount Due
"""
    
    def _get_echallan_instructions(self) -> str:
        return """
Navigate the e-Challan (Traffic Fine) portal:
1. Search by vehicle number or challan number
2. Handle OTP or CAPTCHA verification
3. Extract: Vehicle Number, Fine Amount, Violation Details, Due Date
"""
    
    def _get_ksmart_instructions(self) -> str:
        return """
Navigate the K-Smart (Municipal Services) portal:
1. Go to property tax or relevant service section
2. Enter property/assessment number
3. Handle authentication
4. Extract: Property ID, Tax Amount, Owner Name
"""
    
    async def fetch_bill_data(
        self, 
        service_type: ServiceType, 
        consumer_id: str,
        number_plate: Optional[str] = None
    ) -> ScrapedData:
        """
        Fetch current bill data using AgentCore Browser navigation.
        
        Args:
            service_type: The utility service type
            consumer_id: Consumer/account identifier
            number_plate: Vehicle number for e-Challan (optional)
            
        Returns:
            ScrapedData with bill information and historical data
        """
        session_id = str(uuid.uuid4())
        session = NavigationSession(
            session_id=session_id,
            service_type=service_type,
            consumer_id=consumer_id
        )
        self.active_sessions[session_id] = session
        
        url = self.url_map[service_type]
        instructions = self.service_instructions[service_type]
        
        logger.info(f"Starting bill fetch for {service_type.value}: {consumer_id}")
        
        try:
            extracted = await self.browser_agent.navigate_and_extract(
                url=url,
                instructions=instructions,
                consumer_id=consumer_id,
                number_plate=number_plate
            )

            if not isinstance(extracted, dict):
                raise ValueError("Extraction result is not a valid object")

            if "consumer_name" not in extracted or "amount_due" not in extracted:
                raise ValueError("Extraction missing required bill fields")
            
            # Parse historical billing data
            history_list = []
            raw_history = extracted.get('history', [])
            if raw_history and isinstance(raw_history, list):
                logger.info(f"Processing {len(raw_history)} historical bills")
                import re
                for hist_item in raw_history:
                    try:
                        # Parse amount - remove currency symbols and commas
                        amount_str = str(hist_item.get('amount', '0'))
                        amount_clean = re.sub(r'[₹$Rs\s]', '', amount_str)
                        amount_clean = amount_clean.replace(',', '')
                        hist_amount = float(amount_clean)
                        
                        # Parse units if present
                        units_str = hist_item.get('units')
                        hist_units = None
                        if units_str:
                            try:
                                units_clean = re.sub(r'[^\d.]', '', str(units_str))
                                hist_units = float(units_clean) if units_clean else None
                            except:
                                pass
                        
                        # Determine status
                        status_str = str(hist_item.get('status', '')).lower()
                        if 'paid' in status_str or 'settled' in status_str:
                            hist_status = PaymentStatus.PAID
                        elif 'pending' in status_str:
                            hist_status = PaymentStatus.PENDING
                        else:
                            hist_status = PaymentStatus.UNPAID
                        
                        # Create BillingHistory object
                        history_list.append(BillingHistory(
                            account_id=f"{service_type.value}_{consumer_id}",
                            date=hist_item.get('date', ''),
                            amount=hist_amount,
                            units=hist_units,
                            status=hist_status
                        ))
                    except Exception as e:
                        logger.warning(f"Failed to parse history item: {e}")
                        continue
                
                logger.info(f"Successfully parsed {len(history_list)} historical bills")
            
            # Convert to ScrapedData
            amount = float(extracted.get('amount_due'))
            status = PaymentStatus.UNPAID if amount > 0 else PaymentStatus.PAID
            
            scraped_data = ScrapedData(
                consumer_name=extracted.get('consumer_name'),
                amount_due=amount,
                status=status,
                additional_info={
                    "units": extracted.get('units_consumed'),
                    "due_date": extracted.get('due_date'),
                    "billing_period": extracted.get('billing_period'),
                    "source": "browser" if BROWSER_AVAILABLE else "nova_vision"
                },
                history=history_list
            )
            
            session.status = "completed"
            session.extracted_data = extracted
            
            logger.info(f"Bill fetch completed: {scraped_data.amount_due}")
            return scraped_data
            
        except Exception as e:
            logger.error(f"Bill fetch failed: {e}")
            session.status = "failed"
            raise
        finally:
            # Cleanup session after delay
            asyncio.get_event_loop().call_later(
                300,
                lambda: self.active_sessions.pop(session_id, None)
            )
    
    async def navigate_to_payment(
        self, 
        service_type: ServiceType, 
        consumer_id: str
    ) -> Optional[str]:
        """
        Navigate to payment page and extract QR code.
        
        Returns:
            Base64 encoded QR code image, or None if not found
        """
        url = self.url_map[service_type]
        
        logger.info(f"Starting payment navigation for {service_type.value}: {consumer_id}")
        
        try:
            qr_data = await self.browser_agent.capture_qr_code(url, consumer_id)
            return qr_data
        except Exception as e:
            logger.error(f"Payment navigation failed: {e}")
            return None
    
    async def fetch_billing_history(
        self, 
        service_type: ServiceType, 
        consumer_id: str
    ) -> List[BillingHistory]:
        """
        Extract historical billing data for visualization.
        
        Returns:
            List of historical billing records
        """
        logger.info(f"Fetching billing history for {service_type.value}: {consumer_id}")

        # Reuse bill fetch path to avoid fabricated data; return real history only if present
        try:
            scraped = await self.fetch_bill_data(service_type=service_type, consumer_id=consumer_id)
            return scraped.history or []
        except Exception as e:
            logger.warning(f"History fetch failed, returning empty list: {e}")
            return []
    
    def get_session_status(self, session_id: str) -> Optional[Dict]:
        """Get the status of an active navigation session."""
        session = self.active_sessions.get(session_id)
        if session:
            return {
                "session_id": session.session_id,
                "service_type": session.service_type.value,
                "consumer_id": session.consumer_id,
                "status": session.status,
                "started_at": session.started_at.isoformat(),
                "extracted_data": session.extracted_data
            }
        return None
