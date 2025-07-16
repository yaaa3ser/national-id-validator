from rest_framework import serializers
import re


class NationalIDValidationSerializer(serializers.Serializer):
    """
    Serializer for National ID validation request.
    """
    national_id = serializers.CharField(
        max_length=20,  # Allow some extra characters that will be stripped
        min_length=14,
        help_text="Egyptian National ID (14 digits)",
        error_messages={
            'required': 'National ID is required',
            'min_length': 'National ID must be at least 14 digits',
            'max_length': 'National ID is too long',
        }
    )
    
    include_details = serializers.BooleanField(
        default=True,
        required=False,
        help_text="Include detailed validation information in response"
    )
    
    def validate_national_id(self, value):
        """
        Validate national ID format.
        """
        # Remove any non-digit characters
        cleaned_id = re.sub(r'\D', '', str(value))
        
        if len(cleaned_id) != 14:
            raise serializers.ValidationError(
                f"National ID must be exactly 14 digits after cleaning, got {len(cleaned_id)}"
            )
        
        if not cleaned_id.isdigit():
            raise serializers.ValidationError("National ID must contain only digits")
        
        # Basic format validation
        if cleaned_id[0] not in ['2', '3']:
            raise serializers.ValidationError(
                "Invalid century digit. Must be 2 (1900s) or 3 (2000s)"
            )
        
        return cleaned_id
