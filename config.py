"""
Configuration module for DART analysis system.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
CACHE_DIR = DATA_DIR / "cache"

# Create directories if not exist
for dir_path in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, CACHE_DIR]:
    dir_path.mkdir(exist_ok=True, parents=True)

# DART API Configuration
DART_API_KEY = os.getenv("DART_API")
if not DART_API_KEY:
    raise ValueError("DART_API key not found in .env file")

DART_BASE_URL = "https://opendart.fss.or.kr/api"

# API endpoints
ENDPOINTS = {
    'corp_code': f"{DART_BASE_URL}/corpCode.xml",
    'company_info': f"{DART_BASE_URL}/company.json",
    'financial_statement': f"{DART_BASE_URL}/fnlttSinglAcntAll.json",
}

# Classification settings
COSMETIC_KSIC_CODES = [
    'C20423',  # 화장품 제조업
    'C20412',  # 기타 기초 유기화학물질 제조업
    'C20411',  # 석유화학계 기초화합물 제조업
    'C20421',  # 비누 및 세제 제조업
    'C20422',  # 화장용 유지류 제조업
    'C20429',  # 기타 화장품 제조업
]

CLASSIFICATION_KEYWORDS = {
    'high_priority': ['화장품원료', '화장품 원료', 'cosmetic ingredient', '기능성원료', '기능성 원료'],
    'medium_priority': ['화장품', '색소', '향료', '피부', '스킨', '뷰티', '케미칼'],
    'low_priority': ['화학', '제조', 'chemical', '원료']
}

# Classification scoring
KSIC_MATCH_SCORE = 10
HIGH_PRIORITY_KEYWORD_SCORE = 3
MEDIUM_PRIORITY_KEYWORD_SCORE = 2
LOW_PRIORITY_KEYWORD_SCORE = 1
CLASSIFICATION_THRESHOLD = 5

# Data collection settings
COLLECTION_YEARS = [2021, 2022, 2023, 2024, 2025]
FINANCIAL_REPORT_CODES = {
    'annual': '11011',     # 사업보고서
    'half': '11012',       # 반기보고서
    'q1': '11013',         # 1분기보고서
    'q3': '11014',         # 3분기보고서
}

# Financial metrics to collect
FINANCIAL_METRICS = [
    '매출액',
    '영업이익',
    '당기순이익',
    '자산총계',
    '부채총계',
    '자본총계',
]

# Cache settings
COMPANY_CACHE_TTL = 86400  # 24 hours
FINANCIAL_CACHE_TTL = 604800  # 7 days

# API rate limiting
API_RATE_LIMIT = 10  # requests per second
API_RETRY_COUNT = 3
API_TIMEOUT = 30  # seconds
RETRY_DELAY = 5  # seconds

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = PROJECT_ROOT / "dart_analysis.log"

# Streamlit configuration
PAGE_TITLE = "화장품 원료 회사 분석"
PAGE_ICON = "🧴"
LAYOUT = "wide"
