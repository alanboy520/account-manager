#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试统计功能脚本
用于验证用户使用数量统计功能是否正常工作
"""

import os
import sys
from usage_stats import record_app_launch, record_feature_usage, get_stats_summary

def test_stats():
    """测试统计功能"""
    print("=== 测试用户使用数量统计功能 ===")
    
    # 测试应用启动
    print("1. 测试应用启动统计...")
    record_app_launch()
    print("✓ 应用启动统计已记录")
    
    # 测试各种功能使用
    print("2. 测试功能使用统计...")
    record_feature_usage("password_verify_success")
    record_feature_usage("add_account")
    record_feature_usage("delete_account")
    record_feature_usage("update_account")
    record_feature_usage("add_website")
    print("✓ 所有功能使用统计已记录")
    
    # 显示统计结果
    print("3. 查看统计结果...")
    stats = get_stats_summary()
    print("\n当前统计信息:")
    print(f"应用启动次数: {stats.get('app_launches', 0)}")
    print(f"密码验证成功: {stats.get('password_verify_success', 0)}")
    print(f"密码验证失败: {stats.get('password_verify_failed', 0)}")
    print(f"添加账号次数: {stats.get('add_account', 0)}")
    print(f"删除账号次数: {stats.get('delete_account', 0)}")
    print(f"更新账号次数: {stats.get('update_account', 0)}")
    print(f"添加网站次数: {stats.get('add_website', 0)}")
    
    # 检查数据文件
    stats_file = os.path.join(os.path.dirname(__file__), "usage_stats.json")
    if os.path.exists(stats_file):
        print(f"\n✓ 统计数据文件已创建: {stats_file}")
        print(f"文件大小: {os.path.getsize(stats_file)} 字节")
    else:
        print(f"\n✗ 统计数据文件未找到: {stats_file}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_stats()
    input("按任意键退出...")