"""
Financial data collector for classified companies.
"""

import logging
import pandas as pd
import time
from typing import List, Dict
from tqdm import tqdm

import config
from src.dart_client import DartClient

logger = logging.getLogger(__name__)


class FinancialCollector:
    """Collector for financial statement data."""

    def __init__(self, dart_client: DartClient):
        """
        Initialize collector.

        Args:
            dart_client: DART API client instance
        """
        self.dart_client = dart_client
        self.collection_years = config.COLLECTION_YEARS
        self.financial_metrics = config.FINANCIAL_METRICS

    def _parse_financial_data(self, data: Dict, corp_code: str, corp_name: str, year: int) -> List[Dict]:
        """
        Parse financial statement data.

        Args:
            data: Raw financial data from API
            corp_code: Company code
            corp_name: Company name
            year: Business year

        Returns:
            List of parsed financial records
        """
        records = []

        if not data or 'list' not in data:
            return records

        for item in data['list']:
            account_nm = item.get('account_nm', '')

            # Check if this is a metric we're tracking
            if account_nm in self.financial_metrics:
                # Parse value
                thstrm_amount = item.get('thstrm_amount', '0')

                # Clean value (remove commas, convert to float)
                try:
                    value = float(str(thstrm_amount).replace(',', ''))
                except (ValueError, AttributeError):
                    value = 0.0

                records.append({
                    'corp_code': corp_code,
                    'corp_name': corp_name,
                    'year': year,
                    'metric_name': account_nm,
                    'value': value,
                    'unit': item.get('currency', 'KRW')
                })

        return records

    def collect_company_financials(self, corp_code: str, corp_name: str) -> List[Dict]:
        """
        Collect financial data for a single company across all years.

        Args:
            corp_code: Company code
            corp_name: Company name

        Returns:
            List of financial records
        """
        all_records = []

        for year in self.collection_years:
            try:
                # Try annual report first
                data = self.dart_client.get_financial_statement(
                    corp_code=corp_code,
                    year=year,
                    reprt_code=config.FINANCIAL_REPORT_CODES['annual']
                )

                if data:
                    records = self._parse_financial_data(data, corp_code, corp_name, year)
                    all_records.extend(records)
                    logger.debug(f"Collected {year} data for {corp_name}")
                else:
                    logger.warning(f"No financial data for {corp_name} in {year}")

                # Rate limiting
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error collecting {year} data for {corp_name}: {e}")
                continue

        return all_records

    def collect_all(self, companies_df: pd.DataFrame = None, progress_bar: bool = True) -> pd.DataFrame:
        """
        Collect financial data for all classified companies.

        Args:
            companies_df: DataFrame with classified companies (default: load from file)
            progress_bar: Show progress bar

        Returns:
            DataFrame with financial data
        """
        logger.info("Starting financial data collection")

        # Load companies if not provided
        if companies_df is None:
            companies_file = config.PROCESSED_DATA_DIR / "cosmetic_companies.csv"
            if companies_file.exists():
                companies_df = pd.read_csv(companies_file, encoding='utf-8-sig')
            else:
                logger.error("No companies file found. Run classification first.")
                return pd.DataFrame()

        all_records = []
        iterator = tqdm(companies_df.iterrows(), total=len(companies_df), desc="Collecting financials") if progress_bar else companies_df.iterrows()

        for _, row in iterator:
            corp_code = row['corp_code']
            corp_name = row['corp_name']

            try:
                records = self.collect_company_financials(corp_code, corp_name)
                all_records.extend(records)

                if records:
                    logger.info(f"Collected {len(records)} records for {corp_name}")

            except Exception as e:
                logger.error(f"Error processing {corp_name}: {e}")
                continue

        # Create DataFrame
        df_financials = pd.DataFrame(all_records)

        if not df_financials.empty:
            # Save to file
            output_file = config.PROCESSED_DATA_DIR / "financial_data.csv"
            df_financials.to_csv(output_file, index=False, encoding='utf-8-sig')
            logger.info(f"Saved {len(df_financials)} financial records to {output_file}")
        else:
            logger.warning("No financial data collected")

        return df_financials

    def get_financial_data(self) -> pd.DataFrame:
        """
        Load previously collected financial data from file.

        Returns:
            DataFrame with financial data
        """
        output_file = config.PROCESSED_DATA_DIR / "financial_data.csv"

        if output_file.exists():
            logger.info(f"Loading financial data from {output_file}")
            return pd.read_csv(output_file, encoding='utf-8-sig')
        else:
            logger.warning("No financial data file found. Run collect_all() first.")
            return pd.DataFrame()

    def get_company_summary(self, corp_name: str) -> pd.DataFrame:
        """
        Get financial summary for a specific company.

        Args:
            corp_name: Company name

        Returns:
            DataFrame with company's financial data
        """
        df_financial = self.get_financial_data()

        if df_financial.empty:
            return pd.DataFrame()

        return df_financial[df_financial['corp_name'] == corp_name]
