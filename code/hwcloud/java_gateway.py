__author__ = 'Administrator'
from py4j.java_gateway import JavaGateway, GatewayParameters


class HWSRestMethod(object):
    gateway = JavaGateway(gateway_parameters=GatewayParameters(port=25535))
    rest_method_java = gateway.entry_point

    @staticmethod
    def get(ak, sk, request_url, service_name, region):
        return HWSRestMethod.rest_method_java.get(ak, sk, request_url, service_name, region)

    @staticmethod
    def put(ak, sk, request_url, body, service_name, region):
        return HWSRestMethod.rest_method_java.put(ak, sk, request_url, body, service_name, region)

    @staticmethod
    def post(ak, sk, request_url, body, service_name, region):
        return HWSRestMethod.rest_method_java.post(ak, sk, request_url, body, service_name, region)

    @staticmethod
    def patch(ak, sk, request_url, body, service_name, region):
        return HWSRestMethod.rest_method_java.patch(ak, sk, request_url, body, service_name, region)

    @staticmethod
    def delete(ak, sk, requestUrl, service_name, region):
        return HWSRestMethod.rest_method_java.delete(ak, sk, requestUrl, service_name, region)


