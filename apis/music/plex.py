import logging

import requests

headers = {
    'Accept' : 'application/json, text/plain, */*'
}

# 查询音乐库
def search_music(plex_server_url, plex_token, query):
    search_url = f'{plex_server_url}/search?type=10&query={query}&X-Plex-Token={plex_token}&limit=30&includeCollections=1&includeExternalMedia=1&X-Plex-Language=zh'
    response = requests.get(search_url,headers=headers)

    if response.status_code == 200:
        music_url = []
        music_data = response.json()
        logging.debug(f"search_music music response: {music_data}")
        # 这里你可以处理返回的音乐数据
        for track in music_data['MediaContainer']['Metadata']:
            for media in track['Media']:
                for part in media['Part']:
                    music_url.append(get_music_media(plex_server_url, plex_token, part['key']))
        return music_url
    else:
        logging.debug(f"Failed to query music: {response.status_code} - {response.text}")
        return None

def search_bub_music(plex_server_url, plex_token, query):
    search_url = f'{plex_server_url}/hubs/search?query={query}&X-Plex-Token={plex_token}&limit=10&includeCollections=1&includeExternalMedia=1&X-Plex-Language=zh'
    response = requests.get(search_url,headers=headers)

    music_url = []
    try:
        if response.status_code == 200:
            music_data = response.json()
            logging.debug(f"search_bub_music music response: {music_data}")
            # 这里你可以处理返回的音乐数据
            for track in music_data['MediaContainer']['Hub']:
                # logging.debug(track)
                if track['type'] != 'track':
                    continue
                logging.debug(f"track is: " + track)
                for part in track['Metadata']:
                    for mediaItem in part['Media']:
                        for partItem in mediaItem['Part']:
                            music_url.append(get_music_media(plex_server_url, plex_token, partItem['key']))
            return music_url
        else:
            logging.debug(f"Failed to query music: {response.status_code} - {response.text}")
            return music_url
    except:
        return music_url

# 获取音乐播放地址
def get_music_url(plex_server_url, plex_token, media_id):
    media_url = f'{plex_server_url}/library/metadata/{media_id}/media/1/part/0/file?X-Plex-Token={plex_token}'
    response = requests.get(media_url, headers=headers)

    if response.status_code == 200:
        music_url = response.text
        return music_url
    else:
        logging.debug(f"Failed to get music URL: {response.status_code} - {response.text}")
        return None

def get_music_media(plex_server_url, plex_token, key):
    return f'{plex_server_url}{key}?X-Plex-Token={plex_token}&X-Plex-Language=zh&Accept-Language=zh'
