# import unittest
# from unittest.mock import MagicMock, patch

# from api.resources.album import find_album_by_id


# class TestAlbum(unittest.TestCase):

#     @patch('api.resources.album.requests')
#     def test_find_album_by_id_success(self, mock_requests):
#         # mock the response
#         mock_response = MagicMock()

#         mock_response.status_code = 400
#         mock_response.json.return_value = {
#             'userId': 1,
#             'id': 1,
#             'title': 'hello',
#         }

#         # specify the return value of the get() method
#         mock_requests.get.return_value = mock_response
#         res = find_album_by_id(1)
#         print(res)

#         # call the find_album_by_id and test if the title is 'hello'
#         # self.assertEqual(find_album_by_id(1), 'hello')
#         self.assertEqual(res.status_code, 200)