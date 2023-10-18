本项目是一个基于Python3的服务，部署在服务端之后，可以实现小米小爱开放平台回调服务。

## 功能

- 支持小爱同学技能服务
- 支持三方音乐源查询

> 注意：仅支持Python3，建议使用 **Python3.7 以上版本**

## 运行
```bash
$ git clone https://github.com/ttglad/xiaoai-music-bridge.git
$ cd xiaoai-music-bridge
$ pip3 install -r requirements.txt
$ python app.py
```

## 开启本地plex
修改 app.py
```
LOCAL_MUSIC = True
...

if LOCAL_MUSIC == True:
    # 查询本地nas音乐源 本地音乐源 PLEX
    plex_server_url = 'https://plex_server_url'
    plex_token = 'plex_token'
    mp3_urls = search_bub_music(plex_server_url, plex_token, key)
```

## 开启三方音乐源
修改 app.py
```
target_srcs = ['kugou', 'kuwo', 'qqmusic', 'qianqian', 'fivesing', 'netease', 'migu', 'joox', 'yiting',]
```

## 致谢

本项目受以下项目启发或者有使用一下项目，向这些开发者表示感谢。

- <https://github.com/CharlesPikachu/musicdl>
- <https://github.com/ihainan/NetEaseCloudMusic-XiaoAi>