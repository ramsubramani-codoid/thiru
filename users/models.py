from django.contrib.auth.hashers import make_password
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from django_mysql.models import JSONField
from django.dispatch import receiver
import os
# Create your models here.


class UserManager(BaseUserManager):

    def create_user(self,
                    email,
                    provider=None,
                    username=None,
                    password=None,
                    is_active=True,
                    is_staff=False,
                    is_admin=False,
                    is_superuser=False
                    ):
        if not email:
            raise ValueError("Email is required")
        user_obj = self.model(
            email=email,
            username=username
        )
        if password:
            user_obj.password = make_password(password, 'test')
        else:
            user_obj.password = None
        if provider is not None:
            user_obj.provider = provider
        user_obj.staff = is_staff
        user_obj.admin = is_admin
        user_obj.active = is_active
        user_obj.is_superuser = is_superuser
        user_obj.save(using=self._db)
        return user_obj

    def create_superuser(self, email, username, password):
        user = self.create_user(
            username=username,
            email=email,
            password=password,
            is_active=True,
            is_staff=True,
            is_admin=True,
            is_superuser=True
        )
        return user


class User(AbstractUser):
    email = models.CharField(unique=True, max_length=255)
    username = models.CharField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    mobile = models.CharField(blank=True, null=True, max_length=16)
    address = models.TextField(blank=True, null=True)
    address1 = models.TextField(blank=True, null=True)
    localgovt = models.CharField(max_length=16, blank=True, null=True)
    age = models.TextField(blank=True, null=True)
    gender = models.TextField(blank=True, null=True)
    ward = models.TextField(blank=True, null=True)
    prooftype = models.TextField(blank=True, null=True)
    proofid = models.TextField(blank=True, null=True)
    notify = models.TextField(blank=True, null=True)
    role = models.TextField(blank=True, null=True)
    provider = models.CharField(max_length=16, default='email')
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    valid = models.BooleanField(default=False)
    active = models.BooleanField(default=True)  # can login
    staff = models.BooleanField(default=False)  # staff user non super
    admin = models.BooleanField(default=False)  # superuser
    # fid = ListCharField(
    #     base_field=CharField(max_length=10),
    #     size=20,
    #     max_length=(20 * 11),blank=True, null=True
    # )
    fid = JSONField(blank=True, null=True)

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def is_staff(self):
        return self.staff

    @property
    def is_admin(self):
        return self.admin

    @property
    def is_active(self):
        return self.active


class UserUpload_media(models.Model):
    User_media_id = models.AutoField(primary_key=True)
    Ticket_creation_in = models.IntegerField()
    User_media = models.FileField(
        upload_to='UserUpload', max_length=250, null=True, blank=True)
    User_media_type = models.TextField(blank=True, null=True)
    Time = models.DateTimeField(auto_now_add=timezone.now)
    Valid = models.BooleanField(default=True)

    class Meta:
        db_table = 'UserUpload_media'


@receiver(models.signals.pre_save, sender=UserUpload_media)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old file from filesystem
    when corresponding `MediaFile` object is updated
    with new file.
    """
    if not instance.pk:
        return False

    try:
        old_file = UserUpload_media.objects.get(
            User_media_id=instance.pk).User_media
    except UserUpload_media.DoesNotExist:
        return False

    new_file = instance.User_media
    if not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)


@receiver(models.signals.post_delete, sender=UserUpload_media)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `MediaFile` object is deleted.
    """
    if instance.User_media:
        if os.path.isfile(instance.User_media.path):
            os.remove(instance.User_media.path)


class AgentUpload_media(models.Model):
    Agent_media_id = models.AutoField(primary_key=True)
    Ticket_creation_in = models.IntegerField()
    Agent_media = models.FileField(
        upload_to='AgentUpload', max_length=250, null=True, blank=True)
    Agent_media_type = models.TextField(blank=True, null=True)
    Time = models.DateTimeField(auto_now_add=timezone.now)
    Valid = models.BooleanField(default=True)

    class Meta:
        db_table = 'AgentUpload_media'


@receiver(models.signals.pre_save, sender=AgentUpload_media)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old file from filesystem
    when corresponding `MediaFile` object is updated
    with new file.
    """
    if not instance.pk:
        return False

    try:
        old_file = AgentUpload_media.objects.get(
            Agent_media_id=instance.pk).Agent_media
    except AgentUpload_media.DoesNotExist:
        return False

    new_file = instance.Agent_media
    if not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)


@receiver(models.signals.post_delete, sender=AgentUpload_media)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `MediaFile` object is deleted.
    """
    if instance.Agent_media:
        if os.path.isfile(instance.Agent_media.path):
            os.remove(instance.Agent_media.path)


class verification(models.Model):
    Userid = models.AutoField(primary_key=True)
    Phonenumber = models.CharField(max_length=100, null=False, blank=False)
    OTP = models.CharField(null=False, max_length=100, blank=False)
    Time = models.DateTimeField(auto_now_add=timezone.now)
    valid = models.BooleanField(default=False)

    class Meta:
        db_table = 'OTPVerification'


