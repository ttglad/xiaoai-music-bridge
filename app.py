# -*- coding: UTF-8 -*-
import hashlib
import logging
import os
import yaml

from flask import Flask, abort, request
from hashlib import md5
import hmac
import base64
import urllib.parse
from email.utils import parsedate_to_datetime

from apis.xiaoai.xiaoai import (XiaoAIAudioItem, XiaoAIDirective, XiaoAIOpenResponse,
                                XiaoAIResponse, XiaoAIStream, XiaoAIToSpeak, XiaoAITTSItem,
                                xiaoai_request, xiaoai_response)

from musicdl import musicdl
from apis.music.plex import search_bub_music

def get_md5_base64(data: bytes) -> str:
    if not data:
        return ''
    hash_md5 = md5()
    hash_md5.update(data)
    return base64.b64encode(hash_md5.digest()).decode()

def normalize_query_params(query_string: str) -> str:
    parsed = urllib.parse.parse_qs(query_string, keep_blank_values=True)
    items = []
    for key in sorted(parsed):
        values = sorted(parsed[key])
        for value in values:
            items.append(f"{key}={value}")
    return "&".join(items)

def check_sign(request):

    # 1. HTTP Method
    http_method = request.method.upper()

    # 2. URL Path（不包含 query string）
    url_path = urllib.parse.urlparse(request.url).path

    # 3. Query string 规范化
    raw_query = urllib.parse.urlparse(request.url).query
    normalized_query = normalize_query_params(raw_query)

    # 4. 获取时间头
    date_header = request.headers.get("X-Xiaomi-Date") or request.headers.get("Date", "")
    try:
        parsedate_to_datetime(date_header)  # 验证是否为 RFC1123 格式
    except Exception:
        return "Invalid Date Format", 400

    # 5. x-original-host
    original_host = request.headers.get('X-Original-Host')

    # 6. Content-Type
    content_type = request.headers.get("Content-Type", "")

    # 7. Content-MD5
    body = request.get_data()
    content_md5 = request.headers.get("Content-MD5", get_md5_base64(body if body else b""))

    # 8. 额外 header（MIAI-HmacSHA256-V1 不需要）
    extra_header = ""

    # 构建签名字符串
    signature_string = (
        f"{http_method}\n"
        f"{url_path}\n"
        f"{normalized_query}\n"
        f"{date_header}\n"
        f"{original_host}\n"
        f"{content_type}\n"
        f"{content_md5}\n"
        f"{extra_header}"
    )

    secret_bytes = base64.b64decode(config['xiaoai']['secret-key'].encode("utf-8"))
    # print(secret_bytes)
    # 计算签名
    # expected_signature = base64.b64encode(
    #     hmac.new(SECRET_KEY, signature_string.encode('utf-8'), sha256).digest()
    # ).decode()
    signature = hmac.new(secret_bytes, signature_string.encode('utf-8'), hashlib.sha256).hexdigest()
    expected_signature = (f"{config['xiaoai']['sign-version']} {config['xiaoai']['key-id']}:{config['xiaoai']['scope']}:{signature}")
    # print(expected_signature)

    # 从 header 中读取传入的签名
    provided_signature = request.headers.get("Authorization", "").strip()

    # 验证签名
    if expected_signature != provided_signature:
        # abort(401, f"Signature mismatch.\nExpected: {expected_signature}\nProvided: {provided_signature}")
        abort(401, f"Signature mismatch.")


# 创建小爱文本回复
def build_text_message(to_speak, is_session_end, open_mic, not_understand):
    xiao_ai_response = XiaoAIResponse(
        to_speak=XiaoAIToSpeak(type_=0, text=to_speak),
        open_mic=open_mic, not_understand=not_understand)
    response = xiaoai_response(XiaoAIOpenResponse(version='1.0',
                                                  is_session_end=is_session_end,
                                                  response=xiao_ai_response))
    return response

