#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
准备众测数据脚本
扫描跑批结果文件夹，生成 products.json 供众测网页使用
"""

import os
import json
import base64
from pathlib import Path

# 配置
RESULTS_FOLDER = os.path.expanduser("~/Desktop/模特图效果跑批/跑批结果")
OUTPUT_FILE = os.path.expanduser("~/Desktop/模特图效果跑批/crowdtest/products.json")
IMAGES_FOLDER = os.path.expanduser("~/Desktop/模特图效果跑批/crowdtest/images")

# 是否使用 base64 编码（True: 内嵌图片，False: 复制图片文件）
USE_BASE64 = False


def get_image_as_base64(image_path):
    """将图片转换为 base64 数据 URL"""
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    
    ext = os.path.splitext(image_path)[1].lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.webp': 'image/webp'
    }
    mime = mime_types.get(ext, 'image/jpeg')
    
    return f"data:{mime};base64,{data}"


def copy_image(src_path, dest_folder, new_name, product_id):
    """复制图片到目标文件夹"""
    import shutil
    os.makedirs(dest_folder, exist_ok=True)
    
    ext = os.path.splitext(src_path)[1]
    dest_path = os.path.join(dest_folder, new_name + ext)
    shutil.copy2(src_path, dest_path)
    
    return f"images/{product_id}/{new_name}{ext}"


def scan_results():
    """扫描跑批结果文件夹"""
    products = []
    
    if not os.path.exists(RESULTS_FOLDER):
        print(f"错误：跑批结果文件夹不存在: {RESULTS_FOLDER}")
        return products
    
    # 遍历所有商品文件夹
    folders = sorted([f for f in os.listdir(RESULTS_FOLDER) 
                     if os.path.isdir(os.path.join(RESULTS_FOLDER, f)) and f.startswith("商品")])
    
    print(f"找到 {len(folders)} 个商品文件夹")
    
    for folder_name in folders:
        folder_path = os.path.join(RESULTS_FOLDER, folder_name)
        
        # 检查商品图（必须有）
        product_img_path = os.path.join(folder_path, '商品.jpg')
        if not os.path.exists(product_img_path):
            print(f"  跳过 {folder_name}: 缺少 商品.jpg")
            continue
        
        # 检查模特图（至少要有2张才能评测）
        model_images = {
            'simple': '简单版.jpg',
            'extended': '扩展版.jpg',
            'no_reference': '不垫图版.jpg',
            'no_reference_model': '不垫图版模特.jpg'
        }
        
        available_images = {}
        for key, filename in model_images.items():
            filepath = os.path.join(folder_path, filename)
            if os.path.exists(filepath):
                available_images[key] = filepath
        
        if len(available_images) < 2:
            print(f"  跳过 {folder_name}: 模特图不足2张 (只有 {len(available_images)} 张)")
            continue
        
        # 创建商品数据
        product_id = folder_name.replace("商品", "")
        
        if USE_BASE64:
            # 使用 base64 内嵌图片
            product_data = {
                'id': product_id,
                'name': folder_name,
                'productImage': get_image_as_base64(os.path.join(folder_path, '商品.jpg')),
                'images': {
                    'simple': get_image_as_base64(os.path.join(folder_path, '简单版.jpg')),
                    'extended': get_image_as_base64(os.path.join(folder_path, '扩展版.jpg')),
                    'no_reference': get_image_as_base64(os.path.join(folder_path, '不垫图版.jpg'))
                }
            }
        else:
            # 复制图片文件
            product_folder = os.path.join(IMAGES_FOLDER, product_id)
            
            # 构建图片数据（只复制存在的图片）
            images_data = {}
            for key, filepath in available_images.items():
                images_data[key] = copy_image(filepath, product_folder, key, product_id)
            
            product_data = {
                'id': product_id,
                'name': folder_name,
                'productImage': copy_image(product_img_path, product_folder, 'product', product_id),
                'images': images_data
            }
            
            img_count = len(available_images)
            print(f"  ✓ 已处理: {folder_name} ({img_count}张模特图)")
        
        products.append(product_data)
    
    return products


def main():
    print("=" * 50)
    print("  准备众测数据")
    print("=" * 50)
    print()
    
    # 扫描结果
    products = scan_results()
    
    if not products:
        print("\n没有找到可用的商品数据！")
        return
    
    # 保存 JSON
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    
    print()
    print("=" * 50)
    print(f"✓ 已生成 {len(products)} 个商品的众测数据")
    print(f"✓ 数据文件: {OUTPUT_FILE}")
    if not USE_BASE64:
        print(f"✓ 图片文件夹: {IMAGES_FOLDER}")
    print("=" * 50)
    print()
    print("现在可以启动众测服务器：")
    print(f"  cd {os.path.dirname(OUTPUT_FILE)}")
    print("  python3 -m http.server 8888")
    print()
    print("然后在浏览器中打开：http://localhost:8888")


if __name__ == "__main__":
    main()

