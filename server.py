from flask import Flask, escape, request, render_template, jsonify
import file_util
from flask_apscheduler import APScheduler
from apscheduler.schedulers.background import BackgroundScheduler
import json
import requests
from pathlib import Path
import threading
import bilibili_util
app = Flask("bilibili_auto_download")

dir_download = Path('download')
file_downloaded_video = dir_download / 'downloaded_video.txt'

downloading = False


def get_list_video():
    if file_downloaded_video.exists():
        downloaded_video_list = file_util.read_all_lines(file_downloaded_video)
    else:
        downloaded_video_list = []

    downloading_video = []
    for page_num in range(1000):
        one_page_list_video = bilibili_util.get_one_page_list_video(page_num)
        if len(one_page_list_video) == 0:
            break
        for v in one_page_list_video:
            if v not in downloaded_video_list:
                downloading_video.append(v)
    return downloading_video


def download_video(list_video):
    global downloading
    if downloading:
        print('end download_video because downloading')
        return
    else:
        downloading = True

    try:
        for v in list_video:
            print(v)
            bilibili_util.download(v[0], dir_download / v[1])
            file_util.append_all_text(file_downloaded_video, v[1]+'\n')
    finally:
        downloading = False


def init():
    file_util.create_dir_if_not_exist(dir_download)
    app.config.from_object(APSchedulerJobConfig)

    # 初始化Flask-APScheduler，定时任务
    scheduler = APScheduler(BackgroundScheduler(timezone="Asia/Shanghai"))
    scheduler.init_app(app)
    scheduler.start()


@app.route('/', methods=['get', 'post'])
def index():
    print('index')
    return 'hello i am bilibili_auto_download you cloud visit /download'


@app.route('/download', methods=['get', 'post'])
def download():
    print('def download')
    list_video = get_list_video()
    print(f'download num {len(list_video)}')
    t = threading.Thread(target=download_video, args=(list_video,))
    t.start()

    return str(list_video)


class APSchedulerJobConfig(object):
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = 'Asia/Shanghai'
    JOBS = [
        {
            'id': 'download',
            'func': download,
            'args': '',
            'trigger': {
                'type': 'cron',
                'minute': '*/10'  # 10 分钟检查一次
            }
        }
    ]


def main():
    init()
    app.run(host='0.0.0.0', port='80')


if __name__ == "__main__":
    main()
