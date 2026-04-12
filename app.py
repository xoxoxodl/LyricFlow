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
# 2. Spotify OAuth
# ─────────────────────────────────────────
if "token_info" not in st.session_state:
    st.session_state.token_info = None
 
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
# 3. OAuth 콜백 처리
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
# 4. 메인 UI
# ─────────────────────────────────────────
st.title("🎵 LyricFlow")
st.write("지금 듣는 노래의 가사를 분석하고, 무드가 이어지는 다음 곡을 추천합니다.")
st.divider()
 
# 미인증 상태: 로그인 버튼
if not is_authenticated():
    auth_manager = get_auth_manager()
    auth_url = auth_manager.get_authorize_url()
    st.markdown("### Spotify 계정으로 시작하기")
    st.link_button("🎧 Spotify로 로그인", auth_url, use_container_width=True)
    st.stop()
 
# ─────────────────────────────────────────
# 5. 인증 완료 후 메인 기능
# ─────────────────────────────────────────
sp = get_spotify_client()
 
with st.sidebar:
    st.markdown("### ⚙️ 설정")
    if st.button("로그아웃"):
        st.session_state.token_info = None
        st.rerun()
 
if st.button("지금 재생 중인 노래 분석하기"):
    with st.spinner("음악 정보를 가져오는 중..."):
        try:
            current_playing = sp.current_user_playing_track()
        except spotipy.SpotifyException as e:
            st.error(f"Spotify 오류: {e}")
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
 
            # ── Claude가 직접 분석 (가사 API 불필요) ──
            with st.spinner("Claude가 가사의 서사를 분석 중입니다..."):
                client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
 
                prompt = f"""당신은 음악 가사 분석 전문가입니다.
아래 노래의 가사를 당신의 지식을 바탕으로 분석해 주세요.
가사를 직접 인용하지 말고, 주제와 감정선, 서사를 분석해 주세요.
 
곡 제목: {track_name}
아티스트: {artists}
 
지시사항:
- 요약: 가사의 주제와 감정선을 3줄로 요약해 주세요. (제목이나 번호 생략)
- 키워드: 이 곡의 분위기를 나타내는 키워드 3~5개를 콤마로 구분해서 뽑아주세요.
- 추천: 이 곡과 가사의 서사나 감정선이 이어지는 추천곡 '3곡'을 제안해 주세요.
  (같은 아티스트나 같은 시대 곡 말고, 가사의 내용과 감정이 비슷한 곡으로 추천해 주세요.)
 
출력 형식 (반드시 지킬 것):
요약: [내용]
키워드: [키워드1, 키워드2, 키워드3]
추천1: [곡 제목 - 아티스트] | [이유]
추천2: [곡 제목 - 아티스트] | [이유]
추천3: [곡 제목 - 아티스트] | [이유]"""
 
                try:
                    message = client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=1500,
                        temperature=0.7,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    full_response = message.content[0].text
                except Exception as e:
                    st.error(f"Claude API 오류: {e}")
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
                st.markdown("### 📝 가사 감성 리포트")
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
 
                # 추천곡 처리
                st.divider()
                st.markdown("### 💿 다음 Flow 추천곡")
 
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
                            st.link_button("🎧 들어보기", rec["url"])
                else:
                    st.warning("추천된 곡들을 Spotify에서 찾을 수 없습니다.")
        else:
            st.warning("현재 재생 중인 곡이 없습니다. Spotify를 확인해 주세요!")
 
st.caption("LyricFlow v1.3 | Developed by Tay Kim | Model: claude-sonnet-4-6")