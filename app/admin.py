from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

# Register your models here.


@admin.register(Officer)
class OfficerAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'rank')
    search_fields = ('user__username', 'badge', 'rank')


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_active')
    search_fields = ('user__username', 'role')
    list_filter = ('role', 'is_active')


@admin.register(Ministry)
class MinistryAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username',)


@admin.register(OfficerManagement)
class OfficerManagementAdmin(admin.ModelAdmin):
    list_display = ('officer', 'name', 'badge', 'role', 'active')
    search_fields = ('officer__user__username', 'name', 'badge', 'role')
    list_filter = ('role', 'active')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_issued', 'plate_no', 'amount', 'violation_type', 'status', 'date', 'officer')
    list_filter = ('status', 'violation_type', 'region')
    search_fields = ('ticket_issued', 'plate_no', 'officer__user__username')
    ordering = ('-date',)
    date_hierarchy = 'date'


@admin.register(CourtDate)
class CourtDateAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'scheduled_date', 'location', 'judge', 'created_by', 'created_at')
    list_filter = ('location', 'judge')
    search_fields = ('ticket__ticket_issued', 'location', 'judge')
    ordering = ('-scheduled_date',)
    date_hierarchy = 'scheduled_date'
    readonly_fields = ('id', 'created_at')


@admin.register(Judiciary)
class JudiciaryAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username',)


@admin.register(Defendant)
class DefendantAdmin(admin.ModelAdmin):
    list_display = ('firstname', 'lastname', 'id_no', 'license_no', 'phone_number', 'email')
    search_fields = ('firstname', 'lastname', 'id_no', 'license_no', 'phone_number', 'email')


@admin.register(DefendantFile)
class DefendantFileAdmin(admin.ModelAdmin):
    list_display = ('defendant', 'ticket', 'file', 'uploaded_at')
    search_fields = ('defendant__firstname', 'defendant__lastname', 'ticket__ticket_issued', 'file')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'user', 'ticket', 'timestamp', 'details')
    list_filter = ('action',)
    search_fields = ('user__username', 'ticket__ticket_issued', 'details')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'


@admin.register(TicketManagement)
class TicketManagementAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'resolution_notes', 'resolved_at')
    search_fields = ('ticket__ticket_issued', 'resolution_notes')


@admin.register(Nampol)
class NampolAdmin(admin.ModelAdmin):
    list_display = ('employee',)
    search_fields = ('employee__user__username',)


@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket', 'file_type', 'uploaded_at', 'uploaded_by')
    list_filter = ('file_type',)
    search_fields = ('ticket__ticket_issued', 'description')




