from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, get_user_model

User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    email = request.data['email']
    password = request.data['password']
    full_name = request.data['full_name']
    phone = request.data['phone']

    user = User.objects.create_user(

        email=email,
        password=password,
        full_name=full_name,
        phone=phone
    )
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"message": "User created", "token": token.key})


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    email = request.data['email']
    password = request.data['password']

    user = authenticate(username=email, password=password)
    if user:
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"message": "Login successful", "token": token.key})
    return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
