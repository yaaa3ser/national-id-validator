from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta
import json

from .models import APICallLog, DailyUsageSummary


@admin.register(APICallLog)
class APICallLogAdmin(admin.ModelAdmin):
    """
    Admin interface for API call logs.
    """
    
    list_display = [
        'timestamp', 'api_key_name', 'endpoint', 'method', 'status_code_colored',
        'response_time_ms', 'national_id_count', 'validation_successful_icon',
        'cache_hit_icon', 'ip_address'
    ]
    list_filter = [
        'endpoint', 'method', 'status_code', 'validation_successful', 
        'cache_hit', 'timestamp'
    ]
    search_fields = [
        'api_key__name', 'request_id', 'ip_address', 'endpoint'
    ]
    readonly_fields = [
        'request_id', 'api_key', 'endpoint', 'method', 'path', 'query_params',
        'ip_address', 'user_agent', 'referer', 'request_body', 'request_size_bytes',
        'status_code', 'response_body', 'response_size_bytes', 'response_time_ms',
        'validation_successful', 'national_id_count', 'timestamp', 'cache_hit'
    ]
    
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    def api_key_name(self, obj):
        """Display API key name."""
        return obj.api_key.name if obj.api_key else 'Anonymous'
    api_key_name.short_description = "API Key"
    api_key_name.admin_order_field = 'api_key__name'
    
    def status_code_colored(self, obj):
        """Display status code with color coding."""
        if obj.status_code < 300:
            color = 'green'
        elif obj.status_code < 400:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{}</span>',
            color, obj.status_code
        )
    status_code_colored.short_description = "Status"
    status_code_colored.admin_order_field = 'status_code'
    
    def validation_successful_icon(self, obj):
        """Display validation success with icons."""
        if obj.validation_successful is None:
            return '-'
        elif obj.validation_successful:
            return format_html('<span style="color: green;">✓</span>')
        else:
            return format_html('<span style="color: red;">✗</span>')
    validation_successful_icon.short_description = "Valid"
    validation_successful_icon.admin_order_field = 'validation_successful'
    
    def cache_hit_icon(self, obj):
        """Display cache hit with icons."""
        if obj.cache_hit:
            return format_html('<span style="color: blue;">⚡</span>')
        return '-'
    cache_hit_icon.short_description = "Cache"
    cache_hit_icon.admin_order_field = 'cache_hit'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('api_key')
    
    def has_add_permission(self, request):
        """Disable manual addition of log records."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Make log records read-only."""
        return False


@admin.register(DailyUsageSummary)
class DailyUsageSummaryAdmin(admin.ModelAdmin):
    """
    Admin interface for daily usage summaries.
    """
    
    list_display = [
        'date', 'api_key_name', 'total_requests', 'successful_requests',
        'success_rate_display', 'total_validations', 'cache_hit_rate_display',
        'avg_response_time_ms', 'billable_units'
    ]
    list_filter = ['date', 'api_key']
    search_fields = ['api_key__name']
    readonly_fields = [
        'api_key', 'date', 'total_requests', 'successful_requests', 'failed_requests',
        'total_validations', 'successful_validations', 'failed_validations',
        'avg_response_time_ms', 'min_response_time_ms', 'max_response_time_ms',
        'total_request_bytes', 'total_response_bytes', 'cache_hits', 'cache_misses',
        'billable_units', 'created_at', 'updated_at'
    ]
    
    date_hierarchy = 'date'
    ordering = ['-date']
    
    def api_key_name(self, obj):
        """Display API key name."""
        return obj.api_key.name
    api_key_name.short_description = "API Key"
    api_key_name.admin_order_field = 'api_key__name'
    
    def success_rate_display(self, obj):
        """Display success rate as percentage."""
        return f"{obj.success_rate:.1f}%"
    success_rate_display.short_description = "Success Rate"
    
    def cache_hit_rate_display(self, obj):
        """Display cache hit rate as percentage."""
        return f"{obj.cache_hit_rate:.1f}%"
    cache_hit_rate_display.short_description = "Cache Hit Rate"
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('api_key')
    
    def has_add_permission(self, request):
        """Disable manual addition of summary records."""
        return False
