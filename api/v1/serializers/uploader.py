from rest_framework import serializers
import pandas as pd
import re

from core.validators import FileValidator
from core.constants import MAX_FILE_SIZE, ALLOWED_EXTENSION
from models.models import User

class FileUploadSerializer(serializers.Serializer):
    csv_file = serializers.FileField(
        required=True, 
        validators=[FileValidator(max_size=MAX_FILE_SIZE, allowed_extensions=ALLOWED_EXTENSION)],
        error_messages={
            'required': 'Please upload a file.'
        }
    )
    
    
    def validate(self, attrs):
        
        """
        Validate the uploaded CSV file.
        
        if the file is valid, it reads the CSV into a pandas DataFrame and checks for required columns.
        It also prepares the DataFrame for further processing in the save() method.

        Raises:
            serializers.ValidationError: if it is not a valid CSV file or missing required columns.

        Returns:
            vaidation errors if any
        """
        
        file = attrs.get("csv_file")
        try:
            df = pd.read_csv(file)
        except Exception as e:
            raise serializers.ValidationError(f"Error reading CSV file: {str(e)}")

        required_columns = {'name', 'email', 'age'}
        if not required_columns.issubset(set(df.columns)):
            raise serializers.ValidationError(
                f"CSV file must contain the following columns: {', '.join(required_columns)}"
            )

        attrs["dataframe"] = df  # pass df to save()
        return attrs
    
    def save(self, **kwargs):
        """
        Process the DataFrame, validate each row, and save valid records to the database.
        It collects errors for invalid rows and returns a summary of the operation.
        
        Returns:
            dict: Summary of saved records, failed records, and errors."""
        
        df = self.validated_data.get("dataframe")
        
        errors = []
        valid_instances = []
        seen_emails = set()
        
        for index, row in df.iterrows():
            row_errors = {}
            name = row.get('name')
            email = row.get('email')
            age = row.get('age')
            
            # --- Name validation ---
            if pd.isna(name) or not isinstance(name, str) or not name.strip():
                row_errors['name'] = "Name must be a non-empty string."
                
            # ---- Email validation ---
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if pd.isna(email) or not re.match(email_pattern, str(email)):
                row_errors['email'] = "Invalid email format."
            elif email in seen_emails or User.objects.filter(email=email).exists():
                continue # Skip duplicate emails without errors
            else:
                seen_emails.add(email)
            
            # --- Age validation ---
            if pd.isna(age):
                row_errors['age'] = 'Age is required.'
            else:
                try:
                    age = int(age)
                    if age <= 0 or age > 120:
                        row_errors['age'] = 'Age must be between 1 and 120.'
                except ValueError:
                    row_errors['age'] = 'Age must be an integer.'
            
            if row_errors:
                errors.append({"row": index + 2, "errors": row_errors})  # +2 for header and 0-index
            else:
                valid_instances.append(User(name=name.strip(), email=email.strip(), age=int(age)))

        # bulk create after validation finishes
        if valid_instances:
            User.objects.bulk_create(valid_instances, ignore_conflicts=True)
            
        result = {
            'saved_records': len(valid_instances),
            'failed_records': len(errors),
            'errors': errors
        }
        return result