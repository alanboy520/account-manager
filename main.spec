# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 定义要包含的额外文件
added_files = [
    ('svg_icons_data.py', '.'),
    ('temp\copy.svg', 'temp'),
    ('temp\eye.svg', 'temp'),
    ('temp\eye2.svg', 'temp'),
    ('temp\TdesignJump.svg', 'temp'),
    ('img\ico.ico', 'img'),
    ('data.json', '.'),
    ('secret.key', '.'),
    ('version.json', '.'),
]

# 定义分析选项
a = Analysis(['main.py'],
             pathex=['d:\\Users\\czuu\\Desktop\\4.0'],
             binaries=[],
             datas=added_files,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

# 定义pyz选项
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 定义exe选项
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='账号记事本',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None,
          icon=['img\\ico.ico']
          )