import logging
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache

logger = logging.getLogger(__name__)


class RateLimitMiddleware(MiddlewareMixin):
    def _get_client_ip(self, request):
        """
        Retrieve client IP address from request headers.
        
        returns: str - Client IP address
        
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def process_request(self, request):
        """
        Middleware to limit the number of requests from a single IP address.
        It uses Django's caching framework to track request counts and enforce limits.
        
        returns: JsonResponse with 429 status if rate limit exceeded, else None
        """
        try:
            ip = self._get_client_ip(request)
            key = f'rate-limit-{ip}'

            limit = settings.RATE_LIMIT
            window = settings.RATE_LIMIT_TIME_PERIOD

            request_count = cache.get(key)

            if request_count is None:
                # initialize or increment request count
                cache.set(key, 1, timeout=window)
                request_count = 1
            else:
                # increment
                request_count = cache.incr(key)

            logger.info(f"IP: {ip}, Request count: {request_count}")

            remaining = max(limit - request_count, 0)
            ttl = cache.ttl(key)  # how many seconds until reset

            # check if request count exceeds limit
            if request_count > limit:
                logger.warning(f"Rate limit exceeded for IP: {ip}")
                response = JsonResponse(
                    {
                        'success': False,
                        'message': 'Rate limit exceeded. Try again later.'
                    },
                    status=429
                )
                response["X-RateLimit-Limit"] = str(limit)
                response["X-RateLimit-Remaining"] = "0"
                if ttl > 0:
                    response["Retry-After"] = str(ttl)
                return response

            # Attach headers for allowed requests
            request.rate_limit_info = {
                "limit": limit,
                "remaining": remaining,
                "retry_after": ttl,
            }

        except Exception as e:
            logger.exception("Error in RateLimitMiddleware")

    def process_response(self, request, response):
        """
        Add rate limit headers to the response.
        returns: HttpResponse with rate limit headers
        """
        info = getattr(request, "rate_limit_info", None)
        if info:
            response["X-RateLimit-Limit"] = str(info["limit"])
            response["X-RateLimit-Remaining"] = str(info["remaining"])
            if info["retry_after"] > 0:
                response["Retry-After"] = str(info["retry_after"])
        return response
