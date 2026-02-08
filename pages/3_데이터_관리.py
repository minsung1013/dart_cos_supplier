"""
Data Management page - Data collection, refresh, and export functionality.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

import config
from src.dart_client import DartClient
from src.company_classifier import CompanyClassifier
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
    st.markdown("### 데이터 수집, 새로고침 및 내보내기")
    st.markdown("---")

    # Initialize DART client
    try:
        dart_client = DartClient(config.DART_API_KEY)
    except ValueError as e:
        st.error(f"API 키 오류: {e}")
        st.info("`.env` 파일에 DART_API 키가 설정되어 있는지 확인해주세요.")
        return

    # Data status section
    st.header("데이터 현황")

    col1, col2, col3 = st.columns(3)

    # Check companies file
    companies_file = config.PROCESSED_DATA_DIR / "cosmetic_companies.csv"
    financial_file = config.PROCESSED_DATA_DIR / "financial_data.csv"

    with col1:
        if companies_file.exists():
            companies_df = pd.read_csv(companies_file, encoding='utf-8-sig')
            st.metric("분류된 회사 수", f"{len(companies_df)}개")

            # Show last modified time
            mod_time = datetime.fromtimestamp(companies_file.stat().st_mtime)
            st.caption(f"마지막 업데이트: {mod_time.strftime('%Y-%m-%d %H:%M')}")
        else:
            st.metric("분류된 회사 수", "0개")
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
        st.caption(f"캐시 디렉토리: {config.CACHE_DIR}")

    st.markdown("---")

    # Data collection section
    st.header("데이터 수집")

    st.markdown("""
    **데이터 수집 프로세스:**
    1. **회사 분류**: DART에서 전체 회사 목록을 가져와 화장품 원료 회사를 분류합니다.
    2. **재무 데이터 수집**: 분류된 회사들의 2021-2025년 재무제표를 수집합니다.

    ⚠️ **주의**: 데이터 수집은 시간이 오래 걸릴 수 있습니다 (10-30분).
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1. 회사 분류")

        if st.button("회사 분류 시작", type="primary", use_container_width=True):
            with st.spinner("회사를 분류하는 중입니다..."):
                try:
                    classifier = CompanyClassifier(dart_client)
                    companies_df = classifier.classify_all(progress_bar=False)

                    if not companies_df.empty:
                        st.success(f"✅ {len(companies_df)}개 회사가 분류되었습니다!")
                        st.dataframe(companies_df.head(10))
                    else:
                        st.warning("분류된 회사가 없습니다. 분류 기준을 확인해주세요.")

                except Exception as e:
                    st.error(f"회사 분류 중 오류가 발생했습니다: {e}")
                    import traceback
                    st.code(traceback.format_exc())

    with col2:
        st.subheader("2. 재무 데이터 수집")

        if st.button("재무 데이터 수집 시작", type="primary", use_container_width=True):
            if not companies_file.exists():
                st.error("먼저 회사 분류를 실행해주세요.")
            else:
                with st.spinner("재무 데이터를 수집하는 중입니다..."):
                    try:
                        collector = FinancialCollector(dart_client)
                        financial_df = collector.collect_all(progress_bar=False)

                        if not financial_df.empty:
                            st.success(f"✅ {len(financial_df)}개 재무 레코드가 수집되었습니다!")

                            # Show summary
                            summary = financial_df.groupby('corp_name').size().reset_index(name='레코드 수')
                            st.dataframe(summary.head(10))
                        else:
                            st.warning("수집된 재무 데이터가 없습니다.")

                    except Exception as e:
                        st.error(f"재무 데이터 수집 중 오류가 발생했습니다: {e}")
                        import traceback
                        st.code(traceback.format_exc())

    st.markdown("---")

    # Cache management section
    st.header("캐시 관리")

    st.markdown("""
    API 응답은 자동으로 캐시됩니다:
    - **회사 목록**: 24시간
    - **재무 데이터**: 7일

    캐시를 삭제하면 다음 요청 시 새로운 데이터를 가져옵니다.
    """)

    col1, col2 = st.columns([2, 1])

    with col1:
        cache_files = list(config.CACHE_DIR.glob("*.json"))
        if cache_files:
            total_size = sum(f.stat().st_size for f in cache_files) / 1024 / 1024  # MB
            st.info(f"캐시 파일 {len(cache_files)}개, 총 {total_size:.2f} MB")
        else:
            st.info("캐시 파일이 없습니다.")

    with col2:
        if st.button("캐시 삭제", type="secondary", use_container_width=True):
            try:
                dart_client.clear_cache()
                st.success("✅ 캐시가 삭제되었습니다!")
                st.rerun()
            except Exception as e:
                st.error(f"캐시 삭제 중 오류: {e}")

    st.markdown("---")

    # Data export section
    st.header("데이터 내보내기")

    st.markdown("수집된 데이터를 다양한 형식으로 내보낼 수 있습니다.")

    col1, col2, col3 = st.columns(3)

    with col1:
        if companies_file.exists():
            with open(companies_file, 'rb') as f:
                st.download_button(
                    label="회사 목록 CSV 다운로드",
                    data=f,
                    file_name="cosmetic_companies.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.button("회사 목록 CSV 다운로드", disabled=True, use_container_width=True)

    with col2:
        if financial_file.exists():
            with open(financial_file, 'rb') as f:
                st.download_button(
                    label="재무 데이터 CSV 다운로드",
                    data=f,
                    file_name="financial_data.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.button("재무 데이터 CSV 다운로드", disabled=True, use_container_width=True)

    with col3:
        if st.button("Excel 파일 생성", use_container_width=True):
            if companies_file.exists() or financial_file.exists():
                try:
                    processor = DataProcessor()
                    output_path = config.PROCESSED_DATA_DIR / "cosmetic_analysis.xlsx"
                    processor.export_to_excel(output_path)
                    st.success(f"✅ Excel 파일이 생성되었습니다: {output_path}")

                    # Provide download button
                    with open(output_path, 'rb') as f:
                        st.download_button(
                            label="Excel 파일 다운로드",
                            data=f,
                            file_name="cosmetic_analysis.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"Excel 생성 중 오류: {e}")
            else:
                st.error("내보낼 데이터가 없습니다.")

    st.markdown("---")

    # Configuration section
    st.header("설정 정보")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**API 설정**")
        st.code(f"""
API Key: {config.DART_API_KEY[:10]}...
Base URL: {config.DART_BASE_URL}
Timeout: {config.API_TIMEOUT}초
Retry Count: {config.API_RETRY_COUNT}
        """)

    with col2:
        st.markdown("**분류 설정**")
        st.code(f"""
KSIC 코드: {len(config.COSMETIC_KSIC_CODES)}개
키워드 (고): {len(config.CLASSIFICATION_KEYWORDS['high_priority'])}개
키워드 (중): {len(config.CLASSIFICATION_KEYWORDS['medium_priority'])}개
분류 임계값: {config.CLASSIFICATION_THRESHOLD}점
수집 연도: {config.COLLECTION_YEARS}
        """)

    st.markdown("---")

    # Help section
    st.header("도움말")

    with st.expander("데이터 수집이 실패하는 경우"):
        st.markdown("""
        1. **API 키 확인**: `.env` 파일에 올바른 DART API 키가 설정되어 있는지 확인하세요.
        2. **네트워크 확인**: 인터넷 연결을 확인하세요.
        3. **캐시 삭제**: 캐시를 삭제하고 다시 시도하세요.
        4. **로그 확인**: `dart_analysis.log` 파일에서 상세한 오류 메시지를 확인하세요.
        """)

    with st.expander("분류된 회사가 너무 적거나 많은 경우"):
        st.markdown("""
        1. **기준 조정**: `config.py`에서 `CLASSIFICATION_THRESHOLD` 값을 조정하세요.
           - 값을 낮추면 더 많은 회사가 분류됩니다.
           - 값을 높이면 더 엄격하게 분류됩니다.
        2. **키워드 추가**: `CLASSIFICATION_KEYWORDS`에 관련 키워드를 추가하세요.
        3. **KSIC 코드 추가**: `COSMETIC_KSIC_CODES`에 관련 산업 코드를 추가하세요.
        """)

    with st.expander("데이터 갱신 주기"):
        st.markdown("""
        - **회사 분류**: 분기별 1회 (새로운 회사 상장 반영)
        - **재무 데이터**: 분기별 1회 (분기 실적 발표 후)
        - **캐시**: 자동으로 만료되므로 수동 삭제 불필요
        """)

if __name__ == "__main__":
    main()
