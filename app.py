# -*- coding: utf-8 -*-
"""TaDa LinkedIn Ads 儀表板（雲端版）

資料源：Google Sheet 的 RawData 分頁（由 build_sheet.py 每天自動更新）
部署：Streamlit Community Cloud
存取控制：密碼登入
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from auth import require_password
from data import load_rawdata, load_ad_mapping

st.set_page_config(
    page_title="TaDa LinkedIn Ads 儀表板",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

require_password()

REGION_COLORS = {"歐洲": "#0077B5", "拉美": "#00A651", "非洲": "#E8A020", "亞洲": "#9B59B6"}


# ──────────────────────────────────────────────────────────────────────
#  通用元件
# ──────────────────────────────────────────────────────────────────────
def show_kpis(df: pd.DataFrame) -> None:
    spent = df["花費"].sum()
    imp = df["曝光"].sum()
    clicks = df["點擊"].sum()
    eng = df["互動"].sum()
    reach = df["觸及"].sum()
    follows = df["追蹤"].sum()
    ctr = clicks / imp * 100 if imp > 0 else 0
    eng_rate = eng / imp * 100 if imp > 0 else 0
    cpm = df["CPM"].mean() if "CPM" in df.columns else 0
    cpf = spent / follows if follows > 0 else 0
    cpe = spent / eng if eng > 0 else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("💰 總花費", f"${spent:,.0f}")
    c2.metric("👁️ 總曝光", f"{imp:,.0f}")
    c3.metric("🖱️ 總點擊", f"{clicks:,.0f}")
    c4.metric("👥 觸及人數", f"{reach:,.0f}")
    c5.metric("📡 平均CPM", f"${cpm:.2f}")

    c6, c7, c8, c9, c10 = st.columns(5)
    c6.metric("📣 CTR", f"{ctr:.2f}%")
    c7.metric("❤️ 互動率", f"{eng_rate:.2f}%")
    c8.metric("💬 CPE", f"${cpe:.2f}" if cpe > 0 else "—")
    c9.metric("➕ 追蹤數", f"{follows:,.0f}")
    c10.metric("💎 CPF", f"${cpf:.2f}" if cpf > 0 else "—")


def show_trend(df: pd.DataFrame, color: str = "#0077B5") -> None:
    daily = df.groupby("日期").agg(
        spent=("花費", "sum"),
        impressions=("曝光", "sum"),
        engagements=("互動", "sum"),
        follows=("追蹤", "sum"),
    ).reset_index()
    daily["engagement_rate"] = daily.apply(
        lambda r: r["engagements"] / r["impressions"] * 100 if r["impressions"] > 0 else 0,
        axis=1,
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=daily["日期"], y=daily["spent"], name="花費",
        marker_color=color, opacity=0.55, yaxis="y1",
        hovertemplate="💰 花費：$%{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=daily["日期"], y=daily["follows"], name="追蹤數",
        mode="lines+markers", line=dict(color="#000000", width=2.5),
        marker=dict(size=7), yaxis="y2",
        hovertemplate="➕ 追蹤數：%{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=daily["日期"], y=daily["engagement_rate"], name="互動率",
        mode="lines+markers", line=dict(color="#FF6B6B", width=2.5, dash="dot"),
        marker=dict(size=7), yaxis="y3",
        hovertemplate="❤️ 互動率：%{y:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        plot_bgcolor="white", height=380, hovermode="x unified",
        margin=dict(t=40, b=20, l=10, r=80),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=True, gridcolor="#f0f0f0", domain=[0, 0.92],
                   tickformat="%m/%d", hoverformat="%m/%d"),
        yaxis=dict(title=dict(text="花費 ($)", font=dict(color=color)),
                   showgrid=True, gridcolor="#f0f0f0", tickfont=dict(color=color)),
        yaxis2=dict(title=dict(text="追蹤數", font=dict(color="#000000")),
                    overlaying="y", side="right", showgrid=False,
                    position=0.92, tickfont=dict(color="#000000")),
        yaxis3=dict(title=dict(text="互動率 (%)", font=dict(color="#FF6B6B")),
                    overlaying="y", side="right", showgrid=False,
                    anchor="free", position=1.0, ticksuffix="%",
                    tickfont=dict(color="#FF6B6B")),
    )
    st.plotly_chart(fig, width="stretch")


def show_adset_compare(df: pd.DataFrame) -> None:
    stats = df.groupby("AdSet").agg(
        spent=("花費", "sum"),
        impressions=("曝光", "sum"),
        clicks=("點擊", "sum"),
        engagements=("互動", "sum"),
        follows=("追蹤", "sum"),
        cpm=("CPM", "mean"),
    ).reset_index()
    stats["互動率(%)"] = stats.apply(
        lambda r: r["engagements"] / r["impressions"] * 100 if r["impressions"] > 0 else 0,
        axis=1,
    )
    stats["追蹤成本($)"] = stats.apply(
        lambda r: r["spent"] / r["follows"] if r["follows"] > 0 else None, axis=1
    )
    disp = stats[["AdSet", "spent", "follows", "追蹤成本($)", "互動率(%)", "cpm"]].copy()
    disp.columns = ["Ad Set 名稱", "花費($)", "追蹤數", "追蹤成本($)", "互動率(%)", "CPM($)"]
    disp = disp.sort_values("花費($)", ascending=False).reset_index(drop=True)
    disp["花費($)"] = disp["花費($)"].apply(lambda x: f"${x:,.0f}")
    disp["追蹤數"] = disp["追蹤數"].apply(lambda x: f"{int(x):,}")
    disp["追蹤成本($)"] = disp["追蹤成本($)"].apply(
        lambda x: f"${x:.2f}" if pd.notna(x) else "—"
    )
    disp["互動率(%)"] = disp["互動率(%)"].apply(lambda x: f"{x:.2f}%")
    disp["CPM($)"] = disp["CPM($)"].apply(lambda x: f"${x:.2f}")
    st.dataframe(disp, width="stretch", hide_index=True)


def show_ad_ranking(df: pd.DataFrame) -> None:
    ad_stats = df[df["素材"].notna() & (df["素材"].astype(str) != "")].groupby(
        ["素材", "類型"]
    ).agg(
        spent=("花費", "sum"),
        impressions=("曝光", "sum"),
        clicks=("點擊", "sum"),
        engagements=("互動", "sum"),
        follows=("追蹤", "sum"),
    ).reset_index()
    ad_stats["CTR"] = ad_stats.apply(
        lambda r: r["clicks"] / r["impressions"] * 100 if r["impressions"] > 0 else 0,
        axis=1,
    )
    ad_stats["互動率"] = ad_stats.apply(
        lambda r: r["engagements"] / r["impressions"] * 100 if r["impressions"] > 0 else 0,
        axis=1,
    )
    ad_stats["CPF"] = ad_stats.apply(
        lambda r: r["spent"] / r["follows"] if r["follows"] > 0 else None, axis=1
    )

    col1, col2 = st.columns(2)
    with col1:
        top = ad_stats.sort_values("CTR", ascending=True).tail(10)
        fig = px.bar(top, x="CTR", y="素材", orientation="h",
                     title="CTR Top 10 素材", text_auto=".2f",
                     color_discrete_sequence=["#0077B5"])
        fig.update_layout(height=380, plot_bgcolor="white", showlegend=False,
                          margin=dict(t=40, b=10),
                          yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, width="stretch")
    with col2:
        top2 = ad_stats.sort_values("互動率", ascending=True).tail(10)
        fig2 = px.bar(top2, x="互動率", y="素材", orientation="h",
                      title="互動率 Top 10 素材", text_auto=".2f",
                      color_discrete_sequence=["#E8A020"])
        fig2.update_layout(height=380, plot_bgcolor="white", showlegend=False,
                           margin=dict(t=40, b=10),
                           yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig2, width="stretch")

    st.subheader("📋 素材明細表")
    disp = ad_stats.copy()
    disp.columns = ["素材名稱", "類型", "花費($)", "曝光", "點擊", "互動", "追蹤數",
                    "CTR(%)", "互動率(%)", "CPF($)"]
    disp = disp.sort_values("花費($)", ascending=False)
    for col in ["花費($)", "CTR(%)", "互動率(%)"]:
        disp[col] = disp[col].round(2)
    disp["CPF($)"] = disp["CPF($)"].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "—")
    st.dataframe(disp, width="stretch", height=350)


def show_alerts(df: pd.DataFrame) -> None:
    alerts = []
    ad_stats = df[df["素材"].notna() & (df["素材"].astype(str) != "")].groupby("素材").agg(
        impressions=("曝光", "sum"),
        clicks=("點擊", "sum"),
        spent=("花費", "sum"),
        follows=("追蹤", "sum"),
    ).reset_index()
    ad_stats["CTR"] = ad_stats.apply(
        lambda r: r["clicks"] / r["impressions"] * 100 if r["impressions"] > 0 else 0,
        axis=1,
    )
    ad_stats["CPF"] = ad_stats.apply(
        lambda r: r["spent"] / r["follows"] if r["follows"] > 0 else None, axis=1
    )

    for _, row in ad_stats.iterrows():
        if row["CTR"] < 0.5 and row["impressions"] > 1000:
            alerts.append(("⚠️", "CTR 偏低",
                           f"**{row['素材']}** CTR {row['CTR']:.2f}%，建議調整素材或受眾"))
        if row["CTR"] > 5:
            alerts.append(("🌟", "CTR 優異",
                           f"**{row['素材']}** CTR {row['CTR']:.2f}%，表現突出"))
        if row["CPF"] is not None and row["CPF"] > 20:
            alerts.append(("⚠️", "CPF 偏高",
                           f"**{row['素材']}** CPF ${row['CPF']:.2f}，追蹤成本偏高"))

    adset_stats = df.groupby("AdSet")["花費"].sum().reset_index()
    total = adset_stats["花費"].sum()
    for _, row in adset_stats.iterrows():
        pct = row["花費"] / total * 100 if total > 0 else 0
        if pct > 50:
            alerts.append(("⚠️", "預算集中",
                           f"**{row['AdSet']}** 佔總花費 {pct:.1f}%"))

    if alerts:
        for icon, cat, msg in alerts:
            color = "#fff3cd" if "⚠️" in icon else "#d1f2eb"
            st.markdown(
                f"<div style='background:{color};padding:10px 15px;border-radius:8px;"
                f"margin-bottom:6px'>{icon} <b>[{cat}]</b> {msg}</div>",
                unsafe_allow_html=True,
            )
    else:
        st.success("目前無異常警示。")


# ──────────────────────────────────────────────────────────────────────
#  週報
# ──────────────────────────────────────────────────────────────────────
def get_current_weeks():
    today = pd.Timestamp.today().normalize()
    days_since_monday = today.weekday()
    last_sunday = today - pd.Timedelta(days=days_since_monday + 1)
    last_monday = last_sunday - pd.Timedelta(days=6)
    prev_sunday = last_monday - pd.Timedelta(days=1)
    prev_monday = prev_sunday - pd.Timedelta(days=6)
    return (last_monday, last_sunday), (prev_monday, prev_sunday)


def filter_week(df, start, end):
    s = pd.Timestamp(start)
    e = pd.Timestamp(end)
    return df[(df["日期"] >= s) & (df["日期"] <= e)]


def calc_stats(df):
    if df.empty:
        return {k: "—" for k in ["Spend", "Imp", "CPM", "ENG", "ENG Rate", "CPE", "Follows", "CPF"]}
    spent = df["花費"].sum()
    imp = df["曝光"].sum()
    eng = df["互動"].sum()
    follows = df["追蹤"].sum()
    return {
        "Spend": f"${spent:,.2f}",
        "Imp": f"{int(imp):,}",
        "CPM": f"${df['CPM'].mean():.2f}",
        "ENG": f"{int(eng):,}",
        "ENG Rate": f"{eng / imp * 100:.2f}%" if imp > 0 else "—",
        "CPE": f"${spent / eng:.2f}" if eng > 0 else "—",
        "Follows": f"{int(follows):,}",
        "CPF": f"${spent / follows:.2f}" if follows > 0 else "—",
    }


def show_weekly_report(df_raw: pd.DataFrame) -> None:
    (w1_mon, w1_sun), (w0_mon, w0_sun) = get_current_weeks()
    col_a, col_b = st.columns(2)
    with col_a:
        this_week = st.date_input("📅 本週", value=(w1_mon.date(), w1_sun.date()), key="wk_this")
    with col_b:
        prev_week = st.date_input("📅 前一週", value=(w0_mon.date(), w0_sun.date()), key="wk_prev")
    if len(this_week) != 2 or len(prev_week) != 2:
        st.warning("請選擇完整的週次範圍（起～迄）")
        return
    tw_start, tw_end = pd.Timestamp(this_week[0]), pd.Timestamp(this_week[1])
    pw_start, pw_end = pd.Timestamp(prev_week[0]), pd.Timestamp(prev_week[1])
    st.caption(
        f"本週：{tw_start.strftime('%m/%d')} ~ {tw_end.strftime('%m/%d')}　｜　"
        f"前一週：{pw_start.strftime('%m/%d')} ~ {pw_end.strftime('%m/%d')}"
    )
    st.markdown("---")

    tw = filter_week(df_raw, tw_start, tw_end)
    pw = filter_week(df_raw, pw_start, pw_end)

    st.subheader("📊 週報對比表")
    SECTIONS = [
        ("三區總計", None, "#D6EEF8"),
        ("歐洲", "歐洲", "#D6EAF8"),
        ("拉美", "拉美", "#D5F5E3"),
        ("非洲", "非洲", "#FDEBD0"),
    ]
    rows, bg_colors = [], []
    for label, region_key, bg in SECTIONS:
        tw_r = tw if region_key is None else tw[tw["地區"] == region_key]
        pw_r = pw if region_key is None else pw[pw["地區"] == region_key]
        rows.append({"區域": label, "週別": "前一週", **calc_stats(pw_r)})
        rows.append({"區域": "", "週別": "本週", **calc_stats(tw_r)})
        bg_colors += [bg, bg]

    table_df = pd.DataFrame(rows)

    def apply_bg(row):
        return [f"background-color: {bg_colors[row.name]}" for _ in row]

    styled = table_df.style.apply(apply_bg, axis=1)
    st.dataframe(styled, hide_index=True, width="stretch", height=370)

    st.markdown("---")
    st.subheader("🎨 各地區素材表現亮點（本週）")
    for region_label, icon in [("歐洲", "🇪🇺"), ("拉美", "🌎"), ("非洲", "🌍")]:
        color = REGION_COLORS[region_label]
        st.markdown(
            f"<div style='background:{color};color:white;padding:6px 14px;"
            f"border-radius:6px;font-weight:bold;margin-bottom:8px'>"
            f"{icon} {region_label}</div>",
            unsafe_allow_html=True,
        )
        tw_r = tw[tw["地區"] == region_label]
        if tw_r.empty:
            st.info(f"本週無{region_label}資料")
            continue
        ad = tw_r[tw_r["素材"].notna() & (tw_r["素材"].astype(str) != "")].groupby("素材").agg(
            spent=("花費", "sum"),
            impressions=("曝光", "sum"),
            engagements=("互動", "sum"),
            follows=("追蹤", "sum"),
        ).reset_index()
        ad["ENG Rate"] = ad.apply(
            lambda r: r["engagements"] / r["impressions"] * 100 if r["impressions"] > 0 else 0,
            axis=1,
        )
        ad["CPF"] = ad.apply(
            lambda r: r["spent"] / r["follows"] if r["follows"] > 0 else None, axis=1
        )
        top_eng = ad.nlargest(3, "ENG Rate")
        top_fol = ad.nlargest(3, "follows")
        low_eng = ad[ad["impressions"] > 500].nsmallest(3, "ENG Rate")

        c1, c2, c3 = st.columns(3)
        for widget, title, badge, data in [
            (c1, "ENG Rate 最高", "🌟", top_eng),
            (c2, "Follows 最多", "➕", top_fol),
            (c3, "ENG Rate 最低", "⚠️", low_eng),
        ]:
            with widget:
                st.markdown(f"**{badge} {title}**")
                if data.empty:
                    st.caption("無資料（曝光不足 500）")
                else:
                    disp = data[["素材", "ENG Rate", "follows", "CPF"]].copy()
                    disp.columns = ["素材", "ENG Rate(%)", "Follows", "CPF($)"]
                    disp["ENG Rate(%)"] = disp["ENG Rate(%)"].apply(lambda x: f"{x:.2f}%")
                    disp["CPF($)"] = disp["CPF($)"].apply(
                        lambda x: f"${x:.2f}" if pd.notna(x) else "—"
                    )
                    st.dataframe(disp, hide_index=True, width="stretch")
        st.markdown("")


# ──────────────────────────────────────────────────────────────────────
#  主程式
# ──────────────────────────────────────────────────────────────────────
df_raw = load_rawdata()
if df_raw is None or df_raw.empty:
    st.error("無法載入資料，請檢查 Google Sheet 連線設定。")
    st.stop()

name_map, type_map = load_ad_mapping()
df_raw["AdID"] = df_raw["AdID"].astype(str)
df_raw["素材"] = df_raw["AdID"].map(name_map).fillna(df_raw["素材"])
df_raw["類型"] = df_raw["AdID"].map(type_map).fillna("—")

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/c/ca/LinkedIn_logo_initials.png", width=40)
    st.title("篩選條件")
    min_date = df_raw["日期"].min()
    max_date = df_raw["日期"].max()
    date_range = st.date_input(
        "日期範圍",
        value=(min_date.date(), max_date.date()),
        min_value=min_date.date(),
        max_value=max_date.date(),
    )
    st.markdown("---")
    st.caption(f"資料範圍：{min_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')}")
    st.caption(f"頁面開啟時間：{datetime.now().strftime('%Y/%m/%d %H:%M')}")
    if st.button("🔄 重新載入資料"):
        st.cache_data.clear()
        st.rerun()

df_all = df_raw.copy()
if len(date_range) == 2:
    df_all = df_all[
        (df_all["日期"].dt.date >= date_range[0])
        & (df_all["日期"].dt.date <= date_range[1])
    ]

if not df_all.empty:
    last_day = df_all["日期"].max()
    df_all = df_all[df_all["日期"] < last_day]

df_eu = df_all[df_all["地區"] == "歐洲"]
df_la = df_all[df_all["地區"] == "拉美"]
df_af = df_all[df_all["地區"] == "非洲"]

st.title("📊 TaDa LinkedIn Ads 儀表板")
st.caption(
    f"Campaign：International_Engaement、Website visits_20260617　｜　"
    f"資料：{min_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')}"
)
st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["🌐 三區總覽", "🇪🇺 歐洲", "🌎 拉美", "🌍 非洲", "📅 週報"]
)

with tab1:
    st.subheader("📊 整體 KPI")
    show_kpis(df_all)
    st.markdown("---")
    st.subheader("📈 每日趨勢")
    show_trend(df_all, color="#0077B5")
    st.markdown("---")

    st.subheader("🌍 三區花費比較")
    region_stats = df_all.groupby("地區").agg(
        spent=("花費", "sum"),
        impressions=("曝光", "sum"),
        clicks=("點擊", "sum"),
        reach=("觸及", "sum"),
    ).reset_index()
    region_stats["CTR"] = region_stats.apply(
        lambda r: r["clicks"] / r["impressions"] * 100 if r["impressions"] > 0 else 0,
        axis=1,
    )
    col1, col2, col3 = st.columns(3)
    with col1:
        fig = px.pie(region_stats, values="spent", names="地區", title="花費分布",
                     color="地區", color_discrete_map=REGION_COLORS)
        fig.update_layout(height=300)
        st.plotly_chart(fig, width="stretch")
    with col2:
        fig2 = px.pie(region_stats, values="impressions", names="地區", title="曝光分布",
                      color="地區", color_discrete_map=REGION_COLORS)
        fig2.update_layout(height=300)
        st.plotly_chart(fig2, width="stretch")
    with col3:
        fig3 = px.pie(region_stats, values="clicks", names="地區", title="點擊分布",
                      color="地區", color_discrete_map=REGION_COLORS)
        fig3.update_layout(height=300)
        st.plotly_chart(fig3, width="stretch")

    st.subheader("📋 三區數據對比")
    region_stats["CTR(%)"] = region_stats["CTR"].round(2)
    region_stats["花費($)"] = region_stats["spent"].round(0)
    region_stats["曝光"] = region_stats["impressions"].astype(int)
    region_stats["點擊"] = region_stats["clicks"].astype(int)
    region_stats["觸及"] = region_stats["reach"].astype(int)
    disp_reg = region_stats[["地區", "花費($)", "曝光", "點擊", "CTR(%)", "觸及"]]
    st.dataframe(disp_reg, width="stretch", hide_index=True)

    st.markdown("---")
    st.subheader("⚠️ 全區警示彙總")
    show_alerts(df_all)

for tab, df_region, label, icon, color_key in [
    (tab2, df_eu, "歐洲", "🇪🇺", "歐洲"),
    (tab3, df_la, "拉美", "🌎", "拉美"),
    (tab4, df_af, "非洲", "🌍", "非洲"),
]:
    with tab:
        if df_region.empty:
            st.warning(f"此期間無{label}資料。")
            continue
        st.subheader(f"{icon} {label} KPI")
        show_kpis(df_region)
        st.markdown("---")
        st.subheader("📈 每日趨勢")
        show_trend(df_region, color=REGION_COLORS[color_key])
        st.markdown("---")
        st.subheader("📦 Ad Set 比較")
        show_adset_compare(df_region)
        st.markdown("---")
        st.subheader("🎨 素材表現")
        show_ad_ranking(df_region)
        st.markdown("---")
        st.subheader("⚠️ 自動警示")
        show_alerts(df_region)

with tab5:
    show_weekly_report(df_raw)
