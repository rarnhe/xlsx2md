import argparse
import os
import shutil
import sys
import openpyxl
from PIL import Image as PILImage


def get_image_row_and_col(img):
    """兼容不同 openpyxl 版本的图片位置获取逻辑"""
    if hasattr(img, "anchor") and hasattr(img.anchor, "_from"):
        return img.anchor._from.row + 1, img.anchor._from.col + 1
    elif hasattr(img, "_from") and img._from is not None:
        return img._from.row + 1, img._from.col + 1
    elif hasattr(img, "anchor") and hasattr(img.anchor, "to"):
        return img.anchor.to.row + 1, img.anchor.to.col + 1

    return None, None


def format_multi_note_text(text_str):
    """按换行符拆分文本，并将每一条注渲染为独立的灰色背景框"""
    lines = [line.strip() for line in text_str.splitlines() if line.strip()]
    if not lines:
        return ""

    card_style = (
        "margin: 0 0 8px 0; padding: 8px 12px; background-color: #f5f5f5;"
        " border-radius: 6px; box-sizing: border-box; line-height: 1.5;"
    )

    if len(lines) == 1:
        return (
            f'<div style="{card_style}">'
            '<span style="color: #007bff; font-weight: bold;">注：</span>'
            f"{lines[0]}</div>"
        )

    formatted_cards = []
    total_lines = len(lines)

    for idx, line in enumerate(lines, start=1):
        current_style = (
            card_style
            if idx < total_lines
            else card_style.replace("margin: 0 0 8px 0;", "margin: 0;")
        )
        card_html = (
            f'<div style="{current_style}">'
            f'<span style="color: #007bff; font-weight: bold;">注{idx}：</span>'
            f"{line}</div>"
        )
        formatted_cards.append(card_html)

    return "".join(formatted_cards)


def remove_sheet_dir_if_exists(sheet_dir):
    """辅助函数：如果同名子文件夹存在，则递归彻底删除"""
    if os.path.exists(sheet_dir):
        shutil.rmtree(sheet_dir)


def process_single_sheet(ws, sheet_dir, sheet_title):
    """专门处理单个 Sheet 的导出逻辑"""
    image_dict = {}
    if hasattr(ws, "_images"):
        for img in ws._images:
            row, col = get_image_row_and_col(img)
            if row is None or col is None:
                continue
            if col == 1:
                img_filename = f"img_row_{row}.png"
                image_dict[row] = img_filename

    max_text_row = ws.max_row
    max_img_row = max(image_dict.keys()) if image_dict else 0
    max_row = max(max_text_row, max_img_row)

    # -------------------------------------------------------------
    # 校验 1：扫描整张 Sheet，只要 A 列出现文字（无论在哪一行），直接跳过
    # -------------------------------------------------------------
    for row in range(1, max_row + 1):
        val_a = ws.cell(row=row, column=1).value
        txt_a = str(val_a).strip() if val_a is not None else ""
        if txt_a:
            print(f"  [-] Sheet '{sheet_title}' 跳过转换 (A 列第 {row} 行存在文字)")
            remove_sheet_dir_if_exists(sheet_dir)  # 跳过时清理已有同名文件夹
            return False

    # -------------------------------------------------------------
    # 校验 2：检查“第一个识别到的有效行”
    # -------------------------------------------------------------
    first_valid_row_type = None
    for row in range(1, max_row + 1):
        has_img = row in image_dict
        val = ws.cell(row=row, column=2).value
        txt = str(val).strip() if val is not None else ""

        if not has_img and not txt:
            continue

        if has_img:
            first_valid_row_type = "image"
        elif txt:
            first_valid_row_type = "text_only"
        break

    if first_valid_row_type != "text_only":
        print(f"  [-] Sheet '{sheet_title}' 跳过转换 (首个有效行非 'A列无图且B列有文字')")
        remove_sheet_dir_if_exists(sheet_dir)  # 跳过时清理已有同名文件夹
        return False

    # -------------------------------------------------------------
    # 确认符合条件后，重新创建/刷新目标同名文件夹
    # -------------------------------------------------------------
    remove_sheet_dir_if_exists(sheet_dir)
    os.makedirs(sheet_dir, exist_ok=True)

    if hasattr(ws, "_images"):
        for img in ws._images:
            row, col = get_image_row_and_col(img)
            if row and col == 1:
                img_save_path = os.path.join(sheet_dir, image_dict[row])
                pil_img = PILImage.open(img.ref)
                pil_img.save(img_save_path)
                image_dict[row] = f"./{image_dict[row]}"

    output_md_path = os.path.join(sheet_dir, f"{sheet_title}.md")
    md_blocks = []
    text_counter = 1

    for row in range(1, max_row + 1):
        has_image = row in image_dict
        text_val = ws.cell(row=row, column=2).value
        text_str = str(text_val).strip() if text_val is not None else ""

        if not has_image and not text_str:
            continue

        if has_image:
            img_rel_path = image_dict[row]
            left_content = f"![Image Row {row}]({img_rel_path})"

            if text_str:
                right_content = format_multi_note_text(text_str)
                right_style = (
                    "flex: 0 0 20%; max-width: 20%; padding-left: 15px;"
                    " box-sizing: border-box; align-self: flex-start;"
                )
            else:
                right_content = ""
                right_style = (
                    "flex: 0 0 20%; max-width: 20%; padding-left: 15px;"
                    " box-sizing: border-box;"
                )

            row_md = f"""<div style="display: flex; width: 100%; margin-bottom: 1.5rem; align-items: flex-start;">
  <div style="flex: 0 0 80%; max-width: 80%; padding-right: 15px; box-sizing: border-box;">

{left_content}

  </div>
  <div style="{right_style}">{right_content}</div>
</div>"""

        elif text_str:
            title_text = f"### {text_counter}.{text_str}"
            text_counter += 1

            row_md = f"""<div style="display: flex; width: 100%; margin-bottom: 1.5rem; align-items: flex-start;">
  <div style="flex: 0 0 70%; max-width: 70%; padding-right: 15px; box-sizing: border-box;">

  </div>
  <div style="flex: 0 0 30%; max-width: 30%; padding-left: 15px; box-sizing: border-box;">

{title_text}

  </div>
</div>"""

        md_blocks.append(row_md)

    final_md_content = "\n\n".join(md_blocks) + "\n"

    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write(final_md_content)

    print(f"  [√] Sheet '{sheet_title}' 处理完成 -> {output_md_path}")
    return True


