from django.db import models
from authentication.models import APIKey


class APICallLog(models.Model):
    """
    Model for logging all API calls for tracking and billing purposes.
    """
    
    # Request identification
    api_key = models.ForeignKey(APIKey, on_delete=models.CASCADE, related_name='call_logs', null=True, blank=True)
    request_id = models.CharField(max_length=64, unique=True, db_index=True)
    
    # Request details
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=500)
    query_params = models.TextField(blank=True)
    
    # Client information
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    referer = models.URLField(blank=True)
    
    # Request payload
    request_body = models.TextField(blank=True)
    request_size_bytes = models.PositiveIntegerField(null=True, blank=True)
    
    # Response details
    status_code = models.PositiveIntegerField()
    response_body = models.TextField(blank=True)
    response_size_bytes = models.PositiveIntegerField(null=True, blank=True)
    response_time_ms = models.FloatField(null=True, blank=True)
    
    # Validation results (for National ID endpoints)
    validation_successful = models.BooleanField(null=True, blank=True)
    national_id_count = models.PositiveIntegerField(default=0, help_text="Number of IDs processed in this request")
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Additional metadata
    error_message = models.TextField(blank=True)
    cache_hit = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'API Call Log'
        verbose_name_plural = 'API Call Logs'
        indexes = [
            models.Index(fields=['api_key', 'timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['endpoint', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['status_code', 'timestamp']),
        ]
    
    def __str__(self):
        api_key_name = self.api_key.name if self.api_key else 'Anonymous'
        return f"{api_key_name} - {self.method} {self.endpoint} - {self.timestamp}"


class DailyUsageSummary(models.Model):
    """
    Model for storing daily usage summaries for efficient reporting and billing in the future.
    """
    
    api_key = models.ForeignKey(APIKey, on_delete=models.CASCADE, related_name='daily_summaries')
    date = models.DateField()
    
    # Request counts
    total_requests = models.PositiveIntegerField(default=0)
    successful_requests = models.PositiveIntegerField(default=0)
    failed_requests = models.PositiveIntegerField(default=0)
    
    # Validation counts
    total_validations = models.PositiveIntegerField(default=0)
    successful_validations = models.PositiveIntegerField(default=0)
    failed_validations = models.PositiveIntegerField(default=0)
    
    # Performance metrics
    avg_response_time_ms = models.FloatField(null=True, blank=True)
    min_response_time_ms = models.FloatField(null=True, blank=True)
    max_response_time_ms = models.FloatField(null=True, blank=True)
    
    # Data transfer
    total_request_bytes = models.BigIntegerField(default=0)
    total_response_bytes = models.BigIntegerField(default=0)
    
    # Cache statistics
    cache_hits = models.PositiveIntegerField(default=0)
    cache_misses = models.PositiveIntegerField(default=0)
    
    # Billing information
    billable_units = models.PositiveIntegerField(default=0, help_text="Number of billable units (e.g., validations)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['api_key', 'date']
        ordering = ['-date']
        verbose_name = 'Daily Usage Summary'
        verbose_name_plural = 'Daily Usage Summaries'
        indexes = [
            models.Index(fields=['api_key', 'date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.api_key.name} - {self.date} - {self.total_requests} requests"
    
    @property
    def success_rate(self):
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def cache_hit_rate(self):
        """Calculate cache hit rate percentage."""
        total_cache_operations = self.cache_hits + self.cache_misses
        if total_cache_operations == 0:
            return 0
        return (self.cache_hits / total_cache_operations) * 100
