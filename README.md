# TaDa LinkedIn Ads 儀表板(雲端版)

公開網址的 Streamlit 儀表板,資料源為 Google Sheet
`1Y4wuqUAeLdZ6Qz7WtEEr6F_s15jgO_OxedhMa46vkNs` 的 `RawData` 分頁
(由本機 `Auto_Claude/linkedin_ads/dashboard_sheet/build_sheet.py` 每天自動更新)。

## 部署

部署步驟與 Service Account 申請流程詳見 [`SETUP.md`](./SETUP.md)。

## 本機測試(可選)

```powershell
pip install -r requirements.txt
# 把 .streamlit/secrets.toml.example 複製為 .streamlit/secrets.toml 並填上實際值
streamlit run app.py
```

## 檔案結構

```
linkedin-ads-dashboard-web/
├── app.py                  Streamlit 主程式
├── auth.py                 密碼登入閘
├── data.py                 Google Sheet / Drive 資料載入
├── requirements.txt
├── .gitignore
├── .streamlit/
│   ├── config.toml         主題設定
│   └── secrets.toml.example 密碼與 Service Account 範本(實際值放雲端)
└── SETUP.md                部署步驟
```
