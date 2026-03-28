from tkinter.constants import CASCADE
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from shared.models import BaseModel
from datetime import datetime,timedelta
from config.settings import EMAIL_EXPIRATION_TIME,PHONE_EXPIRATION_TIME
import uuid
import random
from rest_framework_simplejwt.tokens import RefreshToken
import string
import secrets
from django.utils import timezone


ORDINARY_USER,ADMIN,MANAGER=('ordinary_user','admin','manager')
NEW,CODE_VERIFY,DONE,PHOTO_DONE=('new','code_verify','done','photo_done')
VIA_EMAIL,VIA_PHONE=('via_email','via_phone')



class CustomUser(AbstractUser,BaseModel):
    USER_ROLE=(
        (ORDINARY_USER,ORDINARY_USER),
        (ADMIN,ADMIN),
        (MANAGER,MANAGER)
    )

    USER_AUTH_STATUS=(
        (NEW,NEW),
        (CODE_VERIFY,CODE_VERIFY),
        (DONE,DONE),
        (PHOTO_DONE,PHOTO_DONE)
    )

    USER_AUTH_TYPE=(
        (VIA_EMAIL,VIA_EMAIL),
        (VIA_PHONE,VIA_PHONE)
    )

    user_role=models.CharField(max_length=20,choices=USER_ROLE,default=ORDINARY_USER)
    auth_status=models.CharField(max_length=20,choices=USER_AUTH_STATUS,default=NEW)
    auth_type=models.CharField(max_length=20,choices=USER_AUTH_TYPE)
    email=models.EmailField(max_length=50,null=True,blank=True,unique=True)
    phone=models.CharField(max_length=13,null=True,blank=True,unique=True)
    photo=models.ImageField(upload_to='user_photos/',validators=[FileExtensionValidator(allowed_extensions=['png','jpg','heic'])],null=True,blank=True)

    def __str__(self):
        return self.username


    def check_username(self):
        if not self.username:
            temp_username= f"username{uuid.uuid4().__str__().split('-')[-1]}"
            user=CustomUser.objects.filter(username=temp_username).first()
            if user:
                while user.exists():
                    temp_username+=str(random.randint(0,9))
            self.username=temp_username



    def check_pass(self):
        if not self.password:
            temp_password=f"username{uuid.uuid4().__str__().split('-')[-1]}"
            self.password=temp_password

    def hashing_pass(self):
        if not self.password.startswith('pbkdf2_sha256'):
            self.set_password(self.password)


    def check_email(self):
        if self.email:
            self.email = self.email.lower().strip()


    def token(self):
        refresh_token=RefreshToken.for_user(self)

        data={
            'refresh':str(refresh_token),
            'access':str(refresh_token.access_token)
        }
        return data


    def generate_code(self,verify_type):
        a = string.digits + string.ascii_letters
        code = ''.join(secrets.choice(a) for _ in range(6))
        CodeVerify.objects.create(
            code=code,
            user=self,
            verify_type=verify_type
        )
        return code



    # def generate_code(self,verify_type):
    #     code=random.randint(1000,9999)
    #     return code




    def clean(self):
        self.check_email()
        self.check_username()
        self.check_pass()
        self.hashing_pass()


    def save(self,*args,**kwargs):
        self.clean()
        super().save(*args,**kwargs)







class CodeVerify(BaseModel):
    VERIFY_TYPE = (
        (VIA_EMAIL, VIA_EMAIL),
        (VIA_PHONE, VIA_PHONE)
    )

    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='verify_codes')
    code=models.CharField(max_length=6)
    verify_type=models.CharField(max_length=30,choices=VERIFY_TYPE)
    expiration_time=models.DateTimeField()
    is_active = models.BooleanField(default=False)


    def save(self,*args,**kwargs):
        if self.verify_type==VIA_EMAIL:
            self.expiration_time=timezone.now()+timedelta(minutes=EMAIL_EXPIRATION_TIME)
        else:
            self.expiration_time=timezone.now()+timedelta(minutes=PHONE_EXPIRATION_TIME)
        return super().save(*args,**kwargs)

    def __str__(self):
        return f"{self.user.username} | {self.code}"



class Post(models.Model):
    auth=models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='auth')
    text=models.TextField(null=True,blank=True)
    image=models.ImageField(upload_to='post_image/',null=True,blank=True)
    video=models.FileField(upload_to='post_video/',null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)


class PostLike(models.Model):
    auth=models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='like')
    post=models.ForeignKey(Post,on_delete=models.CASCADE,related_name='likes')
    created_at=models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together=('post','auth')



class Comment(models.Model):
    post=models.ForeignKey(Post,on_delete=models.CASCADE)
    auth=models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    text=models.TextField()
    created_at=models.DateTimeField(auto_now_add=True)


class Follow(models.Model):
    follower=models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='follower')
    following=models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='followers')
    created_at=models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together=('follower','following')


class Story(models.Model):
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='stories')
    image=models.ImageField(upload_to='stories/',null=True,blank=True)
    video=models.FileField(upload_to='stories/',null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    expires_at=models.DateTimeField()
