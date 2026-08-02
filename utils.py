import fitz
from PIL import Image
import io


def compress_pdf(input_path: str, output_path: str, quality: int):
    """
    PDF有损压缩：每页渲染为JPEG后重建PDF，体积完全由质量参数控制
    quality范围：10~95，数值越小体积越小、画质越低
    适配场景：扫描试卷、课件截图、图片型PDF
    """
    # 质量参数同时控制「分辨率缩放」和「JPEG压缩强度」，双重压缩保证效果
    scale = quality / 100.0
    jpeg_quality = max(10, min(95, quality))

    # 打开原PDF，创建全新空白PDF
    src_doc = fitz.open(input_path)
    new_doc = fitz.open()

    for page in src_doc:
        # 1. 按比例渲染页面为位图
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))

        # 2. 位图转JPEG字节流，用JPEG质量参数控制压缩强度
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img_buffer = io.BytesIO()
        img.save(img_buffer, format="JPEG", quality=jpeg_quality, optimize=True)
        img_bytes = img_buffer.getvalue()

        # 3. 新PDF添加同尺寸页面，仅插入压缩后的图片
        new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
        new_page.insert_image(new_page.rect, stream=img_bytes)

    # 4. 最大化压缩保存
    new_doc.save(output_path, garbage=4, deflate=True, clean=True)
    src_doc.close()
    new_doc.close()


def compress_image(input_path: str, output_path: str, quality: int, suffix: str):
    img = Image.open(input_path)
    suffix = suffix.lower()

    # 通用优化：移除EXIF/缩略图等元数据，减少无效体积
    save_kwargs = {"optimize": True}
    if "exif" in img.info:
        save_kwargs["exif"] = b""

    # 核心：质量值同时控制分辨率缩放，双重压缩，保证滑块效果明显
    # 质量≥95时保留原尺寸，低于95按比例缩放，和PDF逻辑对齐
    scale = quality / 100.0
    if scale < 0.95:
        new_width = int(img.width * scale)
        new_height = int(img.height * scale)
        # 防止尺寸过小
        new_width = max(10, new_width)
        new_height = max(10, new_height)
        # Pillow版本兼容：高低版本都能用
        try:
            resample = Image.Resampling.LANCZOS
        except AttributeError:
            resample = Image.LANCZOS
        img = img.resize((new_width, new_height), resample)

    if suffix == "png":
        # PNG：用颜色数量化替代纯无损压缩，质量越低颜色越少，体积变化明显
        # 质量10→32色，质量95→256色
        color_count = int(32 + (quality / 100) * 224)
        color_count = max(2, min(256, color_count))

        # 判断是否带透明通道
        has_alpha = (img.mode in ("RGBA", "LA")) or (img.mode == "P" and "transparency" in img.info)
        if has_alpha:
            # 带透明：保留alpha，量化颜色+最高无损压缩
            img = img.convert("RGBA")
            quantized_img = img.quantize(colors=color_count, method=2)
            quantized_img.save(output_path, format="PNG", compress_level=9, **save_kwargs)
        else:
            # 无透明：自适应调色板，质量越低颜色越少，体积越小
            img = img.convert("RGB")
            quantized_img = img.quantize(colors=color_count, method=2)
            quantized_img.save(output_path, format="PNG", compress_level=9, **save_kwargs)

    elif suffix in ("jpg", "jpeg"):
        # JPG：分辨率缩放 + 质量压缩，双重保证体积随滑块明显变化
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")
        img.save(output_path, format="JPEG", quality=quality, progressive=True, **save_kwargs)