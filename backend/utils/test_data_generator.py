"""
Test Data Generator
Generates realistic test data for various field types
"""

import random
import string
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
import re


class DataType(str, Enum):
    """Supported data types"""
    EMAIL = "email"
    PHONE = "phone"
    NAME = "name"
    USERNAME = "username"
    PASSWORD = "password"
    AGE = "age"
    DATE = "date"
    PRICE = "price"
    DISCOUNT_CODE = "discount_code"
    URL = "url"
    ADDRESS = "address"
    ZIPCODE = "zipcode"
    CREDIT_CARD = "credit_card"
    TEXT = "text"
    NUMBER = "number"


class TestDataGenerator:
    """Generate realistic test data for various field types"""
    
    def __init__(self):
        self.first_names = [
            "John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa",
            "James", "Mary", "William", "Patricia", "Richard", "Jennifer", "Thomas",
            "Linda", "Charles", "Barbara", "Daniel", "Elizabeth", "Matthew", "Susan"
        ]
        
        self.last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
            "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
            "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"
        ]
        
        self.domains = [
            "gmail.com", "yahoo.com", "outlook.com", "example.com", "test.com",
            "company.com", "email.com", "domain.com"
        ]
        
        self.streets = [
            "Main St", "Oak Ave", "Maple Dr", "Cedar Ln", "Pine Rd",
            "Elm St", "Park Ave", "Washington Blvd", "Lake Dr", "Hill Rd"
        ]
        
        self.cities = [
            "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
            "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"
        ]
        
        self.states = [
            "NY", "CA", "IL", "TX", "AZ", "PA", "FL", "OH", "WA", "MA"
        ]
    
    def generate_email(self, valid: bool = True) -> str:
        """Generate email address"""
        if valid:
            first = random.choice(self.first_names).lower()
            last = random.choice(self.last_names).lower()
            number = random.randint(1, 999)
            domain = random.choice(self.domains)
            return f"{first}.{last}{number}@{domain}"
        else:
            invalid_patterns = [
                "invalid-email",
                "missing@domain",
                "@nodomain.com",
                "no-at-sign.com",
                "double@@domain.com",
                "spaces in@email.com",
                ""
            ]
            return random.choice(invalid_patterns)
    
    def generate_phone(self, valid: bool = True) -> str:
        """Generate phone number"""
        if valid:
            area_code = random.randint(200, 999)
            prefix = random.randint(200, 999)
            line = random.randint(1000, 9999)
            formats = [
                f"({area_code}) {prefix}-{line}",
                f"{area_code}-{prefix}-{line}",
                f"+1{area_code}{prefix}{line}"
            ]
            return random.choice(formats)
        else:
            invalid_patterns = [
                "123-456-789",  # Too short
                "000-000-0000",  # All zeros
                "phone-number",  # Text
                "12345",  # Too short
                ""
            ]
            return random.choice(invalid_patterns)
    
    def generate_name(self, valid: bool = True) -> str:
        """Generate person name"""
        if valid:
            first = random.choice(self.first_names)
            last = random.choice(self.last_names)
            return f"{first} {last}"
        else:
            invalid_patterns = [
                "123",  # Numbers only
                "A",  # Too short
                "Test User!@#",  # Special chars
                "",  # Empty
                "VeryLongNameThatExceedsReasonableLimitsForAPersonName" * 3
            ]
            return random.choice(invalid_patterns)
    
    def generate_username(self, valid: bool = True) -> str:
        """Generate username"""
        if valid:
            first = random.choice(self.first_names).lower()
            number = random.randint(100, 9999)
            patterns = [
                f"{first}{number}",
                f"{first}_{number}",
                f"{first}.{number}"
            ]
            return random.choice(patterns)
        else:
            invalid_patterns = [
                "ab",  # Too short
                "user name",  # Spaces
                "user@name",  # Invalid chars
                "",  # Empty
                "a" * 100  # Too long
            ]
            return random.choice(invalid_patterns)
    
    def generate_password(self, valid: bool = True) -> str:
        """Generate password"""
        if valid:
            length = random.randint(8, 16)
            chars = string.ascii_letters + string.digits + "!@#$%^&*"
            password = ''.join(random.choice(chars) for _ in range(length))
            # Ensure at least one of each type
            password = (
                random.choice(string.ascii_uppercase) +
                random.choice(string.ascii_lowercase) +
                random.choice(string.digits) +
                random.choice("!@#$%^&*") +
                password[4:]
            )
            return password
        else:
            invalid_patterns = [
                "123",  # Too short
                "password",  # Common
                "12345678",  # No letters
                "abcdefgh",  # No numbers
                "",  # Empty
            ]
            return random.choice(invalid_patterns)
    
    def generate_age(self, valid: bool = True, min_age: int = 18, max_age: int = 100) -> int:
        """Generate age"""
        if valid:
            return random.randint(min_age, max_age)
        else:
            invalid_values = [
                -5,  # Negative
                0,  # Zero
                min_age - 1,  # Below minimum
                max_age + 1,  # Above maximum
                150,  # Unrealistic
                999  # Very large
            ]
            return random.choice(invalid_values)
    
    def generate_date(self, valid: bool = True) -> str:
        """Generate date"""
        if valid:
            days_ago = random.randint(0, 365)
            date = datetime.now() - timedelta(days=days_ago)
            return date.strftime("%Y-%m-%d")
        else:
            invalid_patterns = [
                "2024-13-01",  # Invalid month
                "2024-02-30",  # Invalid day
                "99-99-9999",  # Wrong format
                "not-a-date",  # Text
                "",  # Empty
                "2024/02/30"  # Wrong separator
            ]
            return random.choice(invalid_patterns)
    
    def generate_price(self, valid: bool = True, min_price: float = 1.0, max_price: float = 1000.0) -> float:
        """Generate price"""
        if valid:
            return round(random.uniform(min_price, max_price), 2)
        else:
            invalid_values = [
                -10.50,  # Negative
                0.0,  # Zero
                0.001,  # Too small
                9999999.99,  # Too large
            ]
            return random.choice(invalid_values)
    
    def generate_discount_code(self, valid: bool = True) -> str:
        """Generate discount code"""
        if valid:
            prefixes = ["SAVE", "DISCOUNT", "DEAL", "PROMO", "OFFER"]
            numbers = ["10", "20", "50", "100"]
            suffix = random.choice(numbers)
            prefix = random.choice(prefixes)
            return f"{prefix}{suffix}"
        else:
            invalid_patterns = [
                "EXPIRED",
                "INVALID_CODE",
                "USED_CODE",
                "",
                "CODE_WITH_SPACES",
                "123"  # Too short
            ]
            return random.choice(invalid_patterns)
    
    def generate_url(self, valid: bool = True) -> str:
        """Generate URL"""
        if valid:
            protocols = ["https://", "http://"]
            domains = ["example.com", "test.com", "demo.com", "site.org"]
            paths = ["", "/page", "/products", "/api/v1"]
            
            protocol = random.choice(protocols)
            domain = random.choice(domains)
            path = random.choice(paths)
            return f"{protocol}{domain}{path}"
        else:
            invalid_patterns = [
                "not-a-url",
                "ftp://invalid",
                "http://",  # Incomplete
                "",
                "javascript:alert('xss')"  # XSS attempt
            ]
            return random.choice(invalid_patterns)
    
    def generate_address(self, valid: bool = True) -> str:
        """Generate address"""
        if valid:
            number = random.randint(100, 9999)
            street = random.choice(self.streets)
            city = random.choice(self.cities)
            state = random.choice(self.states)
            zipcode = random.randint(10000, 99999)
            return f"{number} {street}, {city}, {state} {zipcode}"
        else:
            invalid_patterns = [
                "123",
                "",
                "Invalid Address",
                "!@#$%"
            ]
            return random.choice(invalid_patterns)
    
    def generate_zipcode(self, valid: bool = True) -> str:
        """Generate zipcode"""
        if valid:
            return str(random.randint(10000, 99999))
        else:
            invalid_patterns = [
                "123",  # Too short
                "ABCDE",  # Letters
                "00000",  # All zeros
                "",
                "999999"  # Too long
            ]
            return random.choice(invalid_patterns)
    
    def generate_credit_card(self, valid: bool = True) -> str:
        """Generate credit card number"""
        if valid:
            # Generate dummy card (NOT real cards!)
            parts = [
                str(random.randint(4000, 4999)),  # Visa starts with 4
                str(random.randint(1000, 9999)),
                str(random.randint(1000, 9999)),
                str(random.randint(1000, 9999))
            ]
            return " ".join(parts)
        else:
            invalid_patterns = [
                "1234-5678-9012-3456",  # Wrong format
                "0000 0000 0000 0000",  # All zeros
                "1234",  # Too short
                "",
                "abcd efgh ijkl mnop"  # Letters
            ]
            return random.choice(invalid_patterns)
    
    def generate_text(self, valid: bool = True, min_length: int = 10, max_length: int = 100) -> str:
        """Generate text"""
        if valid:
            words = ["Lorem", "ipsum", "dolor", "sit", "amet", "consectetur",
                    "adipiscing", "elit", "sed", "do", "eiusmod", "tempor"]
            length = random.randint(min_length, max_length)
            text = " ".join(random.choice(words) for _ in range(length // 5))
            return text[:length]
        else:
            invalid_patterns = [
                "",
                "a",  # Too short
                "x" * 1000,  # Too long
                "<script>alert('xss')</script>",  # XSS
                "Text with\nnewlines\nand\ttabs"  # Special chars
            ]
            return random.choice(invalid_patterns)
    
    def generate_number(self, valid: bool = True, min_val: int = 1, max_val: int = 100) -> int:
        """Generate number"""
        if valid:
            return random.randint(min_val, max_val)
        else:
            invalid_values = [
                min_val - 1,
                max_val + 1,
                -999,
                0  # If 0 is invalid
            ]
            return random.choice(invalid_values)
    
    def detect_field_type(self, field_name: str) -> DataType:
        """Detect field type from field name"""
        field_lower = field_name.lower()
        
        if any(word in field_lower for word in ["email", "mail"]):
            return DataType.EMAIL
        elif any(word in field_lower for word in ["phone", "mobile", "tel"]):
            return DataType.PHONE
        elif any(word in field_lower for word in ["name", "username", "user"]):
            if "user" in field_lower:
                return DataType.USERNAME
            return DataType.NAME
        elif "password" in field_lower or "pwd" in field_lower:
            return DataType.PASSWORD
        elif "age" in field_lower:
            return DataType.AGE
        elif any(word in field_lower for word in ["date", "dob", "birth"]):
            return DataType.DATE
        elif any(word in field_lower for word in ["price", "cost", "amount"]):
            return DataType.PRICE
        elif any(word in field_lower for word in ["discount", "promo", "coupon", "code"]):
            return DataType.DISCOUNT_CODE
        elif "url" in field_lower or "website" in field_lower:
            return DataType.URL
        elif "address" in field_lower:
            return DataType.ADDRESS
        elif any(word in field_lower for word in ["zip", "postal"]):
            return DataType.ZIPCODE
        elif any(word in field_lower for word in ["card", "credit"]):
            return DataType.CREDIT_CARD
        elif "quantity" in field_lower or "count" in field_lower:
            return DataType.NUMBER
        else:
            return DataType.TEXT
    
    def generate_for_field(self, field_name: str, field_type: Optional[DataType] = None, 
                          valid: bool = True, **kwargs) -> Any:
        """Generate data for a specific field"""
        if field_type is None:
            field_type = self.detect_field_type(field_name)
        
        generators = {
            DataType.EMAIL: self.generate_email,
            DataType.PHONE: self.generate_phone,
            DataType.NAME: self.generate_name,
            DataType.USERNAME: self.generate_username,
            DataType.PASSWORD: self.generate_password,
            DataType.AGE: self.generate_age,
            DataType.DATE: self.generate_date,
            DataType.PRICE: self.generate_price,
            DataType.DISCOUNT_CODE: self.generate_discount_code,
            DataType.URL: self.generate_url,
            DataType.ADDRESS: self.generate_address,
            DataType.ZIPCODE: self.generate_zipcode,
            DataType.CREDIT_CARD: self.generate_credit_card,
            DataType.TEXT: self.generate_text,
            DataType.NUMBER: self.generate_number,
        }
        
        generator = generators.get(field_type, self.generate_text)
        return generator(valid=valid, **kwargs)


# Singleton instance
_test_data_generator_instance: Optional[TestDataGenerator] = None


def get_test_data_generator() -> TestDataGenerator:
    """Get or create singleton TestDataGenerator instance"""
    global _test_data_generator_instance
    if _test_data_generator_instance is None:
        _test_data_generator_instance = TestDataGenerator()
    return _test_data_generator_instance