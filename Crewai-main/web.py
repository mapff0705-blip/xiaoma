
import streamlit as st
import requests
from PIL import Image
import io

# ========== 后端配置 ==========
BASE_URL = "http://localhost:8012/api/crewai"

# ========== 辅助函数 ==========
def fetch_job_status(job_id: str):
    """查询指定 job_id 的状态，并更新全局状态缓存"""
    try:
        resp = requests.get(f"{BASE_URL}/{job_id.strip()}", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            st.session_state['job_status_map'][job_id] = data.get("status", "UNKNOWN")
            return data
        else:
            st.session_state['job_status_map'][job_id] = f"ERROR ({resp.status_code})"
            return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        st.session_state['job_status_map'][job_id] = "CONNECTION ERROR"
        return {"exception": str(e)}


# ========== 初始化 session_state ==========
if 'post_response' not in st.session_state:
    st.session_state['post_response'] = {"message": "尚未提交任务"}
if 'get_response' not in st.session_state:
    st.session_state['get_response'] = {"message": "尚未查询任务状态"}
if 'last_job_id' not in st.session_state:
    st.session_state['last_job_id'] = ""
if 'submitted_jobs' not in st.session_state:
    st.session_state['submitted_jobs'] = []
if 'job_status_map' not in st.session_state:
    st.session_state['job_status_map'] = {}

# ========== Streamlit UI 主逻辑 ==========

st.set_page_config(page_title="CrewAI 任务控制台", layout="wide")
st.title("🚀 CrewAI 任务控制台")

# ===== 第一部分：提交任务 =====
st.header("📤 提交新任务")

with st.form("submit_crew", clear_on_submit=False):
    target_platform = st.text_input("目标平台 (target_platform)", placeholder="例如：抖音，小红书，哔哩哔哩等")

    col_desc, col_img = st.columns([2, 1])

    with col_desc:
        creator_niche = st.text_area(
            "创作者领域 (creator_niche)",
            height=150,
            placeholder="请详细说明创作领域、目标、背景和期望输出..."
        )

    with col_img:
        uploaded_file = st.file_uploader(
            "📎 上传参考图片（可选）",
            type=["png", "jpg", "jpeg"],
            help="支持 PNG/JPG 格式。系统将自动识别图片内容并融合到项目描述中。"
        )

        if uploaded_file is not None:
            try:
                image = Image.open(io.BytesIO(uploaded_file.read()))
                uploaded_file.seek(0)  # 重置指针
                st.image(image, caption="预览", width="stretch")
            except Exception as e:
                st.error(f"无法读取图片: {str(e)}")
                uploaded_file = None

    submitted = st.form_submit_button("启动任务")

if submitted:
    if not target_platform.strip() or not creator_niche.strip():
        st.error("❌ 请填写客户领域和项目描述！")
    else:
        try:
            with st.spinner("正在提交任务到后端..."):
                form_data = {
                    "target_platform": target_platform,
                    "creator_niche": creator_niche
                }
                files = {"file": (
                uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)} if uploaded_file else None

                resp = requests.post(
                    BASE_URL,
                    data=form_data,
                    files=files,
                    timeout=30
                )

                if resp.status_code == 200:
                    response_json = resp.json()
                    job_id = response_json.get("job_id")

                    if job_id and job_id not in st.session_state['submitted_jobs']:
                        st.session_state['submitted_jobs'].insert(0, job_id)
                        st.session_state['job_status_map'][job_id] = "PENDING"
                        # 立即查一次状态（可选）
                        fetch_job_status(job_id)

                    st.session_state['post_response'] = response_json
                    st.session_state['last_job_id'] = job_id
                    st.success(f"✅ 任务已提交！Job ID: `{job_id}`")
                else:
                    error_detail = resp.text
                    try:
                        error_detail = resp.json()
                    except:
                        pass
                    st.session_state['post_response'] = {"error": f"HTTP {resp.status_code}", "detail": error_detail}
                    st.error(f"❌ 提交失败：{resp.status_code}")
        except Exception as e:
            st.session_state['post_response'] = {"exception": str(e)}
            st.error(f"⚠️ 请求异常：{str(e)}")

# 显示 POST 响应
st.subheader("📤 后端返回 (POST /api/crewai)")
st.json(st.session_state['post_response'])

st.markdown("---")

# ===== 第二部分：查询任务状态 =====
st.header("🔍 查询任务状态")

# 显示历史任务 + 状态
if st.session_state['submitted_jobs']:
    st.subheader("📋 已提交的任务")

    for jid in st.session_state['submitted_jobs']:
        status = st.session_state['job_status_map'].get(jid, "UNKNOWN")

        # 状态颜色映射
        status_emoji = {
            "COMPLETE": "🟢",
            "STARTED": "🟡",
            "PENDING": "🔵",
            "ERROR": "🔴",
            "CONNECTION ERROR": "🔴"
        }.get(status, "⚪")

        col_id, col_status, col_btn = st.columns([3, 2, 1])

        with col_id:
            st.code(jid, language="")

        with col_status:
            st.write(f"{status_emoji} {status}")

        with col_btn:
            if st.button("🔄", key=f"refresh_{jid}", help="刷新此任务状态"):
                result = fetch_job_status(jid)
                st.session_state['get_response'] = result
                st.rerun()  # 刷新页面以更新状态显示

    st.markdown("---")

# 手动输入查询
job_id_input = st.text_input("请输入 Job ID", value=st.session_state['last_job_id'])
if st.button("查询状态") and job_id_input.strip():
    result = fetch_job_status(job_id_input.strip())
    st.session_state['get_response'] = result

# 显示 GET 响应
st.subheader("🔍 后端返回 (GET /api/crewai/{job_id})")
st.json(st.session_state['get_response'])

st.markdown("---")
st.caption("💡 提示：确保 FastAPI 服务正在 http://localhost:8012 运行。")



# # streamlit run web.py