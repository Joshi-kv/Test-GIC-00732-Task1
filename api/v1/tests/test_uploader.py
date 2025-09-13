import io
import pandas as pd
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from models.models import User
from api.v1.serializers.uploader import FileUploadSerializer

class FileUploadSerializerTests(TestCase):
    def setUp(self):
        User.objects.create(name="Existing", email="existing@example.com", age=30)

    def make_csv(self, data):
        df = pd.DataFrame(data)
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        csv_bytes = buf.getvalue().encode("utf-8")
        return SimpleUploadedFile("test.csv", csv_bytes, content_type="text/csv")

    def test_valid_upload(self):
        data = [
            {"name": "Alice", "email": "alice@example.com", "age": 25},
            {"name": "Bob", "email": "bob@example.com", "age": 30},
        ]
        file = self.make_csv(data)
        serializer = FileUploadSerializer(data={"csv_file": file})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        result = serializer.save()
        self.assertEqual(result["saved_records"], 2)
        self.assertEqual(result["failed_records"], 0)
        self.assertEqual(result["errors"], [])

    def test_missing_columns(self):
        data = [
            {"name": "Alice", "email": "alice@example.com"},
        ]
        file = self.make_csv(data)
        serializer = FileUploadSerializer(data={"csv_file": file})
        self.assertFalse(serializer.is_valid())
        self.assertIn("CSV file must contain the following columns", str(serializer.errors["non_field_errors"][0]))

    def test_invalid_email(self):
        data = [
            {"name": "Alice", "email": "bademail", "age": 25},
        ]
        file = self.make_csv(data)
        serializer = FileUploadSerializer(data={"csv_file": file})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        result = serializer.save()
        self.assertEqual(result["saved_records"], 0)
        self.assertEqual(result["failed_records"], 1)
        self.assertIn("email", result["errors"][0]["errors"])

    def test_duplicate_email(self):
        data = [
            {"name": "Alice", "email": "alice@example.com", "age": 25},
            {"name": "Bob", "email": "alice@example.com", "age": 30},
            {"name": "Carol", "email": "existing@example.com", "age": 22},
        ]
        file = self.make_csv(data)
        serializer = FileUploadSerializer(data={"csv_file": file})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        result = serializer.save()
        self.assertEqual(result["saved_records"], 1)
        self.assertEqual(result["failed_records"], 0)
        self.assertEqual(result["errors"], [])

    def test_invalid_age(self):
        data = [
            {"name": "Alice", "email": "alice@example.com", "age": -1},
            {"name": "Bob", "email": "bob@example.com", "age": "abc"},
        ]
        file = self.make_csv(data)
        serializer = FileUploadSerializer(data={"csv_file": file})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        result = serializer.save()
        self.assertEqual(result["saved_records"], 0)
        self.assertEqual(result["failed_records"], 2)
        self.assertIn("age", result["errors"][0]["errors"])
        self.assertIn("age", result["errors"][1]["errors"])