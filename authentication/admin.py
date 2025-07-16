from django.contrib import admin
from .models import APIKey


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    """
    Admin interface for API key management.
    """
    
    list_display = [
        'name', 'masked_key', 'status', 'user', 'total_requests', 
        'last_used', 'created_at', 'expires_at', 'is_active'
    ]
    list_filter = ['status', 'is_active', 'created_at', 'last_used']
    search_fields = ['name', 'key', 'user__username', 'user__email']
    readonly_fields = ['id', 'key', 'created_at', 'updated_at', 'total_requests', 'last_used']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'key', 'user', 'description')
        }),
        ('Status & Permissions', {
            'fields': ('status', 'is_active', 'expires_at')
        }),
        ('Rate Limiting', {
            'fields': ('rate_limit_per_minute', 'rate_limit_per_hour', 'rate_limit_per_day')
        }),
        ('Security', {
            'fields': ('allowed_ips',)
        }),
        ('Usage Statistics', {
            'fields': ('total_requests', 'last_used'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_keys', 'deactivate_keys', 'suspend_keys']
    
    def masked_key(self, obj):
        """Display masked API key for security."""
        if obj.key:
            return f"{obj.key[:8]}{'*' * 20}{obj.key[-4:]}"
        return "No key"
    masked_key.short_description = "API Key"
    
    def activate_keys(self, request, queryset):
        """Activate selected API keys."""
        updated = queryset.update(status=APIKey.ACTIVE, is_active=True)
        self.message_user(request, f'{updated} API key(s) activated.')
    activate_keys.short_description = "Activate selected API keys"
    
    def deactivate_keys(self, request, queryset):
        """Deactivate selected API keys."""
        updated = queryset.update(status=APIKey.INACTIVE, is_active=False)
        self.message_user(request, f'{updated} API key(s) deactivated.')
    deactivate_keys.short_description = "Deactivate selected API keys"
    
    def suspend_keys(self, request, queryset):
        """Suspend selected API keys."""
        updated = queryset.update(status=APIKey.SUSPENDED)
        self.message_user(request, f'{updated} API key(s) suspended.')
    suspend_keys.short_description = "Suspend selected API keys"
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user')


# Admin site customization
admin.site.site_header = "National ID API Administration"
admin.site.site_title = "National ID API Admin"
admin.site.index_title = "Welcome to National ID API Administration"
