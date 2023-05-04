import requests
from datetime import datetime
import json
from progress.bar import Bar


class VK:
    url = 'https://api.vk.com/method/'

    def __init__(self, token, version='5.131'):
        self.params = {
            'access_token': token,
            'v': version
        }

    def get_photo_urls(self, album='profile', user_id=None, count=5):
        get_photo_url = self.url + 'photos.get'
        get_photo_params = {
            'album_id': album,
            'extended': 1,
            'owner_id': user_id,
            'count': count
        }
        response = requests.get(get_photo_url, params={**self.params, **get_photo_params}).json()
        photos_params = []
        dict_likes_count = {}
        for i in response['response']['items']:
            if i['likes']['count'] not in dict_likes_count:
                dict_likes_count[i['likes']['count']] = 1
            else:
                dict_likes_count[i['likes']['count']] += 1
        for item_ph in response['response']['items']:
            max_sized = max(item_ph['sizes'], key=(lambda x: x['height']))
            if dict_likes_count[item_ph['likes']['count']] == 1:
                name = str(item_ph['likes']['count']) + '.jpg'
            else:
                name = f"{item_ph['likes']['count']}" \
                       f"({datetime.utcfromtimestamp(item_ph['date']).strftime('%d%m%Y-%H%M%S')}).jpg"
            photos_params.append({'name': name, 'size': max_sized['type'], 'url': max_sized['url']})
        return photos_params


class YaUploader:
    host = 'https://cloud-api.yandex.net:443/'

    def __init__(self, token: str):
        self.token = token

    def get_headers(self):
        return {'Content-Type': 'application/json', 'Authorization': f'OAuth {self.token}'}

    def create_folder(self, folder_name):
        """Create folder on Yandex Disc"""
        uri = 'v1/disk/resources/'
        url = self.host + uri
        params = {'path': f'/{folder_name}'}
        requests.put(url, headers=self.get_headers(), params=params)

    def upload_from_url(self, file_url, file_name, folder_name):
        """Upload file_url as file_name to folder_name"""
        uri = 'v1/disk/resources/upload/'
        url = self.host + uri
        params = {'path': f'/{folder_name}/{file_name}', 'url': file_url}
        response = requests.post(url, headers=self.get_headers(), params=params)
        if response.status_code == 202:
            print(f" Загрузка файла '{file_name}' прошла успешно")



if __name__ == '__main__':
    with open('tokenvk.txt', 'r') as file:
        access_token = file.read().strip()
    reader = VK(access_token)
    album_id = input("Укажите album_id (по умолчанию 'profile'): ") or 'profile'
    photo_amount = 5
    while True:
        try:
            photo_amount = int(input("Укажите количество загружаемых фотографий (по умолчанию 5): ") or 5)
            if photo_amount < 1:
                print("Введите положительное число")
                continue
            break
        except ValueError:
            print("Введите положительное число")
            continue
    photos_info = reader.get_photo_urls(album_id, count=photo_amount)
    with Bar('Request photos from VK...', max=len(photos_info)) as bar:
        result = []
        for item in photos_info:
            result.append({'file-name': item['name'], 'size': item['size']})
            bar.next()
    with open("result.json", "w") as file:
        json.dump(result, file)

    dir_name = input("Укажите название папки для загрузки (по умолчанию 'FromVK'): ") or 'FromVK'
    with open('yandextoken.txt', 'r') as file:
        yandex_token = file.read().strip()
    loader = YaUploader(yandex_token)
    loader.create_folder(dir_name)
    with Bar('Loading to Yandex.Disk...', max=len(photos_info)) as bar:
        for photo in photos_info:
            bar.next()
            loader.upload_from_url(photo['url'], photo['name'], dir_name)