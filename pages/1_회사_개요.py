"""
Company Overview page - Shows classified companies and basic statistics.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import config
from src.data_processor import DataProcessor

# Page configuration
st.set_page_config(
    page_title="회사 개요",
    page_icon="🏢",
    layout="wide"
)

# Load data
@st.cache_data(ttl=3600)
def load_companies_data():
    """Load companies data with caching."""
    processor = DataProcessor()
    return processor.prepare_dashboard_data()

# Main page
def main():
    st.title("🏢 회사 개요")
    st.markdown("### 분류된 화장품 원료 회사 목록 및 통계")
    st.markdown("---")

    try:
        data = load_companies_data()
        companies_df = data['companies']
        metrics_df = data['metrics']

        if companies_df.empty:
            st.warning("선택된 회사가 없습니다. '데이터 관리' 페이지에서 회사를 검색하고 추가해주세요.")
            return

        # Summary statistics
        st.subheader("선택된 회사 요약")

        col1, col2 = st.columns(2)

        with col1:
            total_companies = len(companies_df)
            st.metric("선택된 회사 수", f"{total_companies}개")

        with col2:
            if 'stock_code' in companies_df.columns:
                listed_companies = companies_df[companies_df['stock_code'].notna() & (companies_df['stock_code'] != '')].shape[0]
                st.metric("상장 회사", f"{listed_companies}개")
            else:
                st.metric("상장 회사", "N/A")

        st.markdown("---")

        # Market type distribution
        st.subheader("시장 분포")

        if 'stock_code' in companies_df.columns:
            # Determine market type
            companies_df_copy = companies_df.copy()
            companies_df_copy['market_type'] = companies_df_copy['stock_code'].apply(
                lambda x: '상장' if pd.notna(x) and x.strip() != '' else '비상장'
            )

            market_counts = companies_df_copy['market_type'].value_counts()

            fig_market = px.pie(
                values=market_counts.values,
                names=market_counts.index,
                title='상장 여부별 분포'
            )
            st.plotly_chart(fig_market, use_container_width=True)
        else:
            st.info("시장 정보가 없습니다.")

        # Company list table
        st.subheader("회사 목록")

        # Add search functionality
        col1, col2 = st.columns([2, 1])

        with col1:
            search_method = st.radio(
                "검색 방법",
                options=["직접 입력", "목록에서 선택"],
                horizontal=True,
                index=1
            )

        with col2:
            if st.button("🔄 전체 보기", use_container_width=True):
                st.rerun()

        if search_method == "직접 입력":
            search_query = st.text_input("회사명 검색 (부분 검색 가능)", "", placeholder="예: 코스맥스")
        else:
            search_query = st.selectbox(
                "회사 선택 (입력하여 검색 가능)",
                options=["전체"] + sorted(companies_df['corp_name'].unique().tolist()),
                index=0
            )
            if search_query == "전체":
                search_query = ""

        if search_query:
            df_display = companies_df[companies_df['corp_name'].str.contains(search_query, case=False, na=False)]
        else:
            df_display = companies_df.copy()

        # Show detailed info if only one company is selected
        if len(df_display) == 1:
            st.markdown("---")
            st.subheader("📋 선택된 회사 상세 정보")

            company_row = df_display.iloc[0]

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("회사명", company_row.get('corp_name', 'N/A'))

            with col2:
                stock_code = company_row.get('stock_code', '')
                if pd.notna(stock_code) and stock_code.strip() != '':
                    st.metric("종목코드", stock_code)
                else:
                    st.metric("종목코드", "비상장")

            with col3:
                st.metric("회사코드", company_row.get('corp_code', 'N/A'))

            # Get financial data if available
            if not metrics_df.empty:
                company_metrics = metrics_df[metrics_df['corp_name'] == company_row.get('corp_name')]
                if not company_metrics.empty:
                    st.markdown("#### 최근 재무 현황")

                    latest_year = company_metrics['year'].max()
                    latest_data = company_metrics[company_metrics['year'] == latest_year].iloc[0]

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if '매출액' in latest_data:
                            revenue = latest_data['매출액'] / 100000000
                            st.metric(f"{latest_year}년 매출액", f"{revenue:,.0f}억원")

                    with col2:
                        if '영업이익' in latest_data:
                            op_profit = latest_data['영업이익'] / 100000000
                            st.metric(f"{latest_year}년 영업이익", f"{op_profit:,.0f}억원")

                    with col3:
                        if '영업이익률' in latest_data:
                            st.metric(f"{latest_year}년 영업이익률", f"{latest_data['영업이익률']:.1f}%")

                    st.info("💡 더 자세한 재무 분석은 '재무 분석' 페이지에서 확인하세요.")
                else:
                    st.info("이 회사의 재무 데이터가 아직 수집되지 않았습니다.")

            st.markdown("---")

        # Sort options
        sort_col = st.selectbox(
            "정렬 기준",
            options=['corp_name', 'stock_code'],
            format_func=lambda x: {
                'corp_name': '회사명',
                'stock_code': '종목코드'
            }.get(x, x)
        )

        if sort_col in df_display.columns:
            df_display = df_display.sort_values(by=sort_col, ascending=False)

        # Display table
        display_cols = ['corp_name', 'stock_code', 'corp_code']
        display_cols = [col for col in display_cols if col in df_display.columns]

        df_table = df_display[display_cols].copy()
        df_table = df_table.rename(columns={
            'corp_name': '회사명',
            'stock_code': '종목코드',
            'corp_code': '회사코드'
        })

        st.dataframe(df_table, use_container_width=True, height=400)

        st.markdown(f"**총 {len(df_display)}개 회사 표시 중**")

        # Export functionality
        st.subheader("데이터 내보내기")

        col1, col2 = st.columns(2)

        with col1:
            csv = companies_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="CSV 다운로드",
                data=csv,
                file_name="cosmetic_companies.csv",
                mime="text/csv"
            )

        with col2:
            if st.button("Excel 내보내기"):
                processor = DataProcessor()
                output_path = config.PROCESSED_DATA_DIR / "cosmetic_analysis.xlsx"
                processor.export_to_excel(output_path)
                st.success(f"Excel 파일이 저장되었습니다: {output_path}")

    except Exception as e:
        st.error(f"데이터 로드 중 오류가 발생했습니다: {e}")
        st.info("'데이터 관리' 페이지에서 데이터를 수집해주세요.")

if __name__ == "__main__":
    main()
