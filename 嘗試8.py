# %%
import streamlit as st
import random
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText
import secrets

# --- 1. 頁面基本設定 ---
st.set_page_config(page_title="成大美食導航 NCKU Foodie", page_icon="🍱", layout="centered")

# --- 📧 寄信功能安全設定 ---
MY_EMAIL = st.secrets.get("MY_EMAIL", "dogee1likego@gmail.com")
APP_PASSWORD = st.secrets.get("APP_PASSWORD", "dmfstlzrbhsqopds")

def send_otp_email(otp_code):
    try:
        msg = MIMEText(f"您好！\n\n您的驗證碼為：【 {otp_code} 】")
        msg['Subject'] = '【驗證碼】成大美食管理員登入'
        msg['From'] = MY_EMAIL
        msg['To'] = MY_EMAIL
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(MY_EMAIL, APP_PASSWORD)
            server.send_message(msg)
        return True
    except:
        return False

# --- 2. 資料庫邏輯 ---
DATA_FILE = "restaurants_v5.csv"

def load_data():
    default_list = [
        {"name": "元味屋", "price": 150, "rating": 4.5, "count": 1},
        {"name": "成大館", "price": 100, "rating": 4.0, "count": 1},
        {"name": "麥當勞", "price": 120, "rating": 4.2, "count": 1}
    ]
    if os.path.exists(DATA_FILE):
        try: return pd.read_csv(DATA_FILE).to_dict('records')
        except: return default_list
    return default_list

# 初始化狀態
if 'restaurant_db' not in st.session_state:
    st.session_state.restaurant_db = load_data()
if 'has_rated' not in st.session_state:
    st.session_state.has_rated = False

# --- 3. 側邊欄：管理員入口 ---
with st.sidebar:
    st.title("🍔 搜尋過濾")
    budget = st.slider("💰 預算上限", 0, 500, 200, 10)
    min_rating = st.slider("⭐ 最低評分要求", 1.0, 5.0, 3.5, 0.1)
    
    st.divider()
    st.subheader("🔐 管理員控制台")
    
    # 按鈕：發送驗證碼
    if st.button("📩 取得電子郵件驗證碼"):
        st.session_state.current_otp = str(secrets.randbelow(900000) + 100000)
        if send_otp_email(st.session_state.current_otp):
            st.success("驗證碼已發送！")
    
    # 輸入框：驗證碼
    entered_otp = st.text_input("請輸入 6 位數驗證碼", type="password")
    
    # 權限檢查邏輯
    if 'current_otp' in st.session_state and entered_otp == st.session_state.current_otp:
        st.warning("🔓 管理員模式已開啟")
        
        # --- 新增：退出按鈕 ---
        if st.button("🚪 退出管理模式", use_container_width=True):
            if 'current_otp' in st.session_state:
                del st.session_state.current_otp # 刪除密碼紀錄
            st.rerun() # 立即重整頁面
        
        st.divider()
        
        # 刪除功能
        if st.session_state.restaurant_db:
            names = [res['name'] for res in st.session_state.restaurant_db]
            target = st.selectbox("選擇要刪除的餐廳", names)
            if st.button("❌ 確定刪除這家餐廳"):
                st.session_state.restaurant_db = [r for r in st.session_state.restaurant_db if r['name'] != target]
                pd.DataFrame(st.session_state.restaurant_db).to_csv(DATA_FILE, index=False)
                st.success(f"已成功刪除 {target}")
                st.rerun()
    elif entered_otp:
        st.error("驗證碼不正確")

# --- 4. 主頁面：抽選功能 ---
st.title("🍴 成大生今天吃什麼？")

if st.button("🚀 幫我選一家！", type="primary", use_container_width=True):
    filtered = [r for r in st.session_state.restaurant_db if int(r['price']) <= budget and float(r['rating']) >= min_rating]
    if filtered:
        st.session_state.last_pick = random.choice(filtered)
        st.session_state.has_rated = False # 重置評價狀態，讓新抽選的餐廳可以評分
        st.balloons()
    else:
        st.error("找不到符合條件的餐廳！")

if 'last_pick' in st.session_state and st.session_state.last_pick:
    res = st.session_state.last_pick
    st.success(f"### 🎊 推薦：**{res['name']}**")
    c1, c2, c3 = st.columns(3)
    c1.metric("價位", f"${res['price']}")
    c2.metric("平均評分", f"⭐ {res['rating']:.1f}")
    c3.metric("評價次數", f"{int(res['count'])} 次")
    
    # --- 優化點：評價完即關閉 ---
    st.divider()
    if not st.session_state.has_rated:
        with st.expander(f"✨ 我吃完了，我要評價「{res['name']}」"):
            score = st.slider("評分 (1-5)", 1.0, 5.0, 4.0, 0.1)
            if st.button("提交真實評分"):
                for item in st.session_state.restaurant_db:
                    if item['name'] == res['name']:
                        item['rating'] = round((item['rating'] * item['count'] + score) / (item['count'] + 1), 1)
                        item['count'] += 1
                        break
                pd.DataFrame(st.session_state.restaurant_db).to_csv(DATA_FILE, index=False)
                st.session_state.has_rated = True # 標記已完成評價
                st.rerun()
    else:
        st.info("✅ 感謝您的回饋！您的評價已成功納入數據庫。")

# --- 5. 貢獻新餐廳 ---
st.divider()
st.subheader("📝 貢獻新餐廳")
with st.form("add_form", clear_on_submit=True):
    new_name = st.text_input("餐廳名稱")
    c1, c2 = st.columns(2)
    new_price = c1.number_input("預估價位", value=100, step=10)
    new_rating = c2.slider("初始評分", 1.0, 5.0, 4.0, 0.1)
    if st.form_submit_button("✅ 提交"):
        if new_name and not any(r['name'].strip().lower() == new_name.strip().lower() for r in st.session_state.restaurant_db):
            st.session_state.restaurant_db.append({"name": new_name.strip(), "price": int(new_price), "rating": float(new_rating), "count": 1})
            pd.DataFrame(st.session_state.restaurant_db).to_csv(DATA_FILE, index=False)
            st.rerun()

# --- 6. 完整清單 ---
st.divider()
st.subheader("📊 完整校園名單")
if st.session_state.restaurant_db:
    st.dataframe(pd.DataFrame(st.session_state.restaurant_db), use_container_width=True, hide_index=True)


