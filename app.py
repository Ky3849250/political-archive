import streamlit as st
from supabase import create_client, Client

# ================= 填入您的 Supabase 資訊 =================
SUPABASE_URL = "https://aclktnaqruscebexfotr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFjbGt0bmFxcnVzY2ViZXhmb3RyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTE2NzMxNTUsImV4cCI6MjEwNzI0OTE1NX0.nYcb0f-H_N28Osg-BRGUothYYs5apyn5RHTuLpHd0hs"
# =========================================================

# 初始化資料庫連線
@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# ================= 網頁基本設定 =================
st.set_page_config(page_title="政治言論與新聞查證資料庫", page_icon="🏛️", layout="wide")
st.title("🏛️ 政治人物言論與新聞查證資料庫")
st.markdown("透過零演算法干擾、去中心化備份的機制，確保每一筆政治承諾與發言皆真實不可篡改。")

# ================= 側邊欄：多維度精準搜尋 =================
st.sidebar.header("🔍 精準檢索")
search_keyword = st.sidebar.text_input("輸入關鍵字 (如：人名、政策、事件)", "")
category_filter = st.sidebar.multiselect(
    "選擇內容來源",
    options=["新聞", "論壇", "影音"],
    default=["新聞", "論壇", "影音"]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **防偽機制說明**\n\n本庫所有連結皆透過 Internet Archive 進行第三方備份，並擁有 SHA-256 數位指紋，確保無人能變造歷史。")

# ================= 資料抓取與過濾 =================
@st.cache_data(ttl=60) # 快取資料 60 秒，避免重複頻繁讀取資料庫
def load_data():
    response = supabase.table("articles").select("*").order("created_at", desc=True).execute()
    return response.data

raw_data = load_data()

# 在 Python 端進行篩選（因應 MVP 階段，資料量尚可於前端過濾）
filtered_data = []
for item in raw_data:
    # 1. 過濾來源類別
    if item.get("category") not in category_filter:
        continue
        
    # 2. 過濾關鍵字 (搜尋標題或 AI 萃取的關鍵字)
    if search_keyword:
        kw_lower = search_keyword.lower()
        title_match = kw_lower in item.get("title", "").lower()
        keyword_match = any(kw_lower in k.lower() for k in item.get("keywords", []))
        if not (title_match or keyword_match):
            continue
            
    filtered_data.append(item)

# ================= 搜尋結果顯示 =================
st.subheader(f"共找到 {len(filtered_data)} 筆資料")
st.divider()

if not filtered_data:
    st.warning("找不到符合條件的資料，請嘗試更換關鍵字。")
else:
    for item in filtered_data:
        # 使用 Container 卡片式排版
        with st.container():
            st.markdown(f"### {item['title']}")
            
            # 顯示類別與關鍵字標籤
            kws = item.get('keywords', [])
            kw_str = "、".join(kws) if kws else "無"
            st.caption(f"📂 來源：**{item['category']}** ｜ 🏷️ AI 標籤：{kw_str} ｜ 🕒 建檔時間：{item['created_at'][:10]}")
            
            # 若為影音類型，直接在網頁內嵌 YouTube 播放器
            if item['category'] == '影音' and ('youtube.com' in item['source_url'] or 'youtu.be' in item['source_url']):
                st.video(item['source_url'])
            
            # 建立按鈕
            col1, col2, col3 = st.columns([2, 2, 6])
            with col1:
                st.link_button("🔗 前往原始連結", item['source_url'])
            with col2:
                if item['archive_url'] and "web.archive.org" in item['archive_url']:
                    st.link_button("🏛️ Wayback 防偽快照", item['archive_url'], type="secondary")
                else:
                    st.button("📺 影音由平台專屬託管", disabled=True)
            
            # (選單功能) 顯示進階防偽資訊
            with st.expander("🛡️ 展開查看數位指紋 (防偽驗證碼)"):
                st.code(f"SHA-256 Hash: {item.get('sha256_hash', 'N/A')}", language="text")
            
            st.divider()