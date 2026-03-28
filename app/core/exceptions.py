class AppException(Exception):
    status_code = 500
    error_code = "app_error"

    def __init__(self, message=None, payload=None, headers=None):
        self.message = message or "Application error"
        self.payload = payload
        self.headers = headers
        super().__init__(self.message)


class AccessError(AppException):
    status_code = 403
    error_code = "access_error"


class ConflictError(AppException):
    status_code = 409
    error_code = "conflict_error"


class NotFoundError(AppException):
    status_code = 404
    error_code = "not_found_error"


class AuthenticationError(AppException):
    status_code = 401
    error_code = "auth_error"
    headers = {"www-authenticate": "Bearer"}


class UnprocessableEntityError(AppException):
    status_code = 422
    error_code = "unproc_entity_error"


class ForbiddenError(AppException):
    status_code = 403
    error_code = "forbidden_error"


class BadRequest(AppException):
    status_code = 400
    error_code = "bad_request"
