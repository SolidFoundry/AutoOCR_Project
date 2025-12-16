// ==========================================
// business.js - 核心业务逻辑 
// ==========================================
var VERSION_NAME = "v2.1.2"; // ⚠️ 每次修改代码，记得改这里！

// 配置区
var SERVER_IP = "192.168.3.77"; // ⚠️⚠️⚠️ 请务必修改为你电脑的真实IP
var URL_OCR = "http://" + SERVER_IP + ":5000/ocr_check";
var URL_REPORT = "http://" + SERVER_IP + ":5000/report_status";

// 1. 获取设备ID
var DEVICE_ID = device.getAndroidId();

// 2. 向服务端汇报：我已就绪，运行的是哪个版本
http.postJson(URL_REPORT, {
    "device_id": DEVICE_ID,
    "version": VERSION_NAME,
    "status": "Running"
});

console.hide();
toast("设备 [" + DEVICE_ID + "] 正在运行 " + VERSION_NAME);

// --- 业务逻辑开始 ---

toast("请打开图片，保持不动！");
for(var i=3; i>0; i--){
    toast("倒计时: " + i);
    sleep(1000);
}

// ROOT 截图逻辑
var path = "/sdcard/ocr_temp.png";
var r = shell("screencap -p " + path, true);

if (r.code != 0) {
    alert("截图失败", "请检查 ROOT 权限");
    exit();
}

var img = images.read(path);
if (!img) {
    alert("错误", "图片读取失败");
    exit();
}

// 压缩 (降低网络负载)
var imgBase64 = images.toBase64(img, "jpg", 50);
img.recycle();

toast("🚀 发送中...");

try {
    var payload = {
        "device_id": DEVICE_ID,
        "version": VERSION_NAME,
        "image": imgBase64
    };

    var res = http.postJson(URL_OCR, payload);
    
    if (res.statusCode == 200) {
        var result = res.body.json();
        
        if (result.found) {
            device.vibrate(500);
            alert("🎯 成功！(Ver: " + VERSION_NAME + ")", 
                  "抓到内容: " + result.contact);
        } else {
            toast("👀 未发现");
        }
    } else {
        toast("服务器报错: " + res.statusCode);
    }
} catch (e) {
    toast("网络错误: " + e);
}