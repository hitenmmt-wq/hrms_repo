import logging
import time

logger = logging.getLogger(__name__)


class RequestTimingMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        end_time = time.time()
        duration = (end_time - start_time) * 1000

        response["X-Request-Duration-ms"] = f"{duration:.2f}"

        logger.info(f"[{request.method}] {request.path} completed in {duration:.2f} ms")

        return response
