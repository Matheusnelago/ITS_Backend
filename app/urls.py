from django.urls import path
from app import views

urlpatterns = [
    path('', views.api_root, name='api_root'),
    path('health/', views.health_check, name='health_check'),
    path('register/', views.register, name='register'),
    path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', views.CustomRefreshTokenView.as_view(), name='token_refresh'),
    path('logout/', views.logout, name='logout'),
    path('authenticate/', views.is_authenticated, name='authenticate_user'),

    path('judge/schedule/', views.schedule_court_date, name='judge_schedule'),
    path('judge/cases/', views.get_judge_cases, name='judge_cases'),
    path('judge/cases/<int:case_id>/', views.get_judge_case_detail, name='judge_case_detail'),
    path('judge/cases/judgment/', views.update_case_judgment, name='update_case_judgment'),
    path('judge/calendar/', views.get_judge_calendar, name='judge_calendar'),
    path('judge/calendar/schedule/', views.schedule_judge_court_date, name='schedule_judge_court_date'),
    path('judge/statistics/', views.get_judge_statistics, name='judge_statistics'),

    path('users/', views.get_users, name='get_users'),
    path('users/<int:user_id>/update/', views.update_user, name='update_user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),

    path('officers/', views.officer_list, name='officer_list'),
    path('officers/create/', views.create_officer, name='create_officer'),
    path('officers/tickets/', views.get_all_officer_tickets, name='officer_detail'),

    path('ticket/', views.get_ticket, name='get_ticket'),
    path('tickets/issue/', views.issue_ticket, name='issue_ticket'),
    path('tickets/officer/', views.get_officer_tickets, name='officer_tickets'),
    path('tickets/search/', views.search_tickets, name='search_tickets'),
    path('tickets/lookup/', views.lookup_ticket, name='lookup_ticket'),
    path('tickets/all/', views.get_all_tickets, name='all_tickets'),
    path('tickets/all-officers/', views.get_all_officer_tickets, name='all_officer_tickets'),
    path('tickets/resolve/', views.resolve_ticket, name='resolve_ticket'),
    path('tickets/update-status/', views.update_ticket_status, name='update_ticket_status'),

    path('ticket-management/', views.ticket_management_view, name='ticket_management'),
    path('ticket-management/<int:ticket_id>/', views.ticket_management_view, name='ticket_management_detail'),

    path('analytics/', views.get_analytics_data, name='analytics'),

    path('defendants/', views.get_defendant_info, name='defendant_list'),

    path('audit-logs/', views.get_audit_logs, name='audit_log'),

    # NaTIS Admin Dashboard APIs
    path('natis/vehicle-lookup/', views.lookup_vehicle, name='vehicle_lookup'),
    path('natis/license-verify/', views.verify_driver_license, name='license_verify'),
    path('natis/payment/', views.process_payment, name='process_payment'),
    path('natis/reports/', views.generate_report, name='generate_report'),

    # Officer Dashboard APIs
    path('officer/dashboard/summary/', views.get_officer_dashboard_summary, name='officer_dashboard_summary'),
    path('officer/incidents/', views.get_traffic_incidents, name='traffic_incidents'),
    path('officer/incidents/create/', views.create_traffic_incident, name='create_traffic_incident'),
    path('officer/incidents/resolve/', views.resolve_traffic_incident, name='resolve_traffic_incident'),
    path('officer/missing-persons/', views.get_missing_persons, name='missing_persons'),
    path('officer/warrants/', views.get_warrants_of_arrest, name='warrants_of_arrest'),
    path('officer/news/', views.get_news, name='news'),
]
