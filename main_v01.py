import streamlit as st
import datetime
import pandas as pd
import requests
import urllib.parse
from geopy.geocoders import Nominatim

# --- 🛠️ 工具函式庫 ---

def get_coordinates(place_name):
    geolocator = Nominatim(user_agent="hiking_helper_lite_v2")
    try:
        search_query = f"台灣 {place_name}"
        location = geolocator.geocode(search_query, timeout=10)
        if location:
            return location.latitude, location.longitude, location.address
        return None, None, None
    except Exception:
        return None, None, None

def get_weather_forecast(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_probability_max", "sunrise", "sunset"],
        "timezone": "Asia/Taipei"
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        daily = data.get("daily", {})
        df = pd.DataFrame({
            "日期": daily.get("time"),
            "最高溫": daily.get("temperature_2m_max"),
            "最低溫": daily.get("temperature_2m_min"),
            "降雨機率(%)": daily.get("precipitation_probability_max"),
            "日出": daily.get("sunrise"),
            "日落": daily.get("sunset")
        })
        return df
    except Exception as e:
        st.error(f"天氣資料讀取失敗: {e}")
        return None

def generate_full_details(mountain_name, route_name, date_obj, weather_info=None, custom_notes=""):
    details = []
    
    # 1. 【手動備註】
    if custom_notes:
        details.append("【📝 行程筆記】")
        details.append(custom_notes)
        details.append("\n" + "-"*20 + "\n")
    
    # 2. 【導航連結】
    map_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(mountain_name)}"
    details.append(f"📍 Google Maps 導航：{map_url}")
    details.append("\n" + "-"*20 + "\n")

    # 3. 【天氣與資訊】
    details.append(f"【目的地】{mountain_name}")
    if route_name:
        details.append(f"【路線】{route_name}")
    
    if weather_info:
        max_t = weather_info.get('max_temp', '?')
        min_t = weather_info.get('min_temp', '?')
        rain = weather_info.get('rain_prob', 0)
        sunrise = weather_info.get('sunrise', '未知')[-5:]
        sunset = weather_info.get('sunset', '未知')[-5:]
        
        details.append("\n【☀️ 當日天氣預報】")
        details.append(f"🌡️ 氣溫預測：{min_t}°C ~ {max_t}°C")
        details.append(f"☔ 降雨機率：{rain}%")
        details.append(f"🌅 日出日落：{sunrise} / {sunset}")
        
        if rain >= 30: details.append("⚠️ 降雨機率高，務必攜帶雨衣/雨褲！")
        if min_t < 10: details.append("⚠️ 氣溫較低，請攜帶保暖中層。")
            
    else:
        month = date_obj.month
        details.append("\n【☀️ 季節性氣候提醒】")
        details.append("⚠️ 日期較遠，暫無精準預報，請出發前 3 天再次確認。")
        if month in [12, 1, 2, 3]:
            details.append("❄️ 冬季高山可能結冰，建議攜帶冰爪。")
        elif month in [5, 6]:
            details.append("🌧️ 梅雨季節，注意午後雷陣雨。")
        elif month in [7, 8, 9]:
            details.append("🌪️ 颱風季/夏季，注意防曬與天氣警報。")
    
    # 4. 【裝備檢查】
    details.append("\n【🎒 裝備檢查】")
    details.append("□ 證件 / 入山證 / 離線地圖")
    details.append("□ 頭燈 (含備用電池) ★重要")
    details.append("□ 雨具 / 保暖衣物")
    details.append("□ 行動水 / 行動糧")
    
    # 5. 【外部連結】
    encoded_name = urllib.parse.quote(mountain_name)
    biji_link = f"https://hiking.biji.co/index.php?q={encoded_name}&node=search"
    details.append(f"\n🔗 健行筆記搜尋：{biji_link}")

    return "\n".join(details)

# --- 🎨 頁面 UI 開始 ---

st.set_page_config(page_title="登山行程整合助手", page_icon="🏔️", layout="centered")

# Session 初始化 (確保變數存在)
if 'weather_df' not in st.session_state: st.session_state.weather_df = None
if 'searched_mountain' not in st.session_state: st.session_state.searched_mountain = ""
if 'map_coords' not in st.session_state: st.session_state.map_coords = None

st.title("🏔️ 登山行程整合助手")

# --- 🌤️ 第一區：天氣與日照查詢 ---
st.subheader("1️⃣ 天氣與日照查詢")
st.caption("💡 技巧：輸入「單一山名」(如：合歡南峰) 定位較準確。")

c1, c2 = st.columns([3, 1])
with c1:
    search_input = st.text_input("輸入山名定位", value=st.session_state.searched_mountain, placeholder="例如：合歡山主峰")
with c2:
    st.write("") 
    st.write("")
    btn_search = st.button("🔍 定位並查天氣", use_container_width=True)

if btn_search and search_input:
    with st.spinner(f"正在定位「{search_input}」..."):
        lat, lon, addr = get_coordinates(search_input)
        if lat:
            st.session_state.map_coords = (lat, lon)
            st.session_state.searched_mountain = search_input
            df = get_weather_forecast(lat, lon)
            if df is not None:
                st.session_state.weather_df = df
                st.success(f"📍 定位成功：{addr}")
            else:
                st.warning("定位成功但查無天氣資料。")
        else:
            st.error("❌ 找不到此地點，請嘗試縮短名稱。")

