"""
Egyptian National ID format: 14 digits
- First digit: Birth century (2 for 1900s, 3 for 2000s)
- Digits 2-7: Birth date (YYMMDD)
- Digits 8-9: Governorate code
- Digits 10-13: Sequential number (odd for males, even for females)
- Digit 14: Check digit (not validated as algorithm is not publicly documented)
"""

from datetime import datetime, date
from typing import Dict, Optional, Tuple
import re
import logging

logger = logging.getLogger(__name__)


class EgyptianNationalIDValidator:
    # Egyptian Governorate codes mapping
    GOVERNORATE_CODES = {
        '01': 'Cairo',
        '02': 'Alexandria',
        '03': 'Port Said',
        '04': 'Suez',
        '11': 'Damietta',
        '12': 'Dakahlia',
        '13': 'Sharqia',
        '14': 'Qalyubia',
        '15': 'Kafr El Sheikh',
        '16': 'Gharbiyah',
        '17': 'Menoufia',
        '18': 'Beheira',
        '19': 'Ismailia',
        '21': 'Giza',
        '22': 'Beni Suef',
        '23': 'Fayoum',
        '24': 'Minya',
        '25': 'Asyut',
        '26': 'Sohag',
        '27': 'Qena',
        '28': 'Aswan',
        '29': 'Luxor',
        '31': 'Red Sea',
        '32': 'New Valley',
        '33': 'Matrouh',
        '34': 'North Sinai',
        '35': 'South Sinai',
        '88': 'Foreign Born',
    }
    
    def __init__(self):
        self.current_year = datetime.now().year
    
    def validate(self, national_id: str) -> Tuple[bool, Dict]:
        """
        Validate Egyptian National ID and extract all possible data.
        
        Args:
            national_id (str): The 14-digit national ID
            
        Returns:
            Tuple[bool, Dict]: (is_valid, extracted_data)
        """
        try:
            # Input sanitization
            national_id = self._sanitize_input(national_id)
            
            # Format validation
            format_valid, format_error = self._validate_format(national_id)
            if not format_valid:
                return False, {'error': format_error}
            
            # Extract components
            century_digit = national_id[0]
            birth_date_str = national_id[1:7]
            governorate_code = national_id[7:9]
            sequence_number = national_id[9:13]
            
            # Date validation
            birth_date, date_error = self._validate_and_extract_date(century_digit, birth_date_str)
            if not birth_date:
                return False, {'error': date_error}
            
            
            # Extract all data
            extracted_data = {
                'national_id': national_id,
                'is_valid': True,
                'birth_date': birth_date.isoformat(),
                'age': self._calculate_age(birth_date),
                'gender': self._determine_gender(sequence_number),
                'governorate': self._get_governorate(governorate_code),
                'governorate_code': governorate_code,
                'century': '20th' if century_digit == '2' else '21st',
                'sequence_number': sequence_number,
                'validation_details': {
                    'format_valid': True,
                    'date_valid': True,
                    'governorate_valid': governorate_code in self.GOVERNORATE_CODES
                }
            }
            
            logger.info(f"Successfully validated national ID: {national_id[:4]}****{national_id[-2:]}")
            return True, extracted_data
            
        except Exception as e:
            logger.error(f"Unexpected error validating national ID: {str(e)}")
            return False, {'error': f'Validation failed: {str(e)}'}
    
    def _sanitize_input(self, national_id: str) -> str:
        """Remove any non-digit characters and normalize input."""
        if not isinstance(national_id, str):
            national_id = str(national_id)
        return re.sub(r'\D', '', national_id)
    
    def _validate_format(self, national_id: str) -> Tuple[bool, Optional[str]]:
        """Validate the basic format of the national ID."""
        if not national_id:
            return False, "National ID cannot be empty"
        
        if len(national_id) != 14:
            return False, f"National ID must be exactly 14 digits, got {len(national_id)}"
        
        if not national_id.isdigit():
            return False, "National ID must contain only digits"
        
        # Century digit validation
        if national_id[0] not in ['2', '3']:
            return False, "Invalid century digit. Must be 2 (1900s) or 3 (2000s)"
        
        return True, None
    
    def _validate_and_extract_date(self, century_digit: str, birth_date_str: str) -> Tuple[Optional[date], Optional[str]]:
        """Validate and extract birth date from national ID."""
        try:
            year_suffix = birth_date_str[:2]
            month = birth_date_str[2:4]
            day = birth_date_str[4:6]
            
            # Determine full year based on century digit
            if century_digit == '2':
                full_year = 1900 + int(year_suffix)
            else:  # century_digit == '3'
                full_year = 2000 + int(year_suffix)
            
            # Validate date components
            if not (1 <= int(month) <= 12):
                return None, f"Invalid month: {month}"
            
            if not (1 <= int(day) <= 31):
                return None, f"Invalid day: {day}"
            
            # Create and validate date
            birth_date = date(full_year, int(month), int(day))
            
            # Additional validation: date cannot be in the future
            if birth_date > date.today():
                return None, "Birth date cannot be in the future"
            
            return birth_date, None
            
        except ValueError as e:
            return None, f"Invalid date format: {str(e)}"
    
    def _calculate_age(self, birth_date: date) -> int:
        """Calculate age from birth date."""
        today = date.today()
        age = today.year - birth_date.year
        
        # Adjust if birthday hasn't occurred this year
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1
        
        return age
    
    def _determine_gender(self, sequence_number: str) -> str:
        """Determine gender from sequence number (odd=male, even=female)."""
        last_digit = int(sequence_number[-1])
        return 'Male' if last_digit % 2 == 1 else 'Female'
    
    def _get_governorate(self, governorate_code: str) -> str:
        """Get governorate name from code."""
        return self.GOVERNORATE_CODES.get(governorate_code, f'Unknown Governorate (Code: {governorate_code})')
    
    def get_validation_summary(self, national_id: str) -> Dict:
        """Get a detailed validation summary for debugging purposes."""
        national_id = self._sanitize_input(national_id)
        
        summary = {
            'input': national_id,
            'length': len(national_id),
            'format_checks': {
                'length_valid': len(national_id) == 14,
                'digits_only': national_id.isdigit() if national_id else False,
                'century_digit_valid': national_id[0] in ['2', '3'] if national_id else False,
            }
        }
        
        if len(national_id) == 14:
            summary.update({
                'components': {
                    'century_digit': national_id[0],
                    'birth_date_string': national_id[1:7],
                    'governorate_code': national_id[7:9],
                    'sequence_number': national_id[9:13],
                    'check_digit': national_id[13],
                },
                'governorate_name': self._get_governorate(national_id[7:9])
            })
        
        return summary
