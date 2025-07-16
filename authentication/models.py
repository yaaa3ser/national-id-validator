from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import secrets


class APIKey(models.Model):
    
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    SUSPENDED = 'suspended'
    
    STATUS_CHOICES = [
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive'),
        (SUSPENDED, 'Suspended'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys', null=True, blank=True)
    
    # Status and permissions
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=ACTIVE)
    is_active = models.BooleanField(default=True)
    
    # Rate limiting
    rate_limit_per_minute = models.PositiveIntegerField(default=100)
    rate_limit_per_hour = models.PositiveIntegerField(default=1000)
    rate_limit_per_day = models.PositiveIntegerField(default=10000)
    
    # Usage tracking
    total_requests = models.BigIntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    description = models.TextField(blank=True)
    allowed_ips = models.TextField(
        blank=True, 
        help_text="Comma-separated list of allowed IP addresses (empty for no restrictions)"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'
    
    def __str__(self):
        return f"{self.name} - {self.key[:8]}..."
    
    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_key():
        return secrets.token_urlsafe(32)
    
    def is_valid(self):
        if not self.is_active or self.status != self.ACTIVE:
            return False
        
        if self.expires_at and self.expires_at < timezone.now():
            return False
        
        return True
    
    def is_ip_allowed(self, ip_address):
        """Check if the IP address is allowed for this API key."""
        if not self.allowed_ips:
            return True  # No IP restrictions
        
        allowed_ips = [ip.strip() for ip in self.allowed_ips.split(',')]
        return ip_address in allowed_ips
    
    def increment_usage(self):
        """Increment the usage counter and update last used timestamp."""
        self.total_requests += 1
        self.last_used = timezone.now()
        self.save(update_fields=['total_requests', 'last_used'])
    
    def get_rate_limits(self):
        return {
            'per_minute': self.rate_limit_per_minute,
            'per_hour': self.rate_limit_per_hour,
            'per_day': self.rate_limit_per_day,
        }

