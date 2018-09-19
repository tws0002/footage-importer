import datetime
try:
    from .settings import RESOURCE, META
except ModuleNotFoundError:
    from settings import RESOURCE, META


def find_path(arr, path, is_end=False):
    for obj in arr:
        if obj['label'] == path:
            if is_end:
                return obj['value']
            else:
                if 'children' not in obj:
                    obj['children'] = []
                return obj['children']
    return None


def update_meta():
    cascade = []
    tag_cloud = {}

    for r in RESOURCE.find():
        # cascade
        path = r['parent']
        paths = path.split('/')

        path_data = cascade
        for idx, path in enumerate(paths):
            if idx == len(paths) - 1:
                if find_path(path_data, path) is None:
                    path_data.append({
                        'value': [],
                        'label': path,
                    })
                path_data = find_path(path_data, path, is_end=True)
                break
            elif find_path(path_data, path) is None:
                path_data.append({
                    'value': [],
                    'label': path,
                    'children': []
                })
            path_data = find_path(path_data, path)

        path_data.append(r['_id'])

        # tag_cloud
        tag = r['tag']
        for t in tag:
            if len(t) == 1 or t.isdigit():
                continue
            if t not in tag_cloud:
                tag_cloud[t] = 1
            else:
                tag_cloud[t] += 1

    META.update_one(
        {'_id': 'cascade'},
        {
            '$set': {
                '_id': 'cascade',
                'data': cascade,
                'date': datetime.datetime.utcnow(),
            }
        },
        True
    )

    META.update_one(
        {'_id': 'tagcloud'},
        {
            '$set': {
                '_id': 'tagcloud',
                'data': tag_cloud,
                'date': datetime.datetime.utcnow(),
            }
        },
        True
    )


if __name__ == '__main__':
    update_meta()