def get_default_excel_path():
    """Locate the existing xlsx2md.xlsx beside the repository root."""
    if "__file__" not in globals():
        print("❌ 错误: 无法确定当前脚本文件名（缺少 __file__ 上下文）！")
        sys.exit(1)

    script_path = os.path.abspath(__file__)
    current_dir = os.path.dirname(script_path)
    target_excel_name = "xlsx2md.xlsx"
    target_excel = os.path.join(current_dir, target_excel_name)

    if not os.path.exists(target_excel):
        print(f"❌ 错误: 未找到与脚本同名的 Excel 文件 '{target_excel_name}'！")
        print(f"期待的物理路径: {target_excel}")
        sys.exit(1)

    return target_excel


def process_excel_to_markdown(target_sheet_name=None):
    excel_path = get_default_excel_path()

    base_name = os.path.splitext(os.path.basename(excel_path))[0]
    excel_dir = os.path.dirname(os.path.abspath(excel_path))

    root_target_dir = os.path.abspath(os.path.join(excel_dir, "..", base_name))
    os.makedirs(root_target_dir, exist_ok=True)

    print(f"正在读取默认文件: {excel_path}")
    print(f"主输出目录 (位于 ../): {root_target_dir}\n")

    wb = openpyxl.load_workbook(excel_path, data_only=True)

    if target_sheet_name:
        if target_sheet_name in wb.sheetnames:
            sheets_to_process = [wb[target_sheet_name]]
        else:
            print(
                f"❌ 错误: 在 '{os.path.basename(excel_path)}' 中未找到名为 '{target_sheet_name}' 的 Sheet！"
            )
            print(f"💡 文件中可用的 Sheet 列表为: {wb.sheetnames}")
            sys.exit(1)
    else:
        print("未指定 Sheet 名称，将尝试转换所有符合条件的 Sheet...\n")
        sheets_to_process = wb.worksheets

    for ws in sheets_to_process:
        sheet_title = ws.title
        sheet_dir = os.path.join(root_target_dir, sheet_title)
        process_single_sheet(ws, sheet_dir, sheet_title)

    print(f"\n处理完成！文件已存入主目录: {root_target_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="与脚本同名的 Excel 专用 Sheet 转 Markdown 工具"
    )
    parser.add_argument(
        "sheet",
        nargs="?",
        default=None,
        help="可选: 指定只转换某个特定的 Sheet 名称",
    )

    args = parser.parse_args()
    process_excel_to_markdown(args.sheet)