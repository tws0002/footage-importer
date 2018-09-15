from pymongo import MongoClient


client = MongoClient()
db = client.footage


# GLOBAL
RESOURCE = db.resource
META = db.metadata
FOOTAGE_PATH = 'R:/footage/resource/'

FILTER_STRINGS = ('preview', 'tutorial', 'thumbnail')
FILTER_SIZE = 400
FILTER_SIZE_VIDEO = 0.5
FILTER_SIZE_IMAGE = 0.05
FILTER_DURATION = (0.1, 600)

VIDEO_TYPES = ('mp4', 'mov', 'avi')
IMAGE_TYPES = ('jpg', 'png', 'exr', 'tga')
