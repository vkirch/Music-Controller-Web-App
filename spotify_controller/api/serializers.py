from rest_framework import serializers
from .models import Room 

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ('id', 'code', 'host', 'guest_can_pause', 'vote_to_skip', 'created_at')

class CreateRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields =  ('guest_can_pause', 'vote_to_skip')

class UpdateRoomSerializer(serializers.ModelSerializer):
    #Redefine code from within the serializer because we must be referencing a room code that already exists
    code = serializers.CharField(validators = [])
    class Meta:
        model = Room
        fields =  ('guest_can_pause', 'vote_to_skip', 'code')
