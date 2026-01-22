import js
import json
import os


class Operaton:
    @staticmethod
    def get(path, raw=False):
        url = os.environ["OPERATON_ENGINE_API"].rstrip("/") + "/"+ path.lstrip("/")
        request = js.XMLHttpRequest.new()
        request.open("GET", url, False)
        request.send(None)
        assert request.status in [200], request.responseText
        return request.responseText if raw else json.loads(request.responseText or 'null')

    @staticmethod
    def post(path, data):
        url = os.environ["OPERATON_ENGINE_API"].rstrip("/") + "/"+ path.lstrip("/")
        request = js.XMLHttpRequest.new()
        request.open("POST", url, False)
        request.setRequestHeader("Content-Type", "application/json")
        request.setRequestHeader("X-XSRF-TOKEN", os.environ["OPERATON_CSRF_TOKEN"])
        request.send(json.dumps(data))
        assert request.status in [200, 204], request.responseText
        return json.loads(request.responseText or 'null')
        
    @staticmethod
    def put(path, data):
        url = os.environ["OPERATON_ENGINE_API"].rstrip("/") + "/"+ path.lstrip("/")
        request = js.XMLHttpRequest.new()
        request.open("PUT", url, False)
        request.setRequestHeader("Content-Type", "application/json")
        request.setRequestHeader("X-XSRF-TOKEN", os.environ["OPERATON_CSRF_TOKEN"])
        request.send(json.dumps(data))
        assert request.status in [200, 204], request.responseText
        return json.loads(request.responseText or 'null')

    @staticmethod
    def delete(path):
        url = os.environ["OPERATON_ENGINE_API"].rstrip("/") + "/"+ path.lstrip("/")
        request = js.XMLHttpRequest.new()
        request.setRequestHeader("X-XSRF-TOKEN", os.environ["OPERATON_CSRF_TOKEN"])
        request.open("DELETE", url, False)
        request.send(None)
        assert request.status in [204], request.responseText
        return request.responseText if raw else json.loads(request.responseText or 'null')