from decouple import config
from webdav3.client import Client

NEXTCLOUD_URL = config('NEXTCLOUD_URL')
USERNAME = config('USERNAME')
PASSWORD = config('PASSWORD')

options = {
    'webdav_hostname': NEXTCLOUD_URL,
    'webdav_login':    USERNAME,
    'webdav_password': PASSWORD
}

client = Client(options)

