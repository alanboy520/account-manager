import sys
import ctypes
from ctypes import wintypes
import logging
import base64
import hashlib

# 导入使用统计模块
from usage_stats import record_app_launch, record_feature_usage, get_stats_summary
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QGridLayout, QLabel, QScrollArea, QListWidget, QPushButton, QSizePolicy, 
    QLineEdit, QMessageBox, QMenu, QInputDialog
)
from PyQt6.QtGui import QIcon, QColor, QFont, QPalette, QDesktopServices
from PyQt6.QtCore import Qt, QEvent, QUrl, QTimer
import json
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

# 需要预加载的图标列表
REQUIRED_ICONS = ['copy', 'eye', 'eye2']

# 预加载所有SVG图标
def preload_all_icons():
    # 获取系统文本颜色
    app = QApplication.instance()
    if app:
        palette = app.palette()
        text_color = palette.color(QPalette.ColorRole.WindowText).name()
        for icon_name in REQUIRED_ICONS:
            create_temporary_svg(icon_name, text_color)
        print(f"所有图标已预加载完成，颜色: {text_color}")


# 获取资源文件路径（适配PyInstaller打包环境）
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        # 当程序被PyInstaller打包后
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        # 开发模式
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

# 使用内置SVG图标数据创建临时SVG文件
# 导入内置SVG图标数据
from svg_icons_data import SVG_ICONS

