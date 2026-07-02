import json

from starlette.responses import PlainTextResponse
from starlette.status import (
    HTTP_404_NOT_FOUND,
    HTTP_406_NOT_ACCEPTABLE,
    HTTP_400_BAD_REQUEST,
    HTTP_500_INTERNAL_SERVER_ERROR,
)


def response_error_handler(result):
    if result["status"] == 500:
        return http_500_internal_server_error(
            result.get("details", "Internal Server Error")
        )
    if result["status"] == 406:
        return http_406_not_acceptable(result.get("details", "Not Acceptable"))
    if result["status"] == 400:
        return http_400_bad_request(result.get("details", "Bad Request"))
    if result["status"] == 404:
        return http_404_not_found(result.get("details", "Not Found"))
    else:
        return http_unknown_error(result)


def http_unknown_error(result):
    response_msg = json.dumps(
        {"status_code": result["status"], "details": result.get("details", "Unknown")}
    )
    return PlainTextResponse(response_msg, status_code=result["status"])


def http_400_bad_request(details="Bad Request"):
    response_msg = json.dumps(
        {"status_code": HTTP_400_BAD_REQUEST, "details": details}
    )
    return PlainTextResponse(response_msg, status_code=HTTP_400_BAD_REQUEST)


def http_404_not_found(details="Not Found"):
    response_msg = json.dumps(
        {"status_code": HTTP_404_NOT_FOUND, "details": details}
    )
    return PlainTextResponse(response_msg, status_code=HTTP_404_NOT_FOUND)


def http_406_not_acceptable(details="Not Acceptable"):
    response_msg = json.dumps(
        {"status_code": HTTP_406_NOT_ACCEPTABLE, "details": details}
    )
    return PlainTextResponse(response_msg, status_code=HTTP_406_NOT_ACCEPTABLE)


def http_500_internal_server_error(details="Internal Server Error"):
    response_msg = json.dumps(
        {
            "status_code": HTTP_500_INTERNAL_SERVER_ERROR,
            "details": details,
        }
    )
    return PlainTextResponse(response_msg, status_code=HTTP_500_INTERNAL_SERVER_ERROR)
