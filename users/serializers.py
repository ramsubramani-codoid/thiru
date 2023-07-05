from rest_framework import serializers
from .models import Threshold, User,verification,IssueCategoryBucketing,TicketsModel, Chat
from django.contrib.auth.hashers import make_password

class UserSerializer(serializers.ModelSerializer):
    class Meta:

        model = User
        fields = ['id','email','role','username']

        extra_kwargs = {
            'password': {'write_only':True}
        }
    
    def create(self, validated_data):
        try:
            password = validated_data.pop('password',None)
        except:
            password = None
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.password = make_password(password,'test')
        instance.save()
        return instance

class UserdetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id','email','role','username','address','ward','prooftype','proofid','address1']

class UserupdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id','email','role','username','ward','prooftype','proofid','notify','role','address','address1']

class VerificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = verification
        fields = '__all__'



class UserSerializeradmin(serializers.ModelSerializer):
    class Meta:

        model = User
        fields = ['id', 'email', 'username', 'provider', 'password','ward','prooftype','proofid','notify','role','address','fid','address1','mobile']

        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        try:
            password = validated_data.pop('password', None)
        except:
            password = None
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.password = make_password(password, 'test')
        instance.save()
        return instance

class GetAllIssueBucketing(serializers.ModelSerializer):

    class Meta:
        model = IssueCategoryBucketing
        fields = '__all__'


class ChatSerializer(serializers.ModelSerializer):

    class Meta:
        model = Chat
        fields = '__all__'


class GetAllDataTickets(serializers.ModelSerializer):
    chat = ChatSerializer(read_only=True, many=True)
    class Meta:
        model = TicketsModel
        fields = '__all__'


class getallcategorythreshold(serializers.ModelSerializer):
    class Meta:
        model = Threshold
        fields = '__all__'


