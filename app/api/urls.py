from django.urls import path
from app import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', views.CustomRefreshTokenView.as_view(), name='token_refresh'),
    path('logout/', views.logout, name='logout'),
    path('authenticate/', views.is_authenticated, name='authenticate_user'),

    # Judge APIs - Updated
    path('judge/cases/', views.get_judge_cases, name='judge_cases'),
    path('judge/available-cases/', views.get_judge_available_cases, name='judge_available_cases'),
    path('judge/claim-case/<int:case_id>/', views.claim_case, name='claim_case'),
    path('judge/calendar/', views.get_judge_calendar, name='judge_calendar'),
    path('judge/schedule/', views.schedule_judge_court_date, name='judge_schedule'),
    path('judge/notifications/', views.get_judge_notifications, name='judge_notifications'),
    path('judge/notifications/<int:notification_id>/read/', views.mark_judge_notification_read, name='mark_notification_read'),
    path('judge/statistics/', views.get_judge_statistics, name='judge_statistics'),

    path('users/', views.get_users, name='get_users'),
    path('users/<int:user_id>/update/', views.update_user, name='update_user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),

    path('officers/', views.officer_list, name='officer_list'),
    path('officers/tickets/', views.get_all_officer_tickets, name='officer_detail'),
    path('officers/<int:officer_id>/update/', views.update_officer, name='update_officer'),
    path('officers/<int:officer_id>/delete/', views.delete_officer, name='delete_officer'),

    path('ticket/', views.get_ticket, name='get_ticket'),
    path('tickets/issue/', views.issue_ticket, name='issue_ticket'),
    path('tickets/officer/', views.get_officer_tickets, name='officer_tickets'),
    path('tickets/search/', views.search_tickets, name='search_tickets'),
    path('tickets/lookup/', views.lookup_ticket, name='lookup_ticket'),
    path('tickets/all/', views.get_all_tickets, name='all_tickets'),
    path('tickets/all-officers/', views.get_all_officer_tickets, name='all_officer_tickets'),

    path('analytics/', views.get_analytics_data, name='analytics'),

    path('defendants/', views.get_defendant_info, name='defendant_list'),

    path('audit-logs/', views.get_audit_logs, name='audit_log'),

    # NaTIS Registration APIs
    path('natis/drivers/register/', views.register_driver, name='register_driver'),
    path('natis/drivers/', views.get_drivers, name='get_drivers'),
    path('natis/drivers/<int:driver_id>/', views.get_driver_by_id, name='get_driver_by_id'),
    path('natis/drivers/<int:driver_id>/update/', views.update_driver, name='update_driver'),
    path('natis/vehicles/register/', views.register_vehicle, name='register_vehicle'),
    path('natis/vehicles/', views.get_vehicles, name='get_vehicles'),
    path('natis/vehicles/<int:vehicle_id>/', views.get_vehicle_by_id, name='get_vehicle_by_id'),
    path('natis/vehicles/<int:vehicle_id>/update/', views.update_vehicle, name='update_vehicle'),

    # NaTIS Admin Dashboard APIs
    path('natis/vehicle-lookup/', views.lookup_vehicle, name='lookup_vehicle'),
    path('natis/license-verify/', views.verify_driver_license, name='verify_driver_license'),
    path('natis/payment/', views.process_payment, name='process_payment'),
    path('natis/reports/', views.generate_report, name='generate_report'),
    path('admin/check-overdue/', views.check_overdue_tickets, name='check_overdue'),
]
