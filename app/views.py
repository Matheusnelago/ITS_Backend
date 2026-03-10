from datetime import timedelta
from django.db.models import Count, Sum, Q
from django.http import JsonResponse
from rest_framework import viewsets, response
from .api.serializer import *
from .models import *

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from .api.permissions import IsNaTISAdmin
from rest_framework_simplejwt.tokens import RefreshToken

# JWT Authentication imports
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer

from django.contrib.auth import get_user_model


# Health check endpoint
@api_view(['GET', 'HEAD'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint for monitoring"""
    return JsonResponse({'status': 'ok'})

# Custom JWT Token serializer to include user role
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        # Add user role to the token response
        # First check if user is superuser - they get admin role
        if self.user.is_superuser:
            data['role'] = 'admin'
            data['is_superuser'] = True
        else:
            try:
                user_role = UserRole.objects.get(user=self.user)
                data['role'] = user_role.role
            except UserRole.DoesNotExist:
                data['role'] = 'officer'
            data['is_superuser'] = False
        data['username'] = self.user.username
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class CustomRefreshTokenSerializer(TokenRefreshSerializer):
    pass


class CustomRefreshTokenView(TokenRefreshView):
    serializer_class = CustomRefreshTokenSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    try:
        username = request.data.get('username')
        password = request.data.get('password')
        role = request.data.get('role', 'officer')  # Default role is officer

        if not username or not password:
            return JsonResponse({'error': 'Username and password are required'}, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)

        user = User.objects.create_user(username=username, password=password)
        UserRole.objects.create(user=user, role=role)

        return JsonResponse({'success': True, 'message': 'User registered successfully'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def is_authenticated(request):
    """Check if user is authenticated"""
    # Check for token in Authorization header
    auth_header = request.headers.get('Authorization', '')

    if auth_header.startswith('Bearer '):
        token = auth_header[7:]

        try:
            refresh = RefreshToken(token)
            user_id = refresh['user_id']
            User = get_user_model()
            user = User.objects.get(id=user_id)

            # Check if user is active
            if not user.is_active:
                return JsonResponse({
                    'authenticated': False,
                    'error': 'User account is disabled'
                })

            # Check if user is superuser
            is_superuser = user.is_superuser

            # Get user role - first try to get from UserRole model
            try:
                user_role = UserRole.objects.get(user=user)
                role = user_role.role
                is_active = user_role.is_active
            except UserRole.DoesNotExist:
                # If no UserRole, check if user is superuser
                if user.is_superuser:
                    role = 'admin'
                    is_active = True
                else:
                    role = 'officer'  # Default role
                    is_active = True

            return JsonResponse({
                'authenticated': True,
                'username': user.username,
                'role': role,
                'is_active': is_active,
                'is_superuser': is_superuser
            })
        except Exception as e:
            # Token validation failed, try session auth
            pass

    # Check session auth
    if request.user.is_authenticated:
        if not request.user.is_active:
            return JsonResponse({
                'authenticated': False,
                'error': 'User account is disabled'
            })

        # Check if user is superuser
        is_superuser = request.user.is_superuser

        try:
            user_role = UserRole.objects.get(user=request.user)
            role = user_role.role
            is_active = user_role.is_active
        except UserRole.DoesNotExist:
            # If no UserRole, check if user is superuser
            if request.user.is_superuser:
                role = 'admin'
                is_active = True
            else:
                role = 'officer'
                is_active = True

        return JsonResponse({
            'authenticated': True,
            'username': request.user.username,
            'role': role,
            'is_active': is_active,
            'is_superuser': is_superuser
        })

    return JsonResponse({'authenticated': False})


# REMOVED: Custom login function that conflicts with JWT
# The JWT endpoint at /api/login/ handles authentication properly
# Keeping this comment as reference for what was removed:
# @api_view(['POST'])
# @permission_classes([AllowAny])
# def login(request):
#     ... (removed - was not returning JWT tokens)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        # For JWT, logout is handled on the client side by deleting the token
        return JsonResponse({'success': True, 'message': 'Logout successful'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_officer(request):
    """Create a new officer with user account and role"""
    try:
        username = request.data.get('username')
        password = request.data.get('password')
        badge = request.data.get('badge')
        rank = request.data.get('rank', 'Officer')

        if not username or not password:
            return JsonResponse({'error': 'Username and password are required'}, status=400)

        if not badge:
            return JsonResponse({'error': 'Badge number is required'}, status=400)

        User = get_user_model()

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)

        # Check if badge already exists
        if Officer.objects.filter(badge=badge).exists():
            return JsonResponse({'error': 'Badge number already exists'}, status=400)

        # Create user
        user = User.objects.create_user(username=username, password=password)

        # Create UserRole with 'officer' role
        UserRole.objects.create(user=user, role='officer', is_active=True)

        # Create Officer profile
        officer = Officer.objects.create(user=user, badge=badge, rank=rank)

        # Create OfficerManagement record
        OfficerManagement.objects.create(
            officer=officer,
            name=username,
            badge=badge,
            role='officer',
            action='created',
            active=True
        )

        return JsonResponse({
            'success': True,
            'message': 'Officer created successfully',
            'officer_id': officer.id,
            'user_id': user.id
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user(request, user_id):
    """Delete a user (admin only)"""
    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
        user.delete()
        return JsonResponse({'success': True})
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_tickets(request):
    """Search tickets with filters"""
    query = request.GET.get('q', '')
    status = request.GET.get('status')

    tickets = Ticket.objects.all()

    if query:
        tickets = tickets.filter(
            Q(plate_no__icontains=query) |
            Q(ticket_issued__icontains=query)
        )

    if status:
        tickets = tickets.filter(status=status)

    serializer = TicketSerializer(tickets[:50], many=True)
    return JsonResponse({'success': True, 'data': serializer.data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_audit_logs(request):
    """
    Get audit logs for the Ministry dashboard.
    Returns system activity logs.
    """
    try:
        from .models import UserRole, AuditLog

        # Check if user has ministry role
        try:
            user_role = UserRole.objects.get(user=request.user)
            if user_role.role not in ['ministry', 'admin']:
                return JsonResponse({'error': 'Unauthorized - Ministry access required'}, status=403)
        except UserRole.DoesNotExist:
            return JsonResponse({'error': 'Unauthorized - No role assigned'}, status=403)

        # Get logs with optional filtering
        limit = int(request.GET.get('limit', 100))
        action_filter = request.GET.get('action', None)

        logs = AuditLog.objects.select_related('user', 'ticket').order_by('-timestamp')

        if action_filter:
            logs = logs.filter(action=action_filter)

        logs = logs[:limit]

        log_data = []
        for log in logs:
            log_data.append({
                'id': log.id,
                'action': log.action,
                'user': log.user.username if log.user else 'System',
                'ticket': log.ticket.ticket_issued if log.ticket else None,
                'timestamp': log.timestamp.isoformat(),
                'details': log.details
            })

        return JsonResponse({
            'success': True,
            'data': log_data
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def get_ticket(request):
    """Get ticket details by ticket ID"""
    if request.method == 'GET':
        ticket_id = request.GET.get('ticket_id')
    else:
        ticket_id = request.data.get('ticket_id')

    if not ticket_id:
        return JsonResponse({'error': 'Ticket ID required'}, status=400)

    try:
        ticket = Ticket.objects.get(ticket_issued=ticket_id)
        serializer = TicketSerializer(ticket)
        return JsonResponse(serializer.data)
    except Ticket.DoesNotExist:
        return JsonResponse({'error': 'Ticket not found'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def issue_ticket(request):
    """Issue a new ticket"""
    data = request.data

    # Get the Officer instance from the current user
    officer = None
    try:
        officer = Officer.objects.get(user=request.user)
    except Officer.DoesNotExist:
        # If user doesn't have an Officer profile, allow None
        pass

    try:
        ticket = Ticket.objects.create(
            plate_no=data.get('plate_no'),
            amount=data.get('amount', 0),
            vehicle_make=data.get('vehicle_make'),
            vehicle_model=data.get('vehicle_model'),
            vehicle_color=data.get('vehicle_color'),
            vehicle_year=data.get('vehicle_year'),
            location=data.get('location'),
            gps_coordinates=data.get('gps_coordinates'),
            road_number=data.get('road_number'),
            road_type=data.get('road_type'),
            region=data.get('region'),
            violation_type=data.get('violation_type', 'other'),
            violation_time=data.get('violation_time'),
            officer_notes=data.get('officer_notes'),
            officer=officer,
            status='pending'
        )

        return JsonResponse({
            'success': True,
            'ticket_id': ticket.id,
            'ticket_number': ticket.ticket_issued
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_ticket_attachment(request):
    """Add attachment to a ticket"""
    ticket_id = request.data.get('ticket_id')
    file = request.FILES.get('file')
    file_type = request.data.get('file_type', 'document')
    description = request.data.get('description', '')

    if not ticket_id or not file:
        return JsonResponse({'error': 'Ticket ID and file required'}, status=400)

    try:
        ticket = Ticket.objects.get(id=ticket_id)

        # Get the Officer instance
        officer = None
        try:
            officer = Officer.objects.get(user=request.user)
        except Officer.DoesNotExist:
            pass

        # Create the attachment
        attachment = TicketAttachment.objects.create(
            ticket=ticket,
            file=file,
            file_type=file_type,
            description=description,
            uploaded_by=officer
        )

        return JsonResponse({
            'success': True,
            'message': 'Attachment uploaded successfully',
            'attachment_id': str(attachment.id)
        })
    except Ticket.DoesNotExist:
        return JsonResponse({'error': 'Ticket not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def officer_list(request):
    """Get list of all officers"""
    # Get all OfficerManagement records with active=True
    officers = OfficerManagement.objects.filter(active=True)
    data = []
    for o in officers:
        data.append({
            'id': o.id,
            'name': o.name or (o.officer.user.username if o.officer else 'Unknown'),
            'badge': o.badge or (o.officer.badge if o.officer else ''),
            'role': o.role or 'officer'
        })
    return JsonResponse({'success': True, 'data': data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_officer_tickets(request):
    """Get tickets issued by the current officer"""
    # Get the Officer instance from the current user
    try:
        officer = Officer.objects.get(user=request.user)
        tickets = Ticket.objects.filter(officer=officer).order_by('-date')[:50]
    except Officer.DoesNotExist:
        tickets = Ticket.objects.none()

    serializer = TicketSerializer(tickets, many=True)
    return JsonResponse({'success': True, 'data': serializer.data})


@api_view(['GET'])
@permission_classes([AllowAny])
def lookup_ticket(request):
    """Lookup ticket by license plate or ticket number"""
    query = request.GET.get('q', '')

    if not query:
        return JsonResponse({'error': 'Search query required'}, status=400)

    tickets = Ticket.objects.filter(
        Q(plate_no__icontains=query) |
        Q(ticket_issued__icontains=query)
    )[:10]

    serializer = TicketSerializer(tickets, many=True)
    return JsonResponse({'success': True, 'data': serializer.data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_tickets(request):
    """Get all tickets (admin only)"""
    tickets = Ticket.objects.order_by('-date')[:100]
    serializer = TicketSerializer(tickets, many=True)
    return JsonResponse({'success': True, 'data': serializer.data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_officer_tickets(request):
    """Get all tickets from all officers"""
    tickets = Ticket.objects.exclude(officer__isnull=True).order_by('-date')[:100]
    serializer = TicketSerializer(tickets, many=True)
    return JsonResponse({'success': True, 'data': serializer.data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def schedule_court_date(request):
    """Schedule a court date for a ticket"""
    ticket_id = request.data.get('ticket_id')
    court_date = request.data.get('court_date')
    court_location = request.data.get('court_location')
    judge = request.data.get('judge', '')
    notes = request.data.get('notes', '')

    if not ticket_id or not court_date:
        return JsonResponse({'error': 'Ticket ID and court date required'}, status=400)

    try:
        ticket = Ticket.objects.get(id=ticket_id)

        # Create or update court date
        court_date_obj, created = CourtDate.objects.update_or_create(
            ticket=ticket,
            defaults={
                'scheduled_date': court_date,
                'location': court_location,
                'judge': judge,
                'notes': notes,
                'created_by': request.user
            }
        )

        # Update ticket status
        ticket.status = 'court'
        ticket.save()

        return JsonResponse({
            'success': True,
            'message': 'Court date scheduled successfully',
            'court_date_id': str(court_date_obj.id)
        })
    except Ticket.DoesNotExist:
        return JsonResponse({'error': 'Ticket not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def ticket_management_view(request):
    """
    Get all ticket management records or create/update a ticket management entry
    """
    if request.method == 'GET':
        try:
            # Get ticket ID filter if provided
            ticket_id = request.GET.get('ticket_id')

            if ticket_id:
                tm = TicketManagement.objects.get(ticket_id=ticket_id)
                serializer = TicketManagementSerializer(tm)
                return JsonResponse({'success': True, 'data': serializer.data})
            else:
                tm = TicketManagement.objects.select_related('ticket').all()
                data = []
                for t in tm:
                    data.append({
                        'id': t.id,
                        'ticket_id': t.ticket.id,
                        'ticket_number': t.ticket.ticket_issued,
                        'plate_no': t.ticket.plate_no,
                        'status': t.ticket.status,
                        'amount': float(t.ticket.amount) if t.ticket.amount else 0,
                        'resolution_notes': t.resolution_notes,
                        'resolved_at': t.resolved_at.isoformat() if t.resolved_at else None
                    })
                return JsonResponse({'success': True, 'data': data})
        except TicketManagement.DoesNotExist:
            return JsonResponse({'success': True, 'data': []})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    elif request.method == 'POST':
        ticket_id = request.data.get('ticket_id')
        resolution_notes = request.data.get('resolution_notes', '')

        if not ticket_id:
            return JsonResponse({'error': 'Ticket ID required'}, status=400)

        try:
            ticket = Ticket.objects.get(id=ticket_id)

            # Create or update ticket management
            tm, created = TicketManagement.objects.update_or_create(
                ticket=ticket,
                defaults={
                    'resolution_notes': resolution_notes
                }
            )

            return JsonResponse({
                'success': True,
                'message': 'Ticket management record updated',
                'data': {
                    'id': tm.id,
                    'ticket_id': ticket.id,
                    'resolution_notes': tm.resolution_notes
                }
            })
        except Ticket.DoesNotExist:
            return JsonResponse({'error': 'Ticket not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_ticket(request):
    """
    Resolve a ticket (mark as paid/closed)
    """
    ticket_id = request.data.get('ticket_id')
    resolution_notes = request.data.get('resolution_notes', '')
    new_status = request.data.get('status', 'closed')

    if not ticket_id:
        return JsonResponse({'error': 'Ticket ID required'}, status=400)

    try:
        from django.utils import timezone

        ticket = Ticket.objects.get(id=ticket_id)

        # Update ticket status
        ticket.status = new_status
        ticket.save()

        # Create or update ticket management
        tm, created = TicketManagement.objects.update_or_create(
            ticket=ticket,
            defaults={
                'resolution_notes': resolution_notes,
                'resolved_at': timezone.now()
            }
        )

        return JsonResponse({
            'success': True,
            'message': f'Ticket resolved successfully',
            'data': {
                'ticket_id': ticket.id,
                'ticket_number': ticket.ticket_issued,
                'new_status': new_status
            }
        })
    except Ticket.DoesNotExist:
        return JsonResponse({'error': 'Ticket not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_ticket_status(request):
    """
    Update ticket status (for disputed, court, overdue, etc.)
    """
    ticket_id = request.data.get('ticket_id')
    new_status = request.data.get('status')

    if not ticket_id or not new_status:
        return JsonResponse({'error': 'Ticket ID and status required'}, status=400)

    valid_statuses = ['pending', 'paid', 'overdue', 'disputed', 'court', 'closed']
    if new_status not in valid_statuses:
        return JsonResponse({'error': 'Invalid status'}, status=400)

    try:
        ticket = Ticket.objects.get(id=ticket_id)
        old_status = ticket.status
        ticket.status = new_status
        ticket.save()

        return JsonResponse({
            'success': True,
            'message': f'Ticket status updated from {old_status} to {new_status}',
            'data': {
                'ticket_id': ticket.id,
                'ticket_number': ticket.ticket_issued,
                'old_status': old_status,
                'new_status': new_status
            }
        })
    except Ticket.DoesNotExist:
        return JsonResponse({'error': 'Ticket not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ticket_management(request):
    ticket_management = TicketManagement.objects.all()
    serializer = TicketManagementSerializer(ticket_management, many=True)
    return response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_analytics_data(request):
    """
    Get analytics data for the Ministry dashboard.
    Returns aggregated statistics about tickets, revenue, and violations.
    """
    try:
        from .models import Ticket, UserRole

        # Check if user has ministry role
        try:
            user_role = UserRole.objects.get(user=request.user)
            if user_role.role not in ['ministry', 'admin']:
                return JsonResponse({'error': 'Unauthorized - Ministry access required'}, status=403)
        except UserRole.DoesNotExist:
            return JsonResponse({'error': 'Unauthorized - No role assigned'}, status=403)

        # Get date range from query params (default: last 30 days)
        days = int(request.GET.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)

        # Aggregate ticket statistics
        total_tickets = Ticket.objects.count()
        recent_tickets = Ticket.objects.filter(date__gte=start_date).count()

        # Revenue statistics
        total_revenue = Ticket.objects.aggregate(total=Sum('amount'))['total'] or 0
        recent_revenue = Ticket.objects.filter(date__gte=start_date).aggregate(total=Sum('amount'))['total'] or 0

        # Status breakdown
        status_counts = Ticket.objects.values('status').annotate(count=Count('id'))

        # Violation type breakdown
        violation_counts = Ticket.objects.values('violation_type').annotate(count=Count('id'))

        # Region breakdown
        region_counts = Ticket.objects.exclude(region__isnull=True).exclude(region='').values('region').annotate(count=Count('id'))

        # Monthly trends (last 6 months)
        monthly_data = []
        for i in range(5, -1, -1):
            month_start = timezone.now().replace(day=1) - timedelta(days=i*30)
            month_end = month_start + timedelta(days=30)
            month_tickets = Ticket.objects.filter(date__gte=month_start, date__lt=month_end).count()
            month_revenue = Ticket.objects.filter(date__gte=month_start, date__lt=month_end).aggregate(total=Sum('amount'))['total'] or 0
            monthly_data.append({
                'month': month_start.strftime('%b'),
                'tickets': month_tickets,
                'revenue': float(month_revenue)
            })

        # Top performing officers
        most_tickets_issued_officers = []
        officer_tickets = Ticket.objects.exclude(officer__isnull=True).values(
            'officer__user__username'
        ).annotate(
            ticket_count=Count('id'),
            total_revenue=Sum('amount')
        ).order_by('-ticket_count')[:5]

        for officer in officer_tickets:
            most_tickets_issued_officers.append({
                'name': officer['officer__user__username'] or 'Unknown',
                'tickets': officer['ticket_count'],
                'revenue': float(officer['total_revenue'] or 0)
            })

        # Pending court cases
        pending_court = Ticket.objects.filter(status='court').count()

        # Resolved cases
        resolved = Ticket.objects.filter(status='paid').count()

        return JsonResponse({
            'success': True,
            'data': {
                'total_tickets': total_tickets,
                'recent_tickets': recent_tickets,
                'total_revenue': float(total_revenue),
                'recent_revenue': float(recent_revenue),
                'pending_court': pending_court,
                'resolved_cases': resolved,
                'status_breakdown': list(status_counts),
                'violation_breakdown': list(violation_counts),
                'region_breakdown': list(region_counts),
                'monthly_trends': monthly_data,
                'total tickets per officer': most_tickets_issued_officers
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_users(request):
    """Get all users (admin only)"""
    from django.contrib.auth import get_user_model
    from .models import UserRole
    User = get_user_model()

    users = User.objects.all()[:50]
    data = []
    for u in users:
        # Get user role
        role = 'officer'  # default role
        try:
            user_role = UserRole.objects.get(user=u)
            role = user_role.role
        except UserRole.DoesNotExist:
            # Check if superuser
            if u.is_superuser:
                role = 'admin'

        data.append({
            'id': u.id,
            'username': u.username,
            'email': u.email or '',
            'is_active': u.is_active,
            'role': role
        })

    return JsonResponse({'success': True, 'data': data})


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user(request, user_id):
    """Update a user (admin only)"""
    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)

        if 'badge' in request.data:
            try:
                officer = Officer.objects.get(user=user)
            except Officer.DoesNotExist:
                officer = Officer.objects.create(user=user, badge=request.data['badge'])

            try:
                officer_mgmt = OfficerManagement.objects.get(officer=officer)
            except OfficerManagement.DoesNotExist:
                officer_mgmt = OfficerManagement.objects.create(officer=officer)

            officer_mgmt.name = user.username
            officer_mgmt.role = request.data.get('role', officer_mgmt.role)
            officer_mgmt.save()

        if 'role' in request.data:
            user_role, _ = UserRole.objects.get_or_create(user=user)
            user_role.role = request.data['role']
            user_role.save()

        if 'is_active' in request.data:
            user.is_active = request.data['is_active']
            user.save()

        return JsonResponse({'success': True})
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_defendant_info(request):
    """Get defendant/driver contact information for the current user"""
    try:
        # Try to get defendant info by user
        defendant = Defendant.objects.get(user=request.user)
        return JsonResponse({
            'success': True,
            'contact': {
                'phone_number': defendant.phone_number or '',
                'alt_phone': defendant.alt_phone or '',
                'email': defendant.email or '',
                'physical_address': defendant.physical_address or '',
                'city': defendant.city or '',
                'postal_code': defendant.postal_code or '',
                'email_enabled': defendant.email_enabled,
                'sms_enabled': defendant.sms_enabled,
                'preferred_method': defendant.preferred_method
            }
        })
    except Defendant.DoesNotExist:
        # Return default values if no defendant record exists
        return JsonResponse({
            'success': True,
            'contact': {
                'phone_number': '',
                'alt_phone': '',
                'email': '',
                'physical_address': '',
                'city': '',
                'postal_code': '',
                'email_enabled': True,
                'sms_enabled': True,
                'preferred_method': 'all'
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ======================
# Judge Dashboard API
# ======================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_judge_cases(request):
    """
    Get all cases for the judge dashboard.
    Returns tickets with court status.
    """
    try:
        # Get all tickets that are in court or disputed status
        status_filter = request.GET.get('status', 'court')

        if status_filter == 'all':
            tickets = Ticket.objects.filter(
                Q(status='court') | Q(status='disputed') | Q(status='pending')
            ).order_by('-date')
        else:
            tickets = Ticket.objects.filter(status=status_filter).order_by('-date')

        cases = []
        for ticket in tickets:
            # Get defendant info if exists
            defendant_info = None
            try:
                defendant = Defendant.objects.filter(
                    Q(id_no__icontains=ticket.plate_no[-4:]) |
                    Q(license_no__icontains=ticket.plate_no[-4:])
                ).first()
                if defendant:
                    defendant_info = {
                        'firstname': defendant.firstname,
                        'lastname': defendant.lastname,
                        'id_no': defendant.id_no,
                        'phone_number': defendant.phone_number,
                        'email': defendant.email
                    }
            except:
                pass

            # Get court date if exists
            court_date = None
            try:
                cd = ticket.court_date
                court_date = {
                    'scheduled_date': cd.scheduled_date.isoformat() if cd.scheduled_date else None,
                    'location': cd.location,
                    'notes': cd.notes
                }
            except:
                pass

            cases.append({
                'id': ticket.id,
                'ticket_number': ticket.ticket_issued,
                'plate_no': ticket.plate_no,
                'violation_type': ticket.violation_type,
                'amount': float(ticket.amount) if ticket.amount else 0,
                'status': ticket.status,
                'date': ticket.date.isoformat() if ticket.date else None,
                'location': ticket.location,
                'officer_notes': ticket.officer_notes,
                'defendant': defendant_info,
                'court_date': court_date
            })

        return JsonResponse({
            'success': True,
            'data': cases
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_judge_case_detail(request, case_id):
    """
    Get detailed information about a specific case.
    """
    try:
        ticket = Ticket.objects.get(id=case_id)

        # Get defendant info
        defendant_info = None
        try:
            defendant = Defendant.objects.filter(
                Q(id_no__icontains=ticket.plate_no[-4:]) |
                Q(license_no__icontains=ticket.plate_no[-4:])
            ).first()
            if defendant:
                defendant_info = {
                    'firstname': defendant.firstname,
                    'lastname': defendant.lastname,
                    'id_no': defendant.id_no,
                    'license_no': defendant.license_no,
                    'phone_number': defendant.phone_number,
                    'alt_phone': defendant.alt_phone,
                    'email': defendant.email,
                    'physical_address': defendant.physical_address,
                    'city': defendant.city
                }
        except:
            pass

        # Get court date
        court_date = None
        try:
            cd = ticket.court_date
            court_date = {
                'id': cd.id,
                'scheduled_date': cd.scheduled_date.isoformat() if cd.scheduled_date else None,
                'location': cd.location,
                'notes': cd.notes
            }
        except:
            pass

        # Get officer info
        officer_info = None
        if ticket.officer:
            officer_info = {
                'badge': ticket.officer.badge,
                'rank': ticket.officer.rank,
                'username': ticket.officer.user.username
            }

        return JsonResponse({
            'success': True,
            'data': {
                'id': ticket.id,
                'ticket_number': ticket.ticket_issued,
                'plate_no': ticket.plate_no,
                'vehicle_make': ticket.vehicle_make,
                'vehicle_model': ticket.vehicle_model,
                'vehicle_color': ticket.vehicle_color,
                'vehicle_year': ticket.vehicle_year,
                'violation_type': ticket.violation_type,
                'amount': float(ticket.amount) if ticket.amount else 0,
                'status': ticket.status,
                'date': ticket.date.isoformat() if ticket.date else None,
                'location': ticket.location,
                'gps_coordinates': ticket.gps_coordinates,
                'road_number': ticket.road_number,
                'road_type': ticket.road_type,
                'region': ticket.region,
                'officer_notes': ticket.officer_notes,
                'violation_time': ticket.violation_time.isoformat() if ticket.violation_time else None,
                'defendant': defendant_info,
                'court_date': court_date,
                'officer': officer_info
            }
        })

    except Ticket.DoesNotExist:
        return JsonResponse({'error': 'Case not found'}, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_case_judgment(request):
    """
    Update case judgment/ruling.
    """
    case_id = request.data.get('case_id')
    judgment = request.data.get('judgment', '')
    ruling = request.data.get('ruling', '')  # guilty, not_guilty, adjourned, dismissed
    new_status = request.data.get('status', 'closed')

    if not case_id:
        return JsonResponse({'error': 'Case ID required'}, status=400)

    try:
        ticket = Ticket.objects.get(id=case_id)

        # Update court date with judgment
        try:
            court_date = ticket.court_date
            court_date.notes = (court_date.notes or '') + f"\n\nJudgment: {judgment}\nRuling: {ruling}"
            court_date.save()
        except CourtDate.DoesNotExist:
            # Create court date record if not exists
            CourtDate.objects.create(
                ticket=ticket,
                scheduled_date=timezone.now(),
                location='Court',
                notes=f"Judgment: {judgment}\nRuling: {ruling}"
            )

        # Update ticket status
        ticket.status = new_status
        ticket.save()

        return JsonResponse({
            'success': True,
            'message': 'Judgment recorded successfully'
        })

    except Ticket.DoesNotExist:
        return JsonResponse({'error': 'Case not found'}, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_judge_calendar(request):
    """
    Get calendar events for the judge.
    Returns all court dates.
    """
    try:
        # Get date range
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')

        court_dates = CourtDate.objects.select_related('ticket', 'judge').order_by('scheduled_date')

        if from_date:
            court_dates = court_dates.filter(scheduled_date__gte=from_date)
        if to_date:
            court_dates = court_dates.filter(scheduled_date__lte=to_date)

        events = []
        for cd in court_dates:
            # Get ticket info
            ticket = cd.ticket

            # Determine color based on status
            color = '#3B82F6'  # blue - default
            if ticket.status == 'court':
                color = '#F59E0B'  # amber - pending
            elif ticket.status == 'closed':
                color = '#10B981'  # green - resolved
            elif ticket.status == 'disputed':
                color = '#EF4444'  # red - disputed

            events.append({
                'id': cd.id,
                'title': f"{ticket.ticket_issued} - {ticket.plate_no}",
                'date': cd.scheduled_date.isoformat() if cd.scheduled_date else None,
                'location': cd.location,
                'status': ticket.status,
                'violation_type': ticket.violation_type,
                'plate_no': ticket.plate_no,
                'color': color,
                'notes': cd.notes
            })

        return JsonResponse({
            'success': True,
            'data': events
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def schedule_judge_court_date(request):
    """
    Schedule or update a court date for a case.
    """
    ticket_id = request.data.get('ticket_id')
    scheduled_date = request.data.get('scheduled_date')
    location = request.data.get('location', 'Court')
    notes = request.data.get('notes', '')

    if not ticket_id or not scheduled_date:
        return JsonResponse({'error': 'Ticket ID and scheduled date required'}, status=400)

    try:
        ticket = Ticket.objects.get(id=ticket_id)

        # Create or update court date
        court_date, created = CourtDate.objects.update_or_create(
            ticket=ticket,
            defaults={
                'scheduled_date': scheduled_date,
                'location': location,
                'notes': notes,
                'created_by': request.user
            }
        )

        # Update ticket status to court
        ticket.status = 'court'
        ticket.save()

        return JsonResponse({
            'success': True,
            'message': 'Court date scheduled successfully',
            'data': {
                'id': court_date.id,
                'scheduled_date': court_date.scheduled_date.isoformat(),
                'location': court_date.location
            }
        })

    except Ticket.DoesNotExist:
        return JsonResponse({'error': 'Ticket not found'}, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_judge_statistics(request):
    """
    Get statistics for the judge dashboard.
    """
    try:
        total_cases = Ticket.objects.filter(
            Q(status='court') | Q(status='disputed') | Q(status='closed')
        ).count()

        pending_court = Ticket.objects.filter(status='court').count()
        disputed = Ticket.objects.filter(status='disputed').count()
        resolved = Ticket.objects.filter(status='closed').count()

        # Upcoming court dates
        upcoming = CourtDate.objects.filter(
            scheduled_date__gte=timezone.now()
        ).count()

        # This month
        from datetime import datetime
        start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0)
        this_month = Ticket.objects.filter(
            Q(status='court') | Q(status='disputed'),
            date__gte=start_of_month
        ).count()

        return JsonResponse({
            'success': True,
            'data': {
                'total_cases': total_cases,
                'pending_court': pending_court,
                'disputed': disputed,
                'resolved': resolved,
                'upcoming hearings': upcoming,
                'this_month': this_month
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ======================
# NaTIS Admin Dashboard APIs
# ======================

@api_view(['GET'])
@permission_classes([IsNaTISAdmin])
def lookup_vehicle(request):
    """
    Lookup vehicle by plate number.
    Returns vehicle information and associated tickets.
    """
    plate_number = request.GET.get('plate_no', '').strip().upper()

    if not plate_number:
        return JsonResponse({'error': 'Plate number required'}, status=400)

    try:
        # Find tickets associated with this plate number
        tickets = Ticket.objects.filter(plate_no__iexact=plate_number).order_by('-date')

        if not tickets.exists():
            return JsonResponse({
                'success': True,
                'data': {
                    'found': False,
                    'message': 'No records found for this vehicle',
                    'plate_no': plate_number
                }
            })

        # Get vehicle info from most recent ticket
        latest_ticket = tickets.first()

        # Get all tickets for this vehicle
        ticket_list = []
        for ticket in tickets:
            ticket_list.append({
                'id': ticket.id,
                'ticket_number': ticket.ticket_issued,
                'date': ticket.date.isoformat() if ticket.date else None,
                'violation_type': ticket.violation_type,
                'amount': float(ticket.amount) if ticket.amount else 0,
                'status': ticket.status,
                'location': ticket.location,
                'officer': ticket.officer.user.username if ticket.officer else 'Unknown'
            })

        # Calculate totals
        total_fines = sum(t['amount'] for t in ticket_list)
        paid_fines = sum(t['amount'] for t in ticket_list if t['status'] == 'paid')
        pending_fines = sum(t['amount'] for t in ticket_list if t['status'] in ['pending', 'overdue'])

        return JsonResponse({
            'success': True,
            'data': {
                'found': True,
                'plate_no': plate_number,
                'vehicle': {
                    'make': latest_ticket.vehicle_make,
                    'model': latest_ticket.vehicle_model,
                    'color': latest_ticket.vehicle_color,
                    'year': latest_ticket.vehicle_year
                },
                'tickets': ticket_list,
                'summary': {
                    'total_tickets': len(ticket_list),
                    'total_fines': total_fines,
                    'paid_fines': paid_fines,
                    'pending_fines': pending_fines
                }
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsNaTISAdmin])
def verify_driver_license(request):
    """
    Verify driver license by license number or ID number.
    Returns driver information and any associated tickets.
    """
    license_no = request.GET.get('license_no', '').strip().upper()
    id_no = request.GET.get('id_no', '').strip()

    if not license_no and not id_no:
        return JsonResponse({'error': 'License number or ID number required'}, status=400)

    try:
        # Search for defendant by license number or ID number
        defendant = None

        if license_no:
            defendant = Defendant.objects.filter(license_no__iexact=license_no).first()

        if not defendant and id_no:
            defendant = Defendant.objects.filter(id_no__iexact=id_no).first()

        if not defendant:
            return JsonResponse({
                'success': True,
                'data': {
                    'found': False,
                    'message': 'No driver record found',
                    'license_no': license_no,
                    'id_no': id_no
                }
            })

        # Get associated tickets (searching by matching patterns)
        tickets = Ticket.objects.filter(
            Q(plate_no__icontains=defendant.id_no[-4:] if defendant.id_no else '') |
            Q(plate_no__icontains=defendant.license_no[-4:] if defendant.license_no else '')
        ).order_by('-date')[:10]

        ticket_list = []
        for ticket in tickets:
            ticket_list.append({
                'id': ticket.id,
                'ticket_number': ticket.ticket_issued,
                'plate_no': ticket.plate_no,
                'date': ticket.date.isoformat() if ticket.date else None,
                'violation_type': ticket.violation_type,
                'amount': float(ticket.amount) if ticket.amount else 0,
                'status': ticket.status,
                'location': ticket.location
            })

        return JsonResponse({
            'success': True,
            'data': {
                'found': True,
                'driver': {
                    'id': defendant.id,
                    'firstname': defendant.firstname,
                    'lastname': defendant.lastname,
                    'id_no': defendant.id_no,
                    'license_no': defendant.license_no,
                    'phone_number': defendant.phone_number,
                    'email': defendant.email,
                    'city': defendant.city,
                    'physical_address': defendant.physical_address
                },
                'tickets': ticket_list
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([IsNaTISAdmin])
def process_payment(request):
    """
    Process payment for a traffic fine.
    Updates ticket status to 'paid'.
    """
    ticket_id = request.data.get('ticket_id')
    payment_method = request.data.get('payment_method', 'cash')
    reference_number = request.data.get('reference_number', '')
    amount_paid = request.data.get('amount_paid', 0)

    if not ticket_id:
        return JsonResponse({'error': 'Ticket ID required'}, status=400)

    try:
        ticket = Ticket.objects.get(id=ticket_id)

        if ticket.status == 'paid':
            return JsonResponse({
                'success': False,
                'error': 'Ticket already paid'
            }, status=400)

        # Update ticket status to paid
        ticket.status = 'paid'
        ticket.save()

        # Create audit log
        AuditLog.objects.create(
            action='ticket_paid',
            user=request.user,
            ticket=ticket,
            details=f"Payment processed via {payment_method}. Reference: {reference_number}. Amount: ${amount_paid}"
        )

        return JsonResponse({
            'success': True,
            'message': 'Payment processed successfully',
            'data': {
                'ticket_id': ticket.id,
                'ticket_number': ticket.ticket_issued,
                'amount_paid': float(amount_paid),
                'payment_method': payment_method,
                'reference_number': reference_number,
                'status': 'paid'
            }
        })

    except Ticket.DoesNotExist:
        return JsonResponse({'error': 'Ticket not found'}, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsNaTISAdmin])
def generate_report(request):
    """
    Generate various reports for NaTIS dashboard.
    Supports: traffic_summary, payment_report, violation_report, region_report
    """
    report_type = request.GET.get('type', 'traffic_summary')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    try:
        from django.utils.dateparse import parse_date

        # Base queryset
        tickets = Ticket.objects.all()

        # Apply date filters if provided
        if date_from:
            from_date = parse_date(date_from)
            if from_date:
                tickets = tickets.filter(date__date__gte=from_date)

        if date_to:
            to_date = parse_date(date_to)
            if to_date:
                tickets = tickets.filter(date__date__lte=to_date)

        if report_type == 'traffic_summary':
            # Summary of all traffic data
            total_tickets = tickets.count()
            total_revenue = tickets.aggregate(total=Sum('amount'))['total'] or 0

            # Status breakdown
            status_data = tickets.values('status').annotate(count=Count('id'))

            # Top violations
            violation_data = tickets.values('violation_type').annotate(count=Count('id')).order_by('-count')[:10]

            # Monthly trends
            monthly = []
            for i in range(5, -1, -1):
                month_start = timezone.now().replace(day=1) - timedelta(days=i*30)
                month_end = month_start + timedelta(days=30)
                month_tickets = tickets.filter(date__gte=month_start, date__lt=month_end).count()
                month_revenue = tickets.filter(date__gte=month_start, date__lt=month_end).aggregate(total=Sum('amount'))['total'] or 0
                monthly.append({
                    'month': month_start.strftime('%b %Y'),
                    'tickets': month_tickets,
                    'revenue': float(month_revenue)
                })

            return JsonResponse({
                'success': True,
                'data': {
                    'report_type': 'traffic_summary',
                    'total_tickets': total_tickets,
                    'total_revenue': float(total_revenue),
                    'status_breakdown': list(status_data),
                    'top_violations': list(violation_data),
                    'monthly_trends': monthly
                }
            })

        elif report_type == 'payment_report':
            # Payment/revenue report
            paid_tickets = tickets.filter(status='paid')
            pending_tickets = tickets.filter(status='pending')
            overdue_tickets = tickets.filter(status='overdue')

            paid_total = paid_tickets.aggregate(total=Sum('amount'))['total'] or 0
            pending_total = pending_tickets.aggregate(total=Sum('amount'))['total'] or 0
            overdue_total = overdue_tickets.aggregate(total=Sum('amount'))['total'] or 0

            # Recent payments
            recent_payments = paid_tickets.order_by('-date')[:20]
            payment_list = []
            for t in recent_payments:
                payment_list.append({
                    'ticket_number': t.ticket_issued,
                    'plate_no': t.plate_no,
                    'amount': float(t.amount) if t.amount else 0,
                    'date': t.date.isoformat() if t.date else None,
                    'officer': t.officer.user.username if t.officer else 'Unknown'
                })

            return JsonResponse({
                'success': True,
                'data': {
                    'report_type': 'payment_report',
                    'paid': {
                        'count': paid_tickets.count(),
                        'total': float(paid_total)
                    },
                    'pending': {
                        'count': pending_tickets.count(),
                        'total': float(pending_total)
                    },
                    'overdue': {
                        'count': overdue_tickets.count(),
                        'total': float(overdue_total)
                    },
                    'recent_payments': payment_list
                }
            })

        elif report_type == 'violation_report':
            # Violation type report
            violation_data = tickets.values('violation_type').annotate(
                count=Count('id'),
                total_amount=Sum('amount')
            ).order_by('-count')

            return JsonResponse({
                'success': True,
                'data': {
                    'report_type': 'violation_report',
                    'violations': [{
                        'type': v['violation_type'],
                        'count': v['count'],
                        'total_amount': float(v['total_amount'] or 0)
                    } for v in violation_data]
                }
            })

        elif report_type == 'region_report':
            # Region-based report
            region_data = tickets.exclude(region__isnull=True).exclude(region='').values(
                'region'
            ).annotate(
                count=Count('id'),
                total_amount=Sum('amount')
            ).order_by('-count')

            return JsonResponse({
                'success': True,
                'data': {
                    'report_type': 'region_report',
                    'regions': [{
                        'region': r['region'],
                        'count': r['count'],
                        'total_amount': float(r['total_amount'] or 0)
                    } for r in region_data]
                }
            })

        else:
            return JsonResponse({'error': 'Invalid report type'}, status=400)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ======================
# NaTIS Vehicle & Driver Registration APIs
# ======================

@api_view(['POST'])
@permission_classes([IsNaTISAdmin])
def register_driver(request):
    """
    Register a new driver in the NaTIS system.
    Creates or updates a Defendant record.
    """
    try:
        # Required fields
        firstname = request.data.get('firstname')
        lastname = request.data.get('lastname')
        id_no = request.data.get('id_no')

        # Optional fields
        license_no = request.data.get('license_no', '')
        phone_number = request.data.get('phone_number', '')
        alt_phone = request.data.get('alt_phone', '')
        email = request.data.get('email', '')
        physical_address = request.data.get('physical_address', '')
        city = request.data.get('city', '')
        postal_code = request.data.get('postal_code', '')

        # Validation
        if not firstname or not lastname:
            return JsonResponse({'error': 'First name and last name are required'}, status=400)

        if not id_no:
            return JsonResponse({'error': 'ID number is required'}, status=400)

        # Check if driver with same ID already exists
        existing_driver = Defendant.objects.filter(id_no__iexact=id_no).first()
        if existing_driver:
            return JsonResponse({
                'success': False,
                'error': 'A driver with this ID number already exists',
                'driver_id': existing_driver.id
            }, status=400)

        # Check if license number already exists (if provided)
        if license_no:
            existing_license = Defendant.objects.filter(license_no__iexact=license_no).first()
            if existing_license:
                return JsonResponse({
                    'success': False,
                    'error': 'A driver with this license number already exists',
                    'driver_id': existing_license.id
                }, status=400)

        # Create new driver
        driver = Defendant.objects.create(
            firstname=firstname,
            lastname=lastname,
            id_no=id_no,
            license_no=license_no if license_no else None,
            phone_number=phone_number if phone_number else None,
            alt_phone=alt_phone if alt_phone else None,
            email=email if email else None,
            physical_address=physical_address if physical_address else None,
            city=city if city else None,
            postal_code=postal_code if postal_code else None,
            email_enabled=True,
            sms_enabled=True,
            preferred_method='all'
        )

        # Create audit log
        AuditLog.objects.create(
            action='driver_registered',
            user=request.user,
            details=f"Driver registered: {firstname} {lastname} (ID: {id_no})"
        )

        return JsonResponse({
            'success': True,
            'message': 'Driver registered successfully',
            'driver': {
                'id': driver.id,
                'firstname': driver.firstname,
                'lastname': driver.lastname,
                'id_no': driver.id_no,
                'license_no': driver.license_no,
                'phone_number': driver.phone_number,
                'email': driver.email,
                'city': driver.city
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([IsNaTISAdmin])
def register_vehicle(request):
    """
    Register a new vehicle in the NaTIS system.
    Requires an existing driver/owner.
    """
    try:
        # Required fields
        plate_no = request.data.get('plate_no', '').strip().upper()
        vin = request.data.get('vin', '').strip().upper()
        vehicle_make = request.data.get('vehicle_make')
        vehicle_model = request.data.get('vehicle_model')
        vehicle_color = request.data.get('vehicle_color')
        vehicle_year = request.data.get('vehicle_year')
        owner_id = request.data.get('owner_id')

        # Optional fields
        engine_no = request.data.get('engine_no', '')
        vehicle_type = request.data.get('vehicle_type', 'sedan')
        fuel_type = request.data.get('fuel_type', 'petrol')
        registration_expiry = request.data.get('registration_expiry')
        roadworthy_cert_no = request.data.get('roadworthy_cert_no', '')
        roadworthy_expiry = request.data.get('roadworthy_expiry', '')
        insurance_company = request.data.get('insurance_company', '')
        insurance_policy_no = request.data.get('insurance_policy_no', '')
        insurance_expiry = request.data.get('insurance_expiry', '')
        seating_capacity = request.data.get('seating_capacity', 5)
        gross_vehicle_mass = request.data.get('gross_vehicle_mass')
        tare_mass = request.data.get('tare_mass')

        # Validation
        if not plate_no:
            return JsonResponse({'error': 'Plate number is required'}, status=400)

        if not vin:
            return JsonResponse({'error': 'VIN (Vehicle Identification Number) is required'}, status=400)

        if not vehicle_make or not vehicle_model:
            return JsonResponse({'error': 'Vehicle make and model are required'}, status=400)

        if not owner_id:
            return JsonResponse({'error': 'Owner ID is required'}, status=400)

        # Check if vehicle with same plate already exists
        existing_vehicle = Vehicle.objects.filter(plate_no__iexact=plate_no).first()
        if existing_vehicle:
            return JsonResponse({
                'success': False,
                'error': 'A vehicle with this plate number already exists',
                'vehicle_id': existing_vehicle.id
            }, status=400)

        # Check if vehicle with same VIN already exists
        existing_vin = Vehicle.objects.filter(vin__iexact=vin).first()
        if existing_vin:
            return JsonResponse({
                'success': False,
                'error': 'A vehicle with this VIN already exists',
                'vehicle_id': existing_vin.id
            }, status=400)

        # Check if owner exists
        try:
            owner = Defendant.objects.get(id=owner_id)
        except Defendant.DoesNotExist:
            return JsonResponse({'error': 'Owner not found'}, status=404)

        # Parse dates
        from django.utils.dateparse import parse_date
        reg_expiry = parse_date(registration_expiry) if registration_expiry else None
        rw_expiry = parse_date(roadworthy_expiry) if roadworthy_expiry else None
        ins_expiry = parse_date(insurance_expiry) if insurance_expiry else None

        # Create new vehicle
        vehicle = Vehicle.objects.create(
            plate_no=plate_no,
            vin=vin,
            engine_no=engine_no if engine_no else None,
            vehicle_make=vehicle_make,
            vehicle_model=vehicle_model,
            vehicle_color=vehicle_color,
            vehicle_year=vehicle_year,
            vehicle_type=vehicle_type,
            fuel_type=fuel_type,
            registration_expiry=reg_expiry,
            roadworthy_cert_no=roadworthy_cert_no if roadworthy_cert_no else None,
            roadworthy_expiry=rw_expiry,
            insurance_company=insurance_company if insurance_company else None,
            insurance_policy_no=insurance_policy_no if insurance_policy_no else None,
            insurance_expiry=ins_expiry,
            owner=owner,
            seating_capacity=seating_capacity,
            gross_vehicle_mass=gross_vehicle_mass,
            tare_mass=tare_mass,
            status='registered',
            is_active=True
        )

        # Create audit log
        AuditLog.objects.create(
            action='vehicle_registered',
            user=request.user,
            details=f"Vehicle registered: {plate_no} - {vehicle_year} {vehicle_make} {vehicle_model}"
        )

        return JsonResponse({
            'success': True,
            'message': 'Vehicle registered successfully',
            'vehicle': {
                'id': vehicle.id,
                'plate_no': vehicle.plate_no,
                'vin': vehicle.vin,
                'vehicle_make': vehicle.vehicle_make,
                'vehicle_model': vehicle.vehicle_model,
                'vehicle_color': vehicle.vehicle_color,
                'vehicle_year': vehicle.vehicle_year,
                'vehicle_type': vehicle.vehicle_type,
                'owner': {
                    'id': owner.id,
                    'name': f"{owner.firstname} {owner.lastname}"
                }
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsNaTISAdmin])
def get_drivers(request):
    """
    Get list of all registered drivers.
    Supports search by name, ID number, or license number.
    """
    try:
        query = request.GET.get('q', '')

        drivers = Defendant.objects.all()

        if query:
            drivers = drivers.filter(
                Q(firstname__icontains=query) |
                Q(lastname__icontains=query) |
                Q(id_no__icontains=query) |
                Q(license_no__icontains=query)
            )

        drivers = drivers.order_by('-id')[:100]

        driver_list = []
        for driver in drivers:
            # Get vehicle count for this driver
            vehicle_count = Vehicle.objects.filter(owner=driver).count()

            driver_list.append({
                'id': driver.id,
                'firstname': driver.firstname,
                'lastname': driver.lastname,
                'id_no': driver.id_no,
                'license_no': driver.license_no,
                'phone_number': driver.phone_number,
                'email': driver.email,
                'city': driver.city,
                'physical_address': driver.physical_address,
                'vehicle_count': vehicle_count
            })

        return JsonResponse({
            'success': True,
            'data': driver_list
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsNaTISAdmin])
def get_vehicles(request):
    """
    Get list of all registered vehicles.
    Supports search by plate number, VIN, or owner name.
    """
    try:
        query = request.GET.get('q', '')
        status = request.GET.get('status', '')

        vehicles = Vehicle.objects.select_related('owner').all()

        if query:
            vehicles = vehicles.filter(
                Q(plate_no__icontains=query) |
                Q(vin__icontains=query) |
                Q(vehicle_make__icontains=query) |
                Q(vehicle_model__icontains=query) |
                Q(owner__firstname__icontains=query) |
                Q(owner__lastname__icontains=query)
            )

        if status:
            vehicles = vehicles.filter(status=status)

        vehicles = vehicles.order_by('-registration_date')[:100]

        vehicle_list = []
        for vehicle in vehicles:
            vehicle_list.append({
                'id': vehicle.id,
                'plate_no': vehicle.plate_no,
                'vin': vehicle.vin,
                'engine_no': vehicle.engine_no,
                'vehicle_make': vehicle.vehicle_make,
                'vehicle_model': vehicle.vehicle_model,
                'vehicle_color': vehicle.color,
                'vehicle_year': vehicle.vehicle_year,
                'vehicle_type': vehicle.vehicle_type,
                'fuel_type': vehicle.fuel_type,
                'registration_expiry': vehicle.registration_expiry.isoformat() if vehicle.registration_expiry else None,
                'roadworthy_expiry': vehicle.roadworthy_expiry.isoformat() if vehicle.roadworthy_expiry else None,
                'insurance_expiry': vehicle.insurance_expiry.isoformat() if vehicle.insurance_expiry else None,
                'status': vehicle.status,
                'is_active': vehicle.is_active,
                'owner': {
                    'id': vehicle.owner.id,
                    'name': f"{vehicle.owner.firstname} {vehicle.owner.lastname}",
                    'id_no': vehicle.owner.id_no,
                    'license_no': vehicle.owner.license_no
                } if vehicle.owner else None
            })

        return JsonResponse({
            'success': True,
            'data': vehicle_list
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsNaTISAdmin])
def get_driver_by_id(request, driver_id):
    """
    Get detailed information about a specific driver.
    """
    try:
        driver = Defendant.objects.get(id=driver_id)

        # Get all vehicles owned by this driver
        vehicles = Vehicle.objects.filter(owner=driver)

        vehicle_list = []
        for vehicle in vehicles:
            vehicle_list.append({
                'id': vehicle.id,
                'plate_no': vehicle.plate_no,
                'vehicle_make': vehicle.vehicle_make,
                'vehicle_model': vehicle.vehicle_model,
                'vehicle_color': vehicle.vehicle_color,
                'vehicle_year': vehicle.vehicle_year,
                'status': vehicle.status
            })

        return JsonResponse({
            'success': True,
            'data': {
                'id': driver.id,
                'firstname': driver.firstname,
                'lastname': driver.lastname,
                'id_no': driver.id_no,
                'license_no': driver.license_no,
                'phone_number': driver.phone_number,
                'alt_phone': driver.alt_phone,
                'email': driver.email,
                'physical_address': driver.physical_address,
                'city': driver.city,
                'postal_code': driver.postal_code,
                'vehicles': vehicle_list
            }
        })

    except Defendant.DoesNotExist:
        return JsonResponse({'error': 'Driver not found'}, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsNaTISAdmin])
def get_vehicle_by_id(request, vehicle_id):
    """
    Get detailed information about a specific vehicle.
    """
    try:
        vehicle = Vehicle.objects.select_related('owner').get(id=vehicle_id)

        return JsonResponse({
            'success': True,
            'data': {
                'id': vehicle.id,
                'plate_no': vehicle.plate_no,
                'vin': vehicle.vin,
                'engine_no': vehicle.engine_no,
                'vehicle_make': vehicle.vehicle_make,
                'vehicle_model': vehicle.vehicle_model,
                'vehicle_color': vehicle.vehicle_color,
                'vehicle_year': vehicle.vehicle_year,
                'vehicle_type': vehicle.vehicle_type,
                'fuel_type': vehicle.fuel_type,
                'registration_date': vehicle.registration_date.isoformat() if vehicle.registration_date else None,
                'registration_expiry': vehicle.registration_expiry.isoformat() if vehicle.registration_expiry else None,
                'roadworthy_cert_no': vehicle.roadworthy_cert_no,
                'roadworthy_expiry': vehicle.roadworthy_expiry.isoformat() if vehicle.roadworthy_expiry else None,
                'insurance_company': vehicle.insurance_company,
                'insurance_policy_no': vehicle.insurance_policy_no,
                'insurance_expiry': vehicle.insurance_expiry.isoformat() if vehicle.insurance_expiry else None,
                'seating_capacity': vehicle.seating_capacity,
                'gross_vehicle_mass': vehicle.gross_vehicle_mass,
                'tare_mass': vehicle.tare_mass,
                'status': vehicle.status,
                'is_active': vehicle.is_active,
                'created_at': vehicle.created_at.isoformat() if vehicle.created_at else None,
                'owner': {
                    'id': vehicle.owner.id,
                    'firstname': vehicle.owner.firstname,
                    'lastname': vehicle.owner.lastname,
                    'id_no': vehicle.owner.id_no,
                    'license_no': vehicle.owner.license_no,
                    'phone_number': vehicle.owner.phone_number,
                    'email': vehicle.owner.email
                } if vehicle.owner else None
            }
        })

    except Vehicle.DoesNotExist:
        return JsonResponse({'error': 'Vehicle not found'}, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['PUT'])
@permission_classes([IsNaTISAdmin])
def update_vehicle(request, vehicle_id):
    """
    Update vehicle information.
    """
    try:
        vehicle = Vehicle.objects.get(id=vehicle_id)

        # Update fields if provided
        if 'plate_no' in request.data:
            new_plate = request.data['plate_no'].strip().upper()
            if new_plate != vehicle.plate_no:
                existing = Vehicle.objects.filter(plate_no__iexact=new_plate).exclude(id=vehicle_id).first()
                if existing:
                    return JsonResponse({'error': 'Plate number already in use'}, status=400)
                vehicle.plate_no = new_plate

        if 'vin' in request.data:
            new_vin = request.data['vin'].strip().upper()
            if new_vin != vehicle.vin:
                existing = Vehicle.objects.filter(vin__iexact=new_vin).exclude(id=vehicle_id).first()
                if existing:
                    return JsonResponse({'error': 'VIN already in use'}, status=400)
                vehicle.vin = new_vin

        if 'vehicle_make' in request.data:
            vehicle.vehicle_make = request.data['vehicle_make']
        if 'vehicle_model' in request.data:
            vehicle.vehicle_model = request.data['vehicle_model']
        if 'vehicle_color' in request.data:
            vehicle.vehicle_color = request.data['vehicle_color']
        if 'vehicle_year' in request.data:
            vehicle.vehicle_year = request.data['vehicle_year']
        if 'vehicle_type' in request.data:
            vehicle.vehicle_type = request.data['vehicle_type']
        if 'fuel_type' in request.data:
            vehicle.fuel_type = request.data['fuel_type']
        if 'engine_no' in request.data:
            vehicle.engine_no = request.data['engine_no']
        if 'seating_capacity' in request.data:
            vehicle.seating_capacity = request.data['seating_capacity']
        if 'gross_vehicle_mass' in request.data:
            vehicle.gross_vehicle_mass = request.data['gross_vehicle_mass']
        if 'tare_mass' in request.data:
            vehicle.tare_mass = request.data['tare_mass']
        if 'status' in request.data:
            vehicle.status = request.data['status']
        if 'is_active' in request.data:
            vehicle.is_active = request.data['is_active']

        # Date fields
        from django.utils.dateparse import parse_date
        if 'registration_expiry' in request.data and request.data['registration_expiry']:
            vehicle.registration_expiry = parse_date(request.data['registration_expiry'])
        if 'roadworthy_expiry' in request.data and request.data['roadworthy_expiry']:
            vehicle.roadworthy_expiry = parse_date(request.data['roadworthy_expiry'])
        if 'insurance_expiry' in request.data and request.data['insurance_expiry']:
            vehicle.insurance_expiry = parse_date(request.data['insurance_expiry'])

        # Insurance fields
        if 'insurance_company' in request.data:
            vehicle.insurance_company = request.data['insurance_company']
        if 'insurance_policy_no' in request.data:
            vehicle.insurance_policy_no = request.data['insurance_policy_no']
        if 'roadworthy_cert_no' in request.data:
            vehicle.roadworthy_cert_no = request.data['roadworthy_cert_no']

        vehicle.save()

        return JsonResponse({
            'success': True,
            'message': 'Vehicle updated successfully'
        })

    except Vehicle.DoesNotExist:
        return JsonResponse({'error': 'Vehicle not found'}, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['PUT'])
@permission_classes([IsNaTISAdmin])
def update_driver(request, driver_id):
    """
    Update driver information.
    """
    try:
        driver = Defendant.objects.get(id=driver_id)

        # Update fields if provided
        if 'firstname' in request.data:
            driver.firstname = request.data['firstname']
        if 'lastname' in request.data:
            driver.lastname = request.data['lastname']
        if 'id_no' in request.data:
            new_id = request.data['id_no'].strip()
            if new_id != driver.id_no:
                existing = Defendant.objects.filter(id_no__iexact=new_id).exclude(id=driver_id).first()
                if existing:
                    return JsonResponse({'error': 'ID number already in use'}, status=400)
                driver.id_no = new_id
        if 'license_no' in request.data:
            new_license = request.data['license_no'].strip().upper() if request.data['license_no'] else ''
            if new_license and new_license != (driver.license_no or ''):
                existing = Defendant.objects.filter(license_no__iexact=new_license).exclude(id=driver_id).first()
                if existing:
                    return JsonResponse({'error': 'License number already in use'}, status=400)
            driver.license_no = new_license if new_license else None
        if 'phone_number' in request.data:
            driver.phone_number = request.data['phone_number'] if request.data['phone_number'] else None
        if 'alt_phone' in request.data:
            driver.alt_phone = request.data['alt_phone'] if request.data['alt_phone'] else None
        if 'email' in request.data:
            driver.email = request.data['email'] if request.data['email'] else None
        if 'physical_address' in request.data:
            driver.physical_address = request.data['physical_address'] if request.data['physical_address'] else None
        if 'city' in request.data:
            driver.city = request.data['city'] if request.data['city'] else None
        if 'postal_code' in request.data:
            driver.postal_code = request.data['postal_code'] if request.data['postal_code'] else None

        driver.save()

        return JsonResponse({
            'success': True,
            'message': 'Driver updated successfully'
        })

    except Defendant.DoesNotExist:
        return JsonResponse({'error': 'Driver not found'}, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)



# ======================
# Officer Dashboard APIs - Real-time road data
# ======================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_traffic_incidents(request):
    """
    Get all active traffic incidents (traffic jams, accidents, road closures, etc.)
    """
    try:
        incidents = TrafficIncident.objects.filter(is_active=True).order_by('-reported_at')[:50]

        incident_list = []
        for incident in incidents:
            incident_list.append({
                'id': incident.id,
                'incident_type': incident.incident_type,
                'incident_type_display': incident.get_incident_type_display(),
                'title': incident.title,
                'description': incident.description,
                'location': incident.location,
                'gps_coordinates': incident.gps_coordinates,
                'road_number': incident.road_number,
                'region': incident.region,
                'severity': incident.severity,
                'reported_at': incident.reported_at.isoformat() if incident.reported_at else None,
                'updated_at': incident.updated_at.isoformat() if incident.updated_at else None
            })

        return JsonResponse({
            'success': True,
            'data': incident_list
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_missing_persons(request):
    """
    Get all active missing persons
    """
    try:
        missing_persons = MissingPerson.objects.filter(status='missing').order_by('-reported_at')[:30]

        persons_list = []
        for person in missing_persons:
            persons_list.append({
                'id': person.id,
                'firstname': person.firstname,
                'lastname': person.lastname,
                'id_no': person.id_no,
                'age': person.age,
                'gender': person.gender,
                'gender_display': person.get_gender_display(),
                'description': person.description,
                'last_seen_location': person.last_seen_location,
                'last_seen_date': person.last_seen_date.isoformat() if person.last_seen_date else None,
                'gps_coordinates': person.gps_coordinates,
                'photo': person.photo.url if person.photo else None,
                'status': person.status,
                'reported_at': person.reported_at.isoformat() if person.reported_at else None
            })

        return JsonResponse({
            'success': True,
            'data': persons_list
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_warrants_of_arrest(request):
    """
    Get all active warrants of arrest
    """
    try:
        warrants = WarrantOfArrest.objects.filter(status='active').order_by('-issue_date')[:30]

        warrants_list = []
        for warrant in warrants:
            warrants_list.append({
                'id': warrant.id,
                'firstname': warrant.firstname,
                'lastname': warrant.lastname,
                'id_no': warrant.id_no,
                'alias': warrant.alias,
                'offense': warrant.offense,
                'warrant_number': warrant.warrant_number,
                'issue_date': warrant.issue_date.isoformat() if warrant.issue_date else None,
                'issued_by': warrant.issued_by,
                'status': warrant.status,
                'notes': warrant.notes,
                'created_at': warrant.created_at.isoformat() if warrant.created_at else None
            })

        return JsonResponse({
            'success': True,
            'data': warrants_list
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_news(request):
    """
    Get published news and announcements
    """
    try:
        news_items = News.objects.filter(
            is_published=True
        ).order_by('-published_at')[:20]

        news_list = []
        for news in news_items:
            news_list.append({
                'id': news.id,
                'title': news.title,
                'content': news.content,
                'category': news.category,
                'category_display': news.get_category_display(),
                'priority': news.priority,
                'image': news.image.url if news.image else None,
                'published_at': news.published_at.isoformat() if news.published_at else None,
                'expires_at': news.expires_at.isoformat() if news.expires_at else None
            })

        return JsonResponse({
            'success': True,
            'data': news_list
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_traffic_incident(request):
    """
    Create a new traffic incident
    """
    try:
        incident = TrafficIncident.objects.create(
            incident_type=request.data.get('incident_type', 'other'),
            title=request.data.get('title', ''),
            description=request.data.get('description', ''),
            location=request.data.get('location', ''),
            gps_coordinates=request.data.get('gps_coordinates', ''),
            road_number=request.data.get('road_number', ''),
            region=request.data.get('region', ''),
            severity=request.data.get('severity', 'medium'),
            reported_by=request.user
        )

        return JsonResponse({
            'success': True,
            'message': 'Traffic incident reported successfully',
            'data': {
                'id': incident.id,
                'incident_type': incident.incident_type,
                'title': incident.title,
                'location': incident.location,
                'severity': incident.severity
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_traffic_incident(request):
    """
    Resolve/close a traffic incident
    """
    incident_id = request.data.get('incident_id')

    if not incident_id:
        return JsonResponse({'error': 'Incident ID required'}, status=400)

    try:
        from django.utils import timezone

        incident = TrafficIncident.objects.get(id=incident_id)
        incident.is_active = False
        incident.resolved_at = timezone.now()
        incident.save()

        return JsonResponse({
            'success': True,
            'message': 'Traffic incident resolved successfully'
        })

    except TrafficIncident.DoesNotExist:
        return JsonResponse({'error': 'Incident not found'}, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_officer_dashboard_summary(request):
    """
    Get summary data for officer dashboard
    """
    try:
        officer = None
        try:
            officer = Officer.objects.get(user=request.user)
        except Officer.DoesNotExist:
            pass

        from django.utils import timezone
        from datetime import timedelta

        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)

        tickets_today = 0
        if officer:
            tickets_today = Ticket.objects.filter(
                officer=officer,
                date__date__gte=today,
                date__date__lt=tomorrow
            ).count()

        total_tickets = 0
        if officer:
            total_tickets = Ticket.objects.filter(officer=officer).count()

        active_incidents = TrafficIncident.objects.filter(is_active=True).count()
        missing_persons = MissingPerson.objects.filter(status='missing').count()
        active_warrants = WarrantOfArrest.objects.filter(status='active').count()
        recent_news = News.objects.filter(
            is_published=True,
            published_at__gte=timezone.now() - timedelta(days=7)
        ).count()

        return JsonResponse({
            'success': True,
            'data': {
                'tickets_today': tickets_today,
                'total_tickets': total_tickets,
                'active_incidents': active_incidents,
                'missing_persons': missing_persons,
                'active_warrants': active_warrants,
                'recent_news': recent_news
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
