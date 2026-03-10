
import random, string, datetime
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
import uuid

# Create your models here.

def generate_ticket_number():
    """
    Generate a unique ticket number in format: NAM-YYYY-XXXXXX
    """
    year = datetime.datetime.now().year
    random_digits = ''.join(random.choices(string.digits, k=6))
    return f"NAM-{year}-{random_digits}"


class SettingsBackend(BaseBackend):
    def authenticate(self, request, username = ..., password = ..., **kwargs):
        login_valid = settings.LoGIN_USERNAME == username
        pwd_valid = check_password(password, settings.LoGIN_PASSWORD_HASH)
        if login_valid and pwd_valid:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                user = User(username=username)
                user.save()
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class Officer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    badge = models.CharField(max_length=20, unique=True)
    rank = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.badge}"



class Ministry(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.user)


class UserRole(models.Model):
    ROLE_CHOICES = [
        ('officer', 'Officer'),
        ('judiciary', 'Judiciary'),
        ('ministry', 'Ministry'),
        ('admin', 'Admin'),
        ('natisadmin', 'NaTIS Admin'),
        ('nampoladmin', 'Nampol Admin'),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'User Roles'

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    def is_ministry(self):
        return self.role == 'ministry'

    def is_admin(self):
        return self.role == 'admin'

    def can_view_ministry_dashboard(self):
        """Check if user can view ministry dashboard"""
        return self.role in ['ministry', 'admin']

class Ticket(models.Model):
    """
    Main traffic ticket model
    """
    # Basic ticket info
    ticket_issued = models.CharField(
        max_length=100,
        unique=True,
        default=generate_ticket_number
    )
    date = models.DateTimeField(auto_now_add=True)
    plate_no = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Vehicle details
    vehicle_make = models.CharField(max_length=50, blank=True, null=True)
    vehicle_model = models.CharField(max_length=50, blank=True, null=True)
    vehicle_color = models.CharField(max_length=30, blank=True, null=True)
    vehicle_year = models.CharField(max_length=4, blank=True, null=True)

    # Location details
    location = models.CharField(max_length=200, blank=True, null=True)
    gps_coordinates = models.CharField(max_length=50, blank=True, null=True)
    road_number = models.CharField(max_length=20, blank=True, null=True)
    road_type = models.CharField(
        max_length=20,
        choices=[
            ('national', 'National Road (B1, B2, B3, etc.)'),
            ('district', 'District Road (M1, M2, etc.)'),
            ('urban', 'Urban Road'),
            ('street', 'Street'),
            ('avenue', 'Avenue'),
            ('other', 'Other')
        ],
        blank=True, null=True
    )
    region = models.CharField(
        max_length=50,
        choices=[
            ('khomas', 'Khomas Region'),
            ('erongo', 'Erongo Region'),
            ('omasati', 'Omasati Region'),
            ('oshana', 'Oshana Region'),
            ('oshikoto', 'Oshikoto Region'),
            ('ohangwena', 'Ohangwena Region'),
            ('kunene', 'Kunene Region'),
            ('kavango_east', 'Kavango East Region'),
            ('kavango_west', 'Kavango West Region'),
            ('zambezi', 'Zambezi Region'),
            ('hardap', 'Hardap Region'),
            ('karas', 'Karas Region')
        ],
        blank=True, null=True
    )

    # Violation details
    violation_type = models.CharField(
        max_length=50,
        choices=[
            ('speeding', 'Speeding'),
            ('red_light', 'Red Light Violation'),
            ('illegal_parking', 'Illegal Parking'),
            ('dui', 'Driving Under Influence (DUI)'),
            ('no_license', 'Driving Without License'),
            ('expired_license', 'Expired License'),
            ('no_registration', 'No/Expired Vehicle Registration'),
            ('no_inspection', 'Failed Vehicle Inspection'),
            ('cell_phone', 'Using Cell Phone While Driving'),
            ('seatbelt', 'Not Wearing Seatbelt'),
            ('reckless', 'Reckless Driving'),
            ('overloading', 'Vehicle Overloading'),
            ('one_way', 'One-Way Street Violation'),
            ('stop_sign', 'Failure to Stop at Stop Sign'),
            ('no_helmet', 'Motorcycle - No Helmet'),
            ('illegal_turn', 'Illegal Turn/U-Turn'),
            ('pedestrian', 'Pedestrian Crossing Violation'),
            ('drug_driving', 'Driving Under Drugs'),
            ('hit_run', 'Hit and Run'),
            ('unroadworthy', 'Unroadworthy Vehicle'),
            ('wrong_lane', 'Wrong Lane Usage'),
            ('tailgating', 'Tailgating'),
            ('overtaking', 'Illegal Overtaking'),
            ('no_insurance', 'No Motor Vehicle Insurance'),
            ('unlicensed_vehicle', 'Unlicensed Vehicle'),
            ('noise_violation', 'Excessive Noise'),
            ('other', 'Other Offence')
        ],
        default='speeding'
    )
    violation_time = models.TimeField(blank=True, null=True)
    officer_notes = models.TextField(blank=True, null=True)

    # Status fields
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('paid', 'Paid'),
            ('overdue', 'Overdue'),
            ('disputed', 'Disputed'),
            ('court', 'Court'),
            ('closed', 'Closed')
        ],
        default='pending'
    )
    due_date = models.DateField(blank=True, null=True)

    # Officer info
    officer = models.ForeignKey(
        Officer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issued_tickets'
    )

    def __str__(self):
        return self.ticket_issued

