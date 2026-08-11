from django.shortcuts import render,get_object_or_404
from django.template.defaulttags import comment
from rest_framework.generics import (CreateAPIView,UpdateAPIView,ListAPIView,RetrieveAPIView,DestroyAPIView,get_object_or_404)
from rest_framework import permissions,status
from rest_framework.permissions import IsAuthenticated,AllowAny
from .models import Post
from .serializers import SignUpSerializer, UserChangeInfoSerializer, UserPhotoStatusSerializer, LoginSerializer, \
    PostSerializers, PostDetailSerializers, CommentSerializer
from .models import CustomUser, NEW, CODE_VERIFY, DONE, PHOTO_DONE, VIA_EMAIL, VIA_PHONE, PostLike
from rest_framework.views import APIView
from datetime import datetime
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.utils import timezone
from .models import CodeVerify,CustomUser
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from .permissions import IsAuthor
from .serializers import LoginSerializer




class SignUpView(CreateAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = SignUpSerializer
    queryset = CustomUser




class CodeVerifyView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def post(self,request):
        user=request.user
        code=self.request.data.get('code')

        codes = CodeVerify.objects.filter(user=user,code=code,expiration_time__gte=timezone.now()).first()
        # codes=user.verify_codes.filter(code=code,expiration_time__gte=datetime.now(),is_active=False)
        if not codes:
            raise ValidationError({'message':'Kodingiz xato yoki eskirgan','status':status.HTTP_400_BAD_REQUEST})
        else:
            codes.is_active=True
            codes.save()
        if user.auth_status==NEW:
            user.auth_status=CODE_VERIFY
            user.save()
        response_data={
            'message':'Kod tasdiqlandi',
            'status':status.HTTP_200_OK,
            'access':user.token()['access'],
            'refresh':user.token()['refresh']
        }
        return Response(response_data)

class GetNewCodeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def get(self,request):
        user=request.user
        codes = User.Verify_codes.filter(expiration_time__gte=datetime.now(),is_active=False)
        if code.exists():
            raise ValidationError({'message':'Sizda holi active code bor','status':status.HTTP_400_BAD_REQUEST})
        else:
            if user.auth_type == VIA_EMAIL:
                code = user.generate_code(VIA_EMAIL)
                print(code, '1111111111111111111111111111111')
            elif user.auth_type == VIA_PHONE:
                code = user.generate_code(VIA_PHONE)
                print(code, '11111111111111111111111111111111111')

        response_data = {
            'message': 'Kod yuborildi',
            'status': status.HTTP_201_CREATED,
        }
        return Response(response_data)

#
# class UserChangeInfoView(APIView):
#     def get_object(self,pk):
#         user=get_object_or_404(CustomUser,pk=pk)
#         return user
#
#     def put(self,request,pk):
#         user=self.get_object(pk)
#         serializer=UserChangeInfoSerializer(instance=user,data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             token,created=Token.objects.get_or_create(user=user)
#             return Response({
#                 "status":status.HTTP_200_OK,
#                 "message":"Ma'lumotlar muvaffaqiyatli yangilandi",
#                 "auth_status":user.auth_status,
#                 "token":token.key
#             })
#         return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)



class UserChangeInfoView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def put(self,request):
        user=request.user
        serializer=UserChangeInfoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(instance=user, validated_data=serializer.validated_data)

        response={
            'message':'malumotingiz qoshildi',
            'status':status.HTTP_200_OK,
            'access':user.token()['access'],
            'refresh':user.token()['refresh'],
        }
        return Response(response)




class UserPhotoStatusView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def patch(self,request):
        user=request.user
        serializer=UserChangeInfoSerializer(data=request.data,partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(instance=user, validated_data=serializer.validated_data)

        response={
            'message':'Rasm qoshildi',
            'status':status.HTTP_200_OK,
            'access':user.token()['access'],
            'refresh':user.token()['refresh'],
        }
        return Response(response)



class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.validated_data, status=status.HTTP_200_OK)



class LogoutView(APIView):
    def post(self,request):
        try:
            refresh_token=RefreshToken(refresh)
            refresh_token.blacklist()
        except Exception as e:
            raise ValidationError(detail='xatolik: {e)')

        else:
            response_data={
                'status':status.HTTP_200_OK,
                'message':'tizimdan chiqdingiz'
            }
            return Response(response_data)



class LoginRefreshView(APIView):
    permission_classes = (permissions.AllowAny,)
    def get(self,request):
        refresh=self.request.data.get('refresh',None)
        try:
            refresh_token=RefreshToken(refresh)
        except Exception as e:
            raise ValidationError(detail=f'Xatolik: {e}')

        else:
            response_data={
                'status':status.HTTP_201_CREATED,
                'access':str(refresh_token.access_token)
            }
            return Response(response_data)



class ForgotPasswordView(APIView):
    permission_classes = (AllowAny, )
    def post(self,request):
        serializer=ForgotPasswordSerializers(data=request.data)
        serializer.is_valid(raise_exception=True)
        response_data = serializer.validated_data
        response = {
            'status': status.HTTP_200_OK,
            "message": response_data.get('message'),
            "access": response_data.get('access'),
            "refresh": response_data.get('refresh'),
        }
        return Response(response)


class ResetPasswordCodeView(APIView):
    permission_classes = (IsAuthenticated, )
    def post(self,request):
        code=self.request.data.get('code')
        user=self.request.user
        user_code = CodeVerify.objects.filter(code=code, user=user,expiration_time__gte=datetime.now(), is_active=True)
        if not user_code.exists():
            raise ValidationError({
                'status': status.HTTP_400_BAD_REQUEST,
                'message': "Kodingiz xato yoki eskirgan"
            })
        else:
            user_code.update(is_active=False)


        response = {
            'status': status.HTTP_200_OK,
            'message': 'Kodingiz tasdiqlandi',
        }
        return Response(response)



class ResetPasswordView(APIView):
    permission_classes = (IsAuthenticated, )
    def post(self,request):
        user=request.user
        serializer=ResetPasswordSerializers(data=request.data,instance=user)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response={
            'status':status.HTTP_200_OK,
            'message':"Siz muffaqiyatli parolizni tikladiz",
        }
        return Response(response)




class PostCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Post.objects.all()
    serializer_class = PostSerializers

    def perform_create(self, serializer):
        serializer.save(auth=self.request.user)


class PostUpdateView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Post.objects.all()
    serializer_class = PostSerializers

    def update(self,request,*args,**kwargs):
        instance=self.get_object()

        if instance.auth != request.user:
            raise ValidationError({"message":"Siz o'zingizni postingizni update qila olasiz"})

        serializer=self.get_serializer(instance,data=request.data,partial=True)

        serializer.is_valid(raise_exception=True)

        self.perform_update(serializer)

        response={
            'status':status.HTTP_200_OK,
            "message":'malumotlar yangilandi',
            'data':serializer.validated_data
        }

        return Response(response)

    def perform_update(self, serializer):
        serializer.save()


class PostListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PostSerializers

    def get_queryset(self):
        user=self.request.user
        return Post.objects.filter(aauth=user).order_by('-created_at')

    def list(self,request,*args,**kwargs):
        queryset=self.get_queryset()
        serializer=self.get_serializer(queryset,many=True)

        response={
            'status':status.HTTP_200_OK,
            'message':'sizning postlaringiz',
            'user':request.user.username,
            'data':serializer.data
        }
        return Response(response)


class PostDeleteView(DestroyAPIView):
    permission_classes = (IsAuthenticated,IsAuthor)
    queryset = Post.objects.all()
    serializer_class = PostSerializers

    def destroy(self,request,*args,**kwargs):
        try:
            instance=self.get_object()
            self.perform_destroy(instance)
            response={
                'status':status.HTTP_400_BAD_REQUEST,
                'message':'malumot topilmadi'
            }
        except Exception:
            response={
                'status':status.HTTP_400_BAD_REQUEST,
                'message':'malumot topilmadi',
            }
        return Response(response)


class PostDetailView(APIView):
    permission_classes = (IsAuthenticated,AllowAny)
    def get(self,request,pk):
        post=get_object_or_404(Post,id=pk)

        serializer=PostDetailSerializers(post,context={'request':request})

        response={
            'status':status.HTTP_200_OK,
            'message':'malumotlar',
            'data':serializer.data
        }
        return Response(response)

    def post(self,request,pk):
        user=self.request.user

        if not user.is_authenticated:
            raise ValidationError({'message':'siz royxatdan otmagansiz'})

        postlike, Like=PostLike.objects.get_or_create(auth=user,post_id=pk)

        if not Like:
            postlike.delete()
            return Response({'message':'like ochirildi'})

        response={
            'status':status.HTTP_201_CREATED,
            'message':'like bosildi'
        }
        return Response(response)


class CommentCreateView(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self,request):
        post_id=self.request.data.get('post_id')
        text=self.request.data.get('text')
        post=get_object_or_404(Post,id=post_id)
        comment=Comment.objects.create(auth=self.request.user,post_id=post_id,text=text)

        response={
            "status":status.HTTP_201_CREATED,
            'message':'comment qoshildi',
            'comment':comment.id
        }
        return Response(response)



class CommentUpdateView(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self,request):
        comment_id=self.request.data.get('comment_id')
        new_text=self.request.data.get('text')
        comment=Comment.objects.get(id=comment_id,auth=self.request.user)
        comment.text=new_text
        comment.save()
        response={
            'status':status.HTTP_200_OK,
            'message':'comment yangilandi'
        }
        return Response(response)



class CommentListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CommentSerializer

    def get_queryset(self):
        user=self.request.user
        return Comment.objects.filter(auth=user)


class CommentDeleteView(APIView):
    permission_classes = (IsAuthenticated,IsAuthor)
    def post(self,request):
        user=self.request.user
        comment_id=self.request.data.get('comment_id')
        comment=get_object_or_404(Comment,id=comment_id,auth=user)
        comment.delete()
        response={
            'status':status.HTTP_200_OK,
            'message':'malumot ochirildi'
        }
        return Response(response)