def create_temporary_svg(icon_name, color):
    # 从内置SVG_ICONS字典获取图标内容
    if icon_name in SVG_ICONS:
        svg_content = SVG_ICONS[icon_name]
    else:
        # 使用默认图标
        svg_content = SVG_ICONS['default']

    # 替换颜色占位符
    svg_content = svg_content.replace('{color}', color)

    # 创建临时文件
    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    temp_svg_path = os.path.join(temp_dir, f'{icon_name}.svg')

    try:
        with open(temp_svg_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        return temp_svg_path
    except Exception as e:
        logger.error(f"创建临时SVG文件失败: {str(e)}")
        return None

    # 查找对应图标的SVG内容
    icon_start = f'{icon_name}.svg:'
    icon_end = f'\n\n'
    start_index = svg_content.find(icon_start)
    if start_index == -1:
        print(f"找不到图标: {icon_name}")
        return None

    start_index += len(icon_start)
    end_index = svg_content.find(icon_end, start_index)
    if end_index == -1:
        # 如果是最后一个图标，则结束索引为文件末尾
        end_index = len(svg_content)

    # 提取图标SVG内容
    icon_svg = svg_content[start_index:end_index].strip()

    # 替换颜色占位符
    icon_svg = icon_svg.replace('{color}', color)

    # 获取运行目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 创建temp文件夹路径
    temp_dir = os.path.join(current_dir, 'temp')
    # 确保temp文件夹存在
    os.makedirs(temp_dir, exist_ok=True)
    # 创建临时文件（在temp文件夹中，不包含颜色变量名）
    temp_file_path = os.path.join(temp_dir, f'{icon_name}.svg')

    try:
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            f.write(icon_svg)
        print(f"创建临时SVG文件成功: {temp_file_path}")
        return temp_file_path
    except Exception as e:
        print(f"创建临时SVG文件失败: {str(e)}")
        return None

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ======================= 公共工具函数 =======================
def show_status_message(parent, message, duration=3000):
    """
    显示状态栏提示并在指定时间后自动隐藏
    参数:
    parent: QWidget - 父窗口组件
    message: str - 提示消息
    duration: int - 提示持续时间(毫秒)
    """
    print(f"状态栏提示: {message}")
    status_bar = parent.statusBar()
    status_bar.show()  # 确保状态栏可见
    status_bar.showMessage(message, duration)  # 显示提示
    # 在提示消失后隐藏状态栏
    from PyQt6.QtCore import QTimer
    QTimer.singleShot(duration, lambda: status_bar.hide())

def create_styled_button(button_type, text='', icon_name=None, fixed_width=None, color=None, show_border=False):
    """
    创建具有统一样式的按钮
    参数:
    button_type: str - 按钮类型 ('icon' 或 'text')
    text: str - 按钮文本
    icon_name: str - 图标名称 (仅对icon类型有效，对应SVG_ICONS字典中的图标名)
    fixed_width: int - 固定宽度
    color: str - 图标颜色 (仅对icon类型有效)
    show_border: bool - 是否显示边框 (默认False)
    返回:
    QPushButton - 样式化的按钮
    """
    btn = QPushButton(text)
    btn.setFont(QFont("SimHei", 12))
    
    if fixed_width is not None:
        btn.setFixedWidth(fixed_width)
    
    if button_type == 'icon':
        if icon_name:
            if color:
                # 使用create_temporary_svg创建带颜色的临时SVG文件
                temp_svg_path = create_temporary_svg(icon_name, color)
                if temp_svg_path:
                    print(f"加载临时SVG路径: {temp_svg_path}")
                    icon = QIcon(temp_svg_path)
                    # 确保SVG作为蒙版处理
                    icon.setIsMask(True)
                    btn.setIcon(icon)
            # 如果没有指定颜色，则使用默认颜色
            if not color:
                # 获取系统文本颜色
                app = QApplication.instance()
                if app:
                    palette = app.palette()
                    color = palette.color(QPalette.ColorRole.WindowText).name()
                else:
                    color = "#000000"  # 默认黑色

            # 使用create_temporary_svg创建带颜色的临时SVG文件
            temp_svg_path = create_temporary_svg(icon_name, color)
            if temp_svg_path:
                print(f"加载临时SVG路径: {temp_svg_path}")
                icon = QIcon(temp_svg_path)
                # 确保SVG作为蒙版处理
                icon.setIsMask(True)
                btn.setIcon(icon)
        
        # 图标按钮样式
        if show_border:
            btn.setStyleSheet('''QPushButton {
                background-color: transparent; 
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 2px;
            } 
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
                border-radius: 4px;
            }''')
        else:
            btn.setStyleSheet('''QPushButton {
                background-color: transparent; 
                border: none;
            } 
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3); 
                border-radius: 3px;
            }''')
    
    elif button_type == 'text':
        if show_border:
            btn.setStyleSheet('''QPushButton {
                background-color: transparent;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }''')
        else:
            btn.setStyleSheet('QPushButton {background-color: transparent; border: none;} '
                             'QPushButton:hover {background-color: rgba(255, 255, 255, 0.3);}')
    
    # 强制更新按钮
    btn.update()
    
    return btn

def create_account_info_layout(account_data, parent, copy_callback, toggle_callback, delete_callback, edit_callback, color):
    """
    创建账号信息布局
    返回: QVBoxLayout - 包含账号信息的布局
    """
    layout = QVBoxLayout()
    account = account_data.get("账号", "")
    password = account_data.get("密码", "")
    remark = account_data.get("备注", "")
    
    # 账号标签和按钮
    account_layout = QHBoxLayout()
    account_label = QLabel(account)
    account_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    account_label.setWordWrap(False)
    account_label.setMinimumHeight(20)
    account_label.setStyleSheet("background-color: transparent; border: none;")
    account_layout.addWidget(account_label)
    
    account_button = create_styled_button('icon', icon_name='copy', color=color)
    account_button.setFixedSize(30, 30)
    account_button.clicked.connect(lambda: copy_callback(account))
    account_layout.addWidget(account_button)
    
    layout.addLayout(account_layout)
    
    # 密码标签和按钮
    password_layout = QHBoxLayout()
    password_label = QLabel(' ●●●●●●')
    password_label.setFont(QFont("SimHei", 6))
    password_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    password_label.setWordWrap(False)
    password_label.setMinimumHeight(20)
    password_label.setStyleSheet("background-color: transparent; border: none;")
    password_layout.addWidget(password_label)
    
    password_button1 = create_styled_button('icon', icon_name='eye2', color=color)
    password_button1.setFixedSize(30, 30)
    password_button1.is_closed = True
    password_button1.clicked.connect(lambda: toggle_callback(password_label, password, password_button1))
    password_layout.addWidget(password_button1)
    
    password_button2 = create_styled_button('icon', icon_name='copy', color=color)
    password_button2.setFixedSize(30, 30)
    password_button2.clicked.connect(lambda: copy_callback(password))
    password_layout.addWidget(password_button2)
    
    layout.addLayout(password_layout)
    
    remark_label = QLabel(remark)
    remark_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    remark_label.setWordWrap(True)
    remark_label.setMinimumHeight(20)
    remark_label.setStyleSheet("background-color: transparent; border: none;")
    layout.addWidget(remark_label)
    
    layout.addStretch(1)
    
    # 按钮布局
    button_layout = QHBoxLayout()
    button_layout.setSpacing(5)
    button_layout.addStretch(1)
    
    delete_button = create_styled_button('text', '删除', fixed_width=60, show_border=True)
    delete_button.setFixedHeight(28)
    delete_button.clicked.connect(delete_callback)
    button_layout.addWidget(delete_button)
    
    edit_button = create_styled_button('text', '修改', fixed_width=60, show_border=True)
    edit_button.setFixedHeight(28)
    edit_button.clicked.connect(edit_callback)
    button_layout.addWidget(edit_button)
    
    layout.addLayout(button_layout)
    return layout

def create_input_form(parent, account="", password="", remark="", submit_callback=None, cancel_callback=None):
    """
    创建输入表单布局
    返回: QVBoxLayout - 包含输入表单的布局
    """
    layout = QVBoxLayout()
    layout.setSpacing(10)
    layout.setContentsMargins(10, 5, 10, 5)
    
    # 账号输入框
    account_container = QWidget()
    account_container.setStyleSheet("border: none; border-radius: 5px; padding: 0px;")
    account_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    account_container.setMinimumHeight(30)
    account_layout = QVBoxLayout(account_container)
    account_layout.setContentsMargins(0, 0, 0, 0)
    
    account_input = QLineEdit()
    account_input.setPlaceholderText("输入账号")
    account_input.setText(account)
    account_input.setMinimumHeight(30)
    account_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    account_input.setFont(QFont("SimHei", 10))
    account_input.setStyleSheet("background-color: transparent; border-radius: 5px; border: 1px solid #ccc;")
    account_layout.addWidget(account_input)
    layout.addWidget(account_container)
    
    # 密码输入框
    password_container = QWidget()
    password_container.setStyleSheet("border: none; border-radius: 5px; padding: 0px;")
    password_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    password_container.setMinimumHeight(30)
    password_layout = QVBoxLayout(password_container)
    password_layout.setContentsMargins(0, 0, 0, 0)
    
    password_input = QLineEdit()
    password_input.setPlaceholderText("输入密码")
    password_input.setText(password)
    password_input.setMinimumHeight(30)
    password_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    password_input.setFont(QFont("SimHei", 10))
    password_input.setStyleSheet("background-color: transparent; border-radius: 5px; border: 1px solid #ccc;")
    password_input.setEchoMode(QLineEdit.EchoMode.Normal)
    password_layout.addWidget(password_input)
    layout.addWidget(password_container)
    
    # 备注输入框
    remark_container = QWidget()
    remark_container.setStyleSheet("border: none; border-radius: 5px; padding: 0px;")
    remark_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    remark_container.setMinimumHeight(30)
    remark_layout = QVBoxLayout(remark_container)
    remark_layout.setContentsMargins(0, 0, 0, 0)
    
    remark_input = QLineEdit()
    remark_input.setPlaceholderText("输入备注文本（可空）")
    remark_input.setText(remark)
    remark_input.setMinimumHeight(30)
    remark_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    remark_input.setFont(QFont("SimHei", 10))
    remark_input.setStyleSheet("background-color: transparent; border-radius: 5px; border: 1px solid #ccc;")
    remark_layout.addWidget(remark_input)
    layout.addWidget(remark_container)
    
    # 按钮容器
    button_container = QWidget()
    button_container.setStyleSheet("border: none; border-radius: 5px; padding: 0px;")
    button_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    button_container.setMinimumHeight(30)
    button_layout = QVBoxLayout(button_container)
    button_layout.setContentsMargins(0, 0, 0, 0)
    
    btn_layout = QHBoxLayout()
    btn_layout.setSpacing(10)
    btn_layout.addStretch(1)
    
    if cancel_callback:
        cancel_button = create_styled_button('text', '取消', fixed_width=60, show_border=True)
        cancel_button.setFixedHeight(30)
        cancel_button.clicked.connect(cancel_callback)
        btn_layout.addWidget(cancel_button)
    
    if submit_callback:
        submit_button = create_styled_button('text', '提交' if not account else '确认', fixed_width=60, show_border=True)
        submit_button.setFixedHeight(30)
        submit_button.clicked.connect(lambda: submit_callback(
            account_input.text().strip(),
            password_input.text().strip(),
            remark_input.text().strip()
        ))
        btn_layout.addWidget(submit_button)
    
    button_layout.addLayout(btn_layout)
    layout.addWidget(button_container)
    
    return layout, account_input, password_input, remark_input

def create_plus_button_layout(parent, click_callback):
    """
    创建加号按钮布局
    返回: QVBoxLayout - 包含加号按钮的布局
    """
    layout = QVBoxLayout()
    layout.addStretch(1)
    
    plus_button = QPushButton("+")
    plus_button.setFont(QFont("SimHei", 24, QFont.Weight.Bold))
    plus_button.setStyleSheet("QPushButton {border-radius: 30px; background-color: #2E8B57; border: none; color: white;}")
    plus_button.setFixedSize(60, 60)
    plus_button.clicked.connect(click_callback)
    layout.addWidget(plus_button, alignment=Qt.AlignmentFlag.AlignCenter)
    
    text_label = QLabel("添加新账号")
    text_label.setFont(QFont("SimHei", 10))
    text_label.setStyleSheet("background-color: transparent; border: none;")
    layout.addWidget(text_label, alignment=Qt.AlignmentFlag.AlignCenter)
    
    layout.addStretch(1)
    return layout, plus_button, text_label

def clear_layout(layout):
    """清除布局中的所有元素"""
    while layout.count() > 0:
        item = layout.takeAt(0)
        widget = item.widget()
        if widget:
            widget.hide()
            layout.removeWidget(widget)
        else:
            sub_layout = item.layout()
            if sub_layout:
                clear_layout(sub_layout)
                layout.removeItem(sub_layout)

# ======================= 组件类 =======================
class AccountContainer(QWidget):
    """账号信息容器组件"""
    def __init__(self, account_data=None, index=0, bg_color=None, parent=None):
        super().__init__(parent)
        self.account_data = account_data or {}
        self.index = index
        
        # 获取系统文本颜色
        app = QApplication.instance()
        if app:
            palette = app.palette()
            self.icon_color = palette.color(QPalette.ColorRole.WindowText).name()
        else:
            self.icon_color = "#ffffff"  # 默认白色
        
        # 透明背景，无边框
        self.setStyleSheet("background-color: transparent; border: none; border-radius: 5px; padding: 5px;")
        
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(0)
        
        # 创建账号信息布局
        self.create_account_display()
    
    def create_account_display(self):
        """创建账号显示布局"""
        clear_layout(self.layout)
        
        layout = create_account_info_layout(
            self.account_data,
            self,
            self.copy_to_clipboard,
            self.toggle_password_visibility,
            self.on_delete_button_clicked,
            self.on_edit_button_clicked,
            self.icon_color
        )
        self.layout.addLayout(layout)
        
        # 打印验证颜色值（调试用）
        print(f"实际使用的图标颜色: {self.icon_color}")
    
    def create_input_form(self):
        """创建输入表单布局"""
        clear_layout(self.layout)
        
        layout, self.account_input, self.password_input, self.remark_input = create_input_form(
            self,
            self.account_data.get("账号", ""),
            self.account_data.get("密码", ""),
            self.account_data.get("备注", ""),
            self.on_submit_button_clicked,
            self.on_cancel_button_clicked
        )
        self.layout.addLayout(layout)
        self.layout.addStretch(1)
    
    def copy_to_clipboard(self, text):
        """将文本复制到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        # 使用状态栏提示替代弹窗
        main_window = self.parentWidget()
        while main_window and not isinstance(main_window, TitleBarColorWindow):
            main_window = main_window.parentWidget()
        if main_window:
            show_status_message(main_window, '已复制到剪贴板')

    def toggle_password_visibility(self, label, original_password, button):
        """切换密码显示/隐藏状态、图标和字体大小"""
        if label.text() == ' ●●●●●●':
            label.setText(original_password)
            # 创建带颜色的临时SVG文件
            temp_svg_path = create_temporary_svg('eye', self.icon_color)
            if temp_svg_path:
                button.setIcon(QIcon(temp_svg_path))
                button.setIcon(QIcon(temp_svg_path))
            button.is_closed = False
            label.setFont(QFont("SimHei", 12))
        else:
            label.setText(' ●●●●●●')
            # 创建带颜色的临时SVG文件
            temp_svg_path = create_temporary_svg('eye2', self.icon_color)
            if temp_svg_path:
                button.setIcon(QIcon(temp_svg_path))
            button.is_closed = True
            label.setFont(QFont("SimHei", 6))
            
    def on_delete_button_clicked(self):
        """处理删除按钮点击事件，删除JSON中的当前账号"""
        try:
            # 通知主窗口执行删除操作
            main_window = self.parentWidget()
            while main_window and not isinstance(main_window, TitleBarColorWindow):
                main_window = main_window.parentWidget()
            
            if main_window:
                main_window.delete_account(self.account_data)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除账号时出错：{str(e)}")
    
    def on_submit_button_clicked(self, account, password, remark):
        """处理表单提交事件，验证输入并更新账号信息"""
        print(f"调用函数: AccountContainer.on_submit_button_clicked(账号={account}, 密码={password}, 备注={remark})")
        if not account or not password:
            QMessageBox.warning(self, "输入错误", "账号和密码不能为空！")
            return
        
        try:
            # 通知主窗口执行更新操作
            main_window = self.parentWidget()
            while main_window and not isinstance(main_window, TitleBarColorWindow):
                main_window = main_window.parentWidget()
            
            if main_window:
                main_window.update_account(
                    self.account_data,
                    account,
                    password,
                    remark
                )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新账号时出错：{str(e)}")
    
    def on_edit_button_clicked(self):
        """处理修改按钮点击事件"""
        self.create_input_form()

    def on_cancel_button_clicked(self):
        """处理取消按钮点击事件"""
        self.create_account_display()


class AddAccountContainer(QWidget):
    """添加账号容器组件"""
    def __init__(self, website_key=None, bg_color=None, parent=None):
        super().__init__(parent)
        self.website_key = website_key
        
        # 透明背景，无边框
        self.setStyleSheet("background-color: transparent; border: none; border-radius: 5px; padding: 10px;")
        
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        
        self.create_plus_button()
    
    def create_plus_button(self):
        """创建加号按钮布局"""
        clear_layout(self.layout)
        
        layout, self.plus_button, self.text_label = create_plus_button_layout(
            self,
            self.on_plus_button_clicked
        )
        self.layout.addLayout(layout)
    
    def create_input_form(self):
        """创建输入表单布局"""
        clear_layout(self.layout)
        
        layout, self.account_input, self.password_input, self.remark_input = create_input_form(
            self,
            submit_callback=self.on_submit_button_clicked,
            cancel_callback=self.on_cancel_button_clicked
        )
        self.layout.addLayout(layout)
        self.layout.addStretch(1)
    
    def on_plus_button_clicked(self):
        """处理圆形按钮点击事件"""
        self.create_input_form()
    
    def on_cancel_button_clicked(self):
        """处理取消按钮点击事件"""
        self.create_plus_button()
    
    def on_submit_button_clicked(self, account, password, remark):
        """处理表单提交事件 - 根据is_adding_website决定调用函数"""
        print(f"调用函数: AddAccountContainer.on_submit_button_clicked(账号={account}, 密码={password}, 备注={remark})")
        # 获取主窗口实例
        main_window = self.window()
        if not isinstance(main_window, TitleBarColorWindow):
            # 尝试通过父组件链查找
            parent_widget = self.parentWidget()
            while parent_widget and not isinstance(parent_widget, TitleBarColorWindow):
                parent_widget = parent_widget.parentWidget()
            
            if parent_widget and isinstance(parent_widget, TitleBarColorWindow):
                main_window = parent_widget
        
        if main_window:
            if hasattr(main_window, 'is_adding_website') and main_window.is_adding_website:
                # 如果正在添加新网站，则调用保存网站函数
                print("检测到正在添加新网站，调用保存网站函数")
                # 设置账号信息到容器
                if hasattr(main_window, 'current_add_container') and main_window.current_add_container == self:
                    main_window.on_confirm_new_website()
            elif hasattr(main_window, 'submit_new_account'):
                # 否则调用添加账号函数
                print("正常添加账号")
                main_window.submit_new_account(
                    account, 
                    password, 
                    remark,
                    self.website_key
                )


# ======================= 密码派生加密类 =======================
class PasswordBasedEncryption:
    """基于密码的加密系统 - 无需密钥文件"""
    
    def __init__(self):
        self.salt_size = 16  # 盐的长度
        self.iterations = 100000  # 迭代次数，提高安全性
        
    def _derive_key_from_password(self, password: str, salt: bytes = None) -> tuple:
        """
        从密码派生密钥
        
        参数:
            password: 用户密码
            salt: 盐值，如果不提供则生成新的
            
        返回:
            (key, salt) 密钥和盐值
        """
        if salt is None:
            salt = os.urandom(self.salt_size)
            
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256位密钥
            salt=salt,
            iterations=self.iterations,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    def encrypt_data(self, data: str, password: str) -> bytes:
        """加密数据"""
        key, salt = self._derive_key_from_password(password)
        f = Fernet(key)
        encrypted = f.encrypt(data.encode('utf-8'))
        
        # 将盐和加密数据一起存储
        return salt + encrypted
    
    def decrypt_data(self, encrypted_data: bytes, password: str) -> str:
        """解密数据"""
        if len(encrypted_data) < self.salt_size:
            raise ValueError("无效的数据格式")
            
        # 提取盐（前16字节）
        salt = encrypted_data[:self.salt_size]
        encrypted = encrypted_data[self.salt_size:]
        
        # 重新派生密钥
        key, _ = self._derive_key_from_password(password, salt)
        f = Fernet(key)
        
        try:
            decrypted = f.decrypt(encrypted)
            return decrypted.decode('utf-8')
        except Exception as e:
            raise ValueError("密码错误或数据已损坏") from e


class TitleBarColorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 记录应用启动统计
        try:
            record_app_launch()
        except:
            pass
            
        # 初始化状态栏
        self.statusBar().hide()  # 初始状态下隐藏状态栏
        self.setWindowTitle("账号记事本")
        # 设置窗口图标
        self.setWindowIcon(QIcon(get_resource_path(os.path.join('img', 'ico.ico'))))
        self.resize(710, 430)
        self.setMinimumSize(710, 430)  # 设置最小窗口尺寸
        
        self.website_data = {}
        self.current_website_key = None
        self.title_bar_color = None
        self.resize_timer = None
        self.is_adding_website = False  # 添加逻辑型变量，默认为False
        self.current_columns = 2  # 初始列数，与默认设置保持一致
        
        # 获取系统文本颜色
        palette = self.palette()
        self.icon_color = palette.color(QPalette.ColorRole.WindowText).name()
        
        self._init_ui()
        self.apply_system_theme_color()  # 先应用主题颜色
        self._load_data()  # 再加载数据
        self.show()
        
    def create_visit_button(self):
        """创建访问按钮 - 确保使用正确的颜色"""
        return create_styled_button(
            'icon',
            icon_name='TdesignJump',
            fixed_width=30,
            color=self.icon_color  # 确保使用全局颜色
        )

    def _init_ui(self):
        self.central_widget = QWidget()
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        self.setCentralWidget(self.central_widget)
        
        # 左侧列表区域
        self.left_widget = QWidget()
        self.left_widget.setFixedWidth(100)
        self.left_layout = QVBoxLayout(self.left_widget)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.left_scroll_area = QScrollArea()
        self.left_scroll_area.setWidgetResizable(True)
        self.left_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.left_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.list_widget = QListWidget()
        self.list_widget.setFont(QFont("SimHei", 12))
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.itemClicked.connect(self.on_list_item_clicked)
        # 添加右键菜单支持
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.on_list_context_menu)
        # 设置样式表，取消选中时的光标指示器
        self.list_widget.setStyleSheet("""
            QListWidget {
                outline: none;
                border: none;
                background-color: transparent;
            }
            QListWidget::item {
                outline: none;
                border: none;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: rgba(128, 128, 128, 0.3);
                color: palette(text);
                outline: none;
                border: none;
            }
            QListWidget::item:hover {
                background-color: rgba(128, 128, 128, 0.1);
                outline: none;
                border: none;
            }
            QListWidget::item:focus {
                outline: none;
                border: none;
            }
        """)
        
        self.left_list_container = QWidget()
        self.left_list_layout = QVBoxLayout(self.left_list_container)
        self.left_list_layout.addWidget(self.list_widget)
        self.left_scroll_area.setWidget(self.left_list_container)
        self.left_layout.addWidget(self.left_scroll_area)
        
        # 右侧内容区域
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout(self.right_widget)
        self.right_layout.setSpacing(10)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 顶部工具栏
        self.right_top_widget = QWidget()
        self.right_top_widget.setFixedHeight(40)
        self.top_layout = QHBoxLayout(self.right_top_widget)
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        
        self.website_name_input = QLineEdit()
        self.website_name_input.setPlaceholderText("输入网站名")
        self.website_name_input.setFixedWidth(120)
        self.website_name_input.hide()
        self.top_layout.addWidget(self.website_name_input)
        
        self.website_url_input = QLineEdit()
        self.website_url_input.setPlaceholderText("输入网址")
        self.website_url_input.setFixedWidth(200)
        self.website_url_input.hide()
        self.top_layout.addWidget(self.website_url_input)
        
        self.website_label = QLabel("请从左侧列表选择网站")
        self.website_label.setFont(QFont("SimHei", 12))
        self.website_label.setStyleSheet("margin-left: 5px;")
        self.top_layout.addWidget(self.website_label)
        
        self.visit_button = self.create_visit_button()
        self.visit_button.setFixedHeight(30)
        self.visit_button.clicked.connect(self.on_visit_button_clicked)  # 添加点击事件连接
        self.top_layout.addWidget(self.visit_button)
        
        self.top_layout.addStretch(1)
        
        self.add_account_button = create_styled_button('text', '添加新网站', fixed_width=100)
        self.add_account_button.setFixedHeight(30)
        self.add_account_button.clicked.connect(self.on_add_website_clicked)
        self.top_layout.addWidget(self.add_account_button)
        
        self.confirm_button = create_styled_button('text', '保存', fixed_width=60, show_border=True)
        self.confirm_button.hide()
        self.confirm_button.clicked.connect(self.on_confirm_new_website)
        self.top_layout.addWidget(self.confirm_button)
        
        self.cancel_button = create_styled_button('text', '返回', fixed_width=60, show_border=True)
        self.cancel_button.hide()
        self.cancel_button.clicked.connect(self.on_cancel_new_website)
        self.top_layout.addWidget(self.cancel_button)
        
        # 底部账号容器区域
        self.right_bottom_widget = QWidget()
        self.bottom_layout = QVBoxLayout(self.right_bottom_widget)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.flow_container = QWidget()
        self.flow_layout = QGridLayout(self.flow_container)
        self.flow_layout.setHorizontalSpacing(10)
        self.flow_layout.setVerticalSpacing(10)
        
        self.scroll_area.setWidget(self.flow_container)
        self.bottom_layout.addWidget(self.scroll_area)
        
        self.right_layout.addWidget(self.right_top_widget)
        self.right_layout.addWidget(self.right_bottom_widget)
        
        self.main_layout.addWidget(self.left_widget, 1)
        self.main_layout.addWidget(self.right_widget, 3)
        
        self.installEventFilter(self)

    def on_list_item_clicked(self, item):
        """列表项点击事件处理"""
        website_name = item.text()
        
        for key, info in self.website_data.items():
            if info.get('网站名') == website_name:
                self.current_website_key = key
                website_url = info.get('网址', '未知网址')
                
                # 去除网址中的http://和https://前缀
                if website_url.startswith('http://'):
                    website_url =  website_url[7:]
                elif website_url.startswith('https://'):
                    website_url =  website_url[8:]
                
                self.website_label.setText('网址：'+ website_url)
                self.display_accounts(info)
                break
     
    def on_visit_button_clicked(self):
        """访问按钮点击事件处理"""
        if hasattr(self, 'current_website_key') and self.current_website_key:
            website_info = self.website_data.get(self.current_website_key, {})
            website_url = website_info.get('网址', '')
            
            if website_url:
                # 确保URL有正确的协议前缀
                if not website_url.startswith(('http://', 'https://')):
                    website_url = 'http://' + website_url
                
                # 打开网站
                QDesktopServices.openUrl(QUrl(website_url))
            else:
                QMessageBox.warning(self, "提示", "请先选择一个网站！")
        else:
            QMessageBox.warning(self, "提示", "请先选择一个网站！")

    def display_accounts(self, website_info):
        """显示指定网站的账号"""
        self.clear_flow_layout()
        accounts = website_info.get('列表', [])
        
        # 创建账号容器
        for i, account in enumerate(accounts):
            outer_container = self.create_account_container(account, i)
            self.add_to_flow_layout(outer_container, i)
        
        # 添加"添加账号"容器
        add_outer_container = self.create_add_account_container()
        self.add_to_flow_layout(add_outer_container, len(accounts))
        
        # 更新布局
        self.flow_layout.update()
        self.scroll_area.update()
        self.flow_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

    def create_account_container(self, account_data, index):
        """创建账号容器"""
        outer_container = QWidget()
        outer_container.setFixedSize(260, 160)
        
        # 获取系统文本颜色用于边框
        app = QApplication.instance()
        if app:
            palette = app.palette()
            border_color = palette.color(QPalette.ColorRole.WindowText).name()
        else:
            border_color = "#ffffff"
        
        # 透明背景，显示边框
        outer_container.setStyleSheet(f"background-color: transparent; border: 1px solid {border_color}; border-radius: 8px; padding: 5px;")
        
        outer_layout = QVBoxLayout(outer_container)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        
        container = AccountContainer(account_data, index, self.title_bar_color)
        outer_layout.addWidget(container)
        
        return outer_container

    def create_add_account_container(self):
        """创建添加账号容器"""
        add_outer_container = QWidget()
        add_outer_container.setFixedSize(260, 160)
        
        # 获取系统文本颜色用于边框
        app = QApplication.instance()
        if app:
            palette = app.palette()
            border_color = palette.color(QPalette.ColorRole.WindowText).name()
        else:
            border_color = "#ffffff"
        
        # 透明背景，显示边框
        add_outer_container.setStyleSheet(f"background-color: transparent; border: 1px solid {border_color}; border-radius: 8px; padding: 5px;")
        
        add_outer_layout = QVBoxLayout(add_outer_container)
        add_outer_layout.setContentsMargins(0, 0, 0, 0)
        
        add_container = AddAccountContainer(None, self.title_bar_color)
        add_outer_layout.addWidget(add_container)
        
        return add_outer_container

    def calculate_columns(self):
        """根据窗口宽度计算列数"""
        window_width = self.width()
        if window_width < 850:
            return 2
        elif window_width < 1120:
            return 3
        elif window_width < 1390:
            return 4
        elif window_width < 1660:
            return 5
        else:
            return 6

    def add_to_flow_layout(self, widget, index):
        """将控件添加到流式布局"""
        max_columns = self.calculate_columns()
        
        # 计算位置
        row = index // max_columns
        col = index % max_columns
        self.flow_layout.addWidget(widget, row, col)

    def clear_flow_layout(self):
        """清空流布局中的所有控件"""
        while self.flow_layout.count() > 0:
            item = self.flow_layout.itemAt(0)
            widget = item.widget()
            if widget:
                widget.hide()
                self.flow_layout.removeWidget(widget)

    def _get_encryption_instance(self):
        """获取基于密码的加密实例"""
        return PasswordBasedEncryption()
        
    def _get_password_from_user(self):
        """从用户获取密码（首次使用或密码验证）"""
        from PyQt6.QtWidgets import QInputDialog, QLineEdit
        
        # 检查是否已设置密码
        password_hash_path = os.path.join(
            os.path.dirname(sys.executable) if hasattr(sys, '_MEIPASS') else 
            os.path.dirname(os.path.abspath(__file__)), 
            '.password_hash'
        )
        
        password, ok = QInputDialog.getText(
            self, 
            "密码验证", 
            "请输入密码：", 
            QLineEdit.EchoMode.Password
        )
        
        if ok and password:
            return password
        return None
    
    def _generate_or_load_key(self):
        """向后兼容的方法 - 现在使用密码派生加密"""
        password = self._get_password_from_user()
        if not password:
            return None
        return PasswordBasedEncryption()

    def _get_encryption_password(self):
        """获取用于加密的密码"""
        password, ok = QInputDialog.getText(
            self, 
            "设置密码", 
            "请设置一个密码来保护您的数据：", 
            QLineEdit.EchoMode.Password
        )
        
        if ok and password:
            # 验证密码
            confirm_password, ok2 = QInputDialog.getText(
                self,
                "确认密码",
                "请再次输入密码：",
                QLineEdit.EchoMode.Password
            )
            
            if ok2 and password == confirm_password:
                return password
            elif ok2:
                QMessageBox.warning(self, "警告", "两次输入的密码不一致！")
                return None
        return None

    def _load_data(self):
        """加载数据，要求必须输入正确密码才能加载主界面"""
        try:
            # 获取程序运行目录
            if hasattr(sys, '_MEIPASS'):
                # 当程序被PyInstaller打包后
                current_dir = os.path.dirname(sys.executable)
            else:
                # 开发模式
                current_dir = os.path.dirname(os.path.abspath(__file__))
            
            file_path = os.path.join(current_dir, 'data.json')
            logger.debug(f"数据保存路径: {file_path}")
            logger.debug(f"数据加载路径: {file_path}")
            
            data_loaded_successfully = False
            self.website_data = {}
            
            if os.path.exists(file_path):
                # 数据文件存在，要求密码验证
                max_attempts = 3  # 最多尝试3次
                for attempt in range(max_attempts):
                    password = self._get_password_from_user()
                    if not password:
                        # 用户取消，直接退出程序
                        logger.warning("用户取消密码输入，程序退出")
                        sys.exit(0)
                    
                    cipher = PasswordBasedEncryption()
                    
                    with open(file_path, 'rb') as f:
                        encrypted_data = f.read()
                        
                    try:
                        decrypted_data = cipher.decrypt_data(encrypted_data, password)
                        data = json.loads(decrypted_data)
                        self.website_data = data.get('记录网站', {})
                        data_loaded_successfully = True
                        
                        # 记录密码验证成功统计
                        try:
                            record_feature_usage("password_verify_success")
                        except:
                            pass
                            
                        break  # 密码正确，退出循环
                    except ValueError as e:
                        logger.warning(f"密码错误 (尝试 {attempt + 1}/{max_attempts}): {str(e)}")
                        
                        # 记录密码验证失败统计
                        try:
                            record_feature_usage("password_verify_failed")
                        except:
                            pass
                            
                        if attempt < max_attempts - 1:
                            QMessageBox.warning(self, "密码错误", 
                                              f"密码错误，请重试！({attempt + 1}/{max_attempts})")
                        else:
                            QMessageBox.critical(self, "密码错误", 
                                               "密码错误次数过多，程序将退出！")
                            sys.exit(0)
                            
                    # 尝试旧的密钥文件方式（向后兼容）
                    try:
                        from cryptography.fernet import Fernet
                        key_path = os.path.join(current_dir, 'secret.key')
                        if os.path.exists(key_path):
                            with open(key_path, 'rb') as f:
                                key = f.read()
                            fernet = Fernet(key)
                            decrypted_data = fernet.decrypt(encrypted_data).decode('utf-8')
                            data = json.loads(decrypted_data)
                            self.website_data = data.get('记录网站', {})
                            data_loaded_successfully = True
                            logger.info("成功使用旧密钥文件解密")
                            break
                    except Exception as e2:
                        logger.warning(f"旧密钥解密失败: {str(e2)}")
                        
                    # 尝试以明文方式读取（用于向后兼容）
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            self.website_data = data.get('记录网站', {})
                            data_loaded_successfully = True
                            break
                    except Exception as e3:
                        logger.error(f"明文读取失败: {e3}")
                        
                if not data_loaded_successfully:
                    QMessageBox.critical(self, "错误", "无法解密数据，程序将退出！")
                    sys.exit(0)
            else:
                # 首次使用，创建初始数据文件
                QMessageBox.information(self, "首次使用", "欢迎使用账号记事本！\n\n请设置一个密码来保护您的数据。")
                
                max_attempts = 3
                for attempt in range(max_attempts):
                    password = self._get_encryption_password()
                    if not password:
                        if attempt < max_attempts - 1:
                            reply = QMessageBox.question(self, "确认", 
                                                       "您确定要跳过密码设置吗？\n\n这将导致数据无加密保护。",
                                                       QMessageBox.StandardButton.Yes | 
                                                       QMessageBox.StandardButton.No)
                            if reply == QMessageBox.StandardButton.Yes:
                                self.website_data = self._create_default_data()
                                return
                            else:
                                continue
                        else:
                            QMessageBox.warning(self, "提示", "您取消了密码设置，数据将无加密保护！")
                            self.website_data = self._create_default_data()
                            return
                    else:
                        self._create_initial_data_file(file_path, password)
                        QMessageBox.information(self, "成功", "密码设置成功！您的数据已加密保护。")
                        self.website_data = self._create_default_data()
                        break
            
            self.update_website_list()
                
        except Exception as e:
            logger.error(f"加载数据时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载数据失败：{str(e)}\n程序将退出！")
            sys.exit(0)
    
    def _create_initial_data_file(self, file_path, password=None):
        """创建初始数据文件"""
        try:
            logger.info(f"创建初始数据文件: {file_path}")
            
            initial_data = {
                "记录网站": self._create_default_data()
            }
            
            if password:
                # 使用密码派生加密
                cipher = PasswordBasedEncryption()
                data_to_save = json.dumps(initial_data, ensure_ascii=False, indent=4)
                encrypted_data = cipher.encrypt_data(data_to_save, password)
            else:
                # 向后兼容：使用密钥文件
                cipher = self._generate_or_load_key()
                if not cipher:
                    logger.error("获取加密对象失败")
                    return
                data_to_save = json.dumps(initial_data, ensure_ascii=False, indent=4)
                encrypted_data = cipher.encrypt(data_to_save.encode('utf-8'))
            
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)

            logger.info(f"初始数据文件已创建: {file_path}")
        except Exception as e:
            logger.error(f"创建初始数据文件失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"创建初始数据文件失败: {str(e)}")
    
    def _create_default_data(self):
        """创建默认数据"""
        return {
            "1": {
                "网站名": "示例网站",
                "网址": "https://example.com",
                "列表": [
                    {"账号": "example_user", "密码": "example_pass", "备注": "示例账号"}
                ]
            }
        }
    
    def update_website_list(self):
        """更新网站列表"""
        self.list_widget.clear()
        for info in self.website_data.values():
            self.list_widget.addItem(info.get('网站名', '未知网站'))
        
        if self.list_widget.count() > 0:
            first_item = self.list_widget.item(0)
            self.list_widget.setCurrentItem(first_item)
            self.on_list_item_clicked(first_item)

    def apply_system_theme_color(self):
        try:
            palette = self.palette()
            window_color = palette.color(QPalette.ColorRole.Window)
            base_color = palette.color(QPalette.ColorRole.Base)
            text_color = palette.color(QPalette.ColorRole.WindowText).name()
            
            self.title_bar_color = window_color
            self.icon_color = text_color  # 更新全局图标颜色
            
            self.left_widget.setStyleSheet(f"background-color: {base_color.name()}; color: {text_color}; border-radius: 5px;")
            self.right_top_widget.setStyleSheet(f"background-color: {base_color.name()}; color: {text_color}; border-radius: 5px;")
            self.right_bottom_widget.setStyleSheet(f"background-color: {base_color.name()}; color: {text_color}; border-radius: 5px;")
            
            # 重新创建访问按钮以更新图标颜色
            if hasattr(self, 'visit_button') and self.visit_button:
                self.top_layout.removeWidget(self.visit_button)
                self.visit_button.deleteLater()
                self.visit_button = self.create_visit_button()
                self.visit_button.setFixedHeight(30)
                self.visit_button.clicked.connect(self.on_visit_button_clicked)
                # 找到访问按钮的正确位置并插入（在网站标签之后）
                self.top_layout.insertWidget(3, self.visit_button)
            
            # 重新创建所有外层容器以更新边框颜色
            if hasattr(self, 'current_website_key') and self.current_website_key:
                website_info = self.website_data.get(self.current_website_key)
                if website_info:
                    self.display_accounts(website_info)
            
            if sys.platform.startswith('win32'):
                self._update_title_bar_color(window_color)
        except Exception:
            pass

    def _update_title_bar_color(self, color):
        try:
            dwmapi = ctypes.WinDLL("dwmapi")
            DWMWA_CAPTION_COLOR = 35
            hwnd = int(self.winId())
            
            rgb = color.red() | (color.green() << 8) | (color.blue() << 16)
            color_dword = wintypes.DWORD(rgb)
            
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_CAPTION_COLOR,
                ctypes.byref(color_dword),
                ctypes.sizeof(color_dword)
            )
        except Exception:
            pass

    def on_add_website_clicked(self):
        """添加新网站按钮点击事件处理"""
        self.add_account_button.hide()
        self.visit_button.hide()
        self.website_label.hide()
        
        self.website_name_input.show()
        self.website_url_input.show()
        self.confirm_button.show()
        self.cancel_button.show()
        
        self.clear_flow_layout()
        
        add_outer_container = self.create_add_account_container()
        self.flow_layout.addWidget(add_outer_container, 0, 0)
        self.flow_layout.update()
        
        self.current_add_container = add_outer_container.findChild(AddAccountContainer)
        self.is_adding_website = True  # 设置变量为True，表示正在添加新网站

    def save_website_data(self, website_name, website_url, account_data):
        """
        保存网站数据和账号信息
        参数:
        website_name: str - 网站名称
        website_url: str - 网站URL
        account_data: dict - 账号信息 (包含账号、密码、备注)
        """
        try:
            # 添加新网站
            # 修复空数据时的键值生成
            if self.website_data:
                keys = [int(k) for k in self.website_data.keys() if k.isdigit()]
                new_key = str(max(keys) + 1) if keys else "1"
            else:
                new_key = "1"
                
            self.website_data[new_key] = {
                "网站名": website_name,
                "网址": website_url,
                "列表": [{
                    "账号": account_data.get("account", ""),
                    "密码": account_data.get("password", ""),
                    "备注": account_data.get("remark", "")
                }]
            }
            
            # 更新界面
            self.list_widget.addItem(website_name)
            self._save_data()
            
            # 显示状态栏提示
            show_status_message(self, f"网站 '{website_name}' 和账号 '{account_data.get('account', '')}' 已成功添加！")
            return True
        except Exception as e:
            logger.error(f"保存网站数据时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"保存网站数据失败: {str(e)}")
            return False

    def submit_new_account(self, account, password, remark, website_key=None):
        """
        提交新账号到指定网站
        参数:
        account: str - 账号
        password: str - 密码
        remark: str - 备注
        website_key: str - 网站键值 (可选)
        """
        print(f"调用函数: TitleBarColorWindow.submit_new_account(账号={account}, 密码={password}, 备注={remark}, 网站键值={website_key})")
        if not account or not password:
            QMessageBox.warning(self, "输入错误", "账号和密码不能为空！")
            return False
        
        try:
            # 确定网站键值
            if not website_key:
                if hasattr(self, 'current_website_key') and self.current_website_key:
                    website_key = self.current_website_key
                else:
                    website_keys = list(self.website_data.keys())
                    website_key = website_keys[0] if website_keys else '1'
            
            # 确保网站数据存在
            if website_key not in self.website_data:
                website_name = f"未命名网站{website_key}"
                self.website_data[website_key] = {'网站名': website_name, '网址': '', '列表': []}
            
            website = self.website_data[website_key]
            
            # 确保列表存在
            if '列表' not in website:
                website['列表'] = []
                
            new_account = {'账号': account, '密码': password}
            if remark:
                new_account['备注'] = remark
            
            website['列表'].append(new_account)
            
            # 记录添加账号统计
            try:
                from usage_stats import record_feature_usage
                record_feature_usage("add_account")
            except Exception as e:
                print(f"统计记录失败: {e}")
            
            # 保存数据
            if self._save_data():
                # 使用状态栏提示
                show_status_message(self, f"账号 {account} 已成功添加！")
                self.reload_data_and_preserve_selection()
                return True
            else:
                QMessageBox.critical(self, "错误", "保存数据失败！")
                return False
        except Exception as e:
            logger.exception(f"添加账号时出错：{str(e)}")
            QMessageBox.critical(self, "错误", f"添加账号时出错：{str(e)}")
            return False

    def update_account(self, old_account_data, new_account, new_password, new_remark):
        """更新现有账号信息"""
        try:
            # 查找并更新账号
            updated = False
            for website_key, website_info in self.website_data.items():
                if '列表' in website_info:
                    for account_data in website_info['列表']:
                        if account_data.get('账号') == old_account_data.get('账号'):
                            account_data['账号'] = new_account
                            account_data['密码'] = new_password
                            account_data['备注'] = new_remark
                            updated = True
                            break
                    if updated:
                        break
            
            if updated:
                # 记录更新账号统计
                try:
                    from usage_stats import record_feature_usage
                    record_feature_usage("update_account")
                except Exception as e:
                    print(f"统计记录失败: {e}")
                    
                if self._save_data():
                    show_status_message(self, f"账号 {new_account} 已成功更新！")
                    self.reload_data_and_preserve_selection()
                    return True
                else:
                    QMessageBox.critical(self, "错误", "保存数据失败！")
            else:
                QMessageBox.warning(self, "更新失败", f"未找到账号 {old_account_data.get('账号')}！")
        except Exception as e:
            logger.exception(f"更新账号时出错：{str(e)}")
            QMessageBox.critical(self, "错误", f"更新账号时出错：{str(e)}")
        return False

    def delete_account(self, account_data):
        """删除指定账号"""
        try:
            # 查找并删除账号
            deleted = False
            for website_key, website_info in self.website_data.items():
                if '列表' in website_info:
                    original_length = len(website_info['列表'])
                    website_info['列表'] = [
                        item for item in website_info['列表']
                        if item.get('账号') != account_data.get('账号')
                    ]
                    if len(website_info['列表']) < original_length:
                        deleted = True
                        break
            
            if deleted:
                # 记录删除账号统计
                try:
                    from usage_stats import record_feature_usage
                    record_feature_usage("delete_account")
                except Exception as e:
                    print(f"统计记录失败: {e}")
                    
                if self._save_data():
                    show_status_message(self, f"账号 {account_data.get('账号')} 已成功删除！")
                    self.reload_data_and_preserve_selection()
                    return True
                else:
                    QMessageBox.critical(self, "错误", "保存数据失败！")
            else:
                QMessageBox.warning(self, "删除失败", f"未找到账号 {account_data.get('账号')}！")
        except Exception as e:
            logger.exception(f"删除账号时出错：{str(e)}")
            QMessageBox.critical(self, "错误", f"删除账号时出错：{str(e)}")
        return False

    def on_confirm_new_website(self):
        """保存按钮点击事件处理 - 调用保存函数"""
        website_name = self.website_name_input.text().strip()
        website_url = self.website_url_input.text().strip()
        
        if not website_name:
            QMessageBox.warning(self, "输入错误", "网站名不能为空！")
            return
        if not website_url:
            QMessageBox.warning(self, "输入错误", "网址不能为空！")
            return
        
        # 获取添加账号容器中的账号信息
        if not hasattr(self, 'current_add_container') or not self.current_add_container:
            QMessageBox.warning(self, "提示", "请先添加账号！")
            return
            
        add_container = self.current_add_container
        if not hasattr(add_container, 'account_input') or not add_container.account_input:
            QMessageBox.warning(self, "提示", "请点击'+'按钮添加新账号！")
            return
        
        account = add_container.account_input.text().strip()
        password = add_container.password_input.text().strip()
        remark = add_container.remark_input.text().strip() if hasattr(add_container, 'remark_input') else ""
        
        if not account:
            QMessageBox.warning(self, "输入错误", "账号不能为空！")
            return
        if not password:
            QMessageBox.warning(self, "输入错误", "密码不能为空！")
            return
        
        # 调用保存函数
        account_data = {
            "account": account,
            "password": password,
            "remark": remark
        }
        
        if self.save_website_data(website_name, website_url, account_data):
                # 记录添加网站统计
                try:
                    from usage_stats import record_feature_usage
                    record_feature_usage("add_website")
                except Exception as e:
                    print(f"统计记录失败: {e}")
                
                # 重置界面
                self.website_name_input.hide()
                self.website_url_input.hide()
                self.confirm_button.hide()
                self.cancel_button.hide()
                
                self.website_name_input.clear()
                self.website_url_input.clear()
                
                self.add_account_button.show()
                self.visit_button.show()
                self.website_label.show()
                self.website_label.setText("请从左侧列表选择网站")
                
                # 重新加载数据
                self.reload_data_and_preserve_selection()
                
                # 选中最后一个项目
                count = self.list_widget.count()
                if count > 0:
                    last_item = self.list_widget.item(count - 1)
                    self.list_widget.setCurrentItem(last_item)
                    self.on_list_item_clicked(last_item)
                
                self.is_adding_website = False  # 设置变量为False，表示保存完毕

    def load_encrypted_data(self, file_path):
        """加载加密数据"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    encrypted_data = f.read()
                
                # 获取密码
                password, ok = QInputDialog.getText(
                    self, 
                    "密码验证", 
                    "请输入密码：", 
                    QLineEdit.EchoMode.Password
                )
                
                if ok and password:
                    try:
                        cipher = PasswordBasedEncryption()
                        decrypted_data = cipher.decrypt_data(encrypted_data, password)
                        return json.loads(decrypted_data)
                    except ValueError as e:
                        logger.warning(f"密码派生解密失败: {str(e)}")
                        # 尝试旧的密钥文件方式（向后兼容）
                        try:
                            from cryptography.fernet import Fernet
                            current_dir = os.path.dirname(file_path)
                            key_path = os.path.join(current_dir, 'secret.key')
                            if os.path.exists(key_path):
                                with open(key_path, 'rb') as f:
                                    key = f.read()
                                fernet = Fernet(key)
                                decrypted_data = fernet.decrypt(encrypted_data).decode('utf-8')
                                return json.loads(decrypted_data)
                        except Exception as e2:
                            logger.warning(f"旧密钥解密也失败: {str(e2)}")
                            # 尝试以明文方式读取（用于向后兼容）
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    return json.load(f)
                            except Exception as e3:
                                logger.error(f"明文读取失败: {e3}")
                else:
                    logger.warning("用户取消密码输入")
            return {}
        except Exception as e:
            logger.error(f"加载数据失败: {str(e)}")
            return {}
    
    def _save_data(self):
        """保存网站数据到文件（加密）"""
        try:
            # 获取程序运行目录
            if hasattr(sys, '_MEIPASS'):
                # 当程序被PyInstaller打包后
                current_dir = os.path.dirname(sys.executable)
            else:
                # 开发模式
                current_dir = os.path.dirname(os.path.abspath(__file__))
            
            file_path = os.path.join(current_dir, 'data.json')
            
            # 获取密码
            password = self._get_password_from_user()
            if not password:
                logger.warning("用户取消密码输入，数据未保存")
                return False
            
            cipher = PasswordBasedEncryption()
            data_to_save = json.dumps({"记录网站": self.website_data}, ensure_ascii=False, indent=4)
            encrypted_data = cipher.encrypt_data(data_to_save, password)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)

            return True
        except Exception as e:
            logger.error(f"保存数据失败: {str(e)}")
            return False

    def on_cancel_new_website(self):
        """添加新网站流程的返回按钮点击事件处理"""
        self.website_name_input.hide()
        self.website_url_input.hide()
        self.confirm_button.hide()
        self.cancel_button.hide()
        
        self.website_name_input.clear()
        self.website_url_input.clear()
        
        self.add_account_button.show()
        self.visit_button.show()
        self.website_label.show()
        
        if self.list_widget.count() > 0:
            first_item = self.list_widget.item(0)
            self.list_widget.setCurrentItem(first_item)
            self.on_list_item_clicked(first_item)

    def on_list_context_menu(self, position):
        """列表框右键菜单事件处理"""
        # 获取当前选中项
        item = self.list_widget.itemAt(position)
        if item:
            # 创建右键菜单
            context_menu = QMenu()
            delete_action = context_menu.addAction("删除")
            delete_action.triggered.connect(lambda: self.on_delete_website_clicked(item))
            # 显示菜单
            context_menu.exec(self.list_widget.mapToGlobal(position))

    def on_delete_website_clicked(self, item):
        """删除网站按钮点击事件处理"""
        website_name = item.text()
        # 询问确认
        reply = QMessageBox.question(self, "确认删除", f"确定要删除网站 '{website_name}' 吗？",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # 查找并删除网站
            website_key_to_delete = None
            for key, info in self.website_data.items():
                if info.get('网站名') == website_name:
                    website_key_to_delete = key
                    break
            if website_key_to_delete:
                del self.website_data[website_key_to_delete]
                # 保存数据
                if self._save_data():
                    show_status_message(self, f"网站 '{website_name}' 已成功删除！")
                    # 更新列表
                    self.update_website_list()
                else:
                    QMessageBox.critical(self, "错误", "保存数据失败！")

    def reload_data_and_preserve_selection(self):
        """重新加载数据并保持当前选中项"""
        current_key = self.current_website_key if hasattr(self, 'current_website_key') else None
        
        self._load_data()
        
        if current_key and current_key in self.website_data:
            target_website_name = self.website_data[current_key].get('网站名', '')
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if item.text() == target_website_name:
                    self.list_widget.setCurrentItem(item)
                    self.on_list_item_clicked(item)
                    return
        
        if self.list_widget.count() > 0:
            item = self.list_widget.item(0)
            self.list_widget.setCurrentItem(item)
            self.on_list_item_clicked(item)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.ApplicationPaletteChange:
            self.apply_system_theme_color()
        return super().eventFilter(obj, event)
        
    def resizeEvent(self, event):
        # 计算新的列数
        new_columns = self.calculate_columns()
        
        # 只有当列数发生变化时才更新布局
        if new_columns != self.current_columns:
            if self.resize_timer is not None:
                self.resize_timer.stop()
            
            from PyQt6.QtCore import QTimer
            self.resize_timer = QTimer(self)
            self.resize_timer.setSingleShot(True)
            self.resize_timer.timeout.connect(self.delayed_layout_update)
            self.resize_timer.start(50)
        
        super().resizeEvent(event)
        
    def delayed_layout_update(self):
        # 更新当前列数
        self.current_columns = self.calculate_columns()
        
        # 如果有账号容器并且在显示状态，重新排列容器
        if hasattr(self, 'current_account_containers') and self.current_account_containers:
            self.rearrange_containers()
        else:
            # 否则更新几何和布局
            self.flow_container.updateGeometry()
            self.flow_container.update()
            self.flow_layout.update()
        self.scroll_area.update()
        
        if self.list_widget.count() > 0:
            current_item = self.list_widget.currentItem()
            if current_item:
                self.on_list_item_clicked(current_item)
            else:
                first_item = self.list_widget.item(0)
                self.list_widget.setCurrentItem(first_item)
                self.on_list_item_clicked(first_item)


if __name__ == '__main__':
    # 预加载所有SVG图标
    app = QApplication(sys.argv)
    app.setFont(QFont("SimHei"))
    preload_all_icons()
    window = TitleBarColorWindow()
    sys.exit(app.exec())