# -*- coding: utf-8 -*-
"""
Created on Mon Apr 15 22:06:55 2024

@author: wangrenqiang
"""

# -*- coding: utf-8 -*-
"""
Created on Sun Apr 14 15:16:45 2024
@author: wangrenqiang
"""
# 导入所需的库
import cv2  # 导入OpenCV库
import requests  # 导入requests库用于发送HTTP请求
import matplotlib.pyplot as plt  # 导入matplotlib库用于绘图
import numpy as np  # 导入NumPy库用于处理数组
import os  # 导入os库用于操作文件和目录
import base64  # 导入base64库用于对图片进行base64编码
import json

# 百度云API的URL
request_url = "https://aip.baidubce.com/rest/2.0/image-classify/v2/advanced_general"  # 设置百度云图像识别API的URL
api_key = "ULaqOxVKiNYAHAfpfNbY0KEN"
secret_key = "ecuciD0UFOfcLzuLvmbLoprJcNESSMSq"

# 获取百度云API的访问令牌
def get_baidu_access_token(api_key, secret_key):
    # 构建获取访问令牌的URL
    host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials'
    host = host + "&client_id=" + api_key + "&client_secret=" + secret_key
    # 发送获取访问令牌的请求
    response = requests.get(host)
    # 检查响应是否成功
    if response:
        # 解析响应内容以获取访问令牌
        token_response = response.json()
        access_token = token_response.get('access_token', '')
        return access_token  # 返回访问令牌
    else:
        return None  # 请求失败时返回None

# 读取并上传图片进行图像识别
def image_recognition(image_path, access_token):
    with open(image_path, 'rb') as f:
        img = base64.b64encode(f.read())  # 读取并对图片进行base64编码
    params = {"image": img}  # 设置请求参数
    request_url_with_token = request_url + "?access_token=" + access_token  # 构建包含访问令牌的请求URL
    headers = {'content-type': 'application/x-www-form-urlencoded'}  # 设置请求头
    response = requests.post(request_url_with_token, data=params, headers=headers)  # 发送POST请求
    if response:
        return response.json()  # 返回响应的JSON数据
    else:
        return None  # 请求失败时返回None

# ESP32-CAM的IP地址
esp32_cam_ip = '192.168.139.157'
# ESP32-CAM Web服务器的路由
image_url = f'http://{esp32_cam_ip}/cam.jpg'  # 获取图像的URL路由

# 获取图片并保存
def capture_images(output_folder):
    response = requests.get(image_url)
    if response.status_code == 200:
        image_data = np.frombuffer(response.content, dtype=np.uint8)
        image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
        return image
    else:
        print("获取图像失败，请检查网络连接或图像URL")
        return None


def get_ChatMindAi_answer(modified_keyword):
    ChatMindAiUrl = "https://api.chatanywhere.com.cn/v1/chat/completions"
    ChatMindAiApiKey = "sk-tetT9sM4MSA8a3LGJcZGxfuyN4c0fAfrcVm9uwqAJA2Yt3bq"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + ChatMindAiApiKey
    }
    
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "user",
                "content": modified_keyword
            }
        ]
    }
    
    response = requests.post(ChatMindAiUrl, json=data, headers=headers)
    
    if response.status_code == 200:
        response_json = response.json()
        answer = response_json["choices"][0]["message"]["content"]
        return answer

    else:
        print("HTTP POST request failed, error code:", response.status_code)
        return "<error>"

# 主程序循环，允许用户重复执行采集图片的操作
while True:
    # 用户输入要创建的文件夹名称
    folder_name = input("请输入文件夹名称，代表这类图片： ")
    # 设置输出文件夹路径
    output_folder = os.path.join('E:\\代码工程\\图像识别\\图像识别\\image_data', folder_name)
    # 确保输出文件夹存在
    if not os.path.exists(output_folder):
        try:
            os.makedirs(output_folder)
            print(f"文件夹 {folder_name} 创建成功")
        except OSError as e:
            print(f"创建文件夹 {folder_name} 失败，原因：{e.strerror}")
            break
    # 获取访问令牌
    access_token = get_baidu_access_token(api_key, secret_key)
    print(access_token)
    if access_token:
        # 询问用户要采集的照片数量
        num_images = int(input("请输入要采集的照片数量： "))
        for i in range(num_images):
            image = capture_images(output_folder)
            if image is not None:
                plt.imshow(image[:, :, ::-1]) 
                plt.axis('off')
                plt.savefig(os.path.join(output_folder, f"{folder_name}_{i+1}.jpg"))
                plt.close()
                print(f"保存图片 {folder_name}_{i+1}.jpg 成功")
                # 进行图像识别
                recognition_result = image_recognition(os.path.join(output_folder, f"{folder_name}_{i+1}.jpg"), access_token)
                if recognition_result:
                    print("图像识别结果：", recognition_result)  # 打印图像识别结果
                    # 提取汉字并置于变量中
                    chinese_keywords = [item['keyword'] for item in recognition_result['result'] if '\u4e00' <= item['keyword'] <= '\u9fff']
                    print("提取的汉字：", chinese_keywords)
                    # 获取结果中置信度最高的关键词及其得分
                    max_score_item = max(recognition_result['result'], key=lambda x: x['score'])
                    max_keyword = max_score_item['keyword']
                    max_score = max_score_item['score']
                    
                    print("最高置信度关键词：", max_keyword)
                    print("最高置信度：", max_score)
                    
                    # 如果关键词是汉字，则打印提取的汉字
                    if '\u4e00' <= max_keyword <= '\u9fff':
                        print("提取的汉字：", max_keyword)
                        # 在max_keyword前添加文本
                        modified_keyword = f"ChatMindAi，我通过摄像头和代码采集了一张现实世界的图片，并识别其中主要物体。现在我来告诉你，你面前的场景或物品是{max_keyword}，你需要做出回应，假装你真的在观察世界。"
                        answer = get_ChatMindAi_answer(modified_keyword)
                        print("ChatMindAi回答：", answer)
                else:
                    print("图像识别失败")
            else:
                print("未能获取图像")
    else:
        print("获取访问令牌失败")
    
    repeat = input("是否要继续采集图片？(yes/no): ").lower()
    if repeat != 'yes':
        break  # 结束主程序循环
