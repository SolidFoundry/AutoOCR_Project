// ==========================================
// loader.js - 智能缓存启动器
// ==========================================
var SERVER_IP = "192.168.3.77"; // ⚠️⚠️⚠️ 请务必修改为你电脑的真实IP
var BASE_URL = "http://" + SERVER_IP + ":5000/get_latest_script";

// 本地存储业务逻辑的路径
var LOCAL_PATH = "/sdcard/脚本/business.js"; 

// 使用 AutoX.js 的本地存储功能来记住版本号
var storage = storages.create("script_config_v1");
var currentVer = storage.get("version", "0.0.0"); // 默认为 0.0.0

console.hide();
toast("☁️ 检查更新 (当前: " + currentVer + ")...");

try {
    // 1. 发送请求，带上当前版本号
    var res = http.get(BASE_URL + "?current_version=" + currentVer);
    
    if (res.statusCode == 200) {
        var result = res.body.json();
        
        if (result.status == "update") {
            // === 情况A：有新版本 ===
            var newVer = result.version;
            var newCode = result.code;
            
            toast("⬇️ 发现新版: " + newVer + "，正在下载...");
            
            // 覆盖写入本地
            files.write(LOCAL_PATH, newCode);
            // 更新本地记忆的版本号
            storage.put("version", newVer);
            
            log("✅ 更新完毕，启动新版...");
            sleep(500);
            
        } else {
            // === 情况B：已经是最新 ===
            toast("⚡ 已是最新版 (" + currentVer + ")，直接启动");
        }
        
        // 2. 启动业务脚本
        if (files.exists(LOCAL_PATH)) {
            engines.execScriptFile(LOCAL_PATH);
        } else {
            alert("错误", "本地文件丢失，请清除缓存重试");
            storage.put("version", "0.0.0");
        }
        
    } else {
        toast("⚠️ 服务器异常，尝试运行本地版...");
        runLocal();
    }
} catch (e) {
    toast("❌ 网络不通，运行本地版...");
    runLocal();
}

function runLocal() {
    if (files.exists(LOCAL_PATH)) {
        engines.execScriptFile(LOCAL_PATH);
    } else {
        alert("致命错误", "无网络且无本地文件");
    }
}