# 部署步驟(階段 1)

預計動手時間 **15-20 分鐘**。完成後你會有一個 `https://xxx.streamlit.app` 公開網址,
用密碼登入後看到完整儀表板。

---

## 步驟 A:申請 Google Service Account(讀 Sheet 用,5 分鐘)

1. 打開 https://console.cloud.google.com/
2. 左上角專案選單 → **「新增專案」**
   - 專案名稱:`linkedin-dashboard`(隨意)
   - 建立 → 等 30 秒
3. 確保左上角已切換到新專案
4. 進左側選單 → **「API 與服務」 → 「啟用 API 和服務」**
   - 搜尋 **Google Sheets API** → 啟用
   - 搜尋 **Google Drive API** → 啟用
5. 進左側選單 → **「API 與服務」 → 「憑證」**
   - 上方點 **「+ 建立憑證」 → 「服務帳戶」**
   - 名稱:`dashboard-reader`
   - **建立並繼續** → 角色不選(跳過) → 完成
6. 在憑證頁面找到剛建立的 `dashboard-reader@xxx.iam.gserviceaccount.com`
   - 點進去 → 上方 **「金鑰」** 分頁 → **「新增金鑰」 → 「建立新的金鑰」 → JSON**
   - 下載一個 JSON 檔案,**好好保管**(裡面是私鑰)
7. **複製這個 service account 的 email**(`xxx@xxx.iam.gserviceaccount.com`),下一步要用

## 步驟 B:把 Sheet 共用給 Service Account(1 分鐘)

1. 打開 Google Sheet:
   https://docs.google.com/spreadsheets/d/1Y4wuqUAeLdZ6Qz7WtEEr6F_s15jgO_OxedhMa46vkNs
2. 右上角 **「共用」** → 貼上 Service Account 的 email → 權限選 **「檢視者」** → 傳送
3. 同樣動作:把 Drive 上的 `ad_mapping.csv`(file id `1RmHL-dsATlfkmxaWn9nXy-kK_yKTmC9a`)
   也共用給同一個 email,權限「檢視者」

## 步驟 C:推 code 到 GitHub(5 分鐘)

1. 打開 https://github.com/new
2. Repository name: `linkedin-ads-dashboard`
3. 勾選 **Private**
4. 不勾選 Add README / .gitignore / license(我們已經有了)
5. **Create repository**
6. 建完後,複製右上角顯示的 git URL(類似 `https://github.com/GH-0928/linkedin-ads-dashboard.git`)
7. 回到本機 PowerShell,執行(假設專案在 Desktop):

   ```powershell
   cd C:\Users\garyhuang\Desktop\linkedin-ads-dashboard-web
   git init
   git add .
   git commit -m "初始化:LinkedIn Ads 儀表板雲端版"
   git branch -M main
   git remote add origin https://github.com/GH-0928/linkedin-ads-dashboard.git
   git push -u origin main
   ```

   第一次 push 會跳出 GitHub 登入視窗,用瀏覽器授權即可。

## 步驟 D:部署到 Streamlit Community Cloud(5 分鐘)

1. 打開 https://share.streamlit.io/ → 用 GitHub 登入
2. 右上角 **「New app」**
3. 選擇:
   - Repository: `GH-0928/linkedin-ads-dashboard`
   - Branch: `main`
   - Main file path: `app.py`
4. 點 **「Advanced settings」**
5. 在 **Secrets** 框內貼入(替換 `<...>` 部分):

   ```toml
   [auth]
   password = "<你要設的密碼>"

   [gcp_service_account]
   # 把步驟 A 下載的 JSON 內容貼進來
   # 注意:private_key 必須保留 \n 換行符,寫成單行字串
   ```

   **小訣竅**:JSON 轉 toml 的最簡單方法:打開下載的 JSON,
   把每個 `"key": "value"` 改成 `key = "value"`(去掉 key 的引號),逗號改成換行。
   `private_key` 那行整段照貼即可(包含 `\n`)。

6. **Deploy!** → 等 2-3 分鐘建置完成
7. 完成後會得到 `https://linkedin-ads-dashboard-xxxxxx.streamlit.app` 網址

## 完成驗收

- 開啟網址 → 看到密碼登入頁
- 輸入密碼 → 看到完整儀表板(三區總覽、歐洲、拉美、非洲、週報)
- 側邊欄日期篩選正常運作

---

## 階段 2 預告(等階段 1 跑順)

把上面的 Streamlit Cloud 網址搬到 Cloud Run + Cloudflare,綁定 `ads.garichy.com`。
這部分等階段 1 完成後我們再展開。
