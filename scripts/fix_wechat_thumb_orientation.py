"""修复微信图片「原图」与「缩略图」方向不一致的问题

背景
----
旧版上传逻辑（app/modules/wechat/upload.py）存在两处不一致：

1. 保存原图时直接保存 PIL 读出来的原始像素，没有做 EXIF 方向归一化；
   而 PIL 保存 JPEG/PNG 时默认丢弃 EXIF 段，Orientation 标记随之消失。
   → 手机横拍照片（EXIF Orientation=6）在磁盘上是"侧躺"的原始像素。

2. 生成缩略图时却调用了 ImageOps.exif_transpose()，得到的是正立版本。

结果：大图（灯箱上方）与缩略图（下方）相差 90°，看起来像两张不同的照片。

处理
----
对每一组「原图 + 同名 _thumb.webp」：

1. 先算出浏览器实际显示的朝向（原图经 EXIF 归一化后的结果）；
2. 若浏览器显示的朝向已经和缩略图一致 → 跳过；
3. 否则找出能让原图像素与缩略图对齐的旋转角，把原图转正后覆盖保存；
   JPEG 走 jpegtran（无损，不重新压缩），其余格式走 Pillow；
4. 同步更新 wechat_messages.image_urls 里记录的 width/height。

原图在改写前会备份到 uploads/_backup_orientation_fix/。

用法
----
    python scripts/fix_wechat_thumb_orientation.py --dry-run   # 只看会改什么
    python scripts/fix_wechat_thumb_orientation.py             # 实际执行
"""
import os
import sys
import io
import glob
import json
import shutil
import sqlite3
import argparse
import subprocess
import tempfile

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(PROJECT_ROOT, "static", "wechat", "uploads")
THUMB_DIR = os.path.join(UPLOAD_DIR, "thumbs")
BACKUP_DIR = os.path.join(UPLOAD_DIR, "_backup_orientation_fix")
DB_PATH = os.path.join(PROJECT_ROOT, "instance", "copyez.db")

ANGLES = (0, 90, 180, 270)

# MSE 低于该值视为"同一张图"
MATCH_MSE = 900.0


def _vector(image):
    """把图片缩成 48x48 灰度向量，用于比较内容是否一致。"""
    from PIL import Image

    if image.mode != "L":
        image = image.convert("L")
    width, height = image.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    cropped = image.crop((left, top, left + side, top + side))
    cropped = cropped.resize((48, 48), Image.Resampling.LANCZOS)
    return list(cropped.getdata())


def _mse(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b)) / len(a)


def _find_original(stem):
    for ext in ("jpg", "jpeg", "png", "webp", "gif"):
        candidate = os.path.join(UPLOAD_DIR, f"{stem}.{ext}")
        if os.path.isfile(candidate):
            return candidate
    return None


def _transpose(image, angle):
    """逆时针旋转 90° 的整数倍（无损，像素一一对应）。"""
    from PIL import Image

    if angle == 0:
        return image
    method = {
        90: Image.Transpose.ROTATE_90,
        180: Image.Transpose.ROTATE_180,
        270: Image.Transpose.ROTATE_270,
    }[angle]
    return image.transpose(method)


def _jpegtran_available():
    return shutil.which("jpegtran") is not None


def _rotate_jpeg_lossless(src_path, angle):
    """用 jpegtran 无损旋转 JPEG（不重新压缩，画质零损失）。

    jpegtran 的角度是顺时针，脚本内部用逆时针，两者差 360 取反。
    """
    clockwise = (360 - angle) % 360
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        subprocess.run(
            ["jpegtran", "-rotate", str(clockwise), "-copy", "all",
             "-outfile", tmp_path, src_path],
            check=True, capture_output=True,
        )
        shutil.move(tmp_path, src_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def _rotate_with_pillow(src_path, image, angle, fmt):
    """Pillow 兜底：重新编码保存（仅用于 PNG/WEBP 等 jpegtran 不支持的格式）。"""
    rotated = _transpose(image, angle)
    fmt = (fmt or "").upper()
    if fmt == "PNG":
        rotated.save(src_path, format="PNG", optimize=True)
    elif fmt == "WEBP":
        rotated.save(src_path, format="WEBP", quality=90, method=6)
    else:
        rotated.convert("RGB").save(src_path, format="JPEG", quality=90,
                                    optimize=True, progressive=True)


def _update_db_dims(stem, new_size):
    """把数据库里记录的 width/height 更新为新的像素尺寸。"""
    if not os.path.exists(DB_PATH):
        return 0

    updated = 0
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT id, image_urls FROM wechat_messages WHERE image_urls LIKE ?",
            (f"%{stem}%",),
        )
        rows = cur.fetchall()
        for msg_id, raw in rows:
            try:
                items = json.loads(raw)
                if isinstance(items, str):
                    items = json.loads(items)
            except (TypeError, ValueError):
                continue
            if not isinstance(items, list):
                continue

            changed = False
            for item in items:
                if not isinstance(item, dict):
                    continue
                url = item.get("url") or ""
                if not url:
                    continue
                if os.path.splitext(os.path.basename(url))[0] != stem:
                    continue
                if item.get("width") != new_size[0] or item.get("height") != new_size[1]:
                    item["width"], item["height"] = new_size[0], new_size[1]
                    changed = True

            if changed:
                cur.execute(
                    "UPDATE wechat_messages SET image_urls = ? WHERE id = ?",
                    (json.dumps(items, ensure_ascii=False, sort_keys=True), msg_id),
                )
                updated += 1
        con.commit()
    finally:
        con.close()
    return updated


