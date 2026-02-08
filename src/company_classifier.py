"""
Company classifier for identifying cosmetic raw material suppliers.
"""

import logging
import pandas as pd
from typing import Tuple, List, Dict
from tqdm import tqdm

import config
from src.dart_client import DartClient

logger = logging.getLogger(__name__)


class CompanyClassifier:
    """Classifier for identifying cosmetic raw material companies."""

    def __init__(self, dart_client: DartClient):
        """
        Initialize classifier.

        Args:
            dart_client: DART API client instance
        """
        self.dart_client = dart_client
        self.cosmetic_ksic_codes = config.COSMETIC_KSIC_CODES
        self.keywords = config.CLASSIFICATION_KEYWORDS
        self.threshold = config.CLASSIFICATION_THRESHOLD

    def _check_keywords(self, text: str) -> int:
        """
        Check text for classification keywords and return score.

        Args:
            text: Text to check

        Returns:
            Score based on keyword matches
        """
        if not text:
            return 0

        text_lower = text.lower()
        score = 0

        # Check high priority keywords
        for keyword in self.keywords['high_priority']:
            if keyword.lower() in text_lower:
                score += config.HIGH_PRIORITY_KEYWORD_SCORE

        # Check medium priority keywords
        for keyword in self.keywords['medium_priority']:
            if keyword.lower() in text_lower:
                score += config.MEDIUM_PRIORITY_KEYWORD_SCORE

        # Check low priority keywords
        for keyword in self.keywords['low_priority']:
            if keyword.lower() in text_lower:
                score += config.LOW_PRIORITY_KEYWORD_SCORE

        return score

    def classify_company(self, corp_info: Dict) -> Tuple[bool, int]:
        """
        Classify a single company based on KSIC code and keywords.

        Args:
            corp_info: Company information dictionary

        Returns:
            Tuple of (is_cosmetic_company, classification_score)
        """
        score = 0

        # Get detailed company info from DART
        corp_code = corp_info.get('corp_code')
        detailed_info = self.dart_client.get_company_info(corp_code)

        if detailed_info:
            # Check KSIC code (highest weight)
            ksic_code = detailed_info.get('induty_code', '')
            if ksic_code in self.cosmetic_ksic_codes:
                score += config.KSIC_MATCH_SCORE
                logger.debug(f"{corp_info.get('corp_name')} matched KSIC: {ksic_code}")

            # Check company name
            corp_name = corp_info.get('corp_name', '')
            score += self._check_keywords(corp_name)

            # Check business summary
            business_summary = detailed_info.get('est_dt', '')  # Company establishment purpose
            score += self._check_keywords(business_summary)

        else:
            # If detailed info not available, use basic info
            corp_name = corp_info.get('corp_name', '')
            score += self._check_keywords(corp_name)

        is_cosmetic = score >= self.threshold
        return is_cosmetic, score

    def classify_all(self, corp_list: List[Dict] = None, progress_bar: bool = True) -> pd.DataFrame:
        """
        Classify all companies and return results.

        Args:
            corp_list: List of company dictionaries (default: fetch from API)
            progress_bar: Show progress bar

        Returns:
            DataFrame with classified companies
        """
        logger.info("Starting company classification")

        # Fetch company list if not provided
        if corp_list is None:
            corp_list = self.dart_client.get_corp_codes()

        results = []
        iterator = tqdm(corp_list, desc="Classifying companies") if progress_bar else corp_list

        for corp_info in iterator:
            try:
                is_cosmetic, score = self.classify_company(corp_info)

                if is_cosmetic:
                    results.append({
                        'corp_code': corp_info.get('corp_code'),
                        'corp_name': corp_info.get('corp_name'),
                        'stock_code': corp_info.get('stock_code'),
                        'classification_score': score,
                        'is_cosmetic_raw_material': True
                    })
                    logger.info(f"Classified: {corp_info.get('corp_name')} (score: {score})")

            except Exception as e:
                logger.error(f"Error classifying {corp_info.get('corp_name')}: {e}")
                continue

        df_results = pd.DataFrame(results)
        logger.info(f"Classification complete: {len(df_results)} cosmetic companies found")

        # Save results
        output_file = config.PROCESSED_DATA_DIR / "cosmetic_companies.csv"
        df_results.to_csv(output_file, index=False, encoding='utf-8-sig')
        logger.info(f"Results saved to {output_file}")

        return df_results

    def get_classified_companies(self) -> pd.DataFrame:
        """
        Load previously classified companies from file.

        Returns:
            DataFrame with classified companies
        """
        output_file = config.PROCESSED_DATA_DIR / "cosmetic_companies.csv"

        if output_file.exists():
            logger.info(f"Loading classified companies from {output_file}")
            return pd.read_csv(output_file, encoding='utf-8-sig')
        else:
            logger.warning("No classified companies file found. Run classify_all() first.")
            return pd.DataFrame()