class IssueCategoryBucketing(models.Model):

    Issueid = models.AutoField(primary_key=True)
    IssueName = models.TextField(blank=True, null=True)
    IssueCategory = models.TextField(blank=True, null=True)
    IssueType = models.TextField(blank=True, null=True)
    Time = models.DateTimeField(
        auto_now_add=timezone.now, blank=True, null=True)
    valid = models.BooleanField(default=True)
    Threshold = models.IntegerField(null=True,default=0,blank=True)

    class Meta:
        db_table = 'IssueCategoryBucketing'


class TicketsModel(models.Model):
    TicketId = models.AutoField(primary_key=True)
    IssueName = models.TextField(blank=True, null=True)
    IssueCategory = models.TextField(blank=True, null=True)
    IssueDescription = models.TextField(blank=True, null=True)
    Note = models.TextField(blank=True, null=True)
    localgovt = models.CharField(max_length=300, blank=True, null=True)
    termtype = models.CharField(max_length=300, blank=True, null=True)
    location = models.TextField(blank=True, null=True)
    Username = models.CharField(max_length=255, blank=True, null=True)
    Address = models.TextField(blank=True, null=True)
    Address1 = models.TextField(blank=True, null=True)
    ContactNo = models.TextField(blank=True, null=True)
    GovtType = models.TextField(blank=True, null=True)
    GovtId = models.TextField(blank=True, null=True)
    WardNo = models.TextField(blank=True, null=True)
    Priority = models.TextField(blank=True, null=True)
    Fam = JSONField(blank=True, null=True)
    AfterIssueDescription = models.TextField(blank=True, null=True)
    StatusVerification = models.TextField(blank=True, null=True)
    CreatedBy = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL)
    CreatedFor = models.TextField(blank=True, null=True)
    Time = models.DateTimeField(
        auto_now_add=timezone.now, blank=True, null=True)
    valid = models.TextField(blank=True, null=True, default="0")
    OtherStatus = models.TextField(blank=True, null=True)
    SerialId = models.TextField(blank=True, null=True)
    TicketStatus = models.TextField(blank=True, null=True, default="0")
    SegId = models.TextField(blank=True, null=True)
    FaId = models.TextField(blank=True, null=True)
    SegTime = models.DateTimeField(blank=True, null=True)
    FaTime = models.DateTimeField(blank=True, null=True)
    via = models.CharField(max_length=300, default='Call Center')
    follow = models.IntegerField(default=0)
    FaAssignTime = models.DateTimeField(blank=True, null=True)
    # CompletionDate = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'Tickets Model'


class AddressDetails(models.Model):
    Addressid = models.AutoField(primary_key=True)
    Address = models.TextField(blank=True, null=True)
    Ward = models.TextField(blank=True, null=True)
    Area = models.TextField(blank=True, null=True)
    Lat = models.TextField(blank=True, null=True)
    Long = models.TextField(blank=True, null=True)
    Time = models.DateTimeField(
        auto_now_add=timezone.now, blank=True, null=True)
    valid = models.BooleanField(default=False)

    class Meta:
        db_table = 'Address Details'


class NotificationDetails(models.Model):
    ID = models.AutoField(primary_key=True)
    Role = models.CharField(max_length=255, blank=True, null=True)
    Title = models.CharField(max_length=600, blank=True, null=True)
    Description = models.CharField(max_length=600, blank=True, null=True)
    SourceUrl = models.CharField(max_length=400, null=True, blank=True)
    Type = models.CharField(max_length=400, null=True, blank=True)
    Date = models.DateTimeField(auto_now_add=True, verbose_name='Created On')
    UsersIds = JSONField(blank=True, null=True)
    AccessToken = JSONField(blank=True, null=True)

    class Meta:
        db_table = 'Notification_SendData'
        verbose_name = 'User Category'
        verbose_name_plural = 'User Category'

    def __str__(self):
        return self.Category


class SocialUser(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True, related_name='social_user')
    state = models.CharField(max_length=255, blank=True, null=True)
    temp = models.TextField(blank=True, null=True)


class Chat(models.Model):
    ticket = models.ForeignKey(
        TicketsModel, on_delete=models.CASCADE, related_name='chat')
    message = models.TextField()
    media_type = models.CharField(max_length=300, default='text')
    sender = models.CharField(max_length=300, default='public')
    time = models.DateTimeField(auto_now_add=timezone.now)


class AreaCategory(models.Model):
    ID = models.AutoField(primary_key=True)
    areaName = models.CharField(max_length=400, null=True, blank=True)


class AgentRemarks(models.Model):
    Id = models.AutoField(primary_key=True)
    Ticket_id = models.IntegerField()
    Remarks = models.TextField(blank=True, null=True)
    Date = models.DateTimeField(auto_now_add=timezone.now)

    class Meta:
        db_table = 'Agent_remarks'

class Threshold(models.Model):
    Id = models.AutoField(primary_key=True)
    Category=models.CharField(max_length=400,blank=True)
    Threshold=models.CharField(max_length=400,blank=True)

    class Meta:
        db_table = 'Threshold'
        
    def __str__(self):
        return self.Category