def main():
    parser = argparse.ArgumentParser(description="修复微信图片原图/缩略图方向错位")
    parser.add_argument("--dry-run", action="store_true", help="只报告，不修改文件")
    args = parser.parse_args()

    from PIL import Image, ImageOps

    if not os.path.isdir(THUMB_DIR):
        print(f"[ERROR] 缩略图目录不存在: {THUMB_DIR}")
        return 1

    use_jpegtran = _jpegtran_available()
    print(f"扫描缩略图 {len(glob.glob(os.path.join(THUMB_DIR, '*.webp')))} 个，目录: {THUMB_DIR}")
    print(f"JPEG 无损旋转工具 jpegtran: {'可用' if use_jpegtran else '不可用（改用 Pillow）'}")
    if not args.dry_run:
        os.makedirs(BACKUP_DIR, exist_ok=True)
    print()

    fixed, failed, skipped = [], [], 0

    for thumb_path in sorted(glob.glob(os.path.join(THUMB_DIR, "*.webp"))):
        thumb_name = os.path.basename(thumb_path)
        stem = thumb_name[:-len("_thumb.webp")]
        orig_path = _find_original(stem)
        if not orig_path:
            skipped += 1
            continue

        with Image.open(thumb_path) as thumb_img:
            thumb_vec = _vector(thumb_img)

        with Image.open(orig_path) as orig_img:
            orig_format = orig_img.format
            exif = dict(orig_img.getexif())
            orientation = exif.get(274)
            raw = orig_img.convert("RGB")

        # 浏览器实际显示的朝向（带 EXIF 归一化）
        displayed = ImageOps.exif_transpose(raw.copy()) if orientation not in (None, 1) else raw
        if _mse(thumb_vec, _vector(displayed)) < MATCH_MSE:
            skipped += 1
            continue

        # 原图需要转多少度才能和缩略图对齐
        scores = {}
        for angle in ANGLES:
            scores[angle] = _mse(thumb_vec, _vector(_transpose(raw, angle)))
        best_angle = min(scores, key=scores.get)

        print(f"[错位] {thumb_name}")
        print(f"        原图: {os.path.basename(orig_path)}  EXIF Orientation={orientation}")
        print(f"        旋转 0°={scores[0]:.0f} 90°={scores[90]:.0f} "
              f"180°={scores[180]:.0f} 270°={scores[270]:.0f} → 目标 {best_angle}°（逆时针）")
        print(f"        尺寸: {raw.size} → {_transpose(raw, best_angle).size}")

        if args.dry_run:
            fixed.append((thumb_name, best_angle))
            continue

        backup_path = os.path.join(BACKUP_DIR, os.path.basename(orig_path))
        if not os.path.exists(backup_path):
            shutil.copy2(orig_path, backup_path)

        try:
            if orig_format == "JPEG" and use_jpegtran:
                _rotate_jpeg_lossless(orig_path, best_angle)
            else:
                _rotate_with_pillow(orig_path, raw, best_angle, orig_format)
        except Exception as exc:  # noqa: BLE001
            print(f"        [ERROR] 写回失败: {exc}")
            failed.append((thumb_name, str(exc)))
            continue

        with Image.open(orig_path) as check_img:
            new_size = check_img.size
            after = _mse(thumb_vec, _vector(check_img))
        if after >= MATCH_MSE:
            print(f"        [ERROR] 旋转后校验失败 (MSE={after:.0f})，已还原备份")
            shutil.copy2(backup_path, orig_path)
            failed.append((thumb_name, f"verify mse={after:.0f}"))
            continue

        rows = _update_db_dims(stem, new_size)
        print(f"        [OK] 已旋转 {best_angle}°，新尺寸 {new_size}，"
              f"校验 MSE={after:.0f}，更新 {rows} 条消息尺寸")
        fixed.append((thumb_name, best_angle))

    print()
    print("=" * 60)
    print(f"需要修复: {len(fixed)}  失败: {len(failed)}  已正常/跳过: {skipped}")
    if args.dry_run:
        print("(dry-run，未改动任何文件)")
    else:
        print(f"备份目录: {BACKUP_DIR}")
    for name, reason in failed:
        print(f"  [FAIL] {name}: {reason}")
    print("=" * 60)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
