import logging
import time

from django.http import JsonResponse

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


class BlockMobileMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_agent = request.META.get("HTTP_USER_AGENT", "").lower()
        sec_ch_ua_mobile = request.META.get("HTTP_SEC_CH_UA_MOBILE", "")
        sec_ch_ua_platform = request.META.get("HTTP_SEC_CH_UA_PLATFORM", "").lower()
        accept_header = request.META.get("HTTP_ACCEPT", "").lower()
        viewport_width = request.META.get("HTTP_SEC_CH_VIEWPORT_WIDTH", "")

        # Mobile-specific patterns
        mobile_patterns = [
            "mobile",
            "android",
            "iphone",
            "ipad",
            "ipod",
            "blackberry",
            "windows phone",
            "webos",
            "opera mini",
            "opera mobi",
            "iemobile",
            "kindle",
            "silk",
            "fennec",
        ]

        # Check if it's a mobile device
        is_mobile = (
            any(pattern in user_agent for pattern in mobile_patterns)
            or sec_ch_ua_mobile == "?1"
            or "android" in sec_ch_ua_platform
            or "ios" in sec_ch_ua_platform
            or "wap" in accept_header
            or (
                viewport_width
                and viewport_width.isdigit()
                and int(viewport_width) < 768
            )
        )

        if is_mobile:
            return JsonResponse(
                {
                    "error": "Access from mobile devices is not allowed. Please use a desktop or laptop computer."
                },
                status=403,
            )

        return self.get_response(request)
