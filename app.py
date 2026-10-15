import datetime
import FinanceDataReader as fdr
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# 페이지 설정 (와이드 레이아웃, 깔끔한 리포트 톤)
st.set_page_config(
    page_title="국내 증시 및 개별 종목 통합 분석 리포트",
    page_icon="📈",
    layout="wide",
)

# 전문 애널리스트 리포트풍 스타일링 적용 (CSS - 요약 박스 글자 크기 대폭 확대)
st.markdown(
    """
    <style>
    .main { background-color: #f8f9fa; }
    .reportview-container { background-color: #f8f9fa; }
    
    html, body, [class*="css"] {
        font-size: 19px !important;
        font-family: 'Apple SD Gothic Neo', sans-serif;
        color: #1e293b;
    }
    
    h1 { font-size: 2.4rem !important; color: #0f172a; }
    h2 { font-size: 1.8rem !important; color: #1e293b; margin-top: 30px; font-weight: 700; }
    h3 { font-size: 1.4rem !important; color: #334155; font-weight: 600; margin-top: 20px; }
    
    p, span, label, div {
        font-size: 1.15rem !important;
    }
    
    .stTextInput label, .stFileUploader label { font-size: 1.2rem !important; font-weight: bold; color: #1e293b; }
    .stTextInput input { font-size: 1.2rem !important; background-color: #ffffff; color: #1e293b; }
    
    .summary-card {
        padding: 22px;
        border-radius: 8px;
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: right;
    }
    
    /* 요약 박스 글자 크기 및 가독성 대폭 강화 */
    .insight-box {
        padding: 30px;
        border-radius: 10px;
        background-color: #ffffff;
        border-left: 6px solid #2563eb;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        margin-top: 25px;
        margin-bottom: 30px;
        font-size: 1.3rem !important;
        line-height: 1.8;
    }
    .insight-box h4 { font-size: 1.5rem !important; margin-bottom: 15px; color: #0f172a; }
    .insight-box ul { margin-bottom: 0px; }
    .insight-box li { margin-bottom: 15px; font-size: 1.25rem !important; }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("📊 국내 증시 및 종목 통합 수급 분석 리포트")
st.markdown(
    "**Market Intelligence & Individual Stock Flow Dashboard** | 종합 애널리스트 리포트"
)
st.markdown("---")

today = datetime.datetime.now()
start_date_short = (today - datetime.timedelta(days=90)).strftime("%Y-%m-%d")
end_date = today.strftime("%Y-%m-%d")


@st.cache_data(ttl=3600)
def load_market_index(start, end):
    try:
        df_kospi = fdr.DataReader("KS11", start, end)
        return df_kospi
    except Exception as e:
        return None


@st.cache_data(ttl=86400)
def get_krx_stocks():
    try:
        df_krx = fdr.StockListing("KRX")
        return df_krx
    except Exception as e:
        return None


def resolve_ticker(query):
    query = query.strip()
    if query.isdigit():
        return query

    df_krx = get_krx_stocks()
    if df_krx is not None and not df_krx.empty:
        match = df_krx[df_krx["Name"] == query]
        if not match.empty:
            return str(match.iloc[0]["Code"]).zfill(6)

        match_partial = df_krx[df_krx["Name"].str.contains(query, na=False)]
        if not match_partial.empty:
            return str(match_partial.iloc[0]["Code"]).zfill(6)

    stock_dict = {
        "삼성전자": "005930",
        "삼성전기": "009150",
        "SK하이닉스": "000660",
        "LG에너지솔루션": "373220",
        "삼성바이오로직스": "207940",
        "현대차": "005380",
        "기아": "000270",
        "셀트리온": "068270",
        "KB금융": "105560",
        "POSCO홀딩스": "005490",
        "NAVER": "035420",
        "LG화학": "051910",
        "신한지주": "055550",
        "삼성생명": "032830",
        "하나금융지주": "086790",
        "카카오": "035720",
    }
    return stock_dict.get(query, query)


with st.spinner("시장 데이터를 로딩 중입니다..."):
    df_kospi = load_market_index(start_date_short, end_date)

if df_kospi is not None and not df_kospi.empty:

    st.markdown("### 🔍 분석 설정 및 코스피 전체 수급 데이터 업로드")
    col_c1, col_c2 = st.columns([1, 2])

    with col_c1:
        user_input = st.text_input(
            "종목명 또는 코드 입력", "SK하이닉스", placeholder="예: SK하이닉스 또는 000660"
        )
        target_ticker = resolve_ticker(user_input)
        st.write(f"**적용된 종목 코드:** `{target_ticker}`")

    with col_c2:
        uploaded_file = st.file_uploader(
            "📁 코스피 전체 투자자별 매매동향 파일 업로드 (첨부하신 엑셀/CSV)",
            type=["xlsx", "xls", "csv"],
            help="방금 다운로드하신 코스피 전체 수급 데이터를 업로드해주세요.",
        )

    st.markdown("---")

    df_stock = fdr.DataReader(target_ticker, start_date_short, end_date)

    if df_stock is not None and not df_stock.empty:
        combined_df = pd.merge(
            df_kospi[["Close"]].rename(columns={"Close": "KOSPI"}),
            df_stock[["Close", "Volume"]].rename(
                columns={"Close": "Stock_Close", "Volume": "Volume"}
            ),
            left_index=True,
            right_index=True,
            how="inner",
        )

        combined_df["Flow_Power"] = (
            combined_df["Stock_Close"].diff() * combined_df["Volume"]
        )


        def apply_large_font_to_fig(fig, title_text, height=450):
            fig.update_layout(
                title=dict(text=title_text, font=dict(size=20, color="#1e293b")),
                xaxis=dict(
                    title_font=dict(size=16),
                    tickfont=dict(size=14),
                    showgrid=True,
                ),
                yaxis=dict(
                    title_font=dict(size=16),
                    tickfont=dict(size=14),
                    showgrid=True,
                ),
                hovermode="x unified",
                height=height,
                plot_bgcolor="white",
                paper_bgcolor="white",
                legend=dict(font=dict(size=15)),
            )
            return fig


        # ==========================================
        # 1. 지수와 주가 비교 듀얼 차트
        # ==========================================
        st.subheader("1. 시장 연동성 분석 (KOSPI 지수 vs 개별 종목 주가)")
        st.markdown(
            "_좌측 축은 코스피 지수 흐름을 나타내며, 우측 축은 선택하신 종목의 주가 추이를 보여줍니다._"
        )

        fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
        fig_dual.add_trace(
            go.Scatter(
                x=combined_df.index,
                y=combined_df["KOSPI"],
                name="KOSPI 지수",
                line=dict(color="#64748b", width=2.5, dash="dot"),
            ),
            secondary_y=False,
        )
        fig_dual.add_trace(
            go.Scatter(
                x=combined_df.index,
                y=combined_df["Stock_Close"],
                name=f"{user_input} 주가",
                line=dict(color="#2563eb", width=3),
            ),
            secondary_y=True,
        )

        fig_dual = apply_large_font_to_fig(
            fig_dual, f"<b>KOSPI 및 [{user_input}] 가격 비교 차트</b>", height=450
        )
        fig_dual.update_yaxes(
            title_text="<b>KOSPI 지수</b>",
            secondary_y=False,
            title_font=dict(size=16),
            tickfont=dict(size=14),
        )
        fig_dual.update_yaxes(
            title_text="<b>종목 주가 (원)</b>",
            secondary_y=True,
            title_font=dict(size=16),
            tickfont=dict(size=14),
            showgrid=False,
        )

        st.plotly_chart(fig_dual, use_container_width=True)

        # ==========================================
        # 2. 거래량 막대그래프
        # ==========================================
        st.subheader("2. 개별 종목 거래량 분석 (일별 거래량)")
        st.markdown(
            "_선택한 종목의 일별 거래량 변동 추이를 명확하게 파악할 수 있는 바 차트입니다._"
        )

        fig_vol = go.Figure()
        fig_vol.add_trace(
            go.Bar(
                x=combined_df.index,
                y=combined_df["Volume"],
                name="거래량",
                marker_color="#0ea5e9",
            )
        )
        fig_vol = apply_large_font_to_fig(
            fig_vol, f"<b>[{user_input}] 일별 거래량 추이</b>", height=380
        )
        fig_vol.update_yaxes(title_text="<b>거래량</b>")
        st.plotly_chart(fig_vol, use_container_width=True)

        # ==========================================
        # 3. 수급 막대그래프 (자금 유출입 추정 강도)
        # ==========================================
        st.subheader("3. 수급 강도 분석 (자금 유출입 추정)")
        st.markdown(
            "_가격 변동과 거래량을 결합한 단기 자금 유출입 강도입니다. (빨강: 매수 우위 / 파랑: 매도 우위)_"
        )

        fig_flow = go.Figure()
        colors = [
            "#dc2626" if val > 0 else "#2563eb"
            for val in combined_df["Flow_Power"]
        ]
        fig_flow.add_trace(
            go.Bar(
                x=combined_df.index,
                y=combined_df["Flow_Power"],
                name="수급 강도",
                marker_color=colors,
            )
        )
        fig_flow = apply_large_font_to_fig(
            fig_flow,
            f"<b>[{user_input}] 자금 유출입 추정 강도</b>",
            height=380,
        )
        fig_flow.update_yaxes(title_text="<b>강도 지수</b>")
        st.plotly_chart(fig_flow, use_container_width=True)

        # ==========================================
        # 4. 코스피 전체 최근 2년 누적 외국인 순매수 그래프 (업로드 파일 연동)
        # ==========================================
        st.markdown(
            "### 4. 📈 코스피 전체 외국인 순매수 (금액) — 2024년 11월부터의 누적 및 4주 이동평균선 차트"
        )

        df_uploaded = None
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df_uploaded = pd.read_csv(uploaded_file)
                else:
                    df_uploaded = pd.read_excel(uploaded_file)
            except Exception as e:
                st.error(f"파일 읽기 오류: {e}")

        if df_uploaded is not None and not df_uploaded.empty:
            date_col = next(
                (c for c in df_uploaded.columns if "일자" in str(c) or "날짜" in str(c)),
                df_uploaded.columns[0],
            )
            frgn_col = next(
                (c for c in df_uploaded.columns if "외국인" in str(c)),
                df_uploaded.columns[10],
            )

            df_uploaded[date_col] = pd.to_datetime(
                df_uploaded[date_col], errors="coerce"
            )
            df_uploaded = (
                df_uploaded.dropna(subset=[date_col])
                .sort_values(date_col)
                .set_index(date_col)
            )

            if df_uploaded[frgn_col].dtype == object:
                df_uploaded[frgn_col] = (
                    df_uploaded[frgn_col]
                    .astype(str)
                    .str.replace(",", "")
                    .str.replace("+-", "-")
                )

            df_uploaded["외국인순매수_원"] = (
                pd.to_numeric(df_uploaded[frgn_col], errors="coerce").fillna(0)
                * 1e8
            )

            df_uploaded = df_uploaded[
                df_uploaded.index >= pd.to_datetime("2024-11-01")
            ]

            df_uploaded["누적외인순매수금액"] = df_uploaded["외국인순매수_원"].cumsum()
            df_uploaded["4w_ma"] = (
                df_uploaded["누적외인순매수금액"].rolling(window=20).mean()
            )

            fig_foreign = go.Figure()
            fig_foreign.add_trace(
                go.Scatter(
                    x=df_uploaded.index,
                    y=df_uploaded["누적외인순매수금액"],
                    mode="lines+markers",
                    name="외국인순매수누적",
                    line=dict(color="#ef4444", width=2.5),
                    marker=dict(size=5, symbol="square"),
                )
            )
            fig_foreign.add_trace(
                go.Scatter(
                    x=df_uploaded.index,
                    y=df_uploaded["4w_ma"],
                    mode="lines",
                    name="4w ma",
                    line=dict(color="#3b82f6", width=3),
                )
            )

            fig_foreign = apply_large_font_to_fig(
                fig_foreign, "<b>코스피 전체 외국인 순매수 누적 (원)</b>", height=450
            )
            fig_foreign.update_yaxes(title_text="<b>누적 순매수 금액 (원)</b>")

            col_g1, col_g2 = st.columns([3, 1])

            with col_g1:
                st.plotly_chart(fig_foreign, use_container_width=True)

            with col_g2:
                st.markdown("<br><br>", unsafe_allow_html=True)
                latest_cum = df_uploaded["누적외인순매수금액"].iloc[-1]
                latest_today = df_uploaded["외국인순매수_원"].iloc[-1]
                prev_day = (
                    df_uploaded["외국인순매수_원"].iloc[-2]
                    if len(df_uploaded) > 1
                    else 0
                )

                def format_trillion(val):
                    if abs(val) >= 1e12:
                        return f"{val / 1e12:+,.2f}조 원"
                    elif abs(val) >= 1e8:
                        return f"{val / 1e8:+,.1f}억 원"
                    else:
                        return f"{val:+,.0f} 원"

                today_color = "#ef4444" if latest_today > 0 else "#3b82f6"
                cum_color = "#ef4444" if latest_cum > 0 else "#3b82f6"

                summary_html = f"""
                <div class="summary-card">
                    <p style="font-size:1.1rem; color:{cum_color}; margin-bottom:8px; font-weight:bold;">누적 / {format_trillion(latest_cum)}</p>
                    <hr style="margin: 10px 0; border:0; border-top:1px solid #e2e8f0;">
                    <p style="font-size:1.05rem; color:{today_color}; margin-bottom:5px;">오늘 / {format_trillion(latest_today)}</p>
                    <p style="font-size:1.05rem; color:#64748b; margin-bottom:0px;">전일 / {format_trillion(prev_day)}</p>
                </div>
                """
                st.markdown(summary_html, unsafe_allow_html=True)
        else:
            st.info(
                "📁 상단 파일 업로드 창에 첨부해주신 **`data_5652_20261015.xlsx`** 파일을 업로드해 주세요. 업로드 즉시 코스피 전체 외국인 2년치 누적 수급 차트와 우측 하단 요약 카드가 완벽하게 그려집니다."
            )

        # ==========================================
        # 5 -> 4. 현재 수급 상황 분석 요약 (글자 크기 확대)
        # ==========================================
        st.markdown("---")
        st.subheader("4. 📝 현재 수급 상황 및 체력 분석 요약")

        recent_return = (
            (combined_df["Stock_Close"].iloc[-1] - combined_df["Stock_Close"].iloc[-5])
            / combined_df["Stock_Close"].iloc[-5]
        ) * 100
        recent_vol_avg = combined_df["Volume"].tail(5).mean()
        prev_vol_avg = combined_df["Volume"].iloc[-10:-5].mean()
        vol_change_pct = ((recent_vol_avg - prev_vol_avg) / prev_vol_avg) * 100
        latest_flow = combined_df["Flow_Power"].iloc[-1]

        flow_status = (
            "순유입(매수 우위) 압력" if latest_flow > 0 else "순유출(매도 우위) 압력"
        )
        vol_status = (
            "증가세를 보이며 시장 참여자의 관심이 집중"
            if vol_change_pct > 0
            else "소강상태를 보이며 관망세가 우세"
        )

        comment_html = f"""
        <div class="insight-box">
            <h4>📌 <b>[{user_input}] 현재 수급 상황 및 시장 체력 진단</b></h4>
            <ul>
                <li><b>1. 주가 연동성 동향</b>: 최근 5거래일 동안 [{user_input}] 종목은 약 <b>{recent_return:.2f}%</b>의 등락률을 기록하며 코스피 지수 흐름과 연동되고 있습니다.</li>
                <li><b>2. 거래량 및 참여도</b>: 직전 대비 거래량이 평균 <b>{vol_change_pct:+.1f}%</b> 변화하여 현재 시장 참여자들의 관심도는 <b>{vol_status}</b>인 상태입니다.</li>
                <li><b>3. 단기 수급 압력</b>: 최근 가격 변동과 거래량을 결합한 단기 자금 유출입 추정 결과, 현재 수급은 <b>{flow_status}</b>를 나타내고 있습니다.</li>
            </ul>
        </div>
        """
        st.markdown(comment_html, unsafe_allow_html=True)

    else:
        st.warning("종목 데이터를 불러오지 못했습니다.")
else:
    st.error("코스피 시장 지수 데이터를 불러오는 데 실패했습니다.")