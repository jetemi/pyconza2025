from django.contrib import admin
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from .models import GrantApplication, GrantReview


@admin.register(GrantApplication)
class GrantApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'approved_amount', 'created_at', 'request_travel', 'request_accommodation', 'request_ticket', 'travel_from_display')
    list_filter = ('status', 'created_at', 'request_travel', 'request_accommodation', 'request_ticket', 'gender', 'current_role', 'decided_by')
    search_fields = ('user__username', 'user__email', 'travel_from_city', 'travel_from_country')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user', 'decided_by')
    actions = ['export_to_excel']
    
    fieldsets = (
        ('Application Info', {
            'fields': ('user', 'status', 'created_at', 'updated_at')
        }),
        ('Final Decision', {
            'fields': ('approved_amount', 'decision_notes', 'decided_by', 'decided_at'),
            'classes': ('collapse',)
        }),
        ('Personal Information', {
            'fields': ('gender', 'gender_details', 'current_role', 'current_role_details')
        }),
        ('Application Details', {
            'fields': ('motivation', 'contribution', 'financial_need')
        }),
        ('Travel Information', {
            'fields': ('request_travel', 'travel_from_city', 'travel_from_country', 'travel_amount', 'transportation_type')
        }),
        ('Accommodation & Ticket', {
            'fields': ('request_accommodation', 'accommodation_nights', 'request_ticket')
        }),
        ('Additional Information', {
            'fields': ('additional_info',)
        }),
    )
    
    def export_to_excel(self, request, queryset):
        wb = Workbook()
        ws = wb.active
        ws.title = "Grant Applications"
        
        headers = [
            'User', 'Email', 'First Name', 'Last Name', 'Status', 'Created At',
            'Gender', 'Gender Details', 'Current Role', 'Current Role Details',
            'Motivation', 'Contribution', 'Financial Need', 'Additional Info',
            'Request Travel', 'Travel From City', 'Travel From Country', 'Travel Amount', 'Transportation Type',
            'Request Accommodation', 'Accommodation Nights', 'Request Ticket',
            'Approved Amount', 'Decision Notes', 'Decided By', 'Decided At'
        ]
        
        for col, header in enumerate(headers, 1):
            ws[f'{get_column_letter(col)}1'] = header
        
        for row, app in enumerate(queryset.select_related('user', 'decided_by'), 2):
            ws[f'A{row}'] = app.user.username
            ws[f'B{row}'] = app.user.email
            ws[f'C{row}'] = app.user.first_name
            ws[f'D{row}'] = app.user.last_name
            ws[f'E{row}'] = app.get_status_display()
            ws[f'F{row}'] = app.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ws[f'G{row}'] = app.get_gender_display() if app.gender else ''
            ws[f'H{row}'] = app.gender_details or ''
            ws[f'I{row}'] = app.get_current_role_display() if app.current_role else ''
            ws[f'J{row}'] = app.current_role_details or ''
            ws[f'K{row}'] = app.motivation or ''
            ws[f'L{row}'] = app.contribution or ''
            ws[f'M{row}'] = app.financial_need or ''
            ws[f'N{row}'] = app.additional_info or ''
            ws[f'O{row}'] = 'Yes' if app.request_travel else 'No'
            ws[f'P{row}'] = app.travel_from_city or ''
            ws[f'Q{row}'] = app.travel_from_country.name if app.travel_from_country else ''
            ws[f'R{row}'] = str(app.travel_amount) if app.travel_amount else ''
            ws[f'S{row}'] = app.get_transportation_type_display() if app.transportation_type else ''
            ws[f'T{row}'] = 'Yes' if app.request_accommodation else 'No'
            ws[f'U{row}'] = str(app.accommodation_nights) if app.accommodation_nights else ''
            ws[f'V{row}'] = 'Yes' if app.request_ticket else 'No'
            ws[f'W{row}'] = str(app.approved_amount) if app.approved_amount else ''
            ws[f'X{row}'] = app.decision_notes or ''
            ws[f'Y{row}'] = app.decided_by.username if app.decided_by else ''
            ws[f'Z{row}'] = app.decided_at.strftime('%Y-%m-%d %H:%M:%S') if app.decided_at else ''
        
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="grant_applications.xlsx"'
        wb.save(response)
        return response
    
    export_to_excel.short_description = "Export selected applications to Excel"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
    full_name.short_description = 'Full Name'
    
    def travel_from_display(self, obj):
        return obj.travel_from or "Not specified"
    travel_from_display.short_description = 'Travel From'
    

@admin.register(GrantReview)
class GrantReviewAdmin(admin.ModelAdmin):
    list_display = ('application', 'reviewer', 'score', 'suggested_amount', 'created_at')
    list_filter = ('score', 'created_at', 'reviewer')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('application', 'reviewer')
    