#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
众测结果统计工具
分析所有用户的打标结果，生成统计报告
"""

import os
import json
import glob
from collections import defaultdict
from datetime import datetime

# 配置
RESULTS_FOLDER = os.path.expanduser("~/Desktop/模特图效果跑批/crowdtest/results")
OUTPUT_FOLDER = os.path.expanduser("~/Desktop/模特图效果跑批/crowdtest/statistics")

VERSION_NAMES = {
    'simple': '简单版',
    'extended': '扩展版',
    'no_reference': '不垫图版',
    'no_reference_model': '不垫图版模特',
    'none': '都不满意'
}


def load_all_results():
    """加载所有结果文件"""
    all_results = []
    
    # 从 results 文件夹加载
    if os.path.exists(RESULTS_FOLDER):
        for filepath in glob.glob(os.path.join(RESULTS_FOLDER, "*.json")):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    all_results.append(data)
            except Exception as e:
                print(f"  警告：无法加载 {filepath}: {e}")
    
    # 从下载的文件加载（在 crowdtest 目录下）
    crowdtest_folder = os.path.dirname(RESULTS_FOLDER)
    for filepath in glob.glob(os.path.join(crowdtest_folder, "result_*.json")):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_results.append(data)
        except Exception as e:
            print(f"  警告：无法加载 {filepath}: {e}")
    
    return all_results


def analyze_results(all_results):
    """分析所有结果"""
    
    # 统计数据结构
    stats = {
        'total_users': 0,
        'total_evaluations': 0,
        'version_counts': defaultdict(int),
        'product_stats': defaultdict(lambda: defaultdict(int)),
        'user_stats': defaultdict(lambda: defaultdict(int)),
        'detailed_records': []
    }
    
    seen_users = set()
    
    for submission in all_results:
        user_id = submission.get('userId', 'unknown')
        timestamp = submission.get('timestamp', '')
        results = submission.get('results', [])
        
        if user_id not in seen_users:
            seen_users.add(user_id)
            stats['total_users'] += 1
        
        for result in results:
            product_id = result.get('productId', '')
            product_name = result.get('productName', '')
            order = result.get('order', [])
            
            # 支持新的多选格式和旧的单选格式
            selections = result.get('selections', [])
            is_none = result.get('isNone', False)
            
            # 兼容旧格式
            if not selections and not is_none:
                old_selection = result.get('selection', '')
                if old_selection == 'none':
                    is_none = True
                elif old_selection:
                    selections = [old_selection]
            
            if is_none:
                stats['total_evaluations'] += 1
                stats['version_counts']['none'] += 1
                stats['product_stats'][product_id]['none'] += 1
                stats['user_stats'][user_id]['none'] += 1
                
                stats['detailed_records'].append({
                    'user_id': user_id,
                    'product_id': product_id,
                    'product_name': product_name,
                    'selections': [],
                    'selection_names': '都不满意',
                    'is_none': True,
                    'display_order': order,
                    'timestamp': timestamp
                })
            elif selections:
                stats['total_evaluations'] += 1
                
                for sel in selections:
                    stats['version_counts'][sel] += 1
                    stats['product_stats'][product_id][sel] += 1
                    stats['user_stats'][user_id][sel] += 1
                
                selection_names = [VERSION_NAMES.get(s, s) for s in selections]
                
                stats['detailed_records'].append({
                    'user_id': user_id,
                    'product_id': product_id,
                    'product_name': product_name,
                    'selections': selections,
                    'selection_names': '|'.join(selection_names),
                    'is_none': False,
                    'display_order': order,
                    'timestamp': timestamp
                })
    
    return stats


def generate_report(stats):
    """生成统计报告"""
    
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("           众测结果统计报告")
    report_lines.append("=" * 60)
    report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    # 总体统计
    report_lines.append("【总体统计】")
    report_lines.append(f"  参与用户数: {stats['total_users']}")
    report_lines.append(f"  总评测数: {stats['total_evaluations']}")
    report_lines.append("")
    
    # 各版本得票统计
    report_lines.append("【各版本得票统计】")
    total = stats['total_evaluations']
    for version in ['simple', 'extended', 'no_reference', 'no_reference_model', 'none']:
        count = stats['version_counts'].get(version, 0)
        percentage = (count / total * 100) if total > 0 else 0
        name = VERSION_NAMES.get(version, version)
        bar = "█" * int(percentage / 2) + "░" * (50 - int(percentage / 2))
        report_lines.append(f"  {name:12s}: {count:4d} 票 ({percentage:5.1f}%) {bar}")
    report_lines.append("")
    
    # 各商品统计
    report_lines.append("【各商品统计】")
    for product_id in sorted(stats['product_stats'].keys(), key=lambda x: int(x) if x.isdigit() else 0):
        product_data = stats['product_stats'][product_id]
        total_votes = sum(product_data.values())
        
        report_lines.append(f"  商品{product_id}:")
        for version in ['simple', 'extended', 'no_reference', 'no_reference_model', 'none']:
            count = product_data.get(version, 0)
            percentage = (count / total_votes * 100) if total_votes > 0 else 0
            name = VERSION_NAMES.get(version, version)
            report_lines.append(f"    {name:12s}: {count:2d} 票 ({percentage:5.1f}%)")
        report_lines.append("")
    
    # 用户统计
    report_lines.append("【用户统计】")
    for user_id, user_data in sorted(stats['user_stats'].items()):
        total_votes = sum(user_data.values())
        report_lines.append(f"  用户 [{user_id}] (共 {total_votes} 票):")
        for version in ['simple', 'extended', 'no_reference', 'no_reference_model', 'none']:
            count = user_data.get(version, 0)
            if count > 0:
                name = VERSION_NAMES.get(version, version)
                report_lines.append(f"    {name}: {count} 票")
        report_lines.append("")
    
    report_lines.append("=" * 60)
    
    return "\n".join(report_lines)


def generate_csv(stats):
    """生成 CSV 详细记录"""
    lines = ["用户ID,商品ID,商品名称,选择版本,选择版本名称,是否都不满意,显示顺序,时间戳"]
    
    for record in stats['detailed_records']:
        order_str = "|".join(record['display_order']) if record['display_order'] else ""
        selections_str = "|".join(record.get('selections', [])) if record.get('selections') else ""
        is_none_str = "是" if record.get('is_none', False) else "否"
        lines.append(f"{record['user_id']},{record['product_id']},{record['product_name']},"
                    f"{selections_str},{record.get('selection_names', '')},{is_none_str},{order_str},{record['timestamp']}")
    
    return "\n".join(lines)


def generate_json_summary(stats):
    """生成 JSON 汇总"""
    summary = {
        'generated_at': datetime.now().isoformat(),
        'total_users': stats['total_users'],
        'total_evaluations': stats['total_evaluations'],
        'version_summary': {
            VERSION_NAMES.get(k, k): v 
            for k, v in stats['version_counts'].items()
        },
        'version_percentages': {},
        'product_stats': {},
        'user_stats': {}
    }
    
    total = stats['total_evaluations']
    for version, count in stats['version_counts'].items():
        name = VERSION_NAMES.get(version, version)
        summary['version_percentages'][name] = round(count / total * 100, 2) if total > 0 else 0
    
    for product_id, data in stats['product_stats'].items():
        summary['product_stats'][f"商品{product_id}"] = {
            VERSION_NAMES.get(k, k): v for k, v in data.items()
        }
    
    for user_id, data in stats['user_stats'].items():
        summary['user_stats'][user_id] = {
            VERSION_NAMES.get(k, k): v for k, v in data.items()
        }
    
    return summary


def main():
    print("=" * 50)
    print("  众测结果统计工具")
    print("=" * 50)
    print()
    
    # 加载所有结果
    print("正在加载结果文件...")
    all_results = load_all_results()
    
    if not all_results:
        print("\n没有找到任何结果文件！")
        print(f"请将结果文件放入: {RESULTS_FOLDER}")
        print("或确保下载的 result_*.json 文件在 crowdtest 目录下")
        return
    
    print(f"  找到 {len(all_results)} 个结果文件")
    print()
    
    # 分析结果
    print("正在分析结果...")
    stats = analyze_results(all_results)
    
    # 创建输出目录
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    # 生成报告
    report = generate_report(stats)
    print()
    print(report)
    
    # 保存文件
    report_path = os.path.join(OUTPUT_FOLDER, "report.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n✓ 报告已保存: {report_path}")
    
    csv_path = os.path.join(OUTPUT_FOLDER, "detailed_records.csv")
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write(generate_csv(stats))
    print(f"✓ CSV 详细记录已保存: {csv_path}")
    
    json_path = os.path.join(OUTPUT_FOLDER, "summary.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(generate_json_summary(stats), f, ensure_ascii=False, indent=2)
    print(f"✓ JSON 汇总已保存: {json_path}")


if __name__ == "__main__":
    main()

