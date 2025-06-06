import importlib.metadata
from pathlib import Path

def create_version_info(package_name:str="subdx-dl", github_username:str="Spheres-cu", output_file:str="version.txt"):
    """
    Creates a version info file for PyInstaller
    
    Args:
        package_name (str): Name of your Python package
        github_username (str): Your GitHub username (for CompanyName)
        output_file (str): Path to output version info file
    """
    try:
        # Get package version
        version = importlib.metadata.version(package_name)
        
        # Split version into components
        version_parts = version.split('.')
        file_version = ".".join(version_parts[:4])  # Takes up to 4 parts
        product_version = version
        
        # Create version info content
        #
        # For more details about fixed file info 'ffi' see:
        # https://learn.microsoft.com/en-us/windows/win32/menurc/versioninfo-resource
        # Fixed file info
        content = f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({version_parts[0] if len(version_parts) > 0 else 0}, {version_parts[1] if len(version_parts) > 1 else 0}, {version_parts[2] if len(version_parts) > 2 else 0}, {version_parts[3] if len(version_parts) > 3 else 0}),
    prodvers=({version_parts[0] if len(version_parts) > 0 else 0}, {version_parts[1] if len(version_parts) > 1 else 0}, {version_parts[2] if len(version_parts) > 2 else 0}, {version_parts[3] if len(version_parts) > 3 else 0}),
    mask=0x3f,
    flags=0x0,
    OS=0x4,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'{github_username}'),
        StringStruct(u'FileDescription', u'{package_name}'),
        StringStruct(u'FileVersion', u'{file_version}'),
        StringStruct(u'InternalName', u'{package_name}'),
        StringStruct(u'LegalCopyright', u'Copyright (C) {github_username}'),
        StringStruct(u'OriginalFilename', u'{package_name}.exe'),
        StringStruct(u'ProductName', u'{package_name}'),
        StringStruct(u'ProductVersion', u'{product_version}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
        
        # Write to file
        Path(output_file).write_text(content, encoding='utf-8')
        print(f"Version info file created at: {output_file}")
        
    except importlib.metadata.PackageNotFoundError:
        print(f"Error: Package '{package_name}' not found. Make sure it's installed.")
    except Exception as e:
        print(f"Error creating version info: {str(e)}")
        
create_version_info()

exit()