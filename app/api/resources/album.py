import requests

def find_album_by_id(id):
    url = f'https://jsonplaceholder.typicode.com/albums/{id}'
    response = requests.get(url)
    return response
    
