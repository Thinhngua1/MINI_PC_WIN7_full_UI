import requests

class ApiPublisherModel:
    def __init__(self, endpoint):
        self.endpoint = endpoint

    def post_data_async(self, parsed_data: dict):
        """
        TODO: Chạy thread ẩn, gửi HTTP POST chứa parsed_data lên SQL Server
        """
        pass
