import io
import logging
from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.conf import settings

# Configure logger for test module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
formatter = logging.Formatter("[%(levelname)s] %(name)s - %(message)s")
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)


class RateLimitMiddlewareTests(TestCase):
    def setUp(self):
        self.client = Client()
        cache.clear()
        logger.info("Cache cleared before test run")

    def get_valid_file(self):
        csv_content = "name,email,age\nTest,test@example.com,25\n"
        logger.debug(f"Generated CSV file for upload: {csv_content.strip().replace(chr(10), ' | ')}")
        return SimpleUploadedFile("test.csv", csv_content.encode("utf-8"), content_type="text/csv")

    @override_settings(
        RATE_LIMIT=3,
        RATE_LIMIT_TIME_PERIOD=60,
        CACHES={
            'default': {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': 'redis://127.0.0.1:6379/1',
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                }
            }
        }
    )
    def test_rate_limit_exceeded(self):
        url = '/v1/api/upload-file/'
        logger.info(f"Starting rate limit test with limit={settings.RATE_LIMIT} "
                    f"and window={settings.RATE_LIMIT_TIME_PERIOD} sec")

        for i in range(settings.RATE_LIMIT):
            data = {"csv_file": self.get_valid_file()}
            response = self.client.post(url, data, format='multipart')
            logger.debug(f"Request #{i + 1} --> Status {response.status_code} | "
                         f"Response: {response.content.decode().strip()}")
            self.assertNotEqual(response.status_code, 429)
            self.assertNotEqual(response.status_code, 400)

        # Next request should trigger rate limiting
        data = {"csv_file": self.get_valid_file()}
        response = self.client.post(url, data, format='multipart')
        logger.warning(f"Request #{settings.RATE_LIMIT + 1} --> Status {response.status_code} | "
                       f"Response: {response.content.decode().strip()}")

        self.assertEqual(response.status_code, 429)
        self.assertIn("Rate limit exceeded", response.content.decode())
