import streamlit as st
import os
import spotipy
import anthropic
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
 
# ─────────────────────────────────────────
# 1. 환경 설정
# ─────────────────────────────────────────
load_dotenv()
 
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
 
st.set_page_config(page_title="LyricFlow", page_icon="🎵", layout="centered")
 
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: white; }
    .stButton>button {
        background-color: #1DB954; color: white; border-radius: 25px;
        width: 100%; border: none; font-weight: bold; padding: 12px;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #1ed760; transform: scale(1.02); }
    </style>
    """, unsafe_allow_html=True)
 
# ─────────────────────────────────────────
# 2. 언어 팩
# ─────────────────────────────────────────
LANGUAGES = {
    "한국어": {
        "flag": "🇰🇷",
        "subtitle": "지금 듣는 노래의 가사를 분석하고, 무드가 이어지는 다음 곡을 추천합니다.",
        "login_title": "### Spotify 계정으로 시작하기",
        "login_btn": "🎧 Spotify로 로그인",
        "analyze_btn": "지금 재생 중인 노래 분석하기",
        "loading_track": "음악 정보를 가져오는 중...",
        "loading_claude": "Claude가 가사의 서사를 분석 중입니다...",
        "report_title": "### 📝 가사 감성 리포트",
        "next_title": "### 💿 다음 Flow 추천곡",
        "listen_btn": "🎧 들어보기",
        "no_song": "현재 재생 중인 곡이 없습니다. Spotify를 확인해 주세요!",
        "no_recs": "추천된 곡들을 Spotify에서 찾을 수 없습니다.",
        "spotify_err": "Spotify 오류",
        "claude_err": "Claude API 오류",
        "logout": "로그아웃",
        "settings": "### ⚙️ 설정",
        "lang_label": "🌐 언어",
        "prompt_lang": "한국어",
    },
    "English": {
        "flag": "🇺🇸",
        "subtitle": "Analyze the lyrics of your current song and find what flows next.",
        "login_title": "### Get started with Spotify",
        "login_btn": "🎧 Login with Spotify",
        "analyze_btn": "Analyze Currently Playing",
        "loading_track": "Fetching track info...",
        "loading_claude": "Claude is analyzing the lyrics...",
        "report_title": "### 📝 Lyric Sentiment Report",
        "next_title": "### 💿 Next Flow Picks",
        "listen_btn": "🎧 Listen",
        "no_song": "No song is currently playing. Check your Spotify!",
        "no_recs": "Could not find recommended songs on Spotify.",
        "spotify_err": "Spotify error",
        "claude_err": "Claude API error",
        "logout": "Logout",
        "settings": "### ⚙️ Settings",
        "lang_label": "🌐 Language",
        "prompt_lang": "English",
    },
    "中文": {
        "flag": "🇨🇳",
        "subtitle": "分析正在播放的歌曲歌词，推荐情感相似的下一首歌。",
        "login_title": "### 使用 Spotify 账号开始",
        "login_btn": "🎧 使用 Spotify 登录",
        "analyze_btn": "分析当前播放的歌曲",
        "loading_track": "正在获取音乐信息...",
        "loading_claude": "Claude 正在分析歌词...",
        "report_title": "### 📝 歌词情感报告",
        "next_title": "### 💿 下一首推荐",
        "listen_btn": "🎧 试听",
        "no_song": "当前没有正在播放的歌曲，请检查 Spotify！",
        "no_recs": "在 Spotify 上找不到推荐的歌曲。",
        "spotify_err": "Spotify 错误",
        "claude_err": "Claude API 错误",
        "logout": "退出登录",
        "settings": "### ⚙️ 设置",
        "lang_label": "🌐 语言",
        "prompt_lang": "中文",
    },
    "日本語": {
        "flag": "🇯🇵",
        "subtitle": "再生中の曲の歌詞を分析し、似た雰囲気の次の曲を提案します。",
        "login_title": "### Spotify アカウントで始める",
        "login_btn": "🎧 Spotify でログイン",
        "analyze_btn": "再生中の曲を分析する",
        "loading_track": "音楽情報を取得中...",
        "loading_claude": "Claude が歌詞を分析中です...",
        "report_title": "### 📝 歌詞センチメントレポート",
        "next_title": "### 💿 次のおすすめ曲",
        "listen_btn": "🎧 聴いてみる",
        "no_song": "現在再生中の曲がありません。Spotify を確認してください！",
        "no_recs": "Spotify でおすすめの曲が見つかりませんでした。",
        "spotify_err": "Spotify エラー",
        "claude_err": "Claude API エラー",
        "logout": "ログアウト",
        "settings": "### ⚙️ 設定",
        "lang_label": "🌐 言語",
        "prompt_lang": "日本語",
    },
}
 
# ─────────────────────────────────────────
# 3. Spotify OAuth
# ─────────────────────────────────────────
if "token_info" not in st.session_state:
    st.session_state.token_info = None
if "lang" not in st.session_state:
    st.session_state.lang = "한국어"
 
def get_auth_manager():
    return SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope="user-read-currently-playing",
        cache_handler=spotipy.cache_handler.MemoryCacheHandler(
            token_info=st.session_state.token_info
        ),
        open_browser=False,
    )
 
def is_authenticated():
    if st.session_state.token_info is None:
        return False
    auth_manager = get_auth_manager()
    if auth_manager.is_token_expired(st.session_state.token_info):
        try:
            st.session_state.token_info = auth_manager.refresh_access_token(
                st.session_state.token_info["refresh_token"]
            )
        except Exception:
            st.session_state.token_info = None
            return False
    return True
 
def get_spotify_client():
    return spotipy.Spotify(auth_manager=get_auth_manager())
 
# ─────────────────────────────────────────
# 4. OAuth 콜백 처리
# ─────────────────────────────────────────
code = st.query_params.get("code")
if code and not is_authenticated():
    auth_manager = get_auth_manager()
    try:
        token_info = auth_manager.get_access_token(code, as_dict=True)
        st.session_state.token_info = token_info
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"로그인 처리 중 오류: {e}")
 
# ─────────────────────────────────────────
# 5. 사이드바 (언어 선택 + 로그아웃)
# ─────────────────────────────────────────
with st.sidebar:
    # 언어 선택 — 인증 여부 상관없이 항상 표시
    lang_options = list(LANGUAGES.keys())
    lang_display = [f"{LANGUAGES[l]['flag']} {l}" for l in lang_options]
    selected_idx = st.selectbox(
        "🌐 Language / 언어",
        range(len(lang_options)),
        format_func=lambda i: lang_display[i],
        index=lang_options.index(st.session_state.lang),
    )
    st.session_state.lang = lang_options[selected_idx]
    T = LANGUAGES[st.session_state.lang]
 
    if is_authenticated():
        st.markdown(T["settings"])
        if st.button(T["logout"]):
            st.session_state.token_info = None
            st.rerun()
else:
    T = LANGUAGES[st.session_state.lang]
 
# ─────────────────────────────────────────
# 6. 메인 UI
# ─────────────────────────────────────────
st.title("🎵 LyricFlow")
st.write(T["subtitle"])
st.divider()
 
# 미인증 상태: 로그인 버튼
if not is_authenticated():
    auth_manager = get_auth_manager()
    auth_url = auth_manager.get_authorize_url()
    st.markdown(T["login_title"])
    st.link_button(T["login_btn"], auth_url, use_container_width=True)
    st.stop()
 
# ─────────────────────────────────────────
# 7. 인증 완료 후 메인 기능
# ─────────────────────────────────────────
sp = get_spotify_client()
 
if st.button(T["analyze_btn"]):
    with st.spinner(T["loading_track"]):
        try:
            current_playing = sp.current_user_playing_track()
        except spotipy.SpotifyException as e:
            st.error(f"{T['spotify_err']}: {e}")
            st.stop()
 
        if current_playing and current_playing.get("item"):
            track = current_playing["item"]
            track_name = track["name"]
            artists = ", ".join([a["name"] for a in track["artists"]])
            album_img = track["album"]["images"][0]["url"]
 
            col_img, col_info = st.columns([1, 2])
            with col_img:
                st.image(album_img, use_container_width=True)
            with col_info:
                st.header(track_name)
                st.subheader(artists)
 
            with st.spinner(T["loading_claude"]):
                client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
 
                prompt = f"""You are a music lyrics analysis expert. Please respond entirely in {T['prompt_lang']}.
 
Analyze the following song based on your knowledge of its lyrics.
Do NOT quote lyrics directly. Instead, analyze the themes, emotions, and narrative.
 
Song title: {track_name}
Artist: {artists}
 
Instructions:
- Summary: Summarize the theme and emotional arc in 3 sentences.
- Keywords: Extract 3-5 keywords representing the mood, separated by commas.
- Recommendations: Suggest 3 songs with similar lyrical narrative or emotional tone.
  (Avoid recommending songs by the same artist or from the same era — focus on lyrical and emotional similarity.)
 
Output format (strictly follow this):
요약: [content]
키워드: [keyword1, keyword2, keyword3]
추천1: [Song title - Artist] | [reason]
추천2: [Song title - Artist] | [reason]
추천3: [Song title - Artist] | [reason]"""
 
                try:
                    message = client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=1500,
                        temperature=0.7,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    full_response = message.content[0].text
                except Exception as e:
                    st.error(f"{T['claude_err']}: {e}")
                    st.stop()
 
                # 파싱
                try:
                    summary_part = full_response.split("키워드:")[0].replace("요약:", "").strip()
                    keywords_raw = full_response.split("키워드:")[1].split("추천1:")[0].strip()
                    keywords = [k.strip() for k in keywords_raw.split(",")]
                except IndexError:
                    summary_part = full_response
                    keywords = []
 
                st.divider()
                st.markdown(T["report_title"])
                st.info(summary_part)
 
                if keywords:
                    kw_html = "".join([
                        f'<span style="background-color: #333; color: #1DB954; padding: 6px 14px; '
                        f'border-radius: 20px; margin-right: 8px; font-size: 0.85rem; font-weight: bold; '
                        f'border: 1px solid #1DB954;">#{k}</span>'
                        for k in keywords
                    ])
                    st.markdown(kw_html, unsafe_allow_html=True)
                    st.write("")
 
                st.divider()
                st.markdown(T["next_title"])
 
                recommendations_raw = []
                for i in range(1, 4):
                    marker = f"추천{i}:"
                    next_marker = f"추천{i+1}:" if i < 3 else None
                    if marker in full_response:
                        part = full_response.split(marker)[1]
                        if next_marker and next_marker in part:
                            part = part.split(next_marker)[0]
                        part = part.strip()
                        if "|" in part:
                            title_artist, reason = part.split("|", 1)
                            recommendations_raw.append({
                                "query": title_artist.strip(),
                                "reason": reason.strip()
                            })
 
                valid_recs = []
                for rec in recommendations_raw:
                    try:
                        search_res = sp.search(q=rec["query"], type="track", limit=1)
                        if search_res["tracks"]["items"]:
                            r_track = search_res["tracks"]["items"][0]
                            valid_recs.append({
                                "url": r_track["external_urls"]["spotify"],
                                "img": r_track["album"]["images"][0]["url"],
                                "name": r_track["name"],
                                "artist": r_track["artists"][0]["name"],
                                "reason": rec["reason"],
                            })
                    except Exception:
                        continue
 
                if valid_recs:
                    cols = st.columns(len(valid_recs))
                    for idx, rec in enumerate(valid_recs):
                        with cols[idx]:
                            st.image(rec["img"], use_container_width=True)
                            st.success(f"**{rec['name']}**\n\n{rec['artist']}")
                            st.caption(rec["reason"])
                            st.link_button(T["listen_btn"], rec["url"])
                else:
                    st.warning(T["no_recs"])
        else:
            st.warning(T["no_song"])
 
st.caption("LyricFlow v1.4 | Developed by Tay Kim | Model: claude-sonnet-4-6")