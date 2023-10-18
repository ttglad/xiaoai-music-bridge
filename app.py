#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import logging

from flask import Flask, abort, request

from apis.xiaoai.xiaoai import (XiaoAIAudioItem, XiaoAIDirective, XiaoAIOpenResponse,
                                XiaoAIResponse, XiaoAIStream, XiaoAIToSpeak, XiaoAITTSItem,
                                xiaoai_request, xiaoai_response)

from musicdl import musicdl
from apis.music.plex import search_bub_music

# 是否启用本地 PLEX 音乐
LOCAL_MUSIC = False

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
def get_search_music(key):
    mp3_urls = []

    if LOCAL_MUSIC == True:
        # 查询本地nas音乐源 本地音乐源 PLEX
        plex_server_url = 'https://plex_server_url'
        plex_token = 'plex_token'
        mp3_urls = search_bub_music(plex_server_url, plex_token, key)

    # 查询三方源api
    if len(mp3_urls) <= 0:
        config = {'logfilepath': 'musicdl.log', 'savedir': './', 'search_size_per_source': 1, 'proxies': {}}
        # target_srcs = [
        #     'kugou', 'kuwo', 'qqmusic', 'qianqian', 'fivesing', 'netease', 'migu', 'joox', 'yiting',
        # ]
        target_srcs = [
             'kugou', 'qianqian', 'fivesing'
        ]
        client = musicdl.musicdl(config=config)
        search_results = client.search(key, target_srcs)
        logging.debug(search_results)

        for key, value in search_results.items():
            logging.debug(key)
            logging.debug(len(value))
            for item in value:
                logging.debug(item.get("singers"))
                logging.debug(item.get("album"))
                logging.debug(item.get("songname"))
                logging.debug(item.get("download_url"))
                mp3_urls.append(item.get("download_url"))
            # client.download(value)

    return mp3_urls

def xiaoai_server(event):
    req = xiaoai_request(event)
    if req.request.type == 0 or req.request.type == 1:
        if req.request.slot_info.intent_name == 'Tao_Search':
            slotsList = req.request.slot_info.slots
            musicName = [item for item in slotsList if item['name'] == 'music'][0]['value'] + "" + [item for item in slotsList if item['name'] == 'artist'][0]['value']
            logging.debug(musicName)
            music_url = get_search_music(musicName)
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



app = Flask(__name__)
logging.basicConfig(filename='./app.log', level=logging.INFO)

@app.route('/xiaoai', methods=['POST'])
def index():
    # todo 签名认证
    if not request.json:
        abort(400)
    logging.debug('Input = ' + str(request.json))
    response = xiaoai_server(request.json)
    logging.debug('Response = ' + str(response))
    return response

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=15333, debug=False)