if st.session_state.map_coords:
    lat, lon = st.session_state.map_coords
    
    with st.expander("🗺️ 確認定位位置 (點此展開地圖)", expanded=True):
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}), zoom=12)
        if not ("台灣" in str(st.session_state.searched_mountain) or 21 < lat < 26):
            st.warning("⚠️ 定位點似乎不在台灣本島，請確認關鍵字。")

    if st.session_state.weather_df is not None:
        df = st.session_state.weather_df
        tab1, tab2 = st.tabs(["🌡️ 氣溫走勢", "☔ 降雨機率"])
        with tab1: st.line_chart(df.set_index("日期")[["最高溫", "最低溫"]], color=["#FF5555", "#55AAFF"])
        with tab2: st.bar_chart(df.set_index("日期")["降雨機率(%)"], color="#0000FF")

        with st.expander("🌅 查看每日日出日落時刻"):
            display_df = df[["日期", "日出", "日落", "降雨機率(%)"]].copy()
            display_df["日出"] = display_df["日出"].apply(lambda x: x[-5:] if x else "-")
            display_df["日落"] = display_df["日落"].apply(lambda x: x[-5:] if x else "-")
            st.dataframe(display_df, use_container_width=True)

st.divider()

# --- 📅 第二區：行程確認 & 行事曆 ---
st.subheader("2️⃣ 確認行程 & 加入行事曆")

with st.form("confirm_form"):
    target_name = st.text_input("📍 目的地山岳", value=st.session_state.searched_mountain)
    route_name = st.text_input("🚩 路線/備註 (選填)", placeholder="例如：西北稜 O 型")
    
    c_date, c_time = st.columns(2)
    with c_date:
        hiking_date = st.date_input("出發日期", value=datetime.date.today() + datetime.timedelta(days=1))
    with c_time:
        hiking_time = st.time_input("起登時間", value=datetime.time(6, 0))

    st.write("---")
    
    # 👇👇👇 這裡做了重大優化！ 👇👇👇
    
    # 1. 增加「快速開啟」按鈕在筆記上方，方便你切換
    st.caption("需要查路況或集合地點嗎？點擊下方按鈕，查完回來繼續貼上。")
    st.link_button("🏃 開啟健行筆記搜尋", "https://hiking.biji.co/index.php?node=search", use_container_width=True)

    # 2. 增加 key="user_notes" (這是防止資料消失的關鍵！)
    # 就算你切換視窗回來導致頁面重新整理，Streamlit 也會記得這裡面的字
    custom_notes = st.text_area(
        "📝 手動筆記 (集合地點、裝備清單等)", 
        placeholder="在此貼上健行筆記的資訊...",
        height=150,
        key="user_notes" 
    )

    submitted = st.form_submit_button("✅ 確認並生成行程連結", use_container_width=True, type="primary")

if submitted and target_name:
    st.success(f"已建立行程：**{target_name}**")
    
    # 取得天氣
    selected_date_str = hiking_date.strftime("%Y-%m-%d")
    day_weather_info = None
    if st.session_state.weather_df is not None:
        day_row = st.session_state.weather_df[st.session_state.weather_df["日期"] == selected_date_str]
        if not day_row.empty:
            day_weather_info = {
                'max_temp': day_row.iloc[0]['最高溫'],
                'min_temp': day_row.iloc[0]['最低溫'],
                'rain_prob': day_row.iloc[0]['降雨機率(%)'],
                'sunrise': day_row.iloc[0]['日出'],
                'sunset': day_row.iloc[0]['日落']
            }
            
    # 這裡我們使用 st.session_state.user_notes 來抓取內容
    # 因為表單提交時，key 綁定的值才是最新的
    notes_content = st.session_state.user_notes
            
    details_text = generate_full_details(target_name, route_name, hiking_date, day_weather_info, notes_content)
    
    if route_name:
        cal_title = f"⛰️ {target_name} - {route_name}"
    else:
        cal_title = f"⛰️ {target_name} 登山"

    start_dt = datetime.datetime.combine(hiking_date, hiking_time)
    end_dt = start_dt + datetime.timedelta(hours=6)
    fmt = "%Y%m%dT%H%M%S"
    dates_str = f"{start_dt.strftime(fmt)}/{end_dt.strftime(fmt)}"
    
    cal_base = "https://calendar.google.com/calendar/render?action=TEMPLATE"
    cal_params = {
        "text": cal_title,
        "dates": dates_str,
        "location": target_name,
        "details": details_text
    }
    cal_url = f"{cal_base}&{urllib.parse.urlencode(cal_params)}"
    map_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(target_name)}"

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        st.link_button("🗺️ Google Maps", map_url, use_container_width=True)
    with col_btn2:
        st.link_button("📅 Google 行事曆", cal_url, use_container_width=True)
    
    with st.expander("👀 預覽行事曆最終內容", expanded=True):
        st.text(f"標題：{cal_title}")
        st.text("-" * 30)
        st.text(details_text)
