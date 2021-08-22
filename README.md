**注意**: 本ソフトウェアはまだ少ないサンプルでしか検証していない為、不具合が多発する可能性があります

# video2ss

Fate Grand Orderのフレンドポイント召喚動画から召喚結果のスクリーンショットを抽出する

以下の手順で使用することを想定しています

1. スマホでフレンドポイント召喚動画撮影
2. PCに転送
3. video2ssによる召喚結果スクショ抽出
4. [fgogachacnt](https://github.com/fgosc/fgogachacnt)によるスクショ画像認識


## 必要なソフトウェア
- Python 3.7以降

## 依存ライブラリのインストール

```
$ pip install -r requirements.txt
```

## 使い方

```
$ python video2ss.py -h
usage: video2ss.py [-h] [-o OUTPUT] [-ss SS] [-to TO]
                   [--loglevel {warning,debug,info}]
                   file_name

Get summon screenshots from video

positional arguments:
  file_name             video file

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output folder
  -ss SS                Start
  -to TO                End
  --loglevel {warning,debug,info}
```

スクリーンショットが抽出されたフォルダ(デフォルト: video_screenshot)が作成されるので、そのフォルダを[fgogachacnt](https://github.com/fgosc/fgogachacnt)で処理してください

強制的に10連と認識させるオプション -m 10 の使用を推奨します(フレンドポイント召喚の場合)

### 具体例
```
$ python video2ss.py example.mp4
$ python fgogachacnt.py -f video_screenshot -m 10 > example.csv
$ python csv2report.py example.csv
```

## Tips

### 動画撮影時のポイント

1. 通知はオフにすること
2. カード上にタップ跡をつけないように注意すること「続けて10回召喚」ボタンや確認ダイアログのボタンをむやみに連打していると起こります

下記のようにタップ跡がついたカードは誤認識します

![image](https://user-images.githubusercontent.com/62515228/130352979-3680089b-8dd1-42fc-8b5f-3334ec9befe5.png)

### Youtubeのフレンドポイント召喚動画の処理

[youtube-dl](https://ytdl-org.github.io/youtube-dl/index.html) を使用することで動画をローカルにダウンロードすることができ、本プログラムで処理することが可能です

例:

```
youtube-dl.exe https://www.youtube.com/watch?v=7ecPT7PiNIU -f "bestvideo[ext=mp4][height<=1080]/best[ext=mp4][height<=1080]"
```

## 謝辞

本ソフトウェアは [capy-vod-parser](https://github.com/atlasacademy/capy-vod-parser) を参考に作成しました
