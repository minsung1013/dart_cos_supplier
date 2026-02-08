"""
Main Streamlit dashboard for Korean cosmetic raw material company analysis.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import config
from src.data_processor import DataProcessor

# Page configuration
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout=config.LAYOUT
)

# Load data using cache
@st.cache_data(ttl=3600)
def load_dashboard_data():
    """Load all dashboard data with caching."""
    processor = DataProcessor()
    return processor.prepare_dashboard_data()

# Main app
def main():
    st.title(f"{config.PAGE_ICON} {config.PAGE_TITLE}")
    st.markdown("### DART API 기반 화장품 원료 회사 실적 분석 대시보드")
    st.markdown("---")

    # Load data
    try:
        data = load_dashboard_data()
        companies_df = data['companies']
        metrics_df = data['metrics']
        industry_avg_df = data['industry_avg']

        if companies_df.empty:
            st.warning("아직 분류된 회사 데이터가 없습니다. '데이터 관리' 페이지에서 데이터를 수집해주세요.")
            return

        # Sidebar filters
        st.sidebar.title("필터")
        st.sidebar.markdown("---")

        # Year filter
        if not metrics_df.empty:
            available_years = sorted(metrics_df['year'].unique())
            year_range = st.sidebar.slider(
                "연도 범위",
                min_value=int(min(available_years)),
                max_value=int(max(available_years)),
                value=(int(min(available_years)), int(max(available_years)))
            )

            # Company filter
            available_companies = sorted(metrics_df['corp_name'].unique())
            selected_companies = st.sidebar.multiselect(
                "회사 선택",
                options=available_companies,
                default=available_companies[:min(5, len(available_companies))]
            )

            # Filter data
            df_filtered = metrics_df[
                (metrics_df['year'] >= year_range[0]) &
                (metrics_df['year'] <= year_range[1]) &
                (metrics_df['corp_name'].isin(selected_companies))
            ]
        else:
            df_filtered = pd.DataFrame()
            st.warning("재무 데이터가 없습니다. '데이터 관리' 페이지에서 데이터를 수집해주세요.")
            return

        # Summary metrics
        st.subheader("주요 지표 요약")

        if not df_filtered.empty:
            latest_year = df_filtered['year'].max()
            df_latest = df_filtered[df_filtered['year'] == latest_year]

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                total_companies = len(selected_companies)
                st.metric("선택된 회사 수", f"{total_companies}개")

            with col2:
                if '매출액' in df_latest.columns:
                    avg_revenue = df_latest['매출액'].mean() / 100000000  # Convert to 억원
                    st.metric("평균 매출액 (최근년도)", f"{avg_revenue:,.0f}억원")
                else:
                    st.metric("평균 매출액", "N/A")

            with col3:
                if '영업이익률' in df_latest.columns:
                    avg_op_margin = df_latest['영업이익률'].mean()
                    st.metric("평균 영업이익률", f"{avg_op_margin:.1f}%")
                else:
                    st.metric("평균 영업이익률", "N/A")

            with col4:
                if '매출액_성장률' in df_latest.columns:
                    avg_growth = df_latest['매출액_성장률'].mean()
                    st.metric("평균 매출 성장률 (YoY)", f"{avg_growth:.1f}%")
                else:
                    st.metric("평균 매출 성장률", "N/A")

        st.markdown("---")

        # Revenue trend chart
        st.subheader("매출액 추이")

        if not df_filtered.empty and '매출액' in df_filtered.columns:
            # Convert to 억원
            df_chart = df_filtered.copy()
            df_chart['매출액_억원'] = df_chart['매출액'] / 100000000

            fig_revenue = px.line(
                df_chart,
                x='year',
                y='매출액_억원',
                color='corp_name',
                markers=True,
                labels={'매출액_억원': '매출액 (억원)', 'year': '연도', 'corp_name': '회사명'},
                title='연도별 매출액 추이'
            )
            fig_revenue.update_layout(hovermode='x unified')
            st.plotly_chart(fig_revenue, use_container_width=True)
        else:
            st.info("매출액 데이터가 없습니다.")

        # Operating profit trend
        st.subheader("영업이익 추이")

        if not df_filtered.empty and '영업이익' in df_filtered.columns:
            df_chart = df_filtered.copy()
            df_chart['영업이익_억원'] = df_chart['영업이익'] / 100000000

            fig_profit = px.line(
                df_chart,
                x='year',
                y='영업이익_억원',
                color='corp_name',
                markers=True,
                labels={'영업이익_억원': '영업이익 (억원)', 'year': '연도', 'corp_name': '회사명'},
                title='연도별 영업이익 추이'
            )
            fig_profit.update_layout(hovermode='x unified')
            st.plotly_chart(fig_profit, use_container_width=True)
        else:
            st.info("영업이익 데이터가 없습니다.")

        # Profitability analysis
        st.subheader("수익성 분석")

        col1, col2 = st.columns(2)

        with col1:
            if not df_filtered.empty and '영업이익률' in df_filtered.columns:
                fig_op_margin = px.box(
                    df_filtered,
                    x='year',
                    y='영업이익률',
                    labels={'영업이익률': '영업이익률 (%)', 'year': '연도'},
                    title='연도별 영업이익률 분포'
                )
                st.plotly_chart(fig_op_margin, use_container_width=True)
            else:
                st.info("영업이익률 데이터가 없습니다.")

        with col2:
            if not df_filtered.empty and '순이익률' in df_filtered.columns:
                fig_net_margin = px.box(
                    df_filtered,
                    x='year',
                    y='순이익률',
                    labels={'순이익률': '순이익률 (%)', 'year': '연도'},
                    title='연도별 순이익률 분포'
                )
                st.plotly_chart(fig_net_margin, use_container_width=True)
            else:
                st.info("순이익률 데이터가 없습니다.")

        # Company comparison table
        st.subheader("회사별 비교")

        if not df_latest.empty:
            display_cols = ['corp_name', '매출액', '영업이익', '당기순이익', '영업이익률', '순이익률']
            display_cols = [col for col in display_cols if col in df_latest.columns]

            df_display = df_latest[display_cols].copy()

            # Format numbers
            if '매출액' in df_display.columns:
                df_display['매출액'] = (df_display['매출액'] / 100000000).round(0)
            if '영업이익' in df_display.columns:
                df_display['영업이익'] = (df_display['영업이익'] / 100000000).round(0)
            if '당기순이익' in df_display.columns:
                df_display['당기순이익'] = (df_display['당기순이익'] / 100000000).round(0)

            # Rename columns
            df_display = df_display.rename(columns={
                'corp_name': '회사명',
                '매출액': '매출액 (억원)',
                '영업이익': '영업이익 (억원)',
                '당기순이익': '당기순이익 (억원)',
                '영업이익률': '영업이익률 (%)',
                '순이익률': '순이익률 (%)'
            })

            st.dataframe(df_display, use_container_width=True)
        else:
            st.info("비교할 데이터가 없습니다.")

    except Exception as e:
        st.error(f"데이터 로드 중 오류가 발생했습니다: {e}")
        st.info("'데이터 관리' 페이지에서 데이터를 수집해주세요.")

    # Footer
    st.markdown("---")
    st.markdown("**데이터 출처:** 전자공시시스템(DART) Open API")
    st.markdown("**분석 기간:** 2021-2025년")

if __name__ == "__main__":
    main()
