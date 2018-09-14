import os
import glob
from imohash import hashfile
import time
from .settings import RESOURCE, VIDEO_TYPES, FILTER_STRINGS, IMAGE_TYPES, FILTER_SIZE, FILTER_SIZE_VIDEO, FILTER_SIZE_IMAGE, FILTER_DURATION
import re
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..utility import to_time_string
from opencc import OpenCC
from PIL import Image


def filter_file(file, is_video=True):
    for filter_string in FILTER_STRINGS:
        if filter_string in file:
            return None
    size_threshold = FILTER_SIZE_VIDEO if is_video else FILTER_SIZE_IMAGE
    size = os.stat(file).st_size
    if size < size_threshold * 1024 * 1024:
        return None
    return size


def detect_image_sequence(path):
    obj_list = []
    for image_type in IMAGE_TYPES:
        glob_path = glob.escape(path)
        images = glob.glob(glob_path + '/*.' + image_type)
        if len(images) == 0:
            continue

        feature_map = {}
        for image in images:
            image = image.lower()
            size = filter_file(image, False)
            if size is None:
                continue

            image = image.replace('\\', '/')
            path, filename = os.path.split(image)
            name, ext = os.path.splitext(filename)
            ext = ext.strip('.')

            if not len(name) > 1:
                continue
            if not name[-2:].isdigit():
                continue
            splits = re.findall(r'(.*?)([0-9]+$)', name)
            if len(splits) != 1 and len(splits[0]) != 2:
                continue

            key, num = splits[0]

            if key not in feature_map:
                im = Image.open(image)
                width, height = im.size
                feature_map[key] = {
                    'numbers': [int(num)],
                    'pad': len(num),
                    'width': width,
                    'height': height,
                    'raw': image,
                    'size': size,
                }
            else:
                parent = feature_map[key]
                if len(num) != parent['pad'] or int(num) != parent['numbers'][-1] + 1:
                    continue
                parent['numbers'].append(int(num))
                parent['size'] += size

        for key, value in feature_map.items():
            numbers = sorted(value['numbers'])
            if len(numbers) < 10:
                continue
            obj_list.append({
                'raw': value['raw'],
                'width': value['width'],
                'height': value['height'],
                'pad': value['pad'],
                'startFrame': numbers[0],
                'endFrame': numbers[-1],
                'name': key,
                'type': image_type,
                'duration': len(numbers) / 30.0,
                'size': value['size'],
            })

    return obj_list


def detect_video(path):
    obj_list = []
    files = []
    glob_path = glob.escape(path)
    for video_type in VIDEO_TYPES:
        files.extend(glob.glob(glob_path + '/*.' + video_type))

    for file in files:
        file = file.lower()
        size = filter_file(file)
        if size is None:
            continue

        file = file.replace('\\', '/')
        obj_list.append({
            'raw': file,
            'size': size
        })

    return obj_list


def parse_obj(progress, obj):
    if progress.cancel:
        progress.sig_log.emit('取消中...')
        return None

    progress.sig_log.emit(obj['raw'])

    path, filename = os.path.split(obj['raw'])
    name, ext = os.path.splitext(filename)
    ext = ext.strip('.')
    key = hashfile(obj['raw'], hexdigest=True)
    is_collide = True if RESOURCE.find_one({'_id': key}) else False
    obj = {
        'collide': is_collide,
        'name': name,
        'type': ext,
        '_id': key,
        'raw': obj['raw'],
        **obj
    }

    if is_collide:
        return obj
    else:
        cc = OpenCC('s2twp')
        tag = '{}/{}'.format(obj['parent'], obj['name'])
        tag = re.findall(u'[\u4e00-\u9fff]+|[a-zA-Z0-9]+', tag)
        tag = list(set(tag))
        tag = [cc.convert(t) for t in tag if t != '']
        obj['tag'] = sorted(tag)

        if obj['type'] in VIDEO_TYPES:
            cmd_meta = subprocess.check_output(
                [
                    'ffprobe',
                    '-v', 'quiet',
                    '-print_format', 'json',
                    '-show_format',
                    '-show_entries',
                    'stream=r_frame_rate,width,height',
                    obj['raw']
                ]
            )

            meta = json.loads(cmd_meta.decode('utf-8'))

            obj.update({
                'duration': float(meta['format']['duration']),
                'fps': int(round(eval(meta['streams'][0]['r_frame_rate']))),
                'width': meta['streams'][0]['width'],
                'height': meta['streams'][0]['height'],
            })

    if min(obj['width'], obj['height']) < FILTER_SIZE:
        return None
    elif obj['duration'] < FILTER_DURATION[0] or obj['duration'] > FILTER_DURATION[1]:
        return None
    else:
        return obj


def parse_folder(path, folder):
    root_path = '/'.replace('\\', '/').join(path.split('/')[:-1])
    parent = folder.replace('\\', '/').replace(root_path, '').strip('/')

    obj_list = []
    obj_list.extend(detect_video(folder))
    obj_list.extend(detect_image_sequence(folder))

    obj_list = [{**obj, 'parent': parent.lower()} for obj in obj_list]

    return obj_list


def parse_path(progress, path):
    start_time = time.clock()
    thread_count = min(int(round(os.cpu_count() / 2.0)), 5)
    progress.sig_log.emit('掃描文件...')

    folders = []
    folders = [x[0] for x in os.walk(path)]
    progress.sig_max.emit(len(folders))

    obj_list = []
    progress.sig_log.emit('整理文件列表...')
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        parse_jobs = {executor.submit(parse_folder, path, folder): folder for folder in folders}
        for job in as_completed(parse_jobs):
            obj_list.extend(job.result())
            progress.sig_inc.emit()

    progress.sig_max.emit(len(obj_list))
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        parse_jobs = {executor.submit(parse_obj, progress, obj): obj for obj in obj_list}

        process_count = 0
        for job in as_completed(parse_jobs):
            obj = job.result()
            if obj is not None:
                progress.sig_add_item.emit(obj)
                process_count += 1
            progress.sig_inc.emit()

    progress.sig_log.emit(
        '已解析 {} 個素材 ({})'.format(
            process_count,
            to_time_string(time.clock() - start_time, '時', '分', '秒')
        )
    )
