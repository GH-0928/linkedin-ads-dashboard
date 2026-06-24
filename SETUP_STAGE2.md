# 階段 2 部署步驟:Cloud Run + Cloudflare 綁網域

**目標**:把儀表板搬到 Google Cloud Run,綁 `tadalinkedin.garichy.com` 子網域

預計動手時間 **25-30 分鐘**

---

## 前置確認

- [x] 已綁信用卡到 Google Cloud
- [x] `garichy.com` 由 Cloudflare 管理
- [x] Service Account JSON 內容已知(我們之前用過,值都在你下載的 JSON 檔或對話中)

---

## 步驟 1:把 Secrets 上傳到 Google Secret Manager

Cloud Run 需要把密碼和 Service Account 注入容器,我們用 Secret Manager 管理。

### 1-1. 啟用 Secret Manager API

打開 https://console.cloud.google.com/apis/library/secretmanager.googleapis.com → 點 **「啟用」**

### 1-2. 建立 secret

打開 **Cloud Shell**(右上角終端機圖示 `>_`),會跳出一個瀏覽器內的終端機。

把以下整段貼進去(會跳出 trust dialog,選 Authorize):

```bash
# 設定專案
gcloud config set project linkedin-dashboard-500402

# 建一個叫 streamlit-secrets 的 secret
gcloud secrets create streamlit-secrets --replication-policy="automatic"
```

### 1-3. 把 secrets 內容寫進去

在 Cloud Shell 跑:

```bash
nano /tmp/secrets.toml
```

會打開一個編輯器,**貼入完整 toml 內容**(就是我們之前給 Streamlit Cloud 用的那段 `[auth] + [gcp_service_account]`)。

貼完按:
- `Ctrl + O` → `Enter` 存檔
- `Ctrl + X` 離開

然後跑:

```bash
gcloud secrets versions add streamlit-secrets --data-file=/tmp/secrets.toml
rm /tmp/secrets.toml
```

---

## 步驟 2:授權 Cloud Run 讀 Secret

```bash
PROJECT_NUMBER=$(gcloud projects describe linkedin-dashboard-500402 --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding streamlit-secrets \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

## 步驟 3:部署到 Cloud Run

```bash
# 啟用必要 API
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

# 從 GitHub 拉 code 並部署(會自動 build image)
gcloud run deploy tada-linkedin-ads \
  --source=https://github.com/GH-0928/linkedin-ads-dashboard \
  --region=asia-east1 \
  --allow-unauthenticated \
  --port=8080 \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=2 \
  --update-secrets=/app/.streamlit/secrets.toml=streamlit-secrets:latest
```

第一次跑會花 3-5 分鐘(build image + 部署)。完成後會看到:

```
Service [tada-linkedin-ads] revision [...] has been deployed
Service URL: https://tada-linkedin-ads-xxxx.a.run.app
```

**複製這個 URL**,瀏覽器打開應該看到密碼登入頁 → 確認儀表板能正常運作再走下一步。

---

## 步驟 4:綁定自訂網域 tadalinkedin.garichy.com

### 4-1. 在 Cloud Run 申請 Domain Mapping

```bash
gcloud beta run domain-mappings create \
  --service=tada-linkedin-ads \
  --domain=tadalinkedin.garichy.com \
  --region=asia-east1
```

執行後會輸出一段 DNS 設定資訊,類似:

```
NAME                      RECORD TYPE  CONTENTS
tadalinkedin.garichy.com  CNAME        ghs.googlehosted.com
```

**記下這個 CNAME 目標值**(通常是 `ghs.googlehosted.com`)。

### 4-2. 在 Cloudflare 加 DNS 記錄

1. 打開 https://dash.cloudflare.com → 選 `garichy.com`
2. 左側選單 → **DNS** → **Records**
3. 點 **「Add record」**
4. 填寫:
   | 欄位 | 值 |
   |---|---|
   | Type | `CNAME` |
   | Name | `tadalinkedin` |
   | Target | `ghs.googlehosted.com`(用上一步 Cloud Run 給的值) |
   | Proxy status | 🟠 **DNS only**(灰色雲朵,先不開 Proxy) |
   | TTL | Auto |
5. 點 **Save**

### 4-3. 等 SSL 憑證自動發放(5-15 分鐘)

Cloud Run 會自動為 `tadalinkedin.garichy.com` 申請 Let's Encrypt 憑證。期間打開 https://tadalinkedin.garichy.com 可能會看到憑證錯誤,等就好。

確認方式:
```bash
gcloud beta run domain-mappings describe \
  --domain=tadalinkedin.garichy.com \
  --region=asia-east1
```

看到 `CertificateProvisioned: True` 就是好了。

### 4-4.(可選)開啟 Cloudflare Proxy

確認 https://tadalinkedin.garichy.com 能用之後,可以回 Cloudflare DNS 把 Proxy status 從 🟠 DNS only 切到 🟧 **Proxied**,啟用 CF 的 CDN 和 DDoS 防護。

⚠️ 切完後可能需要等 2-3 分鐘 DNS 傳播。如果切了 Proxied 反而出問題,切回 DNS only 即可。

---

## 完成驗收

- 打開 https://tadalinkedin.garichy.com → 看到密碼登入頁
- 輸入密碼 → 看到儀表板
- 網址列顯示 🔒 安全鎖頭

---

## 後續維護

**code 更新流程**(階段 1 的流程依然有效):
1. 本機改 code
2. `git push`
3. Streamlit Cloud(階段 1 網址)**自動**部署 ✅
4. Cloud Run(階段 2 網址)**需手動**觸發重新部署:
   ```bash
   gcloud run deploy tada-linkedin-ads \
     --source=https://github.com/GH-0928/linkedin-ads-dashboard \
     --region=asia-east1
   ```

如果想 Cloud Run 也自動部署,之後可以加 Cloud Build trigger 監聽 GitHub push,但**先讓基本流程跑順再說**。
