import datetime
from .settings import RESOURCE, META


def find_path(arr, path, is_end=False):
    for obj in arr:
        if obj['label'] == path:
            if is_end:
                return obj['value']
            else:
                if 'children' not in obj:
                    obj['children'] = []
                return obj['children']
    return False


def update_cascade():
    cascade = {'data': []}

    for r in RESOURCE.find():
        path = r['parent']
        paths = path.split('/')

        path_data = cascade['data']
        for idx, path in enumerate(paths):
            if idx == len(paths) - 1:
                if not find_path(path_data, path):
                    path_data.append({
                        'value': [],
                        'label': path,
                    })
                path_data = find_path(path_data, path, is_end=True)
                break
            elif not find_path(path_data, path):
                path_data.append({
                    'value': [],
                    'label': path,
                    'children': []
                })
            path_data = find_path(path_data, path)

        path_data.append(r['_id'])

    META.update_one(
        {'_id': 'cascade'},
        {
            '$set': {
                '_id': 'cascade',
                'data': cascade['data'],
                'date': datetime.datetime.utcnow(),
            }
        },
        True
    )


if __name__ == '__main__':
    update_cascade()