class OfficerManagement(models.Model):
    """Model for managing officer details and assignments"""
    officer = models.OneToOneField(Officer, on_delete=models.CASCADE, related_name='management')
    name = models.CharField(max_length=100, blank=True, null=True)
    badge = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=50, blank=True, null=True)
    action = models.CharField(max_length=50, blank=True, null=True)
    active = models.BooleanField(default=True)
    assigned_tickets = models.OneToOneField(Ticket, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Officer Management for {self.officer.user.username if self.officer else 'Unknown'}"


class TicketManagement(models.Model):
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE)
    resolution_notes = models.TextField(blank=True, null=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

class TicketAttachment(models.Model):
    """
    Model for ticket file attachments
    """
    FILE_TYPE_CHOICES = [
        ('photo', 'Photo'),
        ('document', 'Document'),
        ('video', 'Video'),
        ('evidence', 'Evidence'),
        ('other', 'Other')
    ]

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='ticket_attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_type = models.CharField(max_length=50, choices=FILE_TYPE_CHOICES, default='document')
    description = models.CharField(max_length=200, blank=True, null=True)
    uploaded_by = models.ForeignKey(
        Officer,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_attachments'
    )

    def __str__(self):
        return f"Attachment {self.id} - {self.ticket.ticket_issued}"



class Judiciary(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.user)

class CourtDate(models.Model):
    """
    Model for scheduling court dates for disputed tickets
    """
    ticket = models.OneToOneField(
        Ticket,
        on_delete=models.CASCADE,
        related_name='court_date'
    )
    scheduled_date = models.DateTimeField()
    location = models.CharField(max_length=200)
    judge = models.OneToOneField(Judiciary, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_court_dates'
    )

    def __str__(self):
        return f"Court Date - {self.ticket.ticket_issued} - {self.scheduled_date}"


class Defendant(models.Model):
    """Model for storing defendant/driver information"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='defendant_info'
    )
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    id_no = models.CharField(max_length=20, unique=True)
    license_no = models.CharField(max_length=20, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    alt_phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    physical_address = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=True)
    preferred_method = models.CharField(
        max_length=20,
        choices=[
            ('all', 'All'),
            ('email', 'Email'),
            ('sms', 'SMS')
        ],
        default='all'
    )

    def __str__(self):
        return f"{self.firstname} {self.lastname} ({self.id_no})"

class DefendantFile(models.Model):
    defendant = models.ForeignKey(Defendant, on_delete=models.CASCADE)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    file = models.FileField(upload_to='defendant_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File for {self.defendant} - {self.file.name}"


class AuditLog(models.Model):
    """
    Model for tracking system actions and changes
    """
    action = models.CharField(
        max_length=50,
        choices=[
            ('ticket_issued', 'Ticket Issued'),
            ('ticket_paid', 'Ticket Paid'),
            ('court_date_set', 'Court Date Set'),
            ('message_sent', 'Message Sent'),
            ('attachment_added', 'Attachment Added'),
            ('user_login', 'User Login'),
            ('user_logout', 'User Logout')
        ]
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.action} - {self.timestamp}"


class Nampol(models.Model):
    employee = models.OneToOneField(Officer, on_delete=models.CASCADE)

    def __str__(self):
        return f"Nampol - {self.employee.user.username}"


class Vehicle(models.Model):
    """
    Model for storing registered vehicle information in NaTIS
    Similar to Namibia's National Transport Information System
    """
    # Vehicle identification
    plate_no = models.CharField(max_length=20, unique=True, help_text="Vehicle registration plate number")
    vin = models.CharField(max_length=50, unique=True, help_text="Vehicle Identification Number (VIN)")
    engine_no = models.CharField(max_length=50, blank=True, null=True, help_text="Engine number")

    # Vehicle details
    vehicle_make = models.CharField(max_length=50, help_text="Vehicle manufacturer (e.g., Toyota, BMW)")
    vehicle_model = models.CharField(max_length=50, help_text="Vehicle model name")
    vehicle_color = models.CharField(max_length=30, help_text="Vehicle color")
    vehicle_year = models.CharField(max_length=4, help_text="Year of manufacture")
    vehicle_type = models.CharField(
        max_length=50,
        choices=[
            ('sedan', 'Sedan'),
            ('suv', 'SUV'),
            ('hatchback', 'Hatchback'),
            ('pickup', 'Pickup'),
            ('truck', 'Truck'),
            ('bus', 'Bus'),
            ('motorcycle', 'Motorcycle'),
            ('van', 'Van'),
            ('minibus', 'Minibus'),
            ('other', 'Other')
        ],
        default='sedan'
    )
    fuel_type = models.CharField(
        max_length=20,
        choices=[
            ('petrol', 'Petrol'),
            ('diesel', 'Diesel'),
            ('electric', 'Electric'),
            ('hybrid', 'Hybrid'),
            ('other', 'Other')
        ],
        default='petrol'
    )

    # Registration details
    registration_date = models.DateField(auto_now_add=True)
    registration_expiry = models.DateField(help_text="Vehicle registration expiry date")
    roadworthy_cert_no = models.CharField(max_length=50, blank=True, null=True, help_text="Roadworthy certificate number")
    roadworthy_expiry = models.DateField(blank=True, null=True, help_text="Roadworthy certificate expiry date")

    # Insurance details
    insurance_company = models.CharField(max_length=100, blank=True, null=True)
    insurance_policy_no = models.CharField(max_length=50, blank=True, null=True)
    insurance_expiry = models.DateField(blank=True, null=True)

    # Owner information (linked to defendant)
    owner = models.ForeignKey(
        Defendant,
        on_delete=models.CASCADE,
        related_name='owned_vehicles',
        help_text="Registered owner of the vehicle"
    )

    # Status
    is_active = models.BooleanField(default=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('registered', 'Registered'),
            ('expired', 'Expired'),
            ('suspended', 'Suspended'),
            ('scrapped', 'Scrapped'),
            ('stolen', 'Stolen')
        ],
        default='registered'
    )

    # Additional info
    seating_capacity = models.IntegerField(default=5, help_text="Number of seats")
    gross_vehicle_mass = models.IntegerField(blank=True, null=True, help_text="Gross vehicle mass in kg")
    tare_mass = models.IntegerField(blank=True, null=True, help_text="Tare mass in kg")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-registration_date']

    def __str__(self):
        return f"{self.plate_no} - {self.vehicle_year} {self.vehicle_make} {self.vehicle_model}"


class TrafficIncident(models.Model):
    """Model for tracking real-time traffic incidents like jams, accidents, road closures"""
    INCIDENT_TYPE_CHOICES = [
        ('traffic_jam', 'Traffic Jam'),
        ('accident', 'Road Accident'),
        ('road_closure', 'Road Closure'),
        ('construction', 'Construction/Road Works'),
        ('weather', 'Weather Hazard'),
        ('police_check', 'Police Checkpoint'),
        ('event', 'Special Event'),
        ('other', 'Other')
    ]

    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ]

    incident_type = models.CharField(max_length=30, choices=INCIDENT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=200)
    gps_coordinates = models.CharField(max_length=50, blank=True, null=True)
    road_number = models.CharField(max_length=20, blank=True, null=True)
    region = models.CharField(max_length=50, blank=True, null=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    reported_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reported_incidents'
    )

    def __str__(self):
        return f"{self.get_incident_type_display()} - {self.location}"


class MissingPerson(models.Model):
    """Model for tracking missing persons"""
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ]

    STATUS_CHOICES = [
        ('missing', 'Missing'),
        ('found', 'Found'),
        ('deceased', 'Deceased')
    ]

    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    id_no = models.CharField(max_length=20, blank=True, null=True)
    age = models.IntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    description = models.TextField()
    last_seen_location = models.CharField(max_length=200)
    last_seen_date = models.DateTimeField()
    gps_coordinates = models.CharField(max_length=50, blank=True, null=True)
    photo = models.FileField(upload_to='missing_persons/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='missing')
    reported_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reported_missing_persons'
    )

    def __str__(self):
        return f"{self.firstname} {self.lastname} - {self.get_status_display()}"


class WarrantOfArrest(models.Model):
    """Model for tracking warrants of arrest"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('executed', 'Executed'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled')
    ]

    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    id_no = models.CharField(max_length=20)
    alias = models.CharField(max_length=100, blank=True, null=True)
    offense = models.TextField()
    warrant_number = models.CharField(max_length=50, unique=True)
    issue_date = models.DateField()
    issued_by = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    executed_at = models.DateTimeField(blank=True, null=True)
    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='executed_warrants'
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Warrant {self.warrant_number} - {self.firstname} {self.lastname}"


class News(models.Model):
    """Model for news and announcements"""
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(
        max_length=50,
        choices=[
            ('general', 'General'),
            ('traffic', 'Traffic'),
            ('security', 'Security'),
            ('weather', 'Weather'),
            ('events', 'Events'),
            ('policy', 'Policy Update')
        ],
        default='general'
    )
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High')
        ],
        default='medium'
    )
    image = models.FileField(upload_to='news/', blank=True, null=True)
    is_published = models.BooleanField(default=True)
    published_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_news'
    )

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return self.title
