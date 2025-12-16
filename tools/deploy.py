import os
import time
import subprocess

# ================= 配置区 =================
# 自动定位到 client/loader.js 文件
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOADER_LOCAL_FILE = os.path.join(BASE_DIR, "client", "loader.js")

# 手机上的目标路径
REMOTE_PATH = "/sdcard/脚本/loader.js" 

# AutoX.js 包名
APP_PACKAGE = "org.autojs.autoxjs.v6"
# ==========================================

def get_devices():
    devices = []
    try:
        result = subprocess.run("adb devices", shell=True, capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        for line in lines[1:]:
            if "\tdevice" in line:
                devices.append(line.split('\t')[0])
    except: pass
    return devices

def run_adb(dev_id, cmd):
    subprocess.run(f"adb -s {dev_id} {cmd}", shell=True)

def main():
    print(f"\n>>> 👨‍✈️ 群控指挥官启动...")
    print(f"    本地源文件: {LOADER_LOCAL_FILE}")
    
    if not os.path.exists(LOADER_LOCAL_FILE):
        print(f"❌ 错误：找不到 loader.js")
        return

    devices = get_devices()
    if not devices:
        print("❌ 未发现在线设备，请检查雷电模拟器是否开启ADB。")
        return
        
    print(f"✅ 扫描到 {len(devices)} 台设备: {devices}")
    print("-" * 40)
    
    for dev in devices:
        print(f"🚀 正在处理设备: {dev}")
        
        # 1. 创建目录 (防止报错)
        run_adb(dev, "shell mkdir -p /sdcard/脚本/")

        # 2. 推送 Loader
        print(f"   └─ 安装启动器...", end="")
        # 注意：路径如果包含空格需要小心，这里假设无空格
        run_adb(dev, f'push "{LOADER_LOCAL_FILE}" "{REMOTE_PATH}"')
        print(" OK")
        
        # 3. 重启 AutoX.js
        print(f"   └─ 唤醒应用...", end="")
        run_adb(dev, f"shell am force-stop {APP_PACKAGE}")
        time.sleep(0.5)
        run_adb(dev, f"shell monkey -p {APP_PACKAGE} -c android.intent.category.LAUNCHER 1")
        print(" OK")
        
    print("-" * 40)
    print("🎉 部署完成！")
    print(f"👉 请在手机 AutoX.js 列表中运行：【loader.js】")

if __name__ == "__main__":
    main()