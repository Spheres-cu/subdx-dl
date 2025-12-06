# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import copy_metadata

datas = [('.resources/UnRAR.exe', '.'), ('sdx_dl/language', 'sdx_dl/language')]
hiddenimports = []
datas += collect_data_files('guessit')
datas += collect_data_files('babelfish')
datas += copy_metadata('readchar')
datas += collect_data_files('DrissionPage')
hiddenimports += collect_submodules('guessit')
hiddenimports += collect_submodules('babelfish')
hiddenimports += collect_submodules('DrissionPage')

a = Analysis(
    ['sdx_dl/cli.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [('O', None, 'OPTION'), ('O', None, 'OPTION')],
    name='subdx-dl',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version.txt',
    icon=['.resources/subdx_dl.ico'],
)
