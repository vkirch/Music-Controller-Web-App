from django.db.models.fields import DateTimeField, NullBooleanField
from django.http.response import Http404, JsonResponse
from django.shortcuts import render
from rest_framework import generics, status
from .serializers import RoomSerializer, CreateRoomSerializer, UpdateRoomSerializer
from .models import Room
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime
from django.http import JsonResponse



# Create your views here.
class UpdateRoom(APIView):
    serializer_class = UpdateRoomSerializer
    def patch(self, request, format=None):
        # Checks to see if the current user has an active session with the web browser
        if not self.request.session.exists(self.request.session.session_key):
            self.request.session.create()
        #Validates data against the serializer
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            guest_can_pause = serializer.data.get("guest_can_pause")
            vote_to_skip = serializer.data.get("vote_to_skip")
            code = serializer.data.get("code")

            queryset = Room.objects.filter(code=code)
            if not queryset.exists():
                return Response({"msg":"Room not found"}, status=status.HTTP_404_NOT_FOUND)
            
            room = queryset[0]
            user_id = self.request.session.session_key
            if room.host != user_id:
                return Response({"msg":"You are not the host of the room"}, status=status.HTTP_403_FORBIDDEN)

            room.guest_can_pause = guest_can_pause
            room.vote_to_skip = vote_to_skip
            room.save(update_fields=['guest_can_pause', 'vote_to_skip'])
            return Response(RoomSerializer(room).data, status=status.HTTP_200_OK)

        return Response({"Bad Request":"Invallid Data..."}, status=status.HTTP_400_BAD_REQUEST)

class LeaveRoom(APIView):
    def post(self, request, format=None):
        if 'room_code' in self.request.session:
            #Removes code from the user session
            self.request.session.pop('room_code')
            host_id = self.request.session.session_key
            room_results = Room.objects.filter(host=host_id)
            if len(room_results) > 0:
                room = room_results[0]
                room.delete()
        return Response({'message': 'Success'}, status=status.HTTP_200_OK)

class UserInRoom(APIView):
    def get(self, request, format=None):
        # Checks to see if the current user has an active session with the web browser
        if not self.request.session.exists(self.request.session.session_key):
            self.request.session.create()

        data = {
            'code': self.request.session.get('room_code')
        }
        return JsonResponse(data, status=status.HTTP_200_OK)

class RoomView(generics.ListAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

class JoinRoom(APIView):
    lookup_url_kwarg = "code"

    def post(self, request, format=None):
        # Checks to see if the current user has an active session with the web browser
        if not self.request.session.exists(self.request.session.session_key):
            self.request.session.create()
        
        code = request.data.get(self.lookup_url_kwarg)
        if code != None:
            room_result = Room.objects.filter(code=code)
            if len(room_result) > 0:
                room = room_result[0]
                self.request.session['room_code'] = code
                return Response({"message":"Room Joined!"}, status = status.HTTP_201_CREATED)

            return Response({"Bad Request":"Invalid room code."}, status.HTTP_400_BAD_REQUEST)

        return Response({"Bad Request":"Code parameter not found in request"}, status.HTTP_400_BAD_REQUEST)

class GetRoom(APIView):
    serializer_class = RoomSerializer
    lookup_url_kwarg = "code"

    def get(self, request, format=None):
        code = request.GET.get(self.lookup_url_kwarg)

        if code != None:
            room = Room.objects.filter(code=code)
            if len(room) > 0:
                data = RoomSerializer(room[0]).data
                data['is_host'] = self.request.session.session_key == room[0].host
                return Response(data, status=status.HTTP_200_OK)
            return Response({"Room Not Found": "Invalid Room Code"}, status.HTTP_404_NOT_FOUND)
        return Response({"Bad Request":"Code parameter not found in request"}, status.HTTP_400_BAD_REQUEST)


class CreateRoomView(APIView):
    serializer_class = CreateRoomSerializer

    def post(self, request, format=None):
        # Checks to see if the current user has an active session with the web browser
        if not self.request.session.exists(self.request.session.session_key):
            self.request.session.create()

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            guest_can_pause = serializer.data.get('guest_can_pause')
            vote_to_skip = serializer.data.get('vote_to_skip')
            host = self.request.session.session_key
            created_at = datetime.now()

            #Checks to see if the user already has an active room
            queryset = Room.objects.filter(host=host)
            
            #If room exists, you want to update fields
            if queryset.exists():
                room = queryset[0]
                room.vote_to_skip = vote_to_skip
                room.guest_can_pause = guest_can_pause
                room.created_at = created_at
                room.save(update_fields=['guest_can_pause', 'vote_to_skip', 'created_at'])
                self.request.session['room_code'] = room.code
                return Response(RoomSerializer(room).data, status=status.HTTP_200_OK)
            
            else:
                room = Room(host=host, guest_can_pause=guest_can_pause, vote_to_skip=vote_to_skip, created_at=created_at)
                room.save()
                self.request.session['room_code'] = room.code
                return Response(RoomSerializer(room).data, status=status.HTTP_201_CREATED)

        return Response({'Bad Request': 'Invalid data...'}, status=status.HTTP_400_BAD_REQUEST)