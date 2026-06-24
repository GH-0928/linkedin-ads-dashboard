# -*- coding: utf-8 -*-
"""Google Sheet 資料載入。

讀 RawData 分頁取得每日廣告數據,並從 Drive 上的 ad_mapping.csv 取得素材名稱對照。
所有存取使用 Service Account(secrets 中的 gcp_service_account 區段)。
"""
import io
from typing import Tuple

import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SHEET_ID = "1Y4wuqUAeLdZ6Qz7WtEEr6F_s15jgO_OxedhMa46vkNs"
RAWDATA_TAB = "RawData"
AD_MAPPING_FILE_ID = "1RmHL-dsATlfkmxaWn9nXy-kK_yKTmC9a"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def _get_credentials() -> Credentials:
    info = dict(st.secrets["gcp_service_account"])
    return Credentials.from_service_account_info(info, scopes=SCOPES)


@st.cache_resource
def _sheets_service():
    return build("sheets", "v4", credentials=_get_credentials(), cache_discovery=False)


@st.cache_resource
def _drive_service():
    return build("drive", "v3", credentials=_get_credentials(), cache_discovery=False)


@st.cache_data(ttl=600)
def load_rawdata() -> pd.DataFrame:
    """讀 RawData 分頁,回傳整理後的 DataFrame。"""
    svc = _sheets_service()
    result = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range=f"{RAWDATA_TAB}!A:M",
        valueRenderOption="UNFORMATTED_VALUE",
        dateTimeRenderOption="FORMATTED_STRING",
    ).execute()
    values = result.get("values", [])
    if not values:
        return pd.DataFrame()
    header, rows = values[0], values[1:]
    df = pd.DataFrame(rows, columns=header)

    df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
    for col in ["花費", "曝光", "點擊", "互動", "追蹤", "觸及", "CPM"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    if "AdID" in df.columns:
        df["AdID"] = df["AdID"].astype(str)
    df = df.dropna(subset=["日期"])
    return df


@st.cache_data(ttl=3600)
def load_ad_mapping() -> Tuple[dict, dict]:
    """從 Drive 讀 ad_mapping.csv,回傳 (name_map, type_map) 兩個字典。"""
    try:
        svc = _drive_service()
        content = svc.files().get_media(fileId=AD_MAPPING_FILE_ID).execute()
        m = pd.read_csv(io.BytesIO(content), dtype={"ad_id": str})
        name_map = dict(zip(m["ad_id"], m["素材名稱"]))
        type_map = dict(zip(m["ad_id"], m["類型"]))
        return name_map, type_map
    except Exception as e:
        st.warning(f"無法載入 ad_mapping:{e}")
        return {}, {}
