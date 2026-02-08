"""
Financial Analysis page - Core analysis features.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

import config
from src.data_processor import DataProcessor

# Page configuration
st.set_page_config(
    page_title="재무 분석",
    page_icon="📊",
    layout="wide"
)

# Load data
@st.cache_data(ttl=3600)
def load_analysis_data():
    """Load analysis data with caching."""
    processor = DataProcessor()
    return processor.prepare_dashboard_data()

# Main page
def main():
    st.title("📊 재무 분석")
    st.markdown("### 화장품 원료 회사 심층 재무 분석")
    st.markdown("---")

    try:
        data = load_analysis_data()
        companies_df = data['companies']
        metrics_df = data['metrics']
        industry_avg_df = data['industry_avg']

        if metrics_df.empty:
            st.warning("재무 데이터가 없습니다. '데이터 관리' 페이지에서 재무 데이터를 수집해주세요.")
            return

        # Sidebar filters
        st.sidebar.title("🔍 회사 검색 및 필터")
        st.sidebar.markdown("---")

        # Company search and selection
        available_companies = sorted(metrics_df['corp_name'].unique())

        # Search mode selector
        search_mode = st.sidebar.radio(
            "표시 방식",
            options=["특정 회사만 보기", "여러 회사 비교"],
            index=1  # Default to comparison mode for financial analysis
        )

        if search_mode == "특정 회사만 보기":
            # Single company search
            selected_company = st.sidebar.selectbox(
                "회사 검색 (입력하여 검색)",
                options=available_companies,
                index=0
            )
            selected_companies = [selected_company]

            # Show company info
            company_info = companies_df[companies_df['corp_name'] == selected_company]
            if not company_info.empty:
                st.sidebar.markdown("---")
                st.sidebar.markdown("**선택된 회사 정보**")
                st.sidebar.info(f"""
                **회사명**: {selected_company}
                **종목코드**: {company_info.iloc[0].get('stock_code', 'N/A')}
                **분류점수**: {company_info.iloc[0].get('classification_score', 'N/A')}점
                """)
        else:
            # Multiple company selection
            selected_companies = st.sidebar.multiselect(
                "비교할 회사 선택 (최대 10개)",
                options=available_companies,
                default=available_companies[:min(5, len(available_companies))],
                max_selections=10
            )

            if not selected_companies:
                st.warning("최소 1개 이상의 회사를 선택해주세요.")
                return

        st.sidebar.markdown("---")

        # Year range
        available_years = sorted(metrics_df['year'].unique())
        year_range = st.sidebar.slider(
            "연도 범위",
            min_value=int(min(available_years)),
            max_value=int(max(available_years)),
            value=(int(min(available_years)), int(max(available_years)))
        )

        # Filter data
        df_filtered = metrics_df[
            (metrics_df['year'] >= year_range[0]) &
            (metrics_df['year'] <= year_range[1]) &
            (metrics_df['corp_name'].isin(selected_companies))
        ]

        if df_filtered.empty:
            st.warning("선택한 필터에 해당하는 데이터가 없습니다.")
            return

        # Analysis Section 1: Revenue and Operating Profit Trends
        st.header("1. 매출/영업이익 트렌드 분석")
        st.markdown("연도별 매출액과 영업이익 추이를 확인합니다.")

        col1, col2 = st.columns(2)

        with col1:
            if '매출액' in df_filtered.columns:
                df_chart = df_filtered.copy()
                df_chart['매출액_억원'] = df_chart['매출액'] / 100000000

                fig_revenue = px.line(
                    df_chart,
                    x='year',
                    y='매출액_억원',
                    color='corp_name',
                    markers=True,
                    labels={'매출액_억원': '매출액 (억원)', 'year': '연도', 'corp_name': '회사명'},
                    title='매출액 추이'
                )
                fig_revenue.update_layout(hovermode='x unified', height=400)
                st.plotly_chart(fig_revenue, use_container_width=True)
            else:
                st.info("매출액 데이터가 없습니다.")

        with col2:
            if '영업이익' in df_filtered.columns:
                df_chart = df_filtered.copy()
                df_chart['영업이익_억원'] = df_chart['영업이익'] / 100000000

                fig_profit = px.line(
                    df_chart,
                    x='year',
                    y='영업이익_억원',
                    color='corp_name',
                    markers=True,
                    labels={'영업이익_억원': '영업이익 (억원)', 'year': '연도', 'corp_name': '회사명'},
                    title='영업이익 추이'
                )
                fig_profit.update_layout(hovermode='x unified', height=400)
                st.plotly_chart(fig_profit, use_container_width=True)
            else:
                st.info("영업이익 데이터가 없습니다.")

        # Growth rates
        st.subheader("성장률 분석")

        if '매출액_성장률' in df_filtered.columns:
            fig_growth = px.bar(
                df_filtered,
                x='year',
                y='매출액_성장률',
                color='corp_name',
                barmode='group',
                labels={'매출액_성장률': '매출 성장률 (%)', 'year': '연도', 'corp_name': '회사명'},
                title='연도별 매출 성장률 (YoY)'
            )
            fig_growth.update_layout(hovermode='x unified')
            st.plotly_chart(fig_growth, use_container_width=True)
        else:
            st.info("성장률 데이터가 없습니다.")

        st.markdown("---")

        # Analysis Section 2: Profitability Metrics
        st.header("2. 수익성 지표 분석")
        st.markdown("영업이익률과 순이익률을 통해 수익성을 평가합니다.")

        col1, col2 = st.columns(2)

        with col1:
            if '영업이익률' in df_filtered.columns:
                fig_op_margin = px.line(
                    df_filtered,
                    x='year',
                    y='영업이익률',
                    color='corp_name',
                    markers=True,
                    labels={'영업이익률': '영업이익률 (%)', 'year': '연도', 'corp_name': '회사명'},
                    title='영업이익률 추이'
                )
                fig_op_margin.update_layout(hovermode='x unified', height=400)
                st.plotly_chart(fig_op_margin, use_container_width=True)
            else:
                st.info("영업이익률 데이터가 없습니다.")

        with col2:
            if '순이익률' in df_filtered.columns:
                fig_net_margin = px.line(
                    df_filtered,
                    x='year',
                    y='순이익률',
                    color='corp_name',
                    markers=True,
                    labels={'순이익률': '순이익률 (%)', 'year': '연도', 'corp_name': '회사명'},
                    title='순이익률 추이'
                )
                fig_net_margin.update_layout(hovermode='x unified', height=400)
                st.plotly_chart(fig_net_margin, use_container_width=True)
            else:
                st.info("순이익률 데이터가 없습니다.")

        # Profitability heatmap
        st.subheader("수익성 히트맵")

        if '영업이익률' in df_filtered.columns:
            # Pivot data for heatmap
            df_heatmap = df_filtered.pivot(
                index='corp_name',
                columns='year',
                values='영업이익률'
            )

            fig_heatmap = px.imshow(
                df_heatmap,
                labels=dict(x="연도", y="회사명", color="영업이익률 (%)"),
                title='회사별 영업이익률 히트맵',
                aspect="auto",
                color_continuous_scale='RdYlGn'
            )
            fig_heatmap.update_xaxes(side="bottom")
            st.plotly_chart(fig_heatmap, use_container_width=True)
        else:
            st.info("영업이익률 데이터가 없습니다.")

        st.markdown("---")

        # Analysis Section 3: Industry Average Comparison
        st.header("3. 산업 평균 대비 분석")
        st.markdown("개별 회사의 성과를 산업 평균과 비교합니다.")

        if not industry_avg_df.empty:
            # Combine company data with industry average
            latest_year = df_filtered['year'].max()
            df_latest = df_filtered[df_filtered['year'] == latest_year].copy()
            df_industry_latest = industry_avg_df[industry_avg_df['year'] == latest_year].copy()

            # Revenue comparison
            if '매출액' in df_latest.columns and '매출액' in df_industry_latest.columns:
                st.subheader(f"매출액 비교 ({latest_year}년)")

                df_comparison = df_latest[['corp_name', '매출액']].copy()
                df_comparison['매출액_억원'] = df_comparison['매출액'] / 100000000

                # Add industry average
                industry_avg_revenue = df_industry_latest['매출액'].iloc[0] / 100000000
                df_avg_row = pd.DataFrame([{
                    'corp_name': '산업 평균',
                    '매출액_억원': industry_avg_revenue
                }])
                df_comparison = pd.concat([df_comparison, df_avg_row], ignore_index=True)

                fig_revenue_comp = px.bar(
                    df_comparison,
                    x='corp_name',
                    y='매출액_억원',
                    labels={'매출액_억원': '매출액 (억원)', 'corp_name': '회사명'},
                    title=f'{latest_year}년 매출액 vs 산업 평균',
                    color_discrete_sequence=['steelblue'] * (len(df_comparison) - 1) + ['orange']
                )
                st.plotly_chart(fig_revenue_comp, use_container_width=True)

            # Profitability comparison
            if '영업이익률' in df_latest.columns and '영업이익률' in df_industry_latest.columns:
                st.subheader(f"수익성 비교 ({latest_year}년)")

                col1, col2 = st.columns(2)

                with col1:
                    df_op_comp = df_latest[['corp_name', '영업이익률']].copy()
                    industry_avg_op = df_industry_latest['영업이익률'].iloc[0]

                    df_op_avg = pd.DataFrame([{
                        'corp_name': '산업 평균',
                        '영업이익률': industry_avg_op
                    }])
                    df_op_comp = pd.concat([df_op_comp, df_op_avg], ignore_index=True)

                    fig_op_comp = px.bar(
                        df_op_comp,
                        x='corp_name',
                        y='영업이익률',
                        labels={'영업이익률': '영업이익률 (%)', 'corp_name': '회사명'},
                        title=f'{latest_year}년 영업이익률 vs 산업 평균',
                        color_discrete_sequence=['teal'] * (len(df_op_comp) - 1) + ['orange']
                    )
                    st.plotly_chart(fig_op_comp, use_container_width=True)

                with col2:
                    # Calculate deviation from industry average
                    df_deviation = df_latest[['corp_name', '영업이익률']].copy()
                    df_deviation['산업평균대비'] = df_deviation['영업이익률'] - industry_avg_op

                    fig_deviation = px.bar(
                        df_deviation,
                        x='corp_name',
                        y='산업평균대비',
                        labels={'산업평균대비': '산업 평균 대비 차이 (%p)', 'corp_name': '회사명'},
                        title='산업 평균 대비 영업이익률 편차',
                        color='산업평균대비',
                        color_continuous_scale=['red', 'yellow', 'green'],
                        color_continuous_midpoint=0
                    )
                    st.plotly_chart(fig_deviation, use_container_width=True)

            # Top and bottom performers
            st.subheader("상위/하위 성과 회사")

            col1, col2 = st.columns(2)

            with col1:
                if '영업이익률' in df_latest.columns:
                    top_5 = df_latest.nlargest(5, '영업이익률')[['corp_name', '영업이익률']]
                    st.markdown("**영업이익률 상위 5개사**")
                    st.dataframe(top_5, use_container_width=True)

            with col2:
                if '영업이익률' in df_latest.columns:
                    bottom_5 = df_latest.nsmallest(5, '영업이익률')[['corp_name', '영업이익률']]
                    st.markdown("**영업이익률 하위 5개사**")
                    st.dataframe(bottom_5, use_container_width=True)

        else:
            st.info("산업 평균 데이터가 없습니다.")

        st.markdown("---")

        # Summary table
        st.header("종합 재무 데이터")

        if not df_filtered.empty:
            # Select display columns
            display_cols = ['corp_name', 'year', '매출액', '영업이익', '당기순이익',
                           '영업이익률', '순이익률', '매출액_성장률']
            display_cols = [col for col in display_cols if col in df_filtered.columns]

            df_display = df_filtered[display_cols].copy()

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
                'year': '연도',
                '매출액': '매출액 (억원)',
                '영업이익': '영업이익 (억원)',
                '당기순이익': '당기순이익 (억원)',
                '영업이익률': '영업이익률 (%)',
                '순이익률': '순이익률 (%)',
                '매출액_성장률': '매출 성장률 (%)'
            })

            st.dataframe(df_display, use_container_width=True, height=400)

            # Download button
            csv = df_display.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="데이터 CSV 다운로드",
                data=csv,
                file_name="financial_analysis.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"데이터 분석 중 오류가 발생했습니다: {e}")
        import traceback
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
