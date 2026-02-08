"""
DART API Client for fetching corporate and financial data.
"""

import requests
import time
import json
import xmltodict
import zipfile
import io
import logging
from pathlib import Path
from typing import Dict, List, Optional
from functools import wraps

import config

# Setup logging
logging.basicConfig(
    level=config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def cache_response(ttl_seconds: int):
    """Decorator to cache API responses."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
            cache_file = config.CACHE_DIR / f"{cache_key}.json"

            # Check cache validity
            if cache_file.exists():
                cache_age = time.time() - cache_file.stat().st_mtime
                if cache_age < ttl_seconds:
                    logger.info(f"Using cached data for {func.__name__}")
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            return json.load(f)
                    except Exception as e:
                        logger.warning(f"Failed to read cache: {e}")

            # Fetch new data
            result = func(*args, **kwargs)

            # Save to cache if result is valid
            if result is not None:
                try:
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    logger.info(f"Cached data for {func.__name__}")
                except Exception as e:
                    logger.warning(f"Failed to write cache: {e}")

            return result
        return wrapper
    return decorator


class DartClient:
    """Client for interacting with DART Open API."""

    def __init__(self, api_key: str):
        """
        Initialize DART API client.

        Args:
            api_key: DART API authentication key
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'DART-Analysis/1.0'})

    def _make_request(self, url: str, params: Optional[Dict] = None, retry_count: int = None) -> requests.Response:
        """
        Make HTTP request with retry logic.

        Args:
            url: Request URL
            params: Query parameters
            retry_count: Number of retries (default from config)

        Returns:
            Response object

        Raises:
            requests.RequestException: If all retries fail
        """
        if retry_count is None:
            retry_count = config.API_RETRY_COUNT

        if params is None:
            params = {}

        for attempt in range(retry_count):
            try:
                logger.debug(f"Making request to {url} (attempt {attempt + 1}/{retry_count})")
                response = self.session.get(url, params=params, timeout=config.API_TIMEOUT)

                if response.status_code == 200:
                    return response

                elif response.status_code == 429:  # Rate limit
                    wait_time = 60
                    logger.warning(f"Rate limit hit, waiting {wait_time}s")
                    time.sleep(wait_time)
                    continue

                else:
                    logger.warning(f"API error {response.status_code}: {response.text[:200]}")

            except requests.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1}")
                time.sleep(config.RETRY_DELAY)

            except Exception as e:
                logger.error(f"Request error on attempt {attempt + 1}: {e}")

            if attempt < retry_count - 1:
                time.sleep(config.RETRY_DELAY * (attempt + 1))  # Exponential backoff

        raise requests.RequestException(f"Failed after {retry_count} attempts")

    @cache_response(ttl=config.COMPANY_CACHE_TTL)
    def get_corp_codes(self) -> List[Dict]:
        """
        Fetch complete list of company codes from DART.

        Returns:
            List of company dictionaries with corp_code, corp_name, stock_code, modify_date
        """
        logger.info("Fetching company codes from DART")

        try:
            # Download ZIP file
            url = config.ENDPOINTS['corp_code']
            params = {'crtfc_key': self.api_key}
            response = self._make_request(url, params)

            # Extract ZIP content
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                xml_content = zip_file.read('CORPCODE.xml')

            # Parse XML to dict
            data = xmltodict.parse(xml_content)
            corp_list = data['result']['list']

            logger.info(f"Retrieved {len(corp_list)} companies")
            return corp_list

        except Exception as e:
            logger.error(f"Failed to fetch company codes: {e}")
            return []

    @cache_response(ttl=config.FINANCIAL_CACHE_TTL)
    def get_company_info(self, corp_code: str) -> Optional[Dict]:
        """
        Fetch detailed company information.

        Args:
            corp_code: 8-digit company code

        Returns:
            Dictionary with company details including KSIC code
        """
        logger.debug(f"Fetching company info for {corp_code}")

        try:
            url = config.ENDPOINTS['company_info']
            params = {
                'crtfc_key': self.api_key,
                'corp_code': corp_code
            }

            response = self._make_request(url, params)
            data = response.json()

            if data.get('status') == '000':  # Success
                return data
            else:
                logger.warning(f"API returned status {data.get('status')}: {data.get('message')}")
                return None

        except Exception as e:
            logger.error(f"Failed to fetch company info for {corp_code}: {e}")
            return None

    @cache_response(ttl=config.FINANCIAL_CACHE_TTL)
    def get_financial_statement(self, corp_code: str, year: int, reprt_code: str = None) -> Optional[Dict]:
        """
        Fetch financial statement for a company.

        Args:
            corp_code: 8-digit company code
            year: Business year (e.g., 2023)
            reprt_code: Report code (default: annual report)

        Returns:
            Dictionary with financial data
        """
        if reprt_code is None:
            reprt_code = config.FINANCIAL_REPORT_CODES['annual']

        logger.debug(f"Fetching financial statement for {corp_code}, year {year}")

        try:
            url = config.ENDPOINTS['financial_statement']
            params = {
                'crtfc_key': self.api_key,
                'corp_code': corp_code,
                'bsns_year': str(year),
                'reprt_code': reprt_code,
                'fs_div': 'CFS'  # Consolidated financial statement
            }

            response = self._make_request(url, params)
            data = response.json()

            if data.get('status') == '000':  # Success
                return data
            else:
                # Try with OFS (separate financial statement) if CFS fails
                params['fs_div'] = 'OFS'
                response = self._make_request(url, params)
                data = response.json()

                if data.get('status') == '000':
                    return data
                else:
                    logger.warning(f"No financial data for {corp_code} {year}: {data.get('message')}")
                    return None

        except Exception as e:
            logger.error(f"Failed to fetch financial statement for {corp_code} {year}: {e}")
            return None

    def clear_cache(self):
        """Clear all cached responses."""
        logger.info("Clearing cache")
        cache_files = list(config.CACHE_DIR.glob("*.json"))
        for cache_file in cache_files:
            try:
                cache_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete {cache_file}: {e}")
        logger.info(f"Cleared {len(cache_files)} cache files")
