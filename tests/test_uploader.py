import io
import logging
import pandas as pd
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from models.models import User
from api.v1.serializers.uploader import FileUploadSerializer

# Configure a logger for tests
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Ensure logs show up in test console
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(levelname)s] %(name)s - %(message)s")
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)


class FileUploadSerializerTests(TestCase):
    def setUp(self):
        User.objects.create(name="Existing", email="existing@example.com", age=30)
        logger.info("Setup complete: Created existing user with email existing@example.com")

    def make_csv(self, data):
        df = pd.DataFrame(data)
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        csv_bytes = buf.getvalue().encode("utf-8")
        logger.debug(f"Generated CSV with {len(df)} rows: {df.to_dict(orient="records")}")
        return SimpleUploadedFile("test.csv", csv_bytes, content_type="text/csv")

    def test_valid_upload(self):
        logger.info("Running test_valid_upload...")
        data = [
            {"name": "Alice", "email": "alice@example.com", "age": 25},
            {"name": "Bob", "email": "bob@example.com", "age": 30},
        ]
        file = self.make_csv(data)
        serializer = FileUploadSerializer(data={"csv_file": file})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        result = serializer.save()
        logger.debug("Upload result: %s", result)
        self.assertEqual(result["saved_records"], 2)
        self.assertEqual(result["failed_records"], 0)
        self.assertEqual(result["errors"], [])

    def test_missing_columns(self):
        logger.info("Running test_missing_columns...")
        data = [{"name": "Alice", "email": "alice@example.com"}]
        file = self.make_csv(data)
        serializer = FileUploadSerializer(data={"csv_file": file})
        self.assertFalse(serializer.is_valid())
        logger.warning("Validation errors: %s", serializer.errors)
        self.assertIn("CSV file must contain the following columns", str(serializer.errors["non_field_errors"][0]))

    def test_invalid_email(self):
        logger.info("Running test_invalid_email...")
        data = [{"name": "Alice", "email": "bademail", "age": 25}]
        file = self.make_csv(data)
        serializer = FileUploadSerializer(data={"csv_file": file})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        result = serializer.save()
        logger.error(f"Upload errors: {result["errors"]}")
        self.assertEqual(result["saved_records"], 0)
        self.assertEqual(result["failed_records"], 1)
        self.assertIn("email", result["errors"][0]["errors"])

    def test_duplicate_email(self):
        logger.info("Running test_duplicate_email...")
        data = [
            {"name": "Alice", "email": "alice@example.com", "age": 25},
            {"name": "Bob", "email": "alice@example.com", "age": 30},
            {"name": "Carol", "email": "existing@example.com", "age": 22},
        ]
        file = self.make_csv(data)
        serializer = FileUploadSerializer(data={"csv_file": file})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        result = serializer.save()
        logger.debug(f"Upload result: {result}")
        self.assertEqual(result["saved_records"], 1)
        self.assertEqual(result["failed_records"], 0)
        self.assertEqual(result["errors"], [])

    def test_invalid_age(self):
        logger.info("Running test_invalid_age...")
        data = [
            {"name": "Alice", "email": "alice@example.com", "age": -1},
            {"name": "Bob", "email": "bob@example.com", "age": "abc"},
        ]
        file = self.make_csv(data)
        serializer = FileUploadSerializer(data={"csv_file": file})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        result = serializer.save()
        logger.error(f"Upload errors: {result["errors"]}")
        self.assertEqual(result["saved_records"], 0)
        self.assertEqual(result["failed_records"], 2)
        self.assertIn("age", result["errors"][0]["errors"])
        self.assertIn("age", result["errors"][1]["errors"])
