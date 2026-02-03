#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 markitdown 将文件转换为 Markdown 并按类型分流实现。
提供统一接口 convert_to_markdown_unified，改为传入 E2B 沙箱 ID 与沙箱保存路径；
output_path。如果不传 output_path，则不进行本地保存。
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from markitdown import MarkItDown
from e2b import Sandbox


def save_markdown(text: str, out_path: Path) -> Path:
    """保存 Markdown 文本到指定路径"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    return out_path


def convert_with_markitdown(file_path: str) -> str:
    """通用的 markitdown 转换入口"""
    md = MarkItDown(enable_plugins=False)
    result = md.convert(file_path)
    # 兼容不同版本的返回结构
    text = getattr(result, "text_content", None)
    return text if isinstance(text, str) else str(result)


# ---- 各类型处理函数（可按需要细化实现） ----

def convert_pdf(file_path: str) -> str:
    return convert_with_markitdown(file_path)


def convert_ppt(file_path: str) -> str:
    return convert_with_markitdown(file_path)


def convert_xlsx(file_path: str) -> str:
    return convert_with_markitdown(file_path)


def convert_csv(file_path: str) -> str:
    return convert_with_markitdown(file_path)


def detect_type(file_path: str) -> str:
    """根据扩展名识别文件类型"""
    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix in [".ppt", ".pptx"]:
        return "ppt"
    if suffix in [".xlsx", ".xls"]:
        return "xlsx"
    if suffix == ".csv":
        return "csv"
    return "unknown"


# ---- 统一的对外调用接口与统一返回值 ----

def convert_to_markdown_unified(
    file_path: str,
    sandbox_id: str,
    sandbox_path: str,
    output_path: Optional[str] = None,
    sbx: Optional[Sandbox] = None,
) -> Dict[str, Any]:
    """
    统一入口（通过沙箱 ID 指定沙箱）：
    - 根据文件类型选择转换实现
    - 若提供 output_path，则保存到本地 .md；否则本地不保存
    - 连接到指定沙箱（通过 sandbox_id），保存到 E2B 沙箱 sandbox_path（必做）

    返回统一结构：
    {
      'input_path': <输入文件绝对路径>,
      'file_type': <识别到的类型: pdf/ppt/xlsx/csv/unknown>,
      'local_path': <本地保存的 md 文件绝对路径或 None>,
      'sandbox_path': <沙箱保存的目标路径>,
    }
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"输入文件不存在: {file_path}")

    file_type = detect_type(file_path)

    if file_type == "pdf":
        markdown = convert_pdf(file_path)
    elif file_type == "ppt":
        markdown = convert_ppt(file_path)
    elif file_type == "xlsx":
        markdown = convert_xlsx(file_path)
    elif file_type == "csv":
        markdown = convert_csv(file_path)
    else:
        markdown = convert_with_markitdown(file_path)

    local_path_str: Optional[str] = None
    if output_path:
        out_path = Path(output_path)
        save_markdown(markdown, out_path)
        local_path_str = str(out_path.resolve())

    # 通过传入的沙箱实例或 ID 连接到沙箱并保存
    sbx_inst = sbx or Sandbox.connect(sandbox_id)
    sbx_inst.files.write(sandbox_path, markdown)

    return {
        "input_path": str(Path(file_path).resolve()),
        "file_type": file_type,
        "local_path": local_path_str,
        "sandbox_path": sandbox_path,
    }


def main():

    load_dotenv()

    # 创建一个沙箱，获取其 ID，然后通过统一接口（传 ID）进行保存
    sandbox = Sandbox.create(timeout=60)
    try:
        sandbox_id = getattr(sandbox, "sandbox_id", None) or getattr(sandbox, "sandboxId", None)
        if not sandbox_id:
            raise RuntimeError("无法获取沙箱 ID")

        result = convert_to_markdown_unified(
            file_path="data/test.xlsx",
            sandbox_id=sandbox_id,
            sandbox_path="/home/user/test_unified_by_id.md",
            output_path=None,  # 不保存本地
        )
        print(f"输入: {result['input_path']}")
        print(f"类型: {result['file_type']}")
        print(f"本地保存: {result['local_path']}")
        print(f"沙箱保存: {result['sandbox_path']}")
    finally:
        sandbox.kill()
        print("沙箱已关闭。")


if __name__ == "__main__":
    main()
