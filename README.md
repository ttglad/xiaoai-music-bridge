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

## 配置文件
修改 config.yaml
```
xiaoai:
  server: 0.0.0.0
  port: 15333
  debug: True
  # NOTSET = 0,DEBUG = 10,INFO = 20,WARNING = 30,ERROR = 40,CRITICAL = 50
  log-level: 20
  log-path: ./app.log
  # 小米后台key_id
  key-id: 
  # 小米后台secret
  secret-key: 
  scope: ""
  sign-version: MIAI-HmacSHA256-V1
plex:
  enable: False
  # plex服务地址
  server-url: 
  # plex服务token
  token: 
musicdl:
  log-path: musicdl.log
  save-dir: ./
  search-size: 1
  proxies: {}
  sources:
    - kugou
    #- kuwo
    #- qianqian
    - fivesing
    #- qqmusic
    #- netease
    - migu
    #- joox
    #- yiting
```

## 致谢

本项目受以下项目启发或者有使用一下项目，向这些开发者表示感谢。

- <https://github.com/CharlesPikachu/musicdl>
- <https://github.com/ihainan/NetEaseCloudMusic-XiaoAi>