import os
import pandas as pd

output_dir = os.path.join(os.path.dirname(__file__), '../test_files')
os.makedirs(output_dir, exist_ok=True)

rows = []

# 10 valid rows
for i in range(10):
    rows.append({
        "name": f"ValidUser{i}",
        "email": f"valid{i}@example.com",
        "age": 25 + i
    })

# 10 rows with missing columns (no age)
for i in range(10, 20):
    rows.append({
        "name": f"MissingAgeUser{i}",
        "email": f"missingage{i}@example.com",
        # "age" omitted
    })

# 10 rows with invalid email
for i in range(20, 30):
    rows.append({
        "name": f"InvalidEmailUser{i}",
        "email": f"invalidemail{i}",  # invalid email
        "age": 30
    })

# 10 rows with duplicate emails (same as first valid)
for i in range(30, 40):
    rows.append({
        "name": f"DuplicateEmailUser{i}",
        "email": "valid0@example.com",  # duplicate of first valid
        "age": 35
    })

# 10 rows with invalid age
for i in range(40, 45):
    rows.append({
        "name": f"InvalidAgeUser{i}",
        "email": f"invalidage{i}@example.com",
        "age": -5  # invalid age
    })
for i in range(45, 50):
    rows.append({
        "name": f"InvalidAgeUser{i}",
        "email": f"invalidage{i}@example.com",
        "age": "abc"  # invalid age
    })

df = pd.DataFrame(rows)
df.to_csv(os.path.join(output_dir, "test_data.csv"), index=False)