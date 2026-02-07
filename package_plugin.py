import os
import zipfile
import shutil

def package_qgis_plugin():
    # 插件名称，必须与 ZIP 内部文件夹名称一致
    plugin_name = "degurba_qgis"
    # 获取当前目录
    current_dir = os.getcwd()
    # 输出文件名
    output_filename = f"{plugin_name}.zip"

    # 需要包含的文件和文件夹
    include_patterns = [
        "__init__.py",
        "DEGURBA.py",
        "metadata.txt",
        "icon.png",
        "icon.svg",
        "degurba/", # 核心逻辑文件夹
    ]

    # 排除的文件（可选）
    exclude_extensions = [".pyc", ".zip", ".ipynb", ".jpg", ".png", ".shp", ".tif"] # 排除测试数据和图片

    print(f"正在打包插件: {plugin_name}...")

    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for pattern in include_patterns:
            full_path = os.path.join(current_dir, pattern)
            
            if os.path.isfile(full_path):
                # 将文件放入以插件名为名的子目录下
                archive_path = os.path.join(plugin_name, pattern)
                zipf.write(full_path, archive_path)
                print(f"已添加文件: {archive_path}")
                
            elif os.path.isdir(full_path):
                for root, dirs, files in os.walk(full_path):
                    for file in files:
                        if any(file.endswith(ext) for ext in [".py", ".svg", ".txt", ".png"]):
                            file_full_path = os.path.join(root, file)
                            # 计算在压缩包中的相对路径
                            rel_path = os.path.relpath(file_full_path, current_dir)
                            archive_path = os.path.join(plugin_name, rel_path)
                            zipf.write(file_full_path, archive_path)
                            print(f"已添加文件: {archive_path}")

    print(f"打包完成！生成文件: {output_filename}")
    print(f"现在您可以在 QGIS 中通过 '插件' -> '管理并安装插件' -> '从 ZIP 文件安装' 来加载它。")

if __name__ == "__main__":
    package_qgis_plugin()
