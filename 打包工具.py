#!/usr/bin/env python3
"""
智能打包工具 - 支持版本管理和升级功能
"""

import os
import json
import subprocess
import sys
from datetime import datetime

class PackageBuilder:
    def __init__(self):
        self.project_dir = os.path.dirname(os.path.abspath(__file__))
        self.version_file = os.path.join(self.project_dir, 'version.json')
        self.dist_dir = os.path.join(self.project_dir, 'dist')
        
    def get_current_version(self):
        """获取当前版本号"""
        try:
            with open(self.version_file, 'r', encoding='utf-8') as f:
                version_data = json.load(f)
                return version_data.get('current_version', '1.0.0')
        except FileNotFoundError:
            return '1.0.0'
    
    def update_version(self, new_version=None):
        """更新版本号"""
        if not new_version:
            # 自动递增版本号
            current = self.get_current_version()
            parts = current.split('.')
            if len(parts) == 3:
                parts[2] = str(int(parts[2]) + 1)
                new_version = '.'.join(parts)
        
        version_data = {
            "current_version": new_version,
            "minimum_version": new_version,
            "release_date": datetime.now().strftime('%Y-%m-%d'),
            "download_url": f"https://github.com/你的用户名/你的仓库/releases/tag/v{new_version}",
            "changelog": [
                "优化密码验证功能",
                "新增版本检查机制",
                "提升用户体验"
            ],
            "file_size": "待计算"
        }
        
        with open(self.version_file, 'w', encoding='utf-8') as f:
            json.dump(version_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 版本已更新为: {new_version}")
        return new_version
    
    def calculate_file_size(self):
        """计算最终文件大小"""
        exe_path = os.path.join(self.dist_dir, '账号记事本.exe')
        if os.path.exists(exe_path):
            size_bytes = os.path.getsize(exe_path)
            size_mb = round(size_bytes / (1024 * 1024), 1)
            
            # 更新版本文件中的文件大小
            with open(self.version_file, 'r', encoding='utf-8') as f:
                version_data = json.load(f)
            
            version_data['file_size'] = f"{size_mb}MB"
            
            with open(self.version_file, 'w', encoding='utf-8') as f:
                json.dump(version_data, f, indent=2, ensure_ascii=False)
            
            return f"{size_mb}MB"
        return "未知"
    
    def create_version_file(self):
        """创建初始版本文件"""
        if not os.path.exists(self.version_file):
            # 提示用户设置GitHub信息
            print("⚠️  请设置你的GitHub信息:")
            username = input("请输入你的GitHub用户名: ") or "你的用户名"
            repo_name = input("请输入仓库名(如 account-manager): ") or "你的仓库名"
            
            version_data = {
                "current_version": "4.1.0",
                "minimum_version": "4.1.0",
                "release_date": datetime.now().strftime('%Y-%m-%d'),
                "download_url": f"https://github.com/{username}/{repo_name}/releases/latest",
                "changelog": [
                    "新增密码派生加密功能",
                    "优化启动验证逻辑",
                    "提升安全性和用户体验"
                ],
                "file_size": "待计算",
                "github_username": username,
                "repository_name": repo_name
            }
            
            with open(self.version_file, 'w', encoding='utf-8') as f:
                json.dump(version_data, f, indent=2, ensure_ascii=False)
            
            print("✅ 已创建 version.json 文件")
    
    def clean_build_files(self):
        """清理旧的构建文件"""
        dirs_to_clean = ['build', '__pycache__']
        for dir_name in dirs_to_clean:
            dir_path = os.path.join(self.project_dir, dir_name)
            if os.path.exists(dir_path):
                import shutil
                shutil.rmtree(dir_path)
                print(f"🧹 已清理 {dir_name} 目录")
    
    def build_executable(self):
        """构建可执行文件"""
        print("🔨 开始构建可执行文件...")
        
        # 需要打包的文件列表
        files_to_add = [
            'main.py',
            'version.json',
            'requirements.txt',
            'img/ico.ico',  # 修正图标文件路径
            'usage_stats.py'  # 添加统计模块
        ]
        
        # 检查文件是否存在
        missing_files = []
        for file in files_to_add:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            print("❌ 以下文件缺失:")
            for file in missing_files:
                print(f"   - {file}")
            return False
        
        print("✅ 所有必要文件已检查")
        
        # 确保spec文件存在
        spec_file = os.path.join(self.project_dir, 'main.spec')
        if not os.path.exists(spec_file):
            print("❌ 未找到 main.spec 文件")
            return False
        
        try:
            # 执行打包
            result = subprocess.run([
                sys.executable, '-m', 'PyInstaller', 'main.spec'
            ], cwd=self.project_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ 打包成功！")
                if result.stdout:
                    print("构建输出:", result.stdout[-200:])  # 显示最后200字符
                return True
            else:
                print("❌ 打包失败:")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ 构建出错: {str(e)}")
            return False
    
    def verify_build(self):
        """验证构建结果"""
        exe_path = os.path.join(self.dist_dir, '账号记事本.exe')
        version_path = os.path.join(self.dist_dir, 'version.json')
        
        if os.path.exists(exe_path):
            # 复制version.json到dist目录
            if os.path.exists(self.version_file):
                import shutil
                shutil.copy2(self.version_file, version_path)
            
            file_size = self.calculate_file_size()
            print(f"✅ 构建验证通过")
            print(f"📁 文件位置: {exe_path}")
            print(f"📊 文件大小: {file_size}")
            return True
        else:
            print("❌ 构建验证失败 - 未找到可执行文件")
            return False
    
    def package_all(self, new_version=None):
        """一键打包完整流程"""
        print("🚀 开始智能打包流程...")
        print("=" * 50)
        
        # 步骤1：创建版本文件
        self.create_version_file()
        
        # 步骤2：更新版本号
        if new_version:
            self.update_version(new_version)
        
        # 步骤3：清理旧文件
        self.clean_build_files()
        
        # 步骤4：构建可执行文件
        if not self.build_executable():
            return False
        
        # 步骤5：验证构建结果
        if not self.verify_build():
            return False
        
        print("=" * 50)
        print("🎉 打包完成！")
        print(f"📁 文件位置: {self.dist_dir}")
        print(f"📝 版本信息: {self.get_current_version()}")
        
        return True

def main():
    """主函数"""
    builder = PackageBuilder()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "update":
            new_version = sys.argv[2] if len(sys.argv) > 2 else None
            builder.update_version(new_version)
        elif command == "build":
            builder.package_all()
        elif command == "clean":
            builder.clean_build_files()
        else:
            print("使用方法:")
            print("  python 打包工具.py build          # 一键打包")
            print("  python 打包工具.py update [版本号]   # 更新版本")
            print("  python 打包工具.py clean           # 清理构建文件")
    else:
        # 默认执行完整打包流程
        builder.package_all()

if __name__ == '__main__':
    main()