# 创建小爱音乐回复
def build_music_message(to_speak, mp3_urls):
    all_list = []
    if to_speak is not None:
        info_tts = XiaoAIDirective(
            type_='tts',
            tts_item=XiaoAITTSItem(
                type_='0', text=to_speak
            ))

        all_list.append(info_tts)
    for url in mp3_urls:
        info_audio = XiaoAIDirective(
            type_='audio',
            audio_item=XiaoAIAudioItem(stream=XiaoAIStream(url=url))
        )
        all_list.append(info_audio)
    xiao_ai_response = XiaoAIResponse(directives=all_list, open_mic=False, not_understand=False)
    response = xiaoai_response(XiaoAIOpenResponse(
        version='1.0', is_session_end=True, response=xiao_ai_response))
    return response


# 获取查询到的文件播放流
def get_search_music(key, artist, config=None):
    mp3_urls = []
    if config['plex']['enable'] == True:
        mp3_urls = search_bub_music(config['plex']['server-url'], config['plex']['token'], key)

    # 查询三方源api
    if len(mp3_urls) <= 0:
        musicdl_config = {
            'logfilepath': config['musicdl']['log-path'],
            'savedir': config['musicdl']['save-dir'],
            'search_size_per_source': config['musicdl']['search-size'],
            'proxies': config['musicdl']['proxies']
        }
        target_srcs = config['musicdl']['sources']
        client = musicdl.musicdl(config=musicdl_config)
        search_results = client.search(key, target_srcs)
        logging.debug(f"musicdl search result is: {search_results}")

        for key, value in search_results.items():
            # logging.debug(key)
            # logging.debug(len(value))
            for item in value:
                logging.debug(f"singers is: " + item.get("singers") + f", album is: " + item.get("album") + f", songname is: " + item.get("songname") + f", download_url is: " + item.get("download_url"))
                if not artist or artist == item.get("singers"):
                    mp3_urls.append(item.get("download_url"))
            # client.download(value)

    return mp3_urls

def xiaoai_server(event):
    req = xiaoai_request(event)
    if req.request.type == 0 or req.request.type == 1:
        if req.request.slot_info.intent_name == 'Tao_Search':
            slotsList = req.request.slot_info.slots
            musicName = [item for item in slotsList if item['name'] == 'music'][0]['value']
            artistName = [item for item in slotsList if item['name'] == 'artist'][0]['value']
            logging.debug(f"Tao_Search musicName is: " + musicName + f", artistName is: " + artistName)
            music_url = get_search_music(musicName, artistName, config)
            if len(music_url) > 0:
                return build_music_message('马上播放', music_url)
            else:
                return build_text_message('未找到相关歌手的歌曲', is_session_end=False, open_mic=True, not_understand=True)
        elif req.request.slot_info.intent_name == 'Tao_Want':
            slotsList = req.request.slot_info.slots
            musicName = [item for item in slotsList if item['name'] == 'music'][0]['value']
            logging.debug(f"Tao_Want musicName is: " + musicName)
            music_url = get_search_music(musicName, '', config)
            if len(music_url) > 0:
                return build_music_message('马上播放', music_url)
            else:
                return build_text_message('未找到相关歌曲', is_session_end=False, open_mic=True, not_understand=True)
        elif req.request.slot_info.intent_name == 'Mi_Exit':
            return build_text_message('再见了您！', is_session_end=True, open_mic=False, not_understand=False)
        else:
            return build_text_message('请问您想听什么歌曲呢', is_session_end=False, open_mic=True, not_understand=False)
    elif req.request.type == 2:
        return build_text_message('再见了您！', is_session_end=True, open_mic=False, not_understand=False)
    else:
        return build_text_message('我没听懂哎', is_session_end=True, open_mic=False, not_understand=True)

# 加载配置文件
def load_config():
    config_path = os.environ.get("CONFIG_PATH", "./config.yaml")
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

config = load_config()
app = Flask(__name__)
logging.basicConfig(filename=config['xiaoai']['log-path'], level=config['xiaoai']['log-level'])

@app.route('/xiaoai', methods=['POST'])
def index():

    # 签名认证
    check_sign(request)

    if not request.json:
        abort(400)
    logging.debug('Input = ' + str(request.json))
    response = xiaoai_server(request.json)
    logging.debug('Response = ' + str(response))
    return response

if __name__ == '__main__':
    app.run(host=config['xiaoai']['server'], port=config['xiaoai']['port'], debug=config['xiaoai']['debug'])