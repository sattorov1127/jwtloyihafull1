# from http.client import responses

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import CustomUser, VIA_EMAIL, VIA_PHONE, CodeVerify,CODE_VERIFY,DONE,PHOTO_DONE,Comment,Post,PostLike
from shared.utility import check_email_or_phone,check_email_or_phone_or_username
from rest_framework import status
from django.db.models import Q
# from django.core.mail import send_mail
# from django.conf import settings
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate


class SignUpSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    auth_status = serializers.CharField(read_only=True)
    auth_type = serializers.CharField(read_only=True)

    email_or_phone = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'auth_status', 'auth_type', 'email_or_phone']

    def create(self,validated_data):
        user=super().create(validated_data)
        if user.auth_type==VIA_EMAIL:
            code=user.generate_code(VIA_EMAIL)
            print(code,'1111111111111111111111111111111')
        elif user.auth_type==VIA_PHONE:
            code=user.generate_code(VIA_PHONE)
            print(code,'11111111111111111111111111111111111')
        else:
            raise ValidationError('email yoki telefon raqam xato')
        user.save()
        return user


    def validate(self, attrs):
        user_input = attrs.pop('email_or_phone')
        user_data = self.auth_validate(user_input)
        attrs.update(user_data)
        return attrs

    # def create(self, validated_data):
    #     return CustomUser.objects.create(**validated_data)

    @staticmethod
    def auth_validate(data):
        user_input = data.get('email_or_phone')
        user_input_type=check_email_or_phone(user_input)
        if user_input_type == 'phone':
            return {
                'auth_type': VIA_PHONE,
                'phone': user_input
            }
        elif user_input_type == 'email':
            return {
                'auth_type': VIA_EMAIL,
                'email': user_input
            }
        else:
            raise ValidationError("Email yoki Telefon nomeringiz noto‘g‘ri kiritilgan")


    def validate_email_or_phone(self,email_or_phone):
        user=CustomUser.objects.filter( Q(phone=email_or_phone) | Q(email=email_or_phone)).exists()
        if user:
            raise ValidationError(detail="Bu telefon raqam yoki email bilan oldin ro'yxatdan o'tilgan")
        return email_or_phone


    def to_representation(self, instance):
        data=super().to_representation(instance)
        data['message']='Kodingiz yuborildi'
        data['refresh']=instance.token()['refresh']
        data['access']=instance.token()['access']
        return data



class UserChangeInfoSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        password = data.get('password', None)
        confirm_password = data.get('confirm_password', None)

        if password is None or confirm_password is None or password != confirm_password:
            response = {
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Parollar mos emas yoki xato kiritildi'
            }
            raise ValidationError(response)
        if len([i for i in password if i == ' ']) > 4:
            response = {
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Parollar xato kiritildi'
            }
            raise ValidationError(response)

        return data

    def validate_username(self, username):
        if len(username) < 7:
            raise ValidationError({'message': 'Username kamida 7 ta bolishi kerak'})
        elif not username.isalnum() or username.isdigit():
            raise ValidationError({'message': 'Username da ortiqcha belgilar bolmasligi kerak'})
        elif username[0].isdigit():
            raise ValidationError({'message': 'Username raqam bilan boshlanmasin'})
        return username

    def validate_first_name(self, first_name):
        first_name = first_name.strip()
        if not first_name:
            raise serializers.ValidationError("Ism bo'sh bo'lishi mumkin emas.")
        if len(first_name) < 3:
            raise serializers.ValidationError("Ism kamida 3 ta belgidan iborat bo'lishi kerak.")
        if len(first_name) > 50:
            raise serializers.ValidationError("Ism 50 ta belgidan oshmasligi kerak.")
        if not first_name.isalpha() or first_name[0]==" ' " or not first_name.replace(" ' ",'').isalpha():
            raise serializers.ValidationError("Ism faqat harflardan iborat bo'lishi kerak.")
        return first_name.capitalize()


    def validate_last_name(self, last_name):
        last_name = last_name.strip()
        if not last_name:
            raise serializers.ValidationError("Familiya bo'sh bo'lishi mumkin emas.")
        if len(last_name) < 2:
            raise serializers.ValidationError("Familiya kamida 2 ta belgidan iborat bo'lishi kerak.")
        if len(last_name) > 50:
            raise serializers.ValidationError("Familiya 50 ta belgidan oshmasligi kerak.")
        if not last_name.isalpha():
            raise serializers.ValidationError("Familiya faqat harflardan iborat bo'lishi kerak.")
        return last_name.capitalize()



    def update(self, instance, validated_data):
        instance.first_name=validated_data.get('first_name')
        instance.last_name=validated_data.get('last_name')
        instance.username=validated_data.get('username')
        instance.password.set_password(validated_data.get('password'))
        if instance.auth_status != CODE_VERIFY:
            raise ValidationError({"message":"siz hali tasdiqlanmagansiz","status":status.HTTP_400_BAD_REQUEST})
        instance.auth_status=DONE
        instance.save()
        return instance



