import time
import os
import subprocess
from shutil import copy
import datetime
from .settings import RESOURCE, FOOTAGE_PATH, VIDEO_TYPES
from concurrent.futures import ThreadPoolExecutor, as_completed
from .update_cascade import update_cascade
from ..utility import to_time_string


def import_obj(progress, item):
    obj = item.data

    if progress.cancel:
        progress.sig_log.emit('取消中...')
        return (False,)

    progress.sig_log.emit('預覽生成 > {}'.format(obj['raw']))
    progress.sig_item_change_state.emit(item, '轉檔中')

    resource_path = FOOTAGE_PATH + obj['_id']
    preview_path = resource_path + '/.preview/'
    for path in (resource_path, preview_path):
        if not os.path.isdir(path):
            os.mkdir(path)

    is_video = obj['type'] in VIDEO_TYPES
    if is_video:
        input_cmds = ['-i', obj['raw']]
    else:
        filename = os.path.split(obj['raw'])[0] + f'/{obj["name"]}%0{obj["pad"]}d.{obj["type"]}'
        input_cmds = ['-start_number', str(obj['startFrame']), '-i', filename]

    cmd_gif = subprocess.Popen([
        'ffmpeg',
        *input_cmds,
        '-f', 'lavfi',
        '-i', 'color=000000',
        '-filter_complex',
        '[0:v]fps=5,scale=320:-2[video];[1][video]scale2ref[bg][video];[bg]setsar=1[bg];[bg][video]overlay=shortest=1,split[a][b];[a]palettegen[p];[b][p]paletteuse',
        '-y',
        '-hide_banner', '-loglevel', 'error',
        preview_path + '{}.gif'.format(obj['_id'])
    ])

    cmd_mp4 = subprocess.Popen([
        'ffmpeg',
        *input_cmds,
        '-f', 'lavfi',
        '-i', 'color=000000',
        '-c:v', 'libx264',
        '-crf', '23',
        '-pix_fmt', 'yuv420p',
        '-filter_complex',
        '[0:v]scale=320:-2[video];[1][video]scale2ref[bg][video];[bg]setsar=1[bg];[bg][video]overlay=shortest=1',
        '-an', '-y',
        '-hide_banner', '-loglevel', 'error',
        preview_path + '{}.mp4'.format(obj['_id'])
    ])

    if is_video:
        copy(obj['raw'], resource_path)
    else:
        for i in range(obj['endFrame'] - obj['startFrame'] + 1):
            filename = '/{}{:0{width}}.{}'.format(
                obj['name'],
                obj['startFrame'] + i,
                obj['type'],
                width=obj['pad']
            )
            path = os.path.split(obj['raw'])[0] + filename
            copy(path, resource_path)

    for p in (cmd_gif, cmd_mp4):
        if p.wait() != 0:
            print('error on ffmpeg!')
            print(obj['raw'])
            exit()

    obj['date'] = datetime.datetime.utcnow()
    obj['preview'] = ['gif', 'mp4']

    RESOURCE.update_one({'_id': obj['_id']}, {'$set': obj}, upsert=True)

    return (True, item)


def import_resource(progress, item_list):
    time.clock()
    progress.sig_max.emit(len(item_list))
    progress.sig_log.emit('初始化匯入程序...')

    with ThreadPoolExecutor(max_workers=5) as executor:
        import_jobs = {executor.submit(import_obj, progress, item): item for item in item_list}

        process_count = 0
        for job in as_completed(import_jobs):
            result = job.result()
            if result[0]:
                progress.sig_item_change_state.emit(result[1], '完成')
                progress.sig_inc.emit()
                process_count += 1

    progress.sig_log.emit('整理素材資料庫架構...')
    update_cascade()

    progress.sig_log.emit(
        '已匯入 {} 個素材 ({})'.format(
            process_count,
            to_time_string(time.clock(), '時', '分', '秒')
        )
    )
    if progress.cancel:
        progress.sig_prompt.emit('素材匯入中止！')
    else:
        progress.sig_prompt.emit('素材匯入完成！')
