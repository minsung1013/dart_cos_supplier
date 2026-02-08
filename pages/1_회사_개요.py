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
            st.warning("분류된 회사 데이터가 없습니다. '데이터 관리' 페이지에서 회사 분류를 실행해주세요.")
            return

        # Summary statistics
        st.subheader("분류 결과 요약")

        col1, col2, col3 = st.columns(3)

        with col1:
            total_companies = len(companies_df)
            st.metric("총 분류된 회사 수", f"{total_companies}개")

        with col2:
            if 'stock_code' in companies_df.columns:
                listed_companies = companies_df[companies_df['stock_code'].notna()].shape[0]
                st.metric("상장 회사", f"{listed_companies}개")
            else:
                st.metric("상장 회사", "N/A")

        with col3:
            if 'classification_score' in companies_df.columns:
                avg_score = companies_df['classification_score'].mean()
                st.metric("평균 분류 점수", f"{avg_score:.1f}점")
            else:
                st.metric("평균 분류 점수", "N/A")

        st.markdown("---")

        # Classification score distribution
        st.subheader("분류 점수 분포")

        if 'classification_score' in companies_df.columns:
            fig_score = px.histogram(
                companies_df,
                x='classification_score',
                nbins=20,
                labels={'classification_score': '분류 점수', 'count': '회사 수'},
                title='회사별 분류 점수 분포'
            )
            fig_score.update_layout(showlegend=False)
            st.plotly_chart(fig_score, use_container_width=True)
        else:
            st.info("분류 점수 데이터가 없습니다.")

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
        search_query = st.text_input("회사명 검색", "")

        if search_query:
            df_display = companies_df[companies_df['corp_name'].str.contains(search_query, case=False, na=False)]
        else:
            df_display = companies_df.copy()

        # Sort options
        sort_col = st.selectbox(
            "정렬 기준",
            options=['corp_name', 'classification_score', 'stock_code'],
            format_func=lambda x: {
                'corp_name': '회사명',
                'classification_score': '분류 점수',
                'stock_code': '종목코드'
            }.get(x, x)
        )

        if sort_col in df_display.columns:
            df_display = df_display.sort_values(by=sort_col, ascending=False)

        # Display table
        display_cols = ['corp_name', 'stock_code', 'classification_score', 'corp_code']
        display_cols = [col for col in display_cols if col in df_display.columns]

        df_table = df_display[display_cols].copy()
        df_table = df_table.rename(columns={
            'corp_name': '회사명',
            'stock_code': '종목코드',
            'classification_score': '분류 점수',
            'corp_code': '회사코드'
        })

        st.dataframe(df_table, use_container_width=True, height=400)

        st.markdown(f"**총 {len(df_display)}개 회사 표시 중**")

        # Top companies by classification score
        st.subheader("분류 점수 상위 회사")

        if 'classification_score' in companies_df.columns:
            top_n = st.slider("표시할 회사 수", min_value=5, max_value=20, value=10)

            df_top = companies_df.nlargest(top_n, 'classification_score')[['corp_name', 'classification_score']]

            fig_top = px.bar(
                df_top,
                x='classification_score',
                y='corp_name',
                orientation='h',
                labels={'classification_score': '분류 점수', 'corp_name': '회사명'},
                title=f'분류 점수 상위 {top_n}개 회사'
            )
            fig_top.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_top, use_container_width=True)
        else:
            st.info("분류 점수 데이터가 없습니다.")

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