class UserPhotoStatusSerializer(serializers.Serializer):
    photo=serializers.ImageField()

    def update(self, instance, validated_data):
        photo=validated_data.get('photo',None)
        if photo:
            instance.photo=photo
        if instance.auth_status==DONE:
            instance.auth_status=PHOTO_DONE
        instance.save()
        return instance



class LoginSerializer(TokenObtainPairSerializer):
    password=serializers.CharField(required=True,write_only=True)

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['user_input']=serializers.CharField(required=True,write_only=True)
        self.fields['username']=serializers.CharField(read_only=True)


    def validate(self,attrs):
        user=self.check_user_type(attrs)
        response_data={
            'status':status.HTTP_200_OK,
            'message':'siz tizimga kirdingiz',
            'access':user.token()['access'],
            'refresh':user.token()['refresh']
        }
        return response_data


    def check_user_type(self,data):
        password=data.get('password')
        user_input_data=data.get('user_input')
        user_type=check_email_or_phone_or_username(data.get(user_input_data))
        if user_type=='username':
            user=CustomUser.objects.filter(username=user_input_data).first()
            self.get_object(user)
            username=user_input_data
        elif user_type=="email":
            user=CustomUser.objects.filter(email__icontains=user_input_data.lower()).first()
            self.get_object(user)
            username=user.username
        elif user_type=="phone":
            user=CustomUser.objects.filter(phone_number=user_input_data).first()
            self.get_object(user)
            username=user.username
        else:
            raise ValidationError(detail='malumot topilmadi')

        authentication_kwargs = {
            "password": password,
            self.username_field: username
        }

        if user.auth_status not in [DONE,PHOTO_DONE]:
            raise ValidationError(detail="siz hali toliq royxatdan otmagansiz")

        user=authenticate(**authentication_kwargs)

        if not user:
            raise ValidationError('parol xato')
        return user



    def get_object(self,user):
        if not user:
            raise ValidationError({"message":'xato malumot kiritdingiz','status':status.HTTP_400_BAD_REQUEST})
        return True

class ForgotPasswordSerializers(serializers.Serializer):
    user_input=serializers.CharField(required=True,write_only=True)

    def validate(self, attrs):
        user_data=attrs.get('user_input',None)
        if not user_data:
            raise ValidationError({'message':'email,username yoki telefon raqam kiriting'})
        user=CustomUser.objects.filter(
            Q(username=user_data) | Q(email=user_data) | Q(phone_number=user_data)).first()
        if not user:
            raise ValidationError(detail="xato malumot kiritdingiz yoki ro'yxatdan o'tmagansiz")
        user_type=check_email_or_phone_or_username(user_data)

        if user_type=='phone':
            code = user.generate_code(VIA_PHONE)
            print(code, 'ppppppppppppppppppppppp')
        elif user_type=='email':
            code=send_email(user)
        elif user_type=='username':
            if user.phone_number:
                code = user.generate_code(VIA_PHONE)
                print(code, 'ppppppppppppppppppppppp')
            elif user.email:
                code = send_email(user)
            else:
                raise ValidationError(detail="siz to'liq ro'yxatdan o'tmagansiz ")

        response={
            'status':status.HTTP_201_CREATED,
            'message':'Kodingiz yuborildi',
            'refresh':user.token()['refresh'],
            'access':user.token()['access']
        }
        return response



class ResetPasswordSerializers(serializers.Serializer):
    password=serializers.CharField(required=True,write_only=True)
    conf_password=serializers.CharField(required=True,write_only=True)

    def validate(self, attrs):
        password=attrs.get('password')
        conf_password=attrs.get('conf_password')
        if  password!=conf_password:
            raise ValidationError({'message':'parollar mos emas'})
        elif len(password)<7:
            raise ValidationError({'message':'parol 8 ta belgidan kam bolmasligi kerak'})
        return attrs

    def update(self, instance, validated_data):
        validated_data.pop('conf_password')
        password=validated_data.get('password')
        instance.set_password(password)
        instance.save()
        return instance



class PostSerializers(serializers.ModelSerializer):
    created_at=serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",read_only=True)

    class Meta:
        model=Post
        fields=['id','text','image','video','created_at']


class CommentSerializer(serializers.ModelSerializer):
    created_at=serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",read_only=True)

    class Meta:
        model=Comment
        fields=('id','post','text','created_at')


class PostDetailSerializers(serializers.ModelSerializer):
    created_at=serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",read_only=True)
    comments=CommentSerializer(many=True,read_only=True,source='comment_set')
    likes_count=serializers.SerializerMethodField()
    is_liked=serializers.SerializerMethodField()

    class Meta:
        model=Post
        fields=('id','text','image','video','created_at','comments','likes_count','is_liked')

        def get_likes_count(self,obj):
            return obj.likes.count()

        def get_is_likes(self,obj):
            request=self.context.get('request')
            if request.user.is_authenticated:
                return obj.likes.filter(auth=request.user).exists()
            return False

