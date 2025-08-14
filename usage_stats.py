#!/usr/bin/env python3
"""
用户使用统计模块 - 匿名收集使用数据
"""

import json
import requests
import uuid
import platform
import time
from datetime import datetime
from pathlib import Path

class UsageStats:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.stats_file = self.project_dir / 'usage_stats.json'
        self.config_file = self.project_dir / 'stats_config.json'
        self.session_id = None
        self.user_id = None
        
        # GitHub统计API（使用GitHub API统计仓库访问）
        self.github_repo = "alanboy520/account-manager"
        
    def get_or_create_user_id(self):
        """获取或创建匿名用户ID"""
        config = self.load_config()
        if 'user_id' not in config:
            # 创建匿名用户ID（不包含个人信息）
            config['user_id'] = str(uuid.uuid4())[:8]  # 8位随机ID
            config['first_seen'] = datetime.now().isoformat()
            self.save_config(config)
        return config['user_id']
    
    def load_config(self):
        """加载配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def save_config(self, config):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def record_usage(self, action_type="launch"):
        """记录使用数据"""
        try:
            user_id = self.get_or_create_user_id()
            
            # 收集匿名数据
            usage_data = {
                "user_id": user_id,  # 匿名ID
                "action": action_type,
                "timestamp": datetime.now().isoformat(),
                "version": "4.1.0",
                "platform": platform.system(),
                "platform_version": platform.version(),
                "python_version": platform.python_version(),
                "session_id": str(uuid.uuid4())[:6]
            }
            
            # 保存到本地文件
            self.save_usage_data(usage_data)
            
            # 发送到GitHub统计（通过API调用）
            self.send_to_github_stats(usage_data)
            
            return True
        except Exception as e:
            print(f"统计记录失败: {e}")
            return False
    
    def save_usage_data(self, data):
        """保存使用数据到本地"""
        try:
            stats = []
            if self.stats_file.exists():
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
            
            stats.append(data)
            
            # 只保留最近100条记录
            stats = stats[-100:]
            
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def send_to_github_stats(self, data):
        """发送到GitHub统计"""
        try:
            # 使用GitHub API获取仓库信息（作为统计）
            url = f"https://api.github.com/repos/{self.github_repo}"
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'account-manager-stats'
            }
            
            # 这里可以扩展为实际的统计API
            # 目前使用GitHub仓库访问作为间接统计
            response = requests.get(url, headers=headers, timeout=3)
            if response.status_code == 200:
                repo_data = response.json()
                return True
        except:
            pass
        return False
    
    def get_usage_summary(self):
        """获取使用统计摘要"""
        try:
            if not self.stats_file.exists():
                return {"total_users": 0, "total_uses": 0}
            
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
            
            unique_users = len(set(s['user_id'] for s in stats))
            total_uses = len(stats)
            
            # 按日期统计
            daily_stats = {}
            for stat in stats:
                date = stat['timestamp'][:10]
                daily_stats[date] = daily_stats.get(date, 0) + 1
            
            return {
                "total_users": unique_users,
                "total_uses": total_uses,
                "daily_stats": daily_stats,
                "last_update": datetime.now().isoformat()
            }
        except:
            return {"total_users": 0, "total_uses": 0}
    
    def show_privacy_info(self):
        """显示隐私信息"""
        return """
        📊 使用统计说明
        
        我们收集以下匿名数据：
        ✅ 软件启动次数（无个人信息）
        ✅ 系统类型（Windows/Linux/Mac）
        ✅ 软件版本号
        ✅ 匿名用户ID（随机生成，不含个人信息）
        
        ❌ 不收集：
        × 密码或账号信息
        × 个人身份信息
        × 文件内容
        × IP地址或地理位置
        
        数据仅用于改进软件体验，可随时删除 usage_stats.json 文件清除记录。
        """

# 全局统计实例
stats = UsageStats()

def record_app_launch():
    """记录应用启动"""
    return stats.record_usage("launch")

def record_feature_usage(feature_name):
    """记录功能使用"""
    return stats.record_usage(f"feature_{feature_name}")

def get_stats_summary():
    """获取统计摘要"""
    return stats.get_usage_summary()

if __name__ == "__main__":
    # 测试统计功能
    print("🔍 测试使用统计功能...")
    
    # 记录启动
    record_app_launch()
    
    # 记录功能使用
    record_feature_usage("password_check")
    
    # 显示统计
    summary = get_stats_summary()
    print(f"📊 统计摘要: {summary}")
    
    # 显示隐私信息
    print(stats.show_privacy_info())