import os

# 最大上传限制300MB，必须放在最前面
os.environ["STREAMLIT_SERVER_MAX_UPLOAD_SIZE"] = "300"

import streamlit as st
from utils import compress_pdf, compress_image
import tempfile
from PIL import Image


# 文件大小格式化工具：字节自动转 KB/MB
def format_size(byte_num):
    if byte_num < 1024:
        return f"{byte_num} B"
    elif byte_num < 1024 * 1024:
        return f"{byte_num / 1024:.2f} KB"
    else:
        return f"{byte_num / 1024 / 1024:.2f} MB"


# ===================== 页面基础配置（必须第一条Streamlit代码） =====================
st.set_page_config(
    page_title="文件压缩工具",
    page_icon="📦",
    layout="wide"
)

# ===================== 自定义美化CSS =====================
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
    }
    .stFileUploader {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ===================== 标题区域 =====================
st.markdown("# 📦 PDF / 图片压缩工具")
st.markdown("> 支持PDF、JPG、PNG压缩 | PNG自动保留透明通道")
st.divider()

# ===================== 优化1：参数滑块统一移入侧边栏 =====================
with st.sidebar:
    st.header("⚙️ 压缩参数设置")
    st.divider()

    quality_pdf = st.slider(
        "PDF 压缩质量",
        min_value=10,
        max_value=95,
        value=60,
        help="数值越小，文件体积越小，画质越低"
    )
    st.caption("💡 PDF推荐：60平衡清晰度与体积；30以下极致压缩，适合手机传阅")

    st.divider()

    quality_img = st.slider(
        "图片压缩质量",
        min_value=10,
        max_value=95,
        value=75,
        help="数值越小，文件体积越小，画质越低"
    )
    st.caption("💡 图片推荐：70~85几乎无损；50~65均衡；40以下画质明显下降")

tab1, tab2 = st.tabs(["📄 PDF压缩", "🖼️ 图片压缩"])

# PDF压缩面板
with tab1:
    st.subheader("PDF 文件压缩（图片重采样）")
    st.info("💡 采用图片重采样压缩，适合扫描版、图片多的PDF；压缩后文字不可复制，纯文字电子PDF不建议使用")
    pdf_file = st.file_uploader("上传PDF", type=["pdf"])

    if pdf_file:
        if st.button("开始压缩PDF"):
            with st.spinner("正在压缩..."):
                tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                tmp_in.write(pdf_file.read())
                tmp_in.close()

                tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                tmp_out.close()

                try:
                    compress_pdf(tmp_in.name, tmp_out.name, quality_pdf)
                    with open(tmp_out.name, "rb") as f:
                        data = f.read()

                    # 标准节省比例公式
                    origin_size = pdf_file.size
                    compressed_size = os.path.getsize(tmp_out.name)
                    reduce_rate = (origin_size - compressed_size) / origin_size * 100

                    st.success("✅ PDF压缩完成！")
                    # 三列卡片展示对比数据
                    col1, col2, col3 = st.columns(3)
                    col1.metric("原始大小", format_size(origin_size))
                    col2.metric("压缩后大小", format_size(compressed_size))
                    # 动态修改文案，优化负数观感
                    if reduce_rate >= 0:
                        col3.metric("空间节省", f"{reduce_rate:.1f}%")
                    else:
                        col3.metric("体积膨胀", f"{abs(reduce_rate):.1f}%")

                    st.download_button("📥 下载压缩后的PDF", data, file_name="compressed.pdf")
                except Exception as e:
                    st.error(f"❌ 压缩失败：{e}")
                finally:
                    os.unlink(tmp_in.name)
                    os.unlink(tmp_out.name)

# 图片压缩面板（含优化2：压缩前后对比预览）
with tab2:
    st.subheader("图片压缩（JPG/PNG）")
    st.info("💡PNG：智能调色板压缩，自动保留透明通道\n💡JPG：有损压缩，数值越低画质越模糊、体积越小")
    img_file = st.file_uploader("上传图片", type=["jpg", "jpeg", "png"])

    if img_file:
        # 获取原始后缀
        origin_name = img_file.name
        suffix = origin_name.split(".")[-1].lower()

        # 读取原图用于预览
        original_img = Image.open(img_file)
        img_file.seek(0)  # 重置文件指针，保证后续读取正常

        if st.button("开始压缩图片"):
            with st.spinner("正在压缩..."):
                tmp_in = tempfile.NamedTemporaryFile(delete=False)
                tmp_in.write(img_file.read())
                tmp_in.close()

                tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}")
                tmp_out.close()

                try:
                    compress_image(tmp_in.name, tmp_out.name, quality_img, suffix)
                    with open(tmp_out.name, "rb") as f:
                        data = f.read()

                    origin_size = img_file.size
                    compressed_size = os.path.getsize(tmp_out.name)
                    reduce_rate = (origin_size - compressed_size) / origin_size * 100

                    st.success("✅ 图片压缩完成！")

                    # ===================== 优化2：压缩前后图片左右对比预览 =====================
                    col_pre, col_after = st.columns(2)
                    with col_pre:
                        st.markdown("**🖼️ 原图**")
                        st.image(original_img, use_column_width=True)
                        st.caption(f"文件大小：{format_size(origin_size)}")
                    with col_after:
                        st.markdown("**✅ 压缩后**")
                        compressed_img = Image.open(tmp_out.name)
                        st.image(compressed_img, use_column_width=True)
                        st.caption(f"文件大小：{format_size(compressed_size)}")

                    st.divider()

                    # 三列数据统计
                    col1, col2, col3 = st.columns(3)
                    col1.metric("原始大小", format_size(origin_size))
                    col2.metric("压缩后大小", format_size(compressed_size))
                    if reduce_rate >= 0:
                        col3.metric("空间节省", f"{reduce_rate:.1f}%")
                    else:
                        col3.metric("体积膨胀", f"{abs(reduce_rate):.1f}%")

                    st.download_button("📥 下载压缩图片", data, file_name=f"compressed.{suffix}")
                except Exception as e:
                    st.error(f"❌ 压缩失败：{e}")
                finally:
                    os.unlink(tmp_in.name)
                    os.unlink(tmp_out.name)