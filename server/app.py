from flask import Flask, request, jsonify
from paddleocr import PaddleOCR
import base64
import re
import time
import logging
import os

# 1. 基础设置：屏蔽日志
logging.getLogger("ppocr").setLevel(logging.ERROR)

app = Flask(__name__)

# 全局变量：存储设备状态
device_registry = {}

print("\n" + "="*60)
print(">>> 🤖 AI 视觉服务 (云控管理 + OCR修复版) 启动中...")
# 适配 v5 模型的关键参数
ocr = PaddleOCR(use_textline_orientation=True, lang="ch")
print(">>> ✅ 模型加载完毕！")
print("="*60 + "\n")

# ==========================================
# 🛠️ 辅助功能区
# ==========================================
def get_current_script_info():
    """读取本地 business.js 的版本号和内容"""
    try:
        # ⚠️ 唯一修改的地方：为了适应新目录结构，这里要往上找 client 文件夹
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # 指向 ../client/business.js
        script_path = os.path.join(base_dir, '..', 'client', 'business.js')
        
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 用正则提取 var VERSION_NAME = "xxx";
        match = re.search(r'var VERSION_NAME = "(.*?)";', content)
        version = match.group(1) if match else "Unknown"
        return version, content
    except Exception as e:
        # 如果找不到文件，打印一下路径方便调试
        print(f"❌ 找不到脚本文件，请确认位置: {e}")
        return "Error", str(e)

def write_status_log():
    """写入设备状态统计日志"""
    total = len(device_registry)
    current_ver, _ = get_current_script_info()
    
    updated_count = sum(1 for d in device_registry.values() if d.get('version') == current_ver)
    
    log_content = f"""
================ 设备状态报告 ================
生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
服务端最新代码版本: {current_ver}
在线设备总数: {total}
已更新设备数: {updated_count}
待更新设备数: {total - updated_count}
--------------------------------------------
设备详情:
"""
    for dev_id, info in device_registry.items():
        log_content += f"[{dev_id}] \t版本: {info.get('version')} \t最后活跃: {info.get('last_seen')}\n"
    
    try:
        with open("device_status_log.txt", "w", encoding="utf-8") as f:
            f.write(log_content)
    except Exception as e:
        print(f"❌ 写入日志失败: {e}")

# ==========================================
# ⚙️ OCR 核心配置区
# ==========================================
class ExtractConfig:
    KEYWORDS = [
        "weixin", "wechat", "vx", "wx", "v", 
        "微信", "威信", "卫星", "维新", "微",
        "加", "搜", "私", "➕", "\\+", "十" 
    ]
    ACCOUNT_PATTERN = r"[a-zA-Z0-9\-_]{5,25}"

def clean_noise_text(text_list):
    cleaned = []
    for t in text_list:
        if len(t) == 1 and re.match(r"[a-zA-Z]", t):
            continue 
        cleaned.append(t)
    return cleaned

def universal_extract(text_list, is_test=False):
    # 1. 降噪
    clean_list = clean_noise_text(text_list)
    # 2. 拼接
    full_text = " ".join(clean_list).lower()
    # 3. 构造正则
    kw_pattern = "|".join(ExtractConfig.KEYWORDS)
    regex = rf"({kw_pattern})\s*[:\-：👉\.\s]*\s*({ExtractConfig.ACCOUNT_PATTERN})"
    
    matches = re.findall(regex, full_text)
    found_contacts = set()
    
    if matches:
        for match in matches:
            trigger_word, account = match
            if account.isdigit() and len(account) < 6: continue
            found_contacts.add(account)
            
    if found_contacts:
        return True, ", ".join(found_contacts)
            
    return False, None

# ==========================================
# 📡 路由接口区
# ==========================================

# 【新增接口】Loader 请求下载脚本 (版本比对逻辑)
@app.route('/get_latest_script', methods=['GET'])
def get_latest_script():
    server_version, content = get_current_script_info()
    client_version = request.args.get('current_version')
    
    print(f"📡 版本检查: 客户端[{client_version}] vs 服务端[{server_version}]")
    
    if client_version == server_version:
        return jsonify({"status": "latest", "version": server_version})
    else:
        return jsonify({"status": "update", "version": server_version, "code": content})

# 【新增接口】脚本启动时汇报状态
@app.route('/report_status', methods=['POST'])
def report_status():
    data = request.json
    dev_id = data.get('device_id')
    version = data.get('version')
    
    device_registry[dev_id] = {
        "version": version,
        "last_seen": time.strftime('%H:%M:%S')
    }
    
    write_status_log()
    print(f"📶 设备上线: {dev_id} (Ver: {version})")
    return {"code": 200}

# 【核心接口】OCR 识别 (保持原样)
@app.route('/ocr_check', methods=['POST'])
def ocr_check():
    try:
        data = request.json
        img_base64 = data.get('image')
        device_id = data.get('device_id', 'Unknown')
        
        filename = f"scan_{device_id}.jpg"
        with open(filename, 'wb') as f:
            f.write(base64.b64decode(img_base64))
        
        # 1. 识别
        result = ocr.predict(filename)
        txts = []
        scores = []
        if result and len(result) > 0:
            item = result[0]
            txts = item.get("rec_texts", [])
            scores = item.get("rec_scores", [])
            
            # 打印详细日志
            print(f"\n--- 📸 设备 [{device_id}] OCR原始结果 ---")
            for t, s in zip(txts, scores):
                print(f"{s:.4f} | {t}")
            print("-" * 40)
            
        # 2. 提取
        found, contacts = universal_extract(txts)
        
        if found:
            log_msg = f"[{time.strftime('%H:%M:%S')}] [Dev:{device_id}] 🎯 命中: {contacts}"
            print(log_msg)
            with open("data_result.txt", "a", encoding="utf-8") as f:
                f.write(log_msg + "\n")
            return {"code": 200, "found": True, "contact": contacts}
        else:
            print(f"👀 未发现目标")
            return {"code": 200, "found": False}

    except Exception as e:
        print(f"❌ 报错: {e}")
        return {"code": 500, "msg": str(e)}

# ==========================================
# 🧪 自测模块
# ==========================================
if __name__ == '__main__':
    print("------- 🛡️  正则逻辑自检  -------")
    test_cases = [
        (["请加vx：232323aa"], True),
        (["搜 微：232323bb"], True),
        (["联系 +v：232323cc"], True),
        (["➕：232323dd"], True),
        (["直接+232323ee"], True),
        (["黑话 卫星232323ff"], True),
        (["加v: wang-888", "或者搜vx: 666888"], True),
        (["十：232323dd，直接+"], True), 
    ]

    pass_count = 0
    for txt_list, expected in test_cases:
        found, result_str = universal_extract(txt_list)
        if found == expected: pass_count += 1
        else: print(f"❌ 失败案例: {txt_list}")

    if pass_count == len(test_cases):
        print(f"✅ 自测通过 ({pass_count}/{len(test_cases)})，服务启动中...")
        app.run(host='0.0.0.0', port=5000, threaded=True)
    else:
        print("⚠️ 自测失败，请检查配置！")
        input("按回车强制启动...")
        app.run(host='0.0.0.0', port=5000, threaded=True)