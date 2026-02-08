"""
Data processor for financial analysis and metrics calculation.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict

import config

logger = logging.getLogger(__name__)


class DataProcessor:
    """Processor for financial data analysis."""

    def __init__(self):
        """Initialize data processor."""
        pass

    def load_data(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load companies and financial data from files.

        Returns:
            Tuple of (companies_df, financial_df)
        """
        companies_file = config.PROCESSED_DATA_DIR / "cosmetic_companies.csv"
        financial_file = config.PROCESSED_DATA_DIR / "financial_data.csv"

        companies_df = pd.DataFrame()
        financial_df = pd.DataFrame()

        if companies_file.exists():
            companies_df = pd.read_csv(companies_file, encoding='utf-8-sig')
            logger.info(f"Loaded {len(companies_df)} companies")
        else:
            logger.warning("Companies file not found")

        if financial_file.exists():
            financial_df = pd.read_csv(financial_file, encoding='utf-8-sig')
            logger.info(f"Loaded {len(financial_df)} financial records")
        else:
            logger.warning("Financial data file not found")

        return companies_df, financial_df

    def pivot_financial_data(self, financial_df: pd.DataFrame) -> pd.DataFrame:
        """
        Pivot financial data from long to wide format.

        Args:
            financial_df: Financial data in long format

        Returns:
            DataFrame in wide format (company x year x metric)
        """
        if financial_df.empty:
            return pd.DataFrame()

        # Pivot to wide format
        df_pivot = financial_df.pivot_table(
            index=['corp_code', 'corp_name', 'year'],
            columns='metric_name',
            values='value',
            aggfunc='first'
        ).reset_index()

        return df_pivot

    def calculate_metrics(self, df_pivot: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate financial ratios and metrics.

        Args:
            df_pivot: Pivoted financial data

        Returns:
            DataFrame with calculated metrics
        """
        if df_pivot.empty:
            return pd.DataFrame()

        df = df_pivot.copy()

        # Calculate profitability ratios
        if '매출액' in df.columns and '영업이익' in df.columns:
            df['영업이익률'] = (df['영업이익'] / df['매출액'] * 100).round(2)
            df['영업이익률'] = df['영업이익률'].replace([np.inf, -np.inf], np.nan)

        if '매출액' in df.columns and '당기순이익' in df.columns:
            df['순이익률'] = (df['당기순이익'] / df['매출액'] * 100).round(2)
            df['순이익률'] = df['순이익률'].replace([np.inf, -np.inf], np.nan)

        # Calculate financial ratios
        if '자산총계' in df.columns and '부채총계' in df.columns:
            df['부채비율'] = (df['부채총계'] / (df['자산총계'] - df['부채총계']) * 100).round(2)
            df['부채비율'] = df['부채비율'].replace([np.inf, -np.inf], np.nan)

        # Calculate YoY growth rates for each company
        df = df.sort_values(['corp_code', 'year'])

        for metric in ['매출액', '영업이익', '당기순이익']:
            if metric in df.columns:
                df[f'{metric}_성장률'] = df.groupby('corp_code')[metric].pct_change() * 100
                df[f'{metric}_성장률'] = df[f'{metric}_성장률'].round(2)

        logger.info("Calculated financial metrics")
        return df

    def calculate_industry_average(self, df_metrics: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate industry averages by year.

        Args:
            df_metrics: DataFrame with company metrics

        Returns:
            DataFrame with industry averages
        """
        if df_metrics.empty:
            return pd.DataFrame()

        # Group by year and calculate averages
        numeric_cols = df_metrics.select_dtypes(include=[np.number]).columns
        df_avg = df_metrics.groupby('year')[numeric_cols].mean().reset_index()

        df_avg['corp_name'] = '산업 평균'
        df_avg['corp_code'] = 'INDUSTRY_AVG'

        logger.info("Calculated industry averages")
        return df_avg

    def get_top_performers(self, df_metrics: pd.DataFrame, metric: str, year: int, n: int = 10) -> pd.DataFrame:
        """
        Get top performing companies by metric.

        Args:
            df_metrics: DataFrame with metrics
            metric: Metric name to rank by
            year: Year to analyze
            n: Number of top companies

        Returns:
            DataFrame with top performers
        """
        if df_metrics.empty or metric not in df_metrics.columns:
            return pd.DataFrame()

        df_year = df_metrics[df_metrics['year'] == year].copy()
        df_top = df_year.nlargest(n, metric)[['corp_name', 'year', metric]]

        return df_top

    def get_summary_statistics(self, df_metrics: pd.DataFrame) -> Dict:
        """
        Calculate summary statistics across all data.

        Args:
            df_metrics: DataFrame with metrics

        Returns:
            Dictionary with summary stats
        """
        if df_metrics.empty:
            return {}

        stats = {
            'total_companies': df_metrics['corp_code'].nunique(),
            'years_covered': sorted(df_metrics['year'].unique().tolist()),
            'total_records': len(df_metrics),
        }

        # Calculate latest year stats
        latest_year = df_metrics['year'].max()
        df_latest = df_metrics[df_metrics['year'] == latest_year]

        if '매출액' in df_latest.columns:
            stats['avg_revenue'] = df_latest['매출액'].mean()
            stats['total_revenue'] = df_latest['매출액'].sum()

        if '영업이익률' in df_latest.columns:
            stats['avg_operating_margin'] = df_latest['영업이익률'].mean()

        if '순이익률' in df_latest.columns:
            stats['avg_net_margin'] = df_latest['순이익률'].mean()

        return stats

    def prepare_dashboard_data(self) -> Dict[str, pd.DataFrame]:
        """
        Prepare all data needed for dashboard.

        Returns:
            Dictionary of DataFrames for dashboard
        """
        logger.info("Preparing dashboard data")

        companies_df, financial_df = self.load_data()

        if financial_df.empty:
            logger.warning("No financial data available")
            return {
                'companies': companies_df,
                'financial': pd.DataFrame(),
                'metrics': pd.DataFrame(),
                'industry_avg': pd.DataFrame(),
            }

        # Process data
        df_pivot = self.pivot_financial_data(financial_df)
        df_metrics = self.calculate_metrics(df_pivot)
        df_industry_avg = self.calculate_industry_average(df_metrics)

        logger.info("Dashboard data prepared")

        return {
            'companies': companies_df,
            'financial': financial_df,
            'metrics': df_metrics,
            'industry_avg': df_industry_avg,
        }

    def export_to_excel(self, output_path: str = None):
        """
        Export all data to Excel file.

        Args:
            output_path: Output file path (default: processed_data_dir)
        """
        if output_path is None:
            output_path = config.PROCESSED_DATA_DIR / "cosmetic_analysis.xlsx"

        data = self.prepare_dashboard_data()

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            data['companies'].to_excel(writer, sheet_name='Companies', index=False)
            data['financial'].to_excel(writer, sheet_name='Financial_Raw', index=False)
            data['metrics'].to_excel(writer, sheet_name='Metrics', index=False)
            data['industry_avg'].to_excel(writer, sheet_name='Industry_Average', index=False)

        logger.info(f"Data exported to {output_path}")
