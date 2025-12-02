<?php
/**
 * 众测结果提交接口
 * 接收 POST 请求，保存用户评测结果
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

// 处理 OPTIONS 请求（CORS预检）
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

// 只接受 POST 请求
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// 读取请求数据
$input = file_get_contents('php://input');
$data = json_decode($input, true);

if (!$data) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid JSON']);
    exit;
}

// 验证必需字段
if (!isset($data['userId']) || !isset($data['results'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing required fields']);
    exit;
}

// 创建结果目录
$resultsDir = __DIR__ . '/results';
if (!is_dir($resultsDir)) {
    mkdir($resultsDir, 0755, true);
}

// 生成文件名
$userId = preg_replace('/[^a-zA-Z0-9_\-\x{4e00}-\x{9fa5}]/u', '', $data['userId']);
$timestamp = date('Ymd_His');
$filename = "result_{$userId}_{$timestamp}.json";
$filepath = $resultsDir . '/' . $filename;

// 保存数据
$saved = file_put_contents($filepath, json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));

if ($saved === false) {
    http_response_code(500);
    echo json_encode(['error' => 'Failed to save results']);
    exit;
}

// 返回成功响应
http_response_code(200);
echo json_encode([
    'success' => true,
    'message' => 'Results saved successfully',
    'filename' => $filename
]);

