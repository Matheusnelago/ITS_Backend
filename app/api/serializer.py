from rest_framework import serializers
from ..models import *


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = '__all__'

class OfficerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Officer
        fields = '__all__'

class CourtDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourtDate
        fields = '__all__'

class JudiciarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Judiciary
        fields = '__all__'

class DefendantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Defendant
        fields = '__all__'

class DefendantFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DefendantFile
        fields = '__all__'

class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = '__all__'

class SettingsBackendSerializer(serializers.ModelSerializer):
    class Meta:
        model = SettingsBackend
        fields = '__all__'

class OfficerManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfficerManagement
        fields = '__all__'

class TicketManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketManagement
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = '__all__'

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'


class CaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = '__all__'
