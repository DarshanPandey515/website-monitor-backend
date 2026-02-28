from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Avg, Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from .models import *
from .serializers import *


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username
        })


class LoginAPIView(APIView):

    permission_classes = []

    def post(self, request):

        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)

        if user is None:
            return Response({"error": "Invalid Credentials."}, status=400)

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        response = Response({
            "access": str(access),
        })

        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=False,  # true in prod
            samesite="Lax"

        )

        return response


class RefreshAPIView(APIView):
    permission_classes = []

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response({
                "error": "No refresh token."
            }, status=401)

        try:
            refresh = RefreshToken(refresh_token)
            access = refresh.access_token

            return Response({
                "access": str(access)
            })
        except TokenError:
            return Response({
                "error": "Invalid refresh token"
            }, status=401)


class LogoutAPIView(APIView):
    def post(self, request):
        response = Response({
            "message": "Logged Out"
        })

        response.delete_cookie("refresh_token")
        return response


class WebsiteListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        websites = Website.objects.filter(user=request.user)
        serializer = WebsiteSerializer(websites, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = WebsiteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WebsiteDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        return get_object_or_404(Website, pk=pk, user=request.user)
    
    def get(self, request, pk):
        website = self.get_object(request, pk)
        now = timezone.now()

        last_24h = now - timedelta(hours=24)

        check_24h = website.checks.filter(checked_at__gte=last_24h)

        total_checks = check_24h.count()
        successfull_checks = check_24h.filter(status=True).count()

        uptime = 0
        if total_checks > 0:
            uptime = round((successfull_checks / total_checks) * 100, 2)

        avg_response = check_24h.aggregate(
            avg=Avg("response_time")
        )["avg"] or 0

        recent_checks = website.checks.all()[:50]

        serializer = WebsiteSerializer(website)
        return Response({
            "website": serializer.data,
            "metrics": {
                "uptime_24h": uptime,
                "avg_response_24h": avg_response,
                "total_check_24h": total_checks
            },
            "recent_checks": CheckResultSerializer(recent_checks, many=True).data
        })

    def put(self, request, pk):
        website = self.get_object(request, pk)
        serializer = WebsiteSerializer(website, data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        website = self.get_object(request, pk)
        website.delete()
        return Response(status=204)
