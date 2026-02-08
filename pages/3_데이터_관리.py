"""
Data Management page - Company search and financial data collection.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

import config
from src.dart_client import DartClient
from src.financial_collector import FinancialCollector
from src.data_processor import DataProcessor

# Page configuration
st.set_page_config(
    page_title="데이터 관리",
    page_icon="⚙️",
    layout="wide"
)

# Main page
def main():
    st.title("⚙️ 데이터 관리")
    st.markdown("### 회사 검색 및 재무 데이터 수집")
    st.markdown("---")

    # Initialize DART client
    try:
        dart_client = DartClient(config.DART_API_KEY)
    except ValueError as e:
        st.error(f"API 키 오류: {e}")
        st.info("`.env` 파일에 DART_API 키가 설정되어 있는지 확인해주세요.")
        return

    # Data status section
    st.header("📊 데이터 현황")

    companies_file = config.PROCESSED_DATA_DIR / "selected_companies.csv"
    financial_file = config.PROCESSED_DATA_DIR / "financial_data.csv"

    col1, col2, col3 = st.columns(3)

    with col1:
        if companies_file.exists():
            companies_df = pd.read_csv(companies_file, encoding='utf-8-sig')
            st.metric("선택된 회사 수", f"{len(companies_df)}개")
            mod_time = datetime.fromtimestamp(companies_file.stat().st_mtime)
            st.caption(f"마지막 업데이트: {mod_time.strftime('%Y-%m-%d %H:%M')}")
        else:
            st.metric("선택된 회사 수", "0개")
            st.caption("데이터 없음")

    with col2:
        if financial_file.exists():
            financial_df = pd.read_csv(financial_file, encoding='utf-8-sig')
            st.metric("재무 데이터 레코드", f"{len(financial_df)}개")
            mod_time = datetime.fromtimestamp(financial_file.stat().st_mtime)
            st.caption(f"마지막 업데이트: {mod_time.strftime('%Y-%m-%d %H:%M')}")
        else:
            st.metric("재무 데이터 레코드", "0개")
            st.caption("데이터 없음")

    with col3:
        cache_files = list(config.CACHE_DIR.glob("*.json"))
        st.metric("캐시 파일 수", f"{len(cache_files)}개")

    st.markdown("---")

    # Company search and selection section
    st.header("🔍 회사 검색 및 선택")

    st.markdown("""
    **사용 방법:**
    1. 아래에서 회사명을 검색하여 원하는 회사를 찾습니다.
    2. 찾은 회사를 선택하여 목록에 추가합니다.
    3. 선택된 회사들의 재무 데이터를 수집합니다.
    """)

    col1, col2 = st.columns([2, 1])

    with col1:
        # Search company
        search_query = st.text_input(
            "회사명 검색 (부분 검색 가능)",
            placeholder="예: 코스맥스, LG생활건강, 아모레퍼시픽"
        )

    with col2:
        st.markdown("###")  # Spacing
        search_button = st.button("🔍 검색", use_container_width=True, type="primary")

    # Search results
    if search_button and search_query:
        with st.spinner("회사를 검색하는 중입니다..."):
            try:
                # Get all company codes
                corp_codes = dart_client.get_corp_codes()

                if corp_codes:
                    # Filter by search query
                    search_results = [
                        corp for corp in corp_codes
                        if search_query.lower() in corp.get('corp_name', '').lower()
                    ]

                    if search_results:
                        st.success(f"✅ {len(search_results)}개의 회사를 찾았습니다.")

                        # Display search results
                        df_results = pd.DataFrame(search_results)
                        df_results = df_results[['corp_name', 'stock_code', 'corp_code']]
                        df_results = df_results.rename(columns={
                            'corp_name': '회사명',
                            'stock_code': '종목코드',
                            'corp_code': '회사코드'
                        })

                        # Show results with selection
                        st.dataframe(df_results, use_container_width=True)

                        # Allow user to select companies
                        st.markdown("### 선택할 회사")
                        selected_indices = st.multiselect(
                            "추가할 회사를 선택하세요 (여러 개 선택 가능)",
                            options=range(len(search_results)),
                            format_func=lambda x: search_results[x]['corp_name']
                        )

                        if selected_indices and st.button("✅ 선택된 회사 추가", type="primary"):
                            # Load existing selected companies
                            if companies_file.exists():
                                existing_df = pd.read_csv(companies_file, encoding='utf-8-sig')
                                existing_codes = set(existing_df['corp_code'].tolist())
                            else:
                                existing_df = pd.DataFrame()
                                existing_codes = set()

                            # Add new companies
                            new_companies = []
                            for idx in selected_indices:
                                corp = search_results[idx]
                                if corp['corp_code'] not in existing_codes:
                                    new_companies.append({
                                        'corp_code': corp['corp_code'],
                                        'corp_name': corp['corp_name'],
                                        'stock_code': corp.get('stock_code', ''),
                                    })

                            if new_companies:
                                new_df = pd.DataFrame(new_companies)
                                if not existing_df.empty:
                                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                                else:
                                    combined_df = new_df

                                combined_df.to_csv(companies_file, index=False, encoding='utf-8-sig')
                                st.success(f"✅ {len(new_companies)}개 회사가 추가되었습니다!")
                                st.rerun()
                            else:
                                st.info("선택한 회사가 이미 목록에 있습니다.")

                    else:
                        st.warning(f"'{search_query}'와 일치하는 회사를 찾을 수 없습니다.")
                else:
                    st.error("회사 목록을 가져오는데 실패했습니다.")

            except Exception as e:
                st.error(f"검색 중 오류가 발생했습니다: {e}")

    st.markdown("---")

    # Selected companies management
    st.header("📋 선택된 회사 목록")

    if companies_file.exists():
        companies_df = pd.read_csv(companies_file, encoding='utf-8-sig')

        if not companies_df.empty:
            st.markdown(f"**총 {len(companies_df)}개 회사 선택됨**")

            # Display selected companies
            display_df = companies_df.copy()
            display_df = display_df.rename(columns={
                'corp_name': '회사명',
                'stock_code': '종목코드',
                'corp_code': '회사코드'
            })
            st.dataframe(display_df, use_container_width=True)

            # Remove company option
            col1, col2 = st.columns([3, 1])

            with col1:
                remove_company = st.selectbox(
                    "제거할 회사 선택",
                    options=companies_df['corp_name'].tolist(),
                    key="remove_company"
                )

            with col2:
                st.markdown("###")  # Spacing
                if st.button("❌ 제거", use_container_width=True):
                    companies_df = companies_df[companies_df['corp_name'] != remove_company]
                    companies_df.to_csv(companies_file, index=False, encoding='utf-8-sig')
                    st.success(f"'{remove_company}'가 제거되었습니다.")
                    st.rerun()

            # Collect financial data button
            st.markdown("---")

            if st.button("📊 선택된 회사들의 재무 데이터 수집", type="primary", use_container_width=True):
                with st.spinner("재무 데이터를 수집하는 중입니다... (시간이 걸릴 수 있습니다)"):
                    try:
                        collector = FinancialCollector(dart_client)

                        # Create progress bar
                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        all_records = []
                        total = len(companies_df)

                        for idx, row in companies_df.iterrows():
                            corp_code = row['corp_code']
                            corp_name = row['corp_name']

                            status_text.text(f"수집 중: {corp_name} ({idx + 1}/{total})")
                            progress_bar.progress((idx + 1) / total)

                            records = collector.collect_company_financials(corp_code, corp_name)
                            all_records.extend(records)

                        progress_bar.empty()
                        status_text.empty()

                        if all_records:
                            df_financials = pd.DataFrame(all_records)
                            df_financials.to_csv(financial_file, index=False, encoding='utf-8-sig')

                            st.success(f"✅ {len(all_records)}개 재무 레코드가 수집되었습니다!")

                            # Show summary
                            summary = df_financials.groupby('corp_name').size().reset_index(name='레코드 수')
                            st.dataframe(summary)
                        else:
                            st.warning("수집된 재무 데이터가 없습니다.")

                    except Exception as e:
                        st.error(f"재무 데이터 수집 중 오류가 발생했습니다: {e}")
                        import traceback
                        st.code(traceback.format_exc())

        else:
            st.info("선택된 회사가 없습니다. 위에서 회사를 검색하고 추가해주세요.")
    else:
        st.info("선택된 회사가 없습니다. 위에서 회사를 검색하고 추가해주세요.")

    st.markdown("---")

    # Cache management section
    st.header("🗄️ 캐시 관리")

    col1, col2 = st.columns([2, 1])

    with col1:
        cache_files = list(config.CACHE_DIR.glob("*.json"))
        if cache_files:
            total_size = sum(f.stat().st_size for f in cache_files) / 1024 / 1024  # MB
            st.info(f"캐시 파일 {len(cache_files)}개, 총 {total_size:.2f} MB")
        else:
            st.info("캐시 파일이 없습니다.")

    with col2:
        if st.button("🗑️ 캐시 삭제", type="secondary", use_container_width=True):
            try:
                dart_client.clear_cache()
                st.success("✅ 캐시가 삭제되었습니다!")
                st.rerun()
            except Exception as e:
                st.error(f"캐시 삭제 중 오류: {e}")

    st.markdown("---")

    # Data export section
    st.header("📥 데이터 내보내기")

    col1, col2, col3 = st.columns(3)

    with col1:
        if companies_file.exists():
            with open(companies_file, 'rb') as f:
                st.download_button(
                    label="회사 목록 CSV",
                    data=f,
                    file_name="selected_companies.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.button("회사 목록 CSV", disabled=True, use_container_width=True)

    with col2:
        if financial_file.exists():
            with open(financial_file, 'rb') as f:
                st.download_button(
                    label="재무 데이터 CSV",
                    data=f,
                    file_name="financial_data.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.button("재무 데이터 CSV", disabled=True, use_container_width=True)

    with col3:
        if st.button("Excel 파일 생성", use_container_width=True):
            if companies_file.exists() or financial_file.exists():
                try:
                    processor = DataProcessor()
                    output_path = config.PROCESSED_DATA_DIR / "financial_analysis.xlsx"
                    processor.export_to_excel(output_path)
                    st.success(f"✅ Excel 파일이 생성되었습니다!")

                    with open(output_path, 'rb') as f:
                        st.download_button(
                            label="Excel 다운로드",
                            data=f,
                            file_name="financial_analysis.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"Excel 생성 중 오류: {e}")
            else:
                st.error("내보낼 데이터가 없습니다.")

    st.markdown("---")

    # Help section
    st.header("❓ 도움말")

    with st.expander("회사 검색 팁"):
        st.markdown("""
        - **부분 검색**: 회사명의 일부만 입력해도 검색됩니다. (예: "코스" → "코스맥스", "코스메카코리아" 등)
        - **영문 검색**: 영문 회사명으로도 검색 가능합니다.
        - **종목코드**: 종목코드로도 검색할 수 있습니다.
        """)

    with st.expander("데이터 수집 시간"):
        st.markdown("""
        - **회사당 소요 시간**: 약 5-10초 (5년치 데이터 기준)
        - **10개 회사**: 약 1-2분
        - **네트워크 상태**에 따라 시간이 달라질 수 있습니다.
        """)

    with st.expander("API 사용량"):
        st.markdown(f"""
        - **DART API 키**: {config.DART_API_KEY[:10]}...
        - **일일 제한**: DART API는 일일 10,000회 호출 제한이 있습니다.
        - **캐시 활용**: 동일한 데이터는 캐시에서 불러오므로 API 호출이 절약됩니다.
        """)

if __name__ == "__main__":
    main()
