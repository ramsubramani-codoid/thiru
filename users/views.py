from django_mysql.models.fields import json
from firebase_admin import credentials, messaging
import firebase_admin
from social.views import WhatsappView
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from .serializers import UserSerializer, VerificationSerializer, UserdetailsSerializer, UserSerializeradmin, \
    GetAllIssueBucketing, GetAllDataTickets, UserupdateSerializer, getallcategorythreshold
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password
from .models import AreaCategory, SocialUser, Threshold, verification, IssueCategoryBucketing, TicketsModel, UserUpload_media, AgentUpload_media, \
    AddressDetails, NotificationDetails, Chat, AgentRemarks
from random import randint
from django.core.mail import send_mail
from django.conf import settings
import requests
import clx.xms
import time
from datetime import date, timedelta
from django.utils import timezone

from social.social import client, host, send_whatsapp_file_message, send_whatsapp_message, set_social_user_state
from social.messages import messages

import datetime
import json
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q

User = get_user_model()


cred = credentials.Certificate(
    "users/Notifications/namma-thiruvalikeni-firebase-adminsdk-ti293-243846bc1a.json")
firebase_admin.initialize_app(cred)


@permission_classes((AllowAny,))
class Verifications(APIView):
    def post(self, request, *args, **kwargs):
        request.POST._mutable = True

        n = 6
        randint(100000, 999999)
        range_start = 10 ** (n - 1)
        range_end = (10 ** n) - 1
        otp = randint(range_start, range_end)

        # if id == '1':
        number = request.data['mobile']
        request.data['Phonenumber'] = number
        request.data['OTP'] = "12345"
        verify = verification.objects.filter(Phonenumber=number, valid=1)
        if verify:
            return Response({"message": "Phone Number is already Registered. Please Sign in", "status": "fail"},
                            status=status.HTTP_502_BAD_GATEWAY)
        form_data = VerificationSerializer(data=request.data, )
        if form_data.is_valid():
            form_data.save()

        else:
            return Response({"message": form_data.errors, "status": "fail"}, status=status.HTTP_502_BAD_GATEWAY)
        mobiles = "91" + str(number)

        client = clx.xms.Client(service_plan_id='df8a4334f6924e288d31de3b92abdf23',
                                token='aae2a2d684d941e7b8035b4e2fee5ebc')

        create = clx.xms.api.MtBatchTextSmsCreate()
        create.sender = '447537454953'
        create.recipients = {mobiles}
        create.body = 'blood donation your OTP is ' + str(otp)

        try:
            batch = client.create_batch(create)
        except (requests.exceptions.RequestException,
                clx.xms.exceptions.ApiException) as ex:
            print('Failed to communicate with XMS: %s' % str(ex))

        return Response(
            {"message": "A verification code has been sent to your registered mobile number, please verify.",
             "status": "pass"})


@permission_classes((AllowAny,))
class Registerusers(APIView):
    def post(self, request):
        print(request.data)

        def setData(user):
            return {'id': user.pk, 'name': user.username, 'mobile': user.email}
        request.POST._mutable = True
        phno = request.data['mobile']
        username = request.data['userName']
        user = User.objects.filter(email=phno).first()
        data = {}
        if user:
            tickets = TicketsModel.objects.filter(
                CreatedFor=user.pk, TicketStatus='0').all()
            provider = user.provider
            if tickets:
                details = []
                for ticket in tickets:
                    details.append({
                        'TicketId': ticket.TicketId,
                        'valid': ticket.valid,
                        'TicketStatus': ticket.TicketStatus,
                        'Time': ticket.Time
                    })
                data['tickets'] = details
                if provider == 'whatsapp':
                    data['UserData'] = setData(user)
                    return Response({"message": "ticket by whatsapp", "data": data})
                else:
                    data['UserData'] = setData(user)
                    return Response({"message": "ticket by call", "data": data})
            else:
                if provider == 'whatsapp':
                    return Response({"message": "registered by whatsapp"})
                else:
                    data['UserData'] = setData(user)
                    return Response({"message": "registered by call", "data": data})
        else:
            user = User()
            user.email = phno
            user.username = username
            user.role = 'public'
            user.save()
            verify = verification()
            verify.Phonenumber = phno
            verify.OTP = '12345'
            verify.valid = True
            verify.save()
            data['UserData'] = setData(user)
            return Response({"message": "Registered", "data": data})

    def put(self, request):
        request.POST._mutable = True
        try:
            data = request.data
            obj = User.objects.get(email=data['mobile'])
            for key, value in data.items():
                setattr(obj, key, value)
            obj.save()

            serializer = UserupdateSerializer(obj)

            return Response({"message": "successfully updated", "data": serializer.data, "status": "pass"},
                            status=status.HTTP_200_OK)
        except:
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
                            status=status.HTTP_400_BAD_REQUEST)


@permission_classes((AllowAny,))
class LoginotpUser(APIView):
    def post(self, request, *args, **kwargs):
        request.POST._mutable = True
        try:
            phno = request.data['mobile']
            phverify = verification.objects.filter(Phonenumber=phno, valid=1)

            if phverify:
                n = 6
                randint(100000, 999999)
                range_start = 10 ** (n - 1)
                range_end = (10 ** n) - 1
                otp = randint(range_start, range_end)

                mobiles = "91" + str(phno)

                client = clx.xms.Client(service_plan_id='7ebf3b56b7a345f0b668d8a05305f6a8',
                                        token='46036e6906dc458ea09e799954e44e35')

                create = clx.xms.api.MtBatchTextSmsCreate()
                create.sender = '447537404817'
                create.recipients = {mobiles}
                create.body = 'blood donation your OTP is ' + str(otp)

                try:
                    batch = client.create_batch(create)
                except (requests.exceptions.RequestException,
                        clx.xms.exceptions.ApiException) as ex:
                    print('Failed to communicate with XMS: %s' % str(ex))

                obj = verification.objects.get(Phonenumber=phno, valid=1)
                obj.OTP = "12345"
                obj.Time = datetime.datetime.now()
                obj.save()
                return Response(
                    {"message": "A verification code has been sent to your registered mobile number, please verify.",
                     "status": "pass"}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "You are not a registered user. Please Register", "status": "fail"},
                                status=status.HTTP_502_BAD_GATEWAY)
        except:
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
                            status=status.HTTP_400_BAD_REQUEST)


@permission_classes((AllowAny,))
class verfiyloginuser(APIView):
    def post(self, request, *args, **kwargs):
        request.POST._mutable = True
        try:
            otpval = request.data['OTP']
            phno = request.data['mobile']

            validations = verification.objects.filter(Phonenumber=phno, OTP=otpval, valid=1).values('Time',
                                                                                                    'Userid').last()

            if validations:
                timevalidation = validations['Time']

                experiytime = timevalidation + datetime.timedelta(minutes=5)
                curent = timezone.now()
                if experiytime.time() > curent.time():
                    user = User.objects.filter(email=phno).first()
                    serializer = UserdetailsSerializer(user)
                    token = get_tokens_for_user(user)

                    dataall = TicketsModel.objects.filter(CreatedFor=serializer.data['id'], TicketStatus="0").values(
                        'TicketId', 'IssueName', 'IssueCategory',
                        'Priority', 'valid', 'TicketStatus',
                        'Time', 'termtype', 'follow',
                        'localgovt', 'location').exclude(valid="3")

                    dataallc = TicketsModel.objects.filter(CreatedFor=serializer.data['id'], TicketStatus="1").values(
                        'TicketId', 'IssueName', 'IssueCategory',
                        'Priority', 'valid', 'TicketStatus',
                        'Time', 'termtype', 'localgovt', 'location').exclude(valid="3")

                    dataallIv = TicketsModel.objects.filter(CreatedFor=serializer.data['id'], valid="3").values(
                        'TicketId', 'IssueName', 'IssueCategory',
                        'Priority', 'valid', 'TicketStatus',
                        'Time', 'termtype', 'localgovt',
                        'location')

                    data = {'closeTicketCount': len(dataallc), 'OpenTicketCount': len(dataall),
                            'InvalidTicketCount': len(dataallIv)}
                    data.update(serializer.data)

                    return Response({"message": "successfully login", "token": token, "data": data,
                                     "status": "pass"}, status=status.HTTP_200_OK)
                else:
                    return Response({"message": "Invalid number, the verification number is valid for 5 minutes only!",
                                     "status": "fail"}, status=status.HTTP_406_NOT_ACCEPTABLE)
            else:
                return Response({"message": "Invalid OTP number. please try agian later!!", "status": "fail"},
                                status=status.HTTP_406_NOT_ACCEPTABLE)
        except:
            return Response({"message": "Provide Valid Data", "status": "fail"}, status=status.HTTP_502_BAD_GATEWAY)


@permission_classes((AllowAny,))
class Admincreateuser(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token = request.META.get('HTTP_AUTHORIZATION')

        request.POST._mutable = True
        try:
            serializer = UserSerializeradmin(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'message': "successfully registerd", 'data': serializer.data, "status": "pass",
                                 'token': str(token).split(" ")[1]}, status=status.HTTP_200_OK)
            else:
                return Response({'message': "already registerd", "status": "pass", 'token': str(token).split(" ")[1]},
                                status=status.HTTP_406_NOT_ACCEPTABLE)
        except:
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
                            status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        request.POST._mutable = True
        try:
            data = request.data
            obj = User.objects.filter(email=data['email']).first()
            for key, value in data.items():
                setattr(obj, key, value)
            obj.save()

            serializer = UserupdateSerializer(obj)

            return Response({"message": "successfully updated", "data": serializer.data, "status": "pass"},
                            status=status.HTTP_200_OK)
        except:
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
                            status=status.HTTP_400_BAD_REQUEST)


class Backenduserlogin(APIView):

    def post(self, request):
        request.POST._mutable = True
        try:
            email = request.data['email']
            user = User.objects.filter(email=email).first()

            serializer = UserSerializer(user)
            # admin
            # pbkdf2_sha256$260000$test$rfJdxgRK3l57KQWaPMZQ4cg8qzx6kbCwxdh1OHowgsc=
            # call agent
            # pbkdf2_sha256$260000$test$Uf8llPXkcZLWsBmppiuQiVev9/Scav2TzSjVaw3yHPg=
            password = make_password(request.data['password'], 'test')
            print('from req', password)
            print('from db', user.password)

            if password != user.password:
                return Response({"message": 'Invalid username or password'}, status=status.HTTP_401_UNAUTHORIZED)
            token = get_tokens_for_user(user)
            return Response({'token': token, "data": serializer.data, "message": 'Logged In'}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
                            status=status.HTTP_400_BAD_REQUEST)


def registerUser(request):
    serializer = UserSerializer(data=request.data)

    serializer.is_valid(raise_exception=True)

    serializer.save()

    email = serializer.data['email']

    user = User.objects.filter(email=email).first()

    return get_tokens_for_user(user)


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class RegisterView(APIView):

    def post(self, request):
        token = registerUser(request)
        return Response(token, status=status.HTTP_200_OK)


class LoginView(APIView):

    def post(self, request):
        try:
            email = request.data['email']
            user = User.objects.filter(email=email).first()
            password = make_password(request.data['password'], 'test')
            if password != user.password:
                return Response('Unauthenticated', status=status.HTTP_401_UNAUTHORIZED)
            token = get_tokens_for_user(user)
            return Response({'token': token}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
                            status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):

    def get(self, request):
        response = Response()
        response.data = {
            'message': 'Logged Out!'
        }

        return response


class UserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        token = request.META.get('HTTP_AUTHORIZATION')
        try:
            user = User.objects.get(id=request.user.id)
            serializer = UserSerializer(user)
            return Response({'data': serializer.data, 'token': str(token).split(" ")[1]}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
                            status=status.HTTP_400_BAD_REQUEST)


@permission_classes((AllowAny,))
class GetAllissueDetails(APIView):
    def get(self, request):
        try:
            alldata = []
            category = []
            GetCdata = IssueCategoryBucketing.objects.filter(
                valid=True).values('IssueCategory').distinct()
            for i in GetCdata:
                category.append(i['IssueCategory'])
                datafd = []
                GetCdetail = IssueCategoryBucketing.objects.filter(IssueCategory=i['IssueCategory']).values(
                    'IssueName').distinct()
                for fd in GetCdetail:
                    datafd.append(fd['IssueName'])
                alldata.append({i['IssueCategory']: datafd})
            # alldata.append({'category': category})

            return Response({'data': {'issues': alldata, 'categories': category}}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
                            status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        try:
            issueCategory = request.data['issueCategory']
            issueValue = IssueCategoryBucketing.objects.filter(
                IssueCategory=issueCategory).values('Issueid')
            if issueValue:
                return Response({'data': None, 'message': 'already exist', "status": "exist"}, status=status.HTTP_200_OK)

            else:
                IssueCategoryBucketing(IssueCategory=issueCategory).save()
                return Response({'data': None, 'message': 'issue category created', "status": "pass"}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
                            status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, cat):
        permission_classes = [permissions.IsAuthenticated]
        try:
            obj = IssueCategoryBucketing.objects.get(IssueCategory=cat)
        except:
            return Response({'data': {}, 'status': 'error', 'message': "category not in the list"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            DeleteCat = IssueCategoryBucketing.objects.filter(
                IssueCategory=cat).delete()
            return Response({'data': {}, 'status': 'success', 'message': "Successfully deleted"}, status=status.HTTP_200_OK)

        except:
            return Response({'data': {}, 'status': 'error', 'message': "BAD REQUEST"}, status=status.HTTP_400_BAD_REQUEST)


def serialidcreation():
    svalue = False
    serialid = 0
    while svalue == False:
        n = 10
        randint(100000, 999999)
        range_start = 10 ** (n - 1)
        range_end = (10 ** n) - 1
        serialid = randint(range_start, range_end)
        getdataserial = TicketsModel.objects.filter(
            SerialId=str(serialid)).values('SerialId')
        if getdataserial:
            svalue = False
        else:
            svalue = True

    return serialid


@permission_classes((AllowAny,))
class SegrigationTicketClose(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        token = request.META.get('HTTP_AUTHORIZATION')
        request.POST._mutable = True
        try:
            # Object wich will be updated
            obj = TicketsModel.objects.get(TicketId=request.data['TicketId'])
            serializer = GetAllDataTickets(obj, data=request.data)
            if serializer.is_valid():
                serializer.save()
                getagentmedia = AgentUpload_media.objects.filter(
                    Ticket_creation_in=request.data['TicketId']).values('Agent_media')
                getfordet = TicketsModel.objects.filter(TicketId=request.data['TicketId']).values(
                    'CreatedFor', 'OtherStatus', 'AfterIssueDescription')
                getuserdatacreatefor = User.objects.filter(
                    id=getfordet[0]['CreatedFor']).values('username', 'email', 'role')
                mobile = getuserdatacreatefor[0]['email']
                soc_user = SocialUser.objects.filter(
                    user__email=mobile).first()
                if soc_user:
                    if getfordet:
                        for sendmsg in getfordet:
                            otherstatus = sendmsg.get('OtherStatus', None)
                            if otherstatus:
                                send_whatsapp_message(otherstatus, mobile)
                            afterIssue = sendmsg.get(
                                'AfterIssueDescription', None)
                            if afterIssue:
                                send_whatsapp_message(afterIssue, mobile)
                    send_whatsapp_message(messages['complaint_sorted'], mobile)
                    set_social_user_state('complaint_closed', mobile)
                    if getagentmedia:
                        send_whatsapp_message(
                            messages['complaint_media'], mobile)
                        for sendmsg in getagentmedia:
                            try:
                                media_url = host+'/media/' + \
                                    str(sendmsg['Agent_media'])
                                send_whatsapp_file_message(media_url, mobile)
                            except:
                                print('no')
                    try:
                        whatsapp_client = WhatsappView.clients.get(
                            str(mobile)+'*/'+str(getuserdatacreatefor[0]['username']), None)
                    except:
                        whatsapp_client = None
                    if whatsapp_client:
                        del WhatsappView.clients[str(
                            mobile)+'*/'+str(getuserdatacreatefor[0]['username'])]
                return Response(
                    {'message': "successfully close", "status": "pass",
                        'token': str(token).split(" ")[1]},
                    status=status.HTTP_200_OK)
            else:
                return Response(
                    {'message': "something went wrong", "status": "fail",
                        'token': str(token).split(" ")[1]},
                    status=status.HTTP_502_BAD_GATEWAY)
        except:
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
                            status=status.HTTP_400_BAD_REQUEST)


@permission_classes((AllowAny,))
class TicketCreation(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # print(request.data)
        # print(request.FILES.items())
        # for filename, file in request.FILES.items():
        #     print('file name ',filename)
        #     print('file ',file)

        # myfile is the name of your html file button
        for f in request.FILES.getlist('User_media'):
            filename = f.name
            print(filename)

        token = request.META.get('HTTP_AUTHORIZATION')

        request.POST._mutable = True
        try:
            serializer = GetAllDataTickets(data=request.data)
            if serializer.is_valid():
                id = serializer.save()
                mediaupload(id.TicketId, request.FILES.getlist('User_media'))

                # UserIdALL=[]
                # AllMids=[]
                # GetSegTeam=User.objects.filter(role="ST").values('id','notify')
                # if GetSegTeam:
                #     for add in GetSegTeam:
                #         UserIdALL.append(add['notify'])
                #         AllMids.append(add['id'])
                #
                #     savenotification = NotificationDetails(Role="ST", Title=request.data['IssueName'],
                #                                            Description=request.data['IssueName'], SourceUrl=id.TicketId,
                #                                            Type="auto",UsersIds=AllMids)
                #     savenotification.save()
                #
                #     datasend = {"Id": str(id.TicketId), 'Name': str(request.data['IssueName']), 'click_action': 'FLUTTER_NOTIFICATION_CLICK'}
                #     sendPush(request.data['IssueName'], "Hi Segrigation Team",datasend,UserIdALL)

                return Response(
                    {'message': "successfully registerd", "status": "pass",
                        'token': str(token).split(" ")[1]},
                    status=status.HTTP_200_OK)
            else:
                return Response(
                    {'message': "something went wrong", "status": "fail",
                        'token': str(token).split(" ")[1]},
                    status=status.HTTP_502_BAD_GATEWAY)
        except:
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
                            status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):

        token = request.META.get('HTTP_AUTHORIZATION')

        request.POST._mutable = True
        # print('remarks from field agent', request.data['remarks'])

        # remarks from field agent if no key called valid
        print('comming data from assigned', request.data)
        try:
            request.data['valid']
        except KeyError:
            print('remarks from field agent')
            try:
                agentRemarksUpload(
                    request.data['TicketId'], request.data['remarks'])

                try:
                    ticket = TicketsModel.objects.filter(
                        TicketId=request.data['TicketId']).values(
                        'TicketId', 'IssueName', 'IssueCategory',
                        'Priority', 'valid', 'TicketStatus',
                        'Time', 'termtype', 'localgovt', 'location')
                except:
                    pass

                return Response(
                    {'message': "remark updated", "status": "pass",
                     'data': ticket,
                     'token': str(token).split(" ")[1]},
                    status=status.HTTP_200_OK
                )

            except:
                pass

        try:
            # convet the stringify array from admin ticket assign to array
            try:
                request.data['Fam'] = json.loads(request.data['Fam'])
            except:
                pass

            serialid = serialidcreation()
            request.data['SerialId'] = serialid
            obj: TicketsModel = TicketsModel.objects.get(
                TicketId=request.data['TicketId'])  # Object wich will be updated
            serializer = GetAllDataTickets(obj, data=request.data)
            if serializer.is_valid():
                serializer.save()
                mediaupload(request.data['TicketId'],
                            request.FILES.getlist('User_media'))
                # if request.data['Role'] == 'ST':
                #     try:
                #         famdata=request.data['Fam']
                #         if len(famdata)!=0:
                #             ticid=request.data['TicketId']
                #             saveChat=Chat.objects.filter(ticket=int(ticid),sender='public').values('message','media_type').exclude(media_type='text')
                #
                #     except:
                #         print('st')

                # # start notification
                # if request.data['Role']=='ST':
                #     # send notification for user
                #     AllMids=[]
                #     UserIdALL=[]
                #     GetIdForUser=TicketsModel.objects.filter(TicketId=int(request.data['TicketId'])).values('CreatedFor','IssueName','IssueCategory')
                #
                #     getuserdetails=User.objects.filter(id=int(GetIdForUser[0]['CreatedFor'])).values('id','notify')
                #
                #     AllMids.append(getuserdetails[0]['id'])
                #     UserIdALL.append(getuserdetails[0]['notify'])
                #
                #     savenotification = NotificationDetails(Role="ST For Public", Title=GetIdForUser[0]['IssueName'],
                #                                            Description="We Are Received Your Ticket", SourceUrl=request.data['TicketId'],
                #                                            Type="auto",UsersIds=AllMids)
                #     savenotification.save()
                #
                #     datasend = {"Id": str(request.data['TicketId']), 'Name': str(GetIdForUser[0]['IssueName']), 'click_action': 'FLUTTER_NOTIFICATION_CLICK'}
                #     sendPush(GetIdForUser[0]['IssueName'],"We Are Received Your Ticket",datasend,UserIdALL)
                #
                #
                #     # print(request.data['Fam'],type(request.data['Fam']),type(list(request.data['Fam'])))
                #     try:
                #         FamDet=request.data['Fam']
                #         print(FamDet,type(FamDet))
                #         if FamDet:
                #             AllMainIdFam = []
                #             UserIdALLFam = []
                #             getuserdetailsFam = User.objects.filter(id__in=FamDet).values('id', 'notify')
                #             for ids in getuserdetailsFam:
                #                 AllMainIdFam.append(ids['id'])
                #                 UserIdALLFam.append(ids['notify'])
                #             savenotification = NotificationDetails(Role="ST For FA",
                #                                                    Title=GetIdForUser[0]['IssueName'],
                #                                                    Description="Assigned New Ticket",
                #                                                    SourceUrl=request.data['TicketId'],
                #                                                    Type="auto", UsersIds=AllMainIdFam)
                #             savenotification.save()
                #
                #             datasend = {"Id": str(request.data['TicketId']), 'Name': str(GetIdForUser[0]['IssueName']),
                #                         'click_action': 'FLUTTER_NOTIFICATION_CLICK'}
                #             sendPush(GetIdForUser[0]['IssueName'], "Assigned New Ticket", datasend, UserIdALLFam)
                #     except:
                #         print('no')
                #
                # # end of notification

                try:
                    Agentmediaupload(
                        request.data['TicketId'], request.FILES.getlist('Agent_media'))
                except:
                    print('ss')
                valid = request.data.get('valid', None)
                if valid:
                    user = User.objects.filter(pk=obj.CreatedFor).first()
                    soc_user = SocialUser.objects.filter(user=user).first()
                    if soc_user:
                        if valid == '1':
                            send_whatsapp_message(
                                messages['agent_assigned'], user.email)
                        if valid == '3':
                            send_whatsapp_message(
                                messages['invalid_complaint'], user.email)
                            set_social_user_state(
                                'complaint_closed', user.email)
                return Response(
                    {'message': "successfully Assigned", "status": "pass",
                        'token': str(token).split(" ")[1]},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'message': "something went wrong", "status": "fail",
                        'token': str(token).split(" ")[1]},
                    status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            print(e)
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
                            status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        # public mobile
        # field agent  - number
        # status - any
        # Pdf and excel

        token = request.META.get('HTTP_AUTHORIZATION')
        try:
            dataall = TicketsModel.objects.values('TicketId', 'IssueName', 'IssueCategory', 'IssueDescription', 'Priority',
                                                  'valid', 'Time', 'TicketStatus', 'via', 'CreatedFor', 'Fam', 'Note', 'follow', 'termtype', 'localgovt', 'location', 'FaAssignTime', 'FaTime').order_by('-Time')[:10]
            # 'FaAssignTime','FaTime'
            # serializer = GetAllDataTickets(dataall)
            # print(serializer.data)
            for data in dataall:

                if data['valid'] == '0':
                    Time = data['Time']
                    daydata = IssueCategoryBucketing.objects.filter(
                        IssueCategory="unassigned").values('Threshold')
                    Threshold = Thresholdcalculate(
                        daydata[0]['Threshold'], Time)
                    data['Threshold'] = Threshold
                if data['valid'] == '1':
                    daydata = IssueCategoryBucketing.objects.filter(
                        IssueCategory=data["IssueCategory"]).values('Threshold')
                    Time = data['FaAssignTime']
                    Threshold = Thresholdcalculate(
                        daydata[0]['Threshold'], Time)
                    data['Threshold'] = Threshold
                if data['valid'] == '2' and data['TicketStatus'] == '0':
                    daydata = IssueCategoryBucketing.objects.filter(
                        IssueCategory="completed").values('Threshold')
                    Time = data['FaTime']
                    Threshold = Thresholdcalculate(
                        daydata[0]['Threshold'], Time)
                    data['Threshold'] = Threshold
                else:
                    data['Threshold'] = 0

                # print('threshold',Threshold)

                public = data.get('CreatedFor', None)
                if public:
                    public = User.objects.filter(pk=public).first()
                    pub_mobile = public.email
                    data['CreatedFor'] = pub_mobile
                fams = data.get('Fam', None)
                if fams:
                    Fam = ''
                    for index, fam in enumerate(fams):
                        user = User.objects.filter(pk=fam).first()
                        Fam += user.username + ' - ' + user.mobile
                        if index != fams.__len__()-1:
                            Fam = Fam+'\n'
                    data['Fam'] = Fam
                else:
                    data['Fam'] = 'Not Assigned'

                 # get no of agent remarks for particular tickets
                ticketId = data.get('TicketId', None)
                agentRemarksCount = AgentRemarks.objects.filter(
                    Ticket_id=int(ticketId)).values('Remarks').count()
                data['RemarksCount'] = agentRemarksCount

            return Response(
                {'message': "successfully Retrive", "data": dataall, "status": "pass",
                    'token': str(token).split(" ")[1]}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
                            status=status.HTTP_400_BAD_REQUEST)

    # def get(self, request):
    #     # public mobile
    #     # field agent  - number
    #     # status - any
    #     # Pdf and excel
    #         token = request.META.get('HTTP_AUTHORIZATION')
    #     # try:
    #         dataall = TicketsModel.objects.filter(TicketId=7).values('TicketId', 'IssueName', 'IssueCategory', 'IssueDescription', 'Priority','FaAssignTime','FaTime'
    #                                                                 'valid', 'Time', 'TicketStatus', 'via', 'CreatedFor', 'Fam', 'Note', 'follow', 'termtype', 'localgovt', 'location')
    #         # serializer = GetAllDataTickets(dataall)
    #         # print(serializer.data)
    #         for data in dataall:
    #             if data['valid'] == '0':
    #                     Time=data['Time']
    #                     daydata=IssueCategoryBucketing.objects.filter(IssueCategory="unassigned").values('Threshold')
    #                     Threshold=Thresholdcalculate(daydata[0]['Threshold'],Time)
    #                     data['Threshold']=Threshold
    #             if data['valid'] == '1':
    #                     daydata=IssueCategoryBucketing.objects.filter(IssueCategory=data["IssueCategory"]).values('Threshold')
    #                     Time=data['FaAssignTime']
    #                     Threshold=Thresholdcalculate(daydata[0]['Threshold'],Time)
    #                     data['Threshold']=Threshold
    #             if data['valid'] == '2' and data['TicketStatus'] == '0':
    #                     daydata=IssueCategoryBucketing.objects.filter(IssueCategory="completed").values('Threshold')
    #                     Time=data['FaTime']
    #                     Threshold=Thresholdcalculate(daydata[0]['Threshold'],Time)
    #                     data['Threshold']=Threshold
    #             else:
    #                 data['Threshold']=0

    #             public = data.get('CreatedFor', None)
    #             if public:
    #                 public = User.objects.filter(pk=public).first()
    #                 pub_mobile = public.email
    #                 data['CreatedFor'] = pub_mobile
    #             fams = data.get('Fam', None)
    #             # print('fams', fams)
    #             if fams:
    #                 Fam = ''
    #                 for index, fam in enumerate(fams):
    #                     # print('fam', fam)
    #                     # fam = int(fam)
    #                     user = User.objects.filter(pk=fam).first()
    #                     Fam += user.username + ' - ' + user.mobile
    #                     if index != fams.__len__()-1:
    #                         Fam = Fam+'\n'
    #                 data['Fam'] = Fam
    #             else:
    #                 data['Fam'] = 'Not Assigned'

    #              # get no of agent remarks for particular tickets
    #             ticketId = data.get('TicketId', None)
    #             agentRemarksCount = AgentRemarks.objects.filter(
    #                 Ticket_id=int(ticketId)).values('Remarks').count()
    #             data['RemarksCount'] = agentRemarksCount

    #         return Response(
    #             {'message': "successfully Retrive", "data": dataall, "status": "pass",
    #                 'token': str(token).split(" ")[0]}, status=status.HTTP_200_OK)
    #     # except:
    #         # return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
    #         #                 status=status.HTTP_400_BAD_REQUEST)


@permission_classes((AllowAny,))
class Getparticularticketdetails(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        try:
            getalldata = TicketsModel.objects.filter(TicketId=int(id)).values('IssueName', 'IssueCategory', 'IssueDescription', 'Priority', 'Fam', 'AfterIssueDescription', 'StatusVerification', 'CreatedBy', 'Time',
                                                                              'valid', 'OtherStatus', 'SerialId',
                                                                              'CreatedFor', 'TicketStatus', 'SegId',
                                                                              'FaId', 'Username', 'Address',
                                                                              'ContactNo', 'GovtType', 'GovtId',
                                                                              'WardNo', 'SegTime', 'FaTime',
                                                                              'Address1', 'via', 'follow',
                                                                              'Note', 'termtype', 'localgovt',
                                                                              'location')
            createdby = []
            createdfor = []
            SegIdlist = []
            FaIdlist = []
            print(getalldata)
            try:
                getuserdata = User.objects.filter(
                    id=getalldata[0]['CreatedBy']).values('username', 'email', 'role')
                createdby.append(
                    {'username': getuserdata[0]['username'], 'email': getuserdata[0]['email'],
                     'role': getuserdata[0]['role']})
            except:
                print('d')

            try:
                getuserdatacreatefor = User.objects.filter(id=getalldata[0]['CreatedFor']).values('username', 'email',
                                                                                                  'role')

                createdfor.append(
                    {'username': getuserdatacreatefor[0]['username'], 'email': getuserdatacreatefor[0]['email'],
                     'role': getuserdatacreatefor[0]['role']})
            except:
                print('s')

            try:
                SegId = User.objects.filter(id=getalldata[0]['SegId']).values(
                    'username', 'email', 'role')

                SegIdlist.append(
                    {'username': SegId[0]['username'], 'email': SegId[0]['email'], 'role': SegId[0]['role']})
            except:
                print('d')

            try:
                FaId = User.objects.filter(id=getalldata[0]['FaId']).values(
                    'username', 'email', 'role')

                FaIdlist.append(
                    {'username': FaId[0]['username'], 'email': FaId[0]['email'], 'role': FaId[0]['role']})
            except:
                print('w')

            AddressDetailsData = []
            getparticularaddlong = AddressDetails.objects.filter(Address=getalldata[0]['Address']).values(
                'Address', 'Ward', 'Area',
                'Lat', 'Long'
            )

            if getparticularaddlong:
                for addr in getparticularaddlong:
                    AddressDetailsData.append({'Address': addr['Address'], 'Ward': addr['Ward'], 'Area': addr['Area'],
                                               'Latitute': addr['Lat'], 'Longitude': addr['Long']})

            agentnames = []
            # print(type(getalldata[0]['Fam']), getalldata[0]['Fam'])

            if getalldata[0]['Fam']:

                for fam in getalldata[0]['Fam']:
                    # print(fam)
                    getuserdataid = User.objects.filter(id=fam).values(
                        'id', 'username', 'email', 'role')
                    agentnames.append({'id': getuserdataid[0]['id'], 'username': getuserdataid[0]['username'],
                                       'email': getuserdataid[0]['email'],
                                       'role': getuserdataid[0]['role']})

            # getuserimage

            allgetuserimage = []

            getuserimages = UserUpload_media.objects.filter(Ticket_creation_in=id).values(
                'User_media_id', 'Ticket_creation_in',
                'User_media', 'User_media_type', 'Time', 'Valid'
            )

            # get filed agent remarks
            agentRemarks = AgentRemarks.objects.filter(
                Ticket_id=int(id)).values('Remarks', 'Date')

            # print('agent remarks', agentRemarks)

            saveChat = Chat.objects.filter(ticket=int(id), sender='public').values('id', 'message', 'media_type',
                                                                                   'ticket', 'time').exclude(media_type='text')

            if getuserimages:
                for imgusr in getuserimages:
                    allgetuserimage.append(
                        {'User_media_id': imgusr['User_media_id'], 'Ticket_creation_in': imgusr['Ticket_creation_in'],
                         'User_media': imgusr['User_media'], 'Time': imgusr['Time'], 'Valid': imgusr['Valid'], 'ViaWhatsapp': False, 'User_media_type': imgusr['User_media_type']})
            if saveChat:
                for imgusr in saveChat:
                    allgetuserimage.append(
                        {'User_media_id': imgusr['id'], 'Ticket_creation_in': imgusr['ticket'],
                         'User_media': imgusr['message'], 'Time': imgusr['time'], 'Valid': True, 'ViaWhatsapp': True, 'media_type': imgusr['media_type']})

            # agentuploadimage

            allgetagentimage = []

            getagentimages = AgentUpload_media.objects.filter(Ticket_creation_in=id).values(
                'Agent_media_id', 'Ticket_creation_in',
                'Agent_media', 'Agent_media_type', 'Time', 'Valid'
            )

            if getagentimages:
                for imgusr in getagentimages:
                    allgetagentimage.append(
                        {'Agent_media_id': imgusr['Agent_media_id'], 'Ticket_creation_in': imgusr['Ticket_creation_in'],
                         'Agent_media': imgusr['Agent_media'], 'Time': imgusr['Time'], 'Valid': imgusr['Valid'], 'Agent_media_type': imgusr['Agent_media_type']})

            data = {'Username': getalldata[0]['Username'], 'Address': getalldata[0]['Address'], 'Address1': getalldata[0]['Address1'], 'localgovt': getalldata[0]['localgovt'], 'termtype': getalldata[0]['termtype'],
                    'location': getalldata[0]['location'],
                    'ContactNo': getalldata[0]['ContactNo'], 'GovtType': getalldata[0]['GovtType'],
                    'GovtId': getalldata[0]['GovtId'], 'WardNo': getalldata[0]['WardNo'],
                    'IssueName': getalldata[0]['IssueName'],
                    'IssueCategory': getalldata[0]['IssueCategory'],
                    'IssueDescription': getalldata[0]['IssueDescription'], 'Priority': getalldata[0]['Priority'],
                    'Fam': agentnames, 'AfterIssueDescription': getalldata[0]['AfterIssueDescription'],
                    'StatusVerification': getalldata[0]['StatusVerification'],
                    'CreatedBy': createdby, 'Time': getalldata[0]['Time'], 'valid': getalldata[0]['valid'],
                    'TicketStatus': getalldata[0]['TicketStatus'],
                    'OtherStatus': getalldata[0]['OtherStatus'], 'SerialId': getalldata[0]['SerialId'],
                    'CreatedFor': createdfor, 'UserUploadImage': allgetuserimage, 'AgentUploadImage': allgetagentimage, 'AgentRemarks': agentRemarks,
                    'FieldAgentId': FaIdlist, 'SeggrigationId': SegIdlist, 'SegValidTime': getalldata[0]['SegTime'],
                    'FieldAgentValidTime': getalldata[0]['FaTime'], 'MapAddress': AddressDetailsData, 'via': getalldata[0]['via'], 'Note': getalldata[0]['Note'],
                    'follow': getalldata[0]['follow']}

            token = request.META.get('HTTP_AUTHORIZATION')

            return Response(
                {'data': data, 'message': "successfully Retrive",
                    "status": "pass", 'token': str(token).split(" ")[1]},
                status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"}, status=status.HTTP_400_BAD_REQUEST)


@permission_classes((AllowAny,))
class Fieldagentdata(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        token = request.META.get('HTTP_AUTHORIZATION')
        try:
            getticket = TicketsModel.objects.filter(
                TicketId=id).values('IssueName')
            alldata = []

            getFa = User.objects.filter(fid__contains=getticket[0]['IssueName']).values(
                'id', 'username', 'email')
            for i in getFa:
                alldata.append(i)
            return Response(
                {'data': alldata, 'message': "successfully Retrive", "status": "pass",
                 'token': str(token).split(" ")[1]}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
                            status=status.HTTP_400_BAD_REQUEST)


def fileType(file_name):
    file_extension = file_name.split('.')[-1]
    if(file_extension in ['jpg', 'png', 'jpeg']):
        return 'image'
    elif(file_extension in ['wav', 'ogg', 'mp3']):
        return 'audio'
    elif(file_extension in ['mp4', 'wmv', 'avi']):
        return 'video'
    elif(file_extension in ['doc', 'docx', 'pdf']):
        return 'document'


def mediaupload(TicketId, files):
    for file in files:
        fileObj = UserUpload_media()
        fileObj.Ticket_creation_in = TicketId
        fileObj.User_media = file
        fileObj.User_media_type = fileType(file.name)
        fileObj.save()


def Agentmediaupload(TicketId, files):
    for file in files:
        fileObj = AgentUpload_media()
        fileObj.Ticket_creation_in = TicketId
        fileObj.Agent_media = file
        fileObj.Agent_media_type = fileType(file.name)
        fileObj.save()


def agentRemarksUpload(TicketId, remarks):
    print('tkt id', TicketId, remarks)
    data = AgentRemarks()
    data.Ticket_id = TicketId
    data.Remarks = str(remarks)
    data.save()


@permission_classes((AllowAny,))
class GetParticularUserTickets(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        token = request.META.get('HTTP_AUTHORIZATION')
        try:
            totaldataall = TicketsModel.objects.filter(CreatedFor=id).values('TicketId', 'IssueName', 'IssueCategory',
                                                                             'Priority', 'valid', 'TicketStatus',
                                                                             'Time', 'Address', 'IssueDescription')

            dataall = TicketsModel.objects.filter(CreatedFor=id, TicketStatus="0").values('TicketId', 'IssueName', 'IssueCategory',
                                                                                          'Priority', 'valid', 'TicketStatus',
                                                                                          'Time', 'IssueDescription')

            alldata = {}

            alldata['OverAllTicket'] = totaldataall
            alldata['OpenTicketCount'] = len(dataall)

            dataallc = TicketsModel.objects.filter(CreatedFor=id, TicketStatus="1").values(
                'TicketId', 'IssueName', 'IssueCategory', 'Priority', 'valid', 'TicketStatus', 'Time', 'IssueDescription')

            alldata['closeTicketCount'] = len(dataallc)
            return Response(
                {'data': alldata, 'message': "successfully Retrive", "status": "pass",
                 'token': str(token).split(" ")[1]}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
                            status=status.HTTP_400_BAD_REQUEST)


@permission_classes((AllowAny,))
class GetOpenandCloseTicket(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        token = request.META.get('HTTP_AUTHORIZATION')
        try:
            dataall = TicketsModel.objects.filter(TicketStatus="0").values('TicketId', 'IssueName', 'IssueCategory',
                                                                           'Priority', 'valid', 'TicketStatus',
                                                                           'Time').exclude(valid="3")

            alldata = {}
            alldata['OpenTicket'] = dataall

            alldata['OpenTicketCount'] = len(dataall)

            dataallc = TicketsModel.objects.filter(TicketStatus="1").values('TicketId', 'IssueName', 'IssueCategory',
                                                                            'Priority', 'valid', 'TicketStatus',
                                                                            'Time').exclude(valid="3")

            alldata['CloseTicket'] = dataallc

            alldata['closeTicketCount'] = len(dataallc)

            dataallIv = TicketsModel.objects.filter(valid="3").values('TicketId', 'IssueName', 'IssueCategory',
                                                                      'Priority', 'valid', 'TicketStatus',
                                                                      'Time')

            alldata['InvalidTicketCount'] = len(dataallIv)
            alldata['InvalidTicket'] = dataallIv

            return Response(
                {'data': alldata, 'message': "successfully Retrive", "status": "pass",
                 'token': str(token).split(" ")[1]}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
                            status=status.HTTP_400_BAD_REQUEST)


@permission_classes((AllowAny,))
class GetUserIdUsingMobileNo(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        token = request.META.get('HTTP_AUTHORIZATION')
        try:
            getticket = User.objects.filter(email=id).values('id')
            if getticket:
                return Response(
                    {'data': getticket, 'message': "successfully Retrive", "status": "pass",
                     'token': str(token).split(" ")[1]}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'data': [], 'message': "No Data", "status": "fail",
                     'token': str(token).split(" ")[1]}, status=status.HTTP_406_NOT_ACCEPTABLE)
        except:
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
                            status=status.HTTP_400_BAD_REQUEST)


# @permission_classes((AllowAny,))
# class GetSingleFieldAgentTicket(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def get(self, request, id):
#         token = request.META.get('HTTP_AUTHORIZATION')
#         try:
#             dataall = TicketsModel.objects.order_by('-Time').filter(Fam__contains=int(id), TicketStatus="0").values(
#                 'TicketId', 'IssueName', 'IssueCategory',
#                 'Priority', 'valid', 'TicketStatus',
#                 'Time', 'Fam', 'via')

#             alldata = {}
#             alldata['OpenTicket'] = dataall

#             alldata['OpenTicketCount'] = len(dataall)

#             dataallc = TicketsModel.objects.order_by('-Time').filter(Fam__contains=int(id), TicketStatus="1").values(
#                 'TicketId', 'IssueName', 'IssueCategory',
#                 'Priority', 'valid', 'TicketStatus',
#                 'Time', 'Fam', 'via')

#             alldata['CloseTicket'] = dataallc

#             alldata['closeTicketCount'] = len(dataallc)

#             return Response(
#                 {'data': alldata, 'message': "successfully Retrive", "status": "pass",
#                  'token': str(token).split(" ")[1]}, status=status.HTTP_200_OK)
#         except:
#             return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
#                             status=status.HTTP_400_BAD_REQUEST)

def Thresholdcalculate(days, Time):
    d1 = Time
    d2 = timezone.now()
    d3 = (d2-d1)
    Threshold = 0
    # print('this is date',d3.days)
    if int(d3.days) > days:
        Threshold = 1
    else:
        Threshold = 0
    # print(Threshold)
    return Threshold


@permission_classes((AllowAny,))
class GetSingleFieldAgentTicket(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        token = request.META.get('HTTP_AUTHORIZATION')
        request.GET._mutable = True
        try:
            dataall = TicketsModel.objects.order_by('-Time').filter(Fam__contains=int(id), TicketStatus="0").values(
                'TicketId', 'IssueName', 'ContactNo', 'IssueCategory', 'FaTime', 'FaAssignTime', 'valid',
                'Priority', 'valid', 'TicketStatus',
                'Time', 'Fam', 'via', 'IssueDescription')
            alldata = {}
            for data in dataall:
                if data['valid'] == '1':

                    daydata = IssueCategoryBucketing.objects.filter(
                        IssueCategory=data['IssueCategory']).values('Threshold')
                    Time = data['FaAssignTime']
                    # print('fa time',Time,daydata[0]['Threshold'])
                    Threshold = Thresholdcalculate(
                        daydata[0]['Threshold'], Time)
                    # print('thhis thre',Threshold)
                    data['Threshold'] = Threshold
                elif data['valid'] == '2' and data['TicketStatus'] == '0':
                    daydata = IssueCategoryBucketing.objects.filter(
                        IssueCategory=data['IssueCategory']).values('Threshold')
                    Time = data['FaTime']
                    Threshold = Thresholdcalculate(
                        daydata[0]['Threshold'], Time)
                    data['Threshold'] = Threshold
                else:
                    data['Threshold'] = 0
                agentRemarksCount = AgentRemarks.objects.filter(
                    Ticket_id=data['TicketId']).values('Remarks').count()
                data['RemarksCount'] = agentRemarksCount

            alldata['OpenTicket'] = dataall
            # print('all data',alldata)

            alldata['OpenTicketCount'] = len(dataall)

            dataallc = TicketsModel.objects.order_by('-Time').filter(Fam__contains=int(id), TicketStatus="1").values(
                'TicketId', 'IssueName', 'ContactNo', 'IssueCategory', 'FaTime', 'FaAssignTime', 'valid',
                'Priority', 'valid', 'TicketStatus',
                'Time', 'Fam', 'via', 'IssueDescription')
            for data in dataall:
                data['Threshold'] = 0
                agentRemarksCount = AgentRemarks.objects.filter(
                    Ticket_id=data['TicketId']).values('Remarks').count()
                data['RemarksCount'] = agentRemarksCount
            alldata['CloseTicket'] = dataallc

            alldata['closeTicketCount'] = len(dataallc)

            return Response(
                {'data': alldata, 'message': "successfully Retrive", "status": "pass",
                 'token': str(token).split(" ")[0]}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
                            status=status.HTTP_400_BAD_REQUEST)


@permission_classes((AllowAny,))
class GetCategoryNameCount(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        token = request.META.get('HTTP_AUTHORIZATION')
        try:
            getallcat = IssueCategoryBucketing.objects.filter(
                valid=1).values('IssueCategory').distinct()
            alldata = []
            for data in getallcat:
                Servicesopen = TicketsModel.objects.filter(IssueCategory=data['IssueCategory'],
                                                           TicketStatus="0").values('IssueCategory')
                Servicesclose = TicketsModel.objects.filter(IssueCategory=data['IssueCategory'],
                                                            TicketStatus="1").values('IssueCategory')
                alldata.append({'IssueCategory': data['IssueCategory'], 'Openticket': len(Servicesopen),
                                'Closeticket': len(Servicesclose)})
            return Response(
                {'data': alldata, 'message': "successfully Retrive", "status": "pass",
                 'token': str(token).split(" ")[1]}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
                            status=status.HTTP_400_BAD_REQUEST)


@permission_classes((AllowAny,))
class GetSpecificCategoryName(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, cat):
        token = request.META.get('HTTP_AUTHORIZATION')
        try:
            alldata = {}
            alldata['CategoryName'] = cat
            dataall = TicketsModel.objects.filter(IssueCategory=cat, TicketStatus="0").values('TicketId', 'IssueName', 'IssueCategory', 'Priority', 'valid',
                                                                                              'TicketStatus', 'Time', 'via', 'follow',
                                                                                              'termtype', 'localgovt', 'location')
            alldata['OpenTicket'] = dataall
            alldata['OpenTicketCount'] = len(dataall)
            dataallc = TicketsModel.objects.filter(IssueCategory=cat, TicketStatus="1").values('TicketId', 'IssueName',
                                                                                               'IssueCategory', 'Priority', 'valid',
                                                                                               'TicketStatus', 'Time', 'via', 'follow',
                                                                                               'termtype', 'localgovt', 'location')
            alldata['CloseTicket'] = dataallc
            alldata['closeTicketCount'] = len(dataallc)
            return Response(
                {'data': alldata, 'message': "successfully Retrive", "status": "pass",
                 'token': str(token).split(" ")[1]}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
                            status=status.HTTP_400_BAD_REQUEST)


@permission_classes((AllowAny,))
class GetAllAgentsData(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, cat):
        token = request.META.get('HTTP_AUTHORIZATION')
        try:
            getdata = User.objects.filter(role=cat).values('id', 'username', 'email', 'address',
                                                           'role', 'fid', 'mobile', 'active')
            return Response(
                {'data': getdata, 'message': "successfully Retrive", "status": "pass",
                 'token': str(token).split(" ")[1]}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
                            status=status.HTTP_400_BAD_REQUEST)


@permission_classes((AllowAny,))
class SearchAddress(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, cat):
        token = request.META.get('HTTP_AUTHORIZATION')
        try:
            getaddress = ""
            if cat == "wantfulladdress":
                getaddress = AddressDetails.objects.values('Addressid', 'Address', 'Ward', 'Area',
                                                           'Lat', 'Long')
            else:
                getaddress = AddressDetails.objects.filter(Address__icontains=cat).values('Addressid', 'Address',
                                                                                          'Ward', 'Area', 'Lat',
                                                                                          'Long')
            return Response(
                {'data': getaddress, 'message': "successfully Retrive", "status": "pass",
                 'token': str(token).split(" ")[1]}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"}, status=status.HTTP_400_BAD_REQUEST)


@permission_classes((AllowAny,))
class GetLatLongTickets(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        token = request.META.get('HTTP_AUTHORIZATION')
        try:
            alldata = []
            dataall = TicketsModel.objects.values('TicketId', 'IssueName', 'IssueCategory', 'follow',
                                                  'Priority', 'valid', 'Time',
                                                  'TicketStatus', 'Address', 'via',
                                                  'termtype', 'localgovt', 'location')
            for datas in dataall:
                addressdata = []
                getaddress = AddressDetails.objects.filter(Address=datas['Address']).values('Addressid', 'Address',
                                                                                            'Ward', 'Area', 'Lat',
                                                                                            'Long')
                for adre in getaddress:
                    addressdata.append(
                        {'Addressid': adre['Addressid'], 'Address': adre['Address'], 'Ward': adre['Ward'], 'Area': adre['Area'], 'Lattitude': adre['Lat'], 'Longitude': adre['Long']})
                alldata.append({'TicketId': datas['TicketId'], 'IssueName': datas['IssueName'], 'IssueCategory': datas['IssueCategory'], 'Priority': datas['Priority'],
                               'valid': datas['valid'], 'TicketStatus': datas['TicketStatus'], 'Address': datas['Address'], 'MapAddress': addressdata})

            return Response(
                {'data': alldata, 'message': "successfully Retrive", "status": "pass",
                 'token': str(token).split(" ")[1]}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
                            status=status.HTTP_400_BAD_REQUEST)


@permission_classes((AllowAny,))
class GetParticularCCTickets(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        token = request.META.get('HTTP_AUTHORIZATION')
        try:
            totaldataall = TicketsModel.objects.filter(via='Whatsapp')
            totaldataall = totaldataall.union(
                #     # TicketsModel.objects.filter(CreatedBy=id))
                TicketsModel.objects.filter())
            totaldataall = totaldataall.order_by('-Time').values('TicketId', 'IssueName', 'IssueCategory', 'Priority', 'valid',
                                                                 'TicketStatus', 'Time', 'Address',
                                                                 'IssueDescription', 'via', 'CreatedFor',
                                                                 'Fam', 'location', 'follow',
                                                                 'termtype', 'localgovt', 'FaAssignTime', 'FaTime')
            # 'FaAssignTime','FaTime'

            for data in totaldataall:

                # threshold
                if data['valid'] == '0':
                    Time = data['Time']
                    daydata = IssueCategoryBucketing.objects.filter(
                        IssueCategory="unassigned").values('Threshold')
                    Threshold = Thresholdcalculate(
                        daydata[0]['Threshold'], Time)
                    data['Threshold'] = Threshold
                if data['valid'] == '1':
                    daydata = IssueCategoryBucketing.objects.filter(
                        IssueCategory=data["IssueCategory"]).values('Threshold')
                    Time = data['FaAssignTime']
                    Threshold = Thresholdcalculate(
                        daydata[0]['Threshold'], Time)
                    data['Threshold'] = Threshold
                if data['valid'] == '2' and data['TicketStatus'] == '0':
                    daydata = IssueCategoryBucketing.objects.filter(
                        IssueCategory="completed").values('Threshold')
                    Time = data['FaTime']
                    Threshold = Thresholdcalculate(
                        daydata[0]['Threshold'], Time)
                    data['Threshold'] = Threshold
                else:
                    data['Threshold'] = 0

                public = data.get('CreatedFor', None)
                if public:
                    public = User.objects.filter(pk=public).first()
                    pub_mobile = public.email
                    data['CreatedFor'] = pub_mobile
                fams = data.get('Fam', None)
                if fams:
                    Fam = []
                    for fam in fams:
                        user = User.objects.filter(pk=fam).first()
                        Fam.append(user.username + ' - ' + user.mobile)
                    data['Fam'] = Fam
                else:
                    data['Fam'] = 'Not Assigned'

                # get no of agent remarks for particular tickets
                ticketId = data.get('TicketId', None)
                agentRemarksCount = AgentRemarks.objects.filter(
                    Ticket_id=int(ticketId)).values('Remarks').count()
                data['RemarksCount'] = agentRemarksCount

            dataall = TicketsModel.objects.filter(CreatedBy=id, TicketStatus="0").order_by(
                '-Time').values('TicketId', 'IssueName', 'IssueCategory', 'Priority', 'valid', 'TicketStatus', 'Time', 'IssueDescription', 'via')

            alldata = {}

            alldata['OverAllTicket'] = totaldataall
            alldata['OpenTicketCount'] = len(dataall)

            dataallc = TicketsModel.objects.filter(CreatedBy=id, TicketStatus="1").order_by(
                '-Time').values('TicketId', 'IssueName', 'IssueCategory', 'Priority', 'valid', 'TicketStatus', 'Time', 'IssueDescription', 'via')

            alldata['closeTicketCount'] = len(dataallc)
            alldata
            return Response(
                {'data': alldata, 'message': "successfully Retrive", "status": "pass",
                 'token': str(token).split(" ")[1]}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"}, status=status.HTTP_400_BAD_REQUEST)


@permission_classes((AllowAny,))
class GetSpecicFieldagentdata(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, name):
        token = request.META.get('HTTP_AUTHORIZATION')
        try:
            alldata = []

            getFa = User.objects.filter(fid__contains=name).values(
                'id', 'username', 'email')
            for i in getFa:
                alldata.append(i)
            return Response(
                {'data': alldata, 'message': "successfully Retrive", "status": "pass",
                 'token': str(token).split(" ")[1]}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
                            status=status.HTTP_400_BAD_REQUEST)


@permission_classes((AllowAny,))
class PushNotificationKeyUpload(APIView):
    def post(self, request):
        getkey = User.objects.filter(
            notify=request.data['AccessKey']).values('notify')
        if getkey:
            return Response({'Data': 'Already Register', 'Status': 'pass'}, status=status.HTTP_406_NOT_ACCEPTABLE)
        else:
            Savekey = User.objects.filter(id=request.data['id']).get()
            Savekey.notify = str(request.data['AccessKey'])
            Savekey.save()
        return Response({'Data': 'Key Register', 'Status': 'pass'}, status=status.HTTP_200_OK)


def sendPush(title, msg, dataObject, registration_token):
    # See documentation on defining a message payload.
    # print('insidesendpush')
    sendrange = 450
    for i in range(0, len(registration_token), sendrange):
        sendlist = registration_token[i:i + sendrange]
        # print(len(registration_token[i:i + sendrange]))
        # print(sendlist,'listnew')
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=msg
            ),
            android=messaging.AndroidConfig(
                priority='high',
            ),
            data=dataObject,
            tokens=sendlist,
        )
        # Send a message to the device corresponding to the provided
        # registration token.

        response = messaging.send_multicast(message)

        # print('Successfully sent message:', response)


# @permission_classes((AllowAny,))
# class GetSpecificUserDetails(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#
#     def get(self, request, id):
#         token = request.META.get('HTTP_AUTHORIZATION')
#         try:
#             getticket = User.objects.filter(id=id).values('id','email','username','address','gender','ward','prooftype','proofid','role','fid')
#             if getticket:
#                 return Response(
#                     {'data': getticket, 'message': "successfully Retrive", "status": "pass",
#                      'token': str(token).split(" ")[1]}, status=status.HTTP_200_OK)
#             else:
#                 return Response(
#                     {'data': [], 'message': "No Data", "status": "fail",
#                      'token': str(token).split(" ")[1]}, status=status.HTTP_406_NOT_ACCEPTABLE)
#         except:
#             return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
#                             status=status.HTTP_400_BAD_REQUEST)
#
#

@permission_classes((AllowAny,))
class GetSpecificUserNotification(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        token = request.META.get('HTTP_AUTHORIZATION')
        try:
            GetUserNitification = NotificationDetails.objects.filter(UsersIds__contains=int(
                id)).values('ID', 'Role', 'Title', 'Description', 'SourceUrl', 'Type', 'Date')
            if GetUserNitification:
                return Response(
                    {'data': GetUserNitification, 'message': "successfully Retrive", "status": "pass",
                     'token': str(token).split(" ")[1]}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'data': [], 'message': "No Data", "status": "fail",
                     'token': str(token).split(" ")[1]}, status=status.HTTP_406_NOT_ACCEPTABLE)

        except Exception as e:
            print(type(e))
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
                            status=status.HTTP_400_BAD_REQUEST)


def endDateAdjustment(end_date: str):
    '''
    Date string must be in the form of "year-month-date". Eg., "2021-08-26"
    '''
    end_date: date = date(*map(int, end_date.split('-')))
    return end_date + datetime.timedelta(days=1)


def dateCategories(data):
    week_start = date.today()
    # week_start -= timedelta(days=week_start.weekday())
    cat = data['cat'].lower()

    if (cat == "this week" or cat == "this month"):
        if cat == "this week":
            week_end = week_start - timedelta(days=7)
        elif cat == "this month":
            week_end = week_start - timedelta(days=31)
        tickets = TicketsModel.objects.order_by(
            '-Time').filter(Time__gte=week_end)

    elif cat == "today":
        start_date = date.today()
        tickets = TicketsModel.objects.order_by(
            '-Time').filter(Time__gte=start_date)

    elif cat == "daterange":
        start_date = data['start_date']
        end_date = data['end_date']
        end_date = endDateAdjustment(end_date)
        tickets = TicketsModel.objects.order_by(
            '-Time').filter(Time__range=(start_date, end_date))

    else:
        tickets = TicketsModel.objects.order_by('-Time').all()

    return tickets


def splitTickets(tickets: TicketsModel.objects):
    tickets = tickets.values(
        'TicketId', 'IssueName', 'IssueCategory',
        'Priority', 'valid', 'TicketStatus',
        'Time', 'via', 'follow',
        'termtype', 'localgovt', 'location'
    )
    data = {}
    openTickets = tickets.filter(
        TicketStatus="0").exclude(valid__in=["3", "0"])
    data['OpenTicket'] = openTickets
    data['OpenTicketCount'] = len(openTickets)
    unassignTickets = tickets.filter(valid="0")
    data['UnassignedTicket'] = unassignTickets
    data['UnassignedTicketCount'] = len(unassignTickets)
    closeTickets = tickets.filter(
        TicketStatus="1").exclude(valid__in=["3", "0"])
    data['CloseTicket'] = closeTickets
    data['closeTicketCount'] = len(closeTickets)
    invalidTickets = tickets.filter(valid="3")
    data['InvalidTicket'] = invalidTickets
    data['InvalidTicketCount'] = len(invalidTickets)
    return data


class GetMlaTickets(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token = request.META.get('HTTP_AUTHORIZATION')
        try:
            tickets = dateCategories(request.data)
            data = splitTickets(tickets)
            return Response(
                {'message': "successfully Retrive", "data": data, "status": "pass"}, status=status.HTTP_200_OK)

        except:
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
                            status=status.HTTP_400_BAD_REQUEST)


def splitCountByCategory(tickets: TicketsModel.objects):
    # tickets = tickets.exclude(valid__in=["3", "0"]).values('IssueCategory')
    # exclude invalid tickets(3) only
    tickets = tickets.exclude(valid__in=["3"]).values('IssueCategory')
    getallcat = IssueCategoryBucketing.objects.filter(
        valid=1).values('IssueCategory').distinct()
    alldata = []
    for data in getallcat:
        # open tkt= pending tkt+ completed tkt
        Servicesopen = tickets.filter(IssueCategory=data['IssueCategory'],
                                      TicketStatus="0", valid__in=["1", "2"])
        Servicesclose = tickets.filter(IssueCategory=data['IssueCategory'],
                                       TicketStatus="1")
        Servicesunassign = tickets.filter(IssueCategory=data['IssueCategory'],
                                          valid="0")
        alldata.append({'IssueCategory': data['IssueCategory'], 'Openticket': len(
            Servicesopen), 'Closeticket': len(Servicesclose), 'UnassignTicket': len(Servicesunassign)})
    return alldata


class GetCatAccountByCal(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token = request.META.get('HTTP_AUTHORIZATION')
        try:
            tickets = dateCategories(request.data)
            data = splitCountByCategory(tickets)

            return Response(
                {'data': data, 'message': "successfully Retrive", "status": "pass",
                    'token': str(token).split(" ")[1]}, status=status.HTTP_200_OK)

        except:
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"}, status=status.HTTP_400_BAD_REQUEST)


class FollowUp(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ticketId = request.data.get('ticketId', None)
        ticket: TicketsModel = TicketsModel.objects.filter(
            TicketId=ticketId).first()
        if(ticketId is None or ticket is None):
            return Response({'data': {}, 'message': "No ticket found", "status": "pass", }, status=status.HTTP_200_OK)
        else:
            ticket.follow += 1
            ticket.save()
        return Response({'data': {}, 'message': "successfully followed up", "status": "pass", }, status=status.HTTP_200_OK)


class UpdateDeleteUserMedia(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, user_media_id):
        request.POST._mutable = True

        try:
            obj = UserUpload_media.objects.get(User_media_id=user_media_id)
        except:
            return Response({'data': {}, 'status': 'error', 'message': "ID not in the list"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            data = request.data
            obj = UserUpload_media.objects.get(User_media_id=user_media_id)
            for key, value in data.items():
                setattr(obj, key, value)
            obj.save()
            return Response({'data': {}, 'status': 'success', 'message': "Successfully Updated"}, status=status.HTTP_200_OK)
        except:
            return Response({'data': {}, 'status': 'error', 'message': "BAD REQUEST"}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, user_media_id):
        # permission_classes = [permissions.IsAuthenticated]
        try:
            obj = UserUpload_media.objects.get(User_media_id=user_media_id)
        except:
            return Response({'data': {}, 'status': 'error', 'message': "ID not in the list"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            DeleteMedia = UserUpload_media.objects.filter(
                User_media_id=user_media_id).delete()
            return Response({'data': {}, 'status': 'success', 'message': "Successfully deleted"}, status=status.HTTP_200_OK)

        except:
            return Response({'data': {}, 'status': 'error', 'message': "BAD REQUEST"}, status=status.HTTP_400_BAD_REQUEST)


class UpdateDeleteAgentMedia(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, agent_media_id):
        # permission_classes = [permissions.IsAuthenticated]
        try:
            obj = AgentUpload_media.objects.get(Agent_media_id=agent_media_id)
        except:
            return Response({'data': {}, 'status': 'error', 'message': "ID not in the list"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            DeleteMedia = AgentUpload_media.objects.filter(
                Agent_media_id=agent_media_id).delete()
            return Response({'data': {}, 'status': 'success', 'message': "Successfully deleted"}, status=status.HTTP_200_OK)

        except:
            return Response({'data': {}, 'status': 'error', 'message': "BAD REQUEST"}, status=status.HTTP_400_BAD_REQUEST)


@permission_classes((AllowAny,))
class GetAreaCategory(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        token = request.META.get('HTTP_AUTHORIZATION')
        try:
            getAreaCategory = AreaCategory.objects.all().values('ID', 'areaName')
            if getAreaCategory:
                category = []

                for fd in getAreaCategory:
                    category.append(fd['areaName'])

                return Response(
                    {'data': category, 'message': "successfully Retrive", "status": "pass",
                     'token': str(token).split(" ")[1]}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'data': [], 'message': "No Data", "status": "fail",
                     'token': str(token).split(" ")[1]}, status=status.HTTP_406_NOT_ACCEPTABLE)

        except Exception as e:
            print(type(e))
            return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
                            status=status.HTTP_400_BAD_REQUEST)


@permission_classes((AllowAny,))
class getCategoryThreshold(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        token = request.META.get('HTTP_AUTHORIZATION')
        print('htreshold', request.data)
        obj = IssueCategoryBucketing.objects.all().values('IssueCategory', 'IssueName',
                                                          'Issueid', 'Time', 'valid', 'Threshold', 'IssueType')
        return Response({'message': "successfully Retrive", "data": obj, "status": "pass",
                         'token': str(token).split(" ")[0]}, status=status.HTTP_200_OK)

    # def post(self, request):
    #         token = request.META.get('HTTP_AUTHORIZATION')
    #         obj = getallcategorythreshold(data=request.data)
    #         if obj.is_valid():
    #             obj.save()
    #             return Response(
    #                 {'message': "successfully registerd", "status": "pass",
    #                     'token': str(token).split(" ")[1]},
    #                 status=status.HTTP_200_OK)
    #         else:
    #             return Response(
    #                 {'message': "something went wrong", "status": "fail",
    #                     'token': str(token).split(" ")[1]},
    #                 status=status.HTTP_502_BAD_GATEWAY)

    def put(self, request):
        token = request.META.get('HTTP_AUTHORIZATION')
        try:
            data = request.data
            print(data)
            for key, value in data.items():
                obj = IssueCategoryBucketing.objects.get(Issueid=key)
                obj.Threshold = value
                obj.save()
            return Response({'data': {}, 'status': 'success', 'message': "Successfully Updated"}, status=status.HTTP_200_OK)
        except:
            return Response(
                {'message': "something went wrong", "status": "fail",
                 'token': str(token).split(" ")[0]},
                status=status.HTTP_502_BAD_GATEWAY)


# @permission_classes((AllowAny,))
# class GetAllTicketsPaginator(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def get(self, request,page,size):
#         try:
#             dataall = TicketsModel.objects.values('TicketId', 'IssueName', 'IssueCategory',
#                                                   'IssueDescription', 'Priority',
#                                                   'valid', 'Time', 'TicketStatus', 'via',
#                                                   'CreatedFor', 'Fam', 'Note', 'follow', 'termtype',
#                                                   'localgovt', 'location', 'FaAssignTime', 'FaTime').order_by('-Time')


#             page = request.GET.get('page', page)
#             paginator = Paginator(dataall, size)
#             try:
#                 employees = paginator.page(page)
#             except PageNotAnInteger:
#                 employees = paginator.page(request.POST['page'])
#             except EmptyPage:
#                 employees = paginator.page(paginator.num_pages)
#             all = []
#             ticketsCount=TicketsModel.objects.count()
#             print('ticket count',ticketsCount)
#             # all.append({'ticketsCount':ticketsCount})
#             # all['ticketsCount']=ticketsCount
#             for i in list(employees):
#                 if i['valid'] == '0':
#                     Time = i['Time']
#                     daydata = IssueCategoryBucketing.objects.filter(IssueCategory="unassigned").values('Threshold')
#                     Threshold = Thresholdcalculate(daydata[0]['Threshold'], Time)
#                     i['Threshold'] = Threshold
#                 if i['valid'] == '1':
#                     daydata = IssueCategoryBucketing.objects.filter(IssueCategory=i["IssueCategory"]).values(
#                         'Threshold')
#                     Time = i['FaAssignTime']
#                     Threshold = Thresholdcalculate(daydata[0]['Threshold'], Time)
#                     i['Threshold'] = Threshold
#                 if i['valid'] == '2' and i['TicketStatus'] == '0':
#                     daydata = IssueCategoryBucketing.objects.filter(IssueCategory="completed").values('Threshold')
#                     Time = i['FaTime']
#                     Threshold = Thresholdcalculate(daydata[0]['Threshold'], Time)
#                     i['Threshold'] = Threshold
#                 else:
#                     i['Threshold'] = 0

#                     # print('threshold',Threshold)

#                 public = i.get('CreatedFor', None)
#                 if public:
#                     public = User.objects.filter(pk=public).first()
#                     pub_mobile = public.email
#                     i['CreatedFor'] = pub_mobile
#                 fams = i.get('Fam', None)
#                 if fams:
#                     Fam = ''
#                     for index, fam in enumerate(fams):
#                         user = User.objects.filter(pk=fam).first()
#                         Fam += user.username + ' - ' + user.mobile
#                         if index != fams.__len__() - 1:
#                             Fam = Fam + '\n'
#                     i['Fam'] = Fam
#                 else:
#                     i['Fam'] = 'Not Assigned'

#                 # get no of agent remarks for particular tickets
#                 ticketId = i.get('TicketId', None)
#                 agentRemarksCount = AgentRemarks.objects.filter(
#                     Ticket_id=int(ticketId)).values('Remarks').count()
#                 i['RemarksCount'] = agentRemarksCount

#                 all.append(i)
#             return Response(
#                 {'message': "successfully Retrive", "data": {'ticketsData':all,'ticketsCount':ticketsCount}, "status": "pass"}, status=status.HTTP_200_OK)
#         except:
#             return Response({"message": "Something went wrong. Please try again later.", "status": "fail"},
#                             status=status.HTTP_400_BAD_REQUEST)

# @permission_classes((AllowAny,))
# class FilterSearchPaginatorForAdmin(APIView):
#     def get(self, request, pageno, size, Filter, SFilter):
#         # print('data comming')
#         Word = self.request.query_params.get('word', None)
#         print('incoming data ', Filter, SFilter, Word)
#         try:
#             if Filter == "Unassigned" or Filter == "Pending":
#                 ValidId = "0"
#                 if Filter == "Pending":
#                     ValidId = "1"
#                 if SFilter != "AL":
#                     if SFilter == "TicketId":
#                         getdata = TicketsModel.objects.filter(TicketId=int(Word), valid=ValidId).values('TicketId', 'IssueName', 'IssueCategory',
#                                                                                                         'IssueDescription', 'Priority',
#                                                                                                         'valid', 'Time', 'TicketStatus', 'via',
#                                                                                                         'CreatedFor', 'Fam', 'Note', 'follow', 'termtype',
#                                                                                                         'localgovt', 'location', 'FaAssignTime', 'FaTime').order_by('-Time')
#                         ticketsCount = TicketsModel.objects.filter(
#                             TicketId=int(Word), valid=ValidId).count()
#                     elif SFilter == "IssueCategory":
#                         getdata = TicketsModel.objects.filter(IssueCategory__icontains=Word, valid=ValidId).values('TicketId', 'IssueName',
#                                                                                                                    'IssueCategory',
#                                                                                                                    'IssueDescription', 'Priority',
#                                                                                                                    'valid', 'Time', 'TicketStatus',
#                                                                                                                    'via',
#                                                                                                                    'CreatedFor', 'Fam', 'Note',
#                                                                                                                    'follow', 'termtype',
#                                                                                                                    'localgovt', 'location',
#                                                                                                                    'FaAssignTime', 'FaTime').order_by(
#                             '-Time')
#                         ticketsCount = TicketsModel.objects.filter(
#                             IssueCategory__icontains=Word, valid=ValidId).count()
#                     elif SFilter == "localgovt":
#                         getdata = TicketsModel.objects.filter(localgovt__icontains=Word, valid=ValidId).values('TicketId', 'IssueName',
#                                                                                                                'IssueCategory',
#                                                                                                                'IssueDescription', 'Priority',
#                                                                                                                'valid', 'Time', 'TicketStatus',
#                                                                                                                'via',
#                                                                                                                'CreatedFor', 'Fam', 'Note',
#                                                                                                                'follow', 'termtype',
#                                                                                                                'localgovt', 'location',
#                                                                                                                'FaAssignTime', 'FaTime').order_by(
#                             '-Time')
#                         ticketsCount = TicketsModel.objects.filter(
#                             localgovt__icontains=Word, valid=ValidId).count()
#                     elif SFilter == "via":
#                         getdata = TicketsModel.objects.filter(via__icontains=Word, valid=ValidId).values('TicketId', 'IssueName',
#                                                                                                          'IssueCategory',
#                                                                                                          'IssueDescription', 'Priority',
#                                                                                                          'valid', 'Time', 'TicketStatus',
#                                                                                                          'via',
#                                                                                                          'CreatedFor', 'Fam', 'Note',
#                                                                                                          'follow', 'termtype',
#                                                                                                          'localgovt', 'location',
#                                                                                                          'FaAssignTime', 'FaTime').order_by(
#                             '-Time')
#                         ticketsCount = TicketsModel.objects.filter(
#                             via__icontains=Word, valid=ValidId).count()
#                     elif SFilter == "ContactNo":
#                         getdata = TicketsModel.objects.filter(ContactNo__icontains=Word, valid=ValidId).values('TicketId', 'IssueName',
#                                                                                                                'IssueCategory',
#                                                                                                                'IssueDescription', 'Priority',
#                                                                                                                'valid', 'Time', 'TicketStatus',
#                                                                                                                'via',
#                                                                                                                'CreatedFor', 'Fam', 'Note',
#                                                                                                                'follow', 'termtype',
#                                                                                                                'localgovt', 'location',
#                                                                                                                'FaAssignTime', 'FaTime').order_by(
#                             '-Time')
#                         ticketsCount = TicketsModel.objects.filter(
#                             ContactNo__icontains=Word, valid=ValidId).count()

#                     elif SFilter == "IssueDescription":
#                         getdata = TicketsModel.objects.filter(IssueDescription__icontains=Word, valid=ValidId).values('TicketId', 'IssueName',
#                                                                                                                       'IssueCategory',
#                                                                                                                       'IssueDescription', 'Priority',
#                                                                                                                       'valid', 'Time', 'TicketStatus',
#                                                                                                                       'via',
#                                                                                                                       'CreatedFor', 'Fam', 'Note',
#                                                                                                                       'follow', 'termtype',
#                                                                                                                       'localgovt', 'location',
#                                                                                                                       'FaAssignTime', 'FaTime').order_by(
#                             '-Time')
#                         ticketsCount = TicketsModel.objects.filter(
#                             IssueDescription__icontains=Word, valid=ValidId).count()

#                 elif SFilter == "AL":
#                     # print('this print')
#                     getdata = TicketsModel.objects.filter(Q(localgovt__icontains=Word) | Q(IssueCategory__icontains=Word) | Q(TicketId__icontains=Word) | Q(via__icontains=Word) | Q(ContactNo__icontains=Word) | Q(IssueDescription__icontains=Word), valid=ValidId).values('TicketId',
#                                                                                                                                                                                                                                                                              'IssueName',
#                                                                                                                                                                                                                                                                              'IssueCategory',
#                                                                                                                                                                                                                                                                              'IssueDescription',
#                                                                                                                                                                                                                                                                              'Priority',
#                                                                                                                                                                                                                                                                              'valid', 'Time',
#                                                                                                                                                                                                                                                                              'TicketStatus',
#                                                                                                                                                                                                                                                                              'via',
#                                                                                                                                                                                                                                                                              'CreatedFor', 'Fam',
#                                                                                                                                                                                                                                                                              'Note',
#                                                                                                                                                                                                                                                                              'follow', 'termtype',
#                                                                                                                                                                                                                                                                              'localgovt',
#                                                                                                                                                                                                                                                                              'location',
#                                                                                                                                                                                                                                                                              'FaAssignTime',
#                                                                                                                                                                                                                                                                              'FaTime').order_by(
#                         '-Time')
#                     ticketsCount = TicketsModel.objects.filter(Q(localgovt__icontains=Word) | Q(
#                         IssueCategory__icontains=Word) | Q(TicketId__icontains=Word) | Q(via__icontains=Word), valid=ValidId).count()

#             elif Filter == "Completed" or Filter == "Closed":

#                 ValidId = "2"
#                 ticketStatusval = "0"
#                 if Filter == "Closed":
#                     ValidId = "2"
#                     ticketStatusval = "1"

#                 if SFilter != "AL":
#                     if SFilter == "TicketId":
#                         getdata = TicketsModel.objects.filter(TicketId=int(Word), valid=ValidId, TicketStatus=ticketStatusval).values('TicketId', 'IssueName', 'IssueCategory',
#                                                                                                                                       'IssueDescription', 'Priority',
#                                                                                                                                       'valid', 'Time', 'TicketStatus', 'via',
#                                                                                                                                       'CreatedFor', 'Fam', 'Note', 'follow', 'termtype',
#                                                                                                                                       'localgovt', 'location', 'FaAssignTime', 'FaTime').order_by('-Time')
#                         ticketsCount = TicketsModel.objects.filter(TicketId=int(
#                             Word), valid=ValidId, TicketStatus=ticketStatusval).count()
#                     elif SFilter == "IssueCategory":
#                         getdata = TicketsModel.objects.filter(IssueCategory__icontains=Word, valid=ValidId, TicketStatus=ticketStatusval).values('TicketId', 'IssueName',
#                                                                                                                                                  'IssueCategory',
#                                                                                                                                                  'IssueDescription', 'Priority',
#                                                                                                                                                  'valid', 'Time', 'TicketStatus',
#                                                                                                                                                  'via',
#                                                                                                                                                  'CreatedFor', 'Fam', 'Note',
#                                                                                                                                                  'follow', 'termtype',
#                                                                                                                                                  'localgovt', 'location',
#                                                                                                                                                  'FaAssignTime', 'FaTime').order_by(
#                             '-Time')
#                         ticketsCount = TicketsModel.objects.filter(
#                             IssueCategory__icontains=Word, valid=ValidId, TicketStatus=ticketStatusval).count()
#                     elif SFilter == "localgovt":
#                         getdata = TicketsModel.objects.filter(localgovt__icontains=Word, valid=ValidId, TicketStatus=ticketStatusval).values('TicketId', 'IssueName',
#                                                                                                                                              'IssueCategory',
#                                                                                                                                              'IssueDescription', 'Priority',
#                                                                                                                                              'valid', 'Time', 'TicketStatus',
#                                                                                                                                              'via',
#                                                                                                                                              'CreatedFor', 'Fam', 'Note',
#                                                                                                                                              'follow', 'termtype',
#                                                                                                                                              'localgovt', 'location',
#                                                                                                                                              'FaAssignTime', 'FaTime').order_by(
#                             '-Time')
#                         ticketsCount = TicketsModel.objects.filter(
#                             localgovt__icontains=Word, valid=ValidId, TicketStatus=ticketStatusval).count()
#                     elif SFilter == "via":
#                         getdata = TicketsModel.objects.filter(via__icontains=Word, valid=ValidId, TicketStatus=ticketStatusval).values('TicketId', 'IssueName',
#                                                                                                                                        'IssueCategory',
#                                                                                                                                        'IssueDescription', 'Priority',
#                                                                                                                                        'valid', 'Time', 'TicketStatus',
#                                                                                                                                        'via',
#                                                                                                                                        'CreatedFor', 'Fam', 'Note',
#                                                                                                                                        'follow', 'termtype',
#                                                                                                                                        'localgovt', 'location',
#                                                                                                                                        'FaAssignTime', 'FaTime').order_by(
#                             '-Time')
#                         ticketsCount = TicketsModel.objects.filter(
#                             via__icontains=Word, valid=ValidId, TicketStatus=ticketStatusval).count()

#                     elif SFilter == "ContactNo":
#                         getdata = TicketsModel.objects.filter(ContactNo__icontains=Word, valid=ValidId).values('TicketId', 'IssueName',
#                                                                                                                'IssueCategory',
#                                                                                                                'IssueDescription', 'Priority',
#                                                                                                                'valid', 'Time', 'TicketStatus',
#                                                                                                                'via',
#                                                                                                                'CreatedFor', 'Fam', 'Note',
#                                                                                                                'follow', 'termtype',
#                                                                                                                'localgovt', 'location',
#                                                                                                                'FaAssignTime', 'FaTime').order_by(
#                             '-Time')
#                         ticketsCount = TicketsModel.objects.filter(
#                             ContactNo__icontains=Word, valid=ValidId).count()

#                     elif SFilter == "IssueDescription":
#                         getdata = TicketsModel.objects.filter(IssueDescription__icontains=Word, valid=ValidId).values('TicketId', 'IssueName',
#                                                                                                                       'IssueCategory',
#                                                                                                                       'IssueDescription', 'Priority',
#                                                                                                                       'valid', 'Time', 'TicketStatus',
#                                                                                                                       'via',
#                                                                                                                       'CreatedFor', 'Fam', 'Note',
#                                                                                                                       'follow', 'termtype',
#                                                                                                                       'localgovt', 'location',
#                                                                                                                       'FaAssignTime', 'FaTime').order_by(
#                             '-Time')
#                         ticketsCount = TicketsModel.objects.filter(
#                             IssueDescription__icontains=Word, valid=ValidId).count()

#                 elif SFilter == "AL":
#                     getdata = TicketsModel.objects.filter(Q(localgovt__icontains=Word) | Q(IssueCategory__icontains=Word) | Q(TicketId__icontains=Word) | Q(via__icontains=Word) | Q(ContactNo__icontains=Word) | Q(IssueDescription__icontains=Word), valid=ValidId, TicketStatus=ticketStatusval).values('TicketId',
#                                                                                                                                                                                                                                                                                                            'IssueName',
#                                                                                                                                                                                                                                                                                                            'IssueCategory',
#                                                                                                                                                                                                                                                                                                            'IssueDescription',
#                                                                                                                                                                                                                                                                                                            'Priority',
#                                                                                                                                                                                                                                                                                                            'valid', 'Time',
#                                                                                                                                                                                                                                                                                                            'TicketStatus',
#                                                                                                                                                                                                                                                                                                            'via',
#                                                                                                                                                                                                                                                                                                            'CreatedFor', 'Fam',
#                                                                                                                                                                                                                                                                                                            'Note',
#                                                                                                                                                                                                                                                                                                            'follow', 'termtype',
#                                                                                                                                                                                                                                                                                                            'localgovt',
#                                                                                                                                                                                                                                                                                                            'location',
#                                                                                                                                                                                                                                                                                                            'FaAssignTime',
#                                                                                                                                                                                                                                                                                                            'FaTime').order_by(
#                         '-Time')
#                     ticketsCount = TicketsModel.objects.filter(Q(localgovt__icontains=Word) | Q(IssueCategory__icontains=Word) | Q(
#                         TicketId__icontains=Word) | Q(via__icontains=Word), valid=ValidId, TicketStatus=ticketStatusval).count()

#             elif Filter == "Invalid":
#                 ValidId = "3"
#                 if SFilter != "AL":
#                     if SFilter == "TicketId":
#                         getdata = TicketsModel.objects.filter(TicketId=int(Word), valid=ValidId).values('TicketId', 'IssueName', 'IssueCategory',
#                                                                                                         'IssueDescription', 'Priority',
#                                                                                                         'valid', 'Time', 'TicketStatus', 'via',
#                                                                                                         'CreatedFor', 'Fam', 'Note', 'follow', 'termtype',
#                                                                                                         'localgovt', 'location', 'FaAssignTime', 'FaTime').order_by('-Time')
#                         ticketsCount = TicketsModel.objects.filter(
#                             TicketId=int(Word), valid=ValidId).count()
#                     elif SFilter == "IssueCategory":
#                         getdata = TicketsModel.objects.filter(IssueCategory__icontains=Word, valid=ValidId).values('TicketId', 'IssueName',
#                                                                                                                    'IssueCategory',
#                                                                                                                    'IssueDescription', 'Priority',
#                                                                                                                    'valid', 'Time', 'TicketStatus',
#                                                                                                                    'via',
#                                                                                                                    'CreatedFor', 'Fam', 'Note',
#                                                                                                                    'follow', 'termtype',
#                                                                                                                    'localgovt', 'location',
#                                                                                                                    'FaAssignTime', 'FaTime').order_by(
#                             '-Time')
#                         ticketsCount = TicketsModel.objects.filter(
#                             IssueCategory__icontains=Word, valid=ValidId).count()
#                     elif SFilter == "localgovt":
#                         getdata = TicketsModel.objects.filter(localgovt__icontains=Word, valid=ValidId).values('TicketId', 'IssueName',
#                                                                                                                'IssueCategory',
#                                                                                                                'IssueDescription', 'Priority',
#                                                                                                                'valid', 'Time', 'TicketStatus',
#                                                                                                                'via',
#                                                                                                                'CreatedFor', 'Fam', 'Note',
#                                                                                                                'follow', 'termtype',
#                                                                                                                'localgovt', 'location',
#                                                                                                                'FaAssignTime', 'FaTime').order_by(
#                             '-Time')
#                         ticketsCount = TicketsModel.objects.filter(
#                             localgovt__icontains=Word, valid=ValidId).count()
#                     elif SFilter == "via":
#                         getdata = TicketsModel.objects.filter(via__icontains=Word, valid=ValidId).values('TicketId', 'IssueName',
#                                                                                                          'IssueCategory',
#                                                                                                          'IssueDescription', 'Priority',
#                                                                                                          'valid', 'Time', 'TicketStatus',
#                                                                                                          'via',
#                                                                                                          'CreatedFor', 'Fam', 'Note',
#                                                                                                          'follow', 'termtype',
#                                                                                                          'localgovt', 'location',
#                                                                                                          'FaAssignTime', 'FaTime').order_by(
#                             '-Time')
#                         ticketsCount = TicketsModel.objects.filter(
#                             via__icontains=Word, valid=ValidId).count()

#                     elif SFilter == "ContactNo":
#                         getdata = TicketsModel.objects.filter(ContactNo__icontains=Word, valid=ValidId).values('TicketId', 'IssueName',
#                                                                                                                'IssueCategory',
#                                                                                                                'IssueDescription', 'Priority',
#                                                                                                                'valid', 'Time', 'TicketStatus',
#                                                                                                                'via',
#                                                                                                                'CreatedFor', 'Fam', 'Note',
#                                                                                                                'follow', 'termtype',
#                                                                                                                'localgovt', 'location',
#                                                                                                                'FaAssignTime', 'FaTime').order_by(
#                             '-Time')
#                         ticketsCount = TicketsModel.objects.filter(
#                             ContactNo__icontains=Word, valid=ValidId).count()

#                     elif SFilter == "IssueDescription":
#                         getdata = TicketsModel.objects.filter(IssueDescription__icontains=Word, valid=ValidId).values('TicketId', 'IssueName',
#                                                                                                                       'IssueCategory',
#                                                                                                                       'IssueDescription', 'Priority',
#                                                                                                                       'valid', 'Time', 'TicketStatus',
#                                                                                                                       'via',
#                                                                                                                       'CreatedFor', 'Fam', 'Note',
#                                                                                                                       'follow', 'termtype',
#                                                                                                                       'localgovt', 'location',
#                                                                                                                       'FaAssignTime', 'FaTime').order_by(
#                             '-Time')
#                         ticketsCount = TicketsModel.objects.filter(
#                             IssueDescription__icontains=Word, valid=ValidId).count()

#                 elif SFilter == "AL":
#                     print('this print')
#                     getdata = TicketsModel.objects.filter(Q(localgovt__icontains=Word) | Q(IssueCategory__icontains=Word) | Q(TicketId__icontains=Word) | Q(via__icontains=Word) | Q(ContactNo__icontains=Word) | Q(IssueDescription__icontains=Word), valid=ValidId).values('TicketId',
#                                                                                                                                                                                                                                                                              'IssueName',
#                                                                                                                                                                                                                                                                              'IssueCategory',
#                                                                                                                                                                                                                                                                              'IssueDescription',
#                                                                                                                                                                                                                                                                              'Priority',
#                                                                                                                                                                                                                                                                              'valid', 'Time',
#                                                                                                                                                                                                                                                                              'TicketStatus',
#                                                                                                                                                                                                                                                                              'via',
#                                                                                                                                                                                                                                                                              'CreatedFor', 'Fam',
#                                                                                                                                                                                                                                                                              'Note',
#                                                                                                                                                                                                                                                                              'follow', 'termtype',
#                                                                                                                                                                                                                                                                              'localgovt',
#                                                                                                                                                                                                                                                                              'location',
#                                                                                                                                                                                                                                                                              'FaAssignTime',
#                                                                                                                                                                                                                                                                              'FaTime').order_by(
#                         '-Time')
#                     ticketsCount = TicketsModel.objects.filter(Q(localgovt__icontains=Word) | Q(
#                         IssueCategory__icontains=Word) | Q(TicketId__icontains=Word) | Q(via__icontains=Word), valid=ValidId).count()

#             elif Filter == "AL":
#                 if SFilter != "AL":
#                     if SFilter == "TicketId":
#                         getdata = TicketsModel.objects.filter(TicketId=int(Word)).values('TicketId', 'IssueName', 'IssueCategory',
#                                                                                          'IssueDescription', 'Priority',
#                                                                                          'valid', 'Time', 'TicketStatus', 'via',
#                                                                                          'CreatedFor', 'Fam', 'Note', 'follow', 'termtype',
#                                                                                          'localgovt', 'location', 'FaAssignTime', 'FaTime').order_by('-Time')
#                         ticketsCount = TicketsModel.objects.filter(
#                             TicketId=int(Word)).count()
#                     elif SFilter == "IssueCategory":
#                         getdata = TicketsModel.objects.filter(IssueCategory__icontains=Word).values('TicketId', 'IssueName',
#                                                                                                     'IssueCategory',
#                                                                                                     'IssueDescription', 'Priority',
#                                                                                                     'valid', 'Time', 'TicketStatus',
#                                                                                                     'via',
#                                                                                                     'CreatedFor', 'Fam', 'Note',
#                                                                                                     'follow', 'termtype',
#                                                                                                     'localgovt', 'location',
#                                                                                                     'FaAssignTime', 'FaTime').order_by(
#                             '-Time')
#                         ticketsCount = TicketsModel.objects.filter(
#                             IssueCategory__icontains=Word).count()
#                     elif SFilter == "localgovt":
#                         getdata = TicketsModel.objects.filter(localgovt__icontains=Word).values('TicketId', 'IssueName',
#                                                                                                 'IssueCategory',
#                                                                                                 'IssueDescription', 'Priority',
#                                                                                                 'valid', 'Time', 'TicketStatus',
#                                                                                                 'via',
#                                                                                                 'CreatedFor', 'Fam', 'Note',
#                                                                                                 'follow', 'termtype',
#                                                                                                 'localgovt', 'location',
#                                                                                                 'FaAssignTime', 'FaTime').order_by(
#                             '-Time')
#                         ticketsCount = TicketsModel.objects.filter(
#                             localgovt__icontains=Word).count()
#                     elif SFilter == "via":
#                         getdata = TicketsModel.objects.filter(via__icontains=Word).values('TicketId', 'IssueName',
#                                                                                           'IssueCategory',
#                                                                                           'IssueDescription', 'Priority',
#                                                                                           'valid', 'Time', 'TicketStatus',
#                                                                                           'via',
#                                                                                           'CreatedFor', 'Fam', 'Note',
#                                                                                           'follow', 'termtype',
#                                                                                           'localgovt', 'location',
#                                                                                           'FaAssignTime', 'FaTime').order_by(
#                             '-Time')
#                         ticketsCount = TicketsModel.objects.filter(
#                             via__icontains=Word).count()
#                     elif SFilter == "ContactNo":
#                         getdata = TicketsModel.objects.filter(ContactNo__icontains=Word).values('TicketId', 'IssueName',
#                                                                                                 'IssueCategory',
#                                                                                                 'IssueDescription', 'Priority',
#                                                                                                 'valid', 'Time', 'TicketStatus',
#                                                                                                 'via',
#                                                                                                 'CreatedFor', 'Fam', 'Note',
#                                                                                                 'follow', 'termtype',
#                                                                                                 'localgovt', 'location',
#                                                                                                 'FaAssignTime', 'FaTime').order_by(
#                             '-Time')
#                         ticketsCount = TicketsModel.objects.filter(
#                             ContactNo__icontains=Word).count()

#                     elif SFilter == "IssueDescription":
#                         getdata = TicketsModel.objects.filter(IssueDescription__icontains=Word).values('TicketId', 'IssueName',
#                                                                                                        'IssueCategory',
#                                                                                                        'IssueDescription', 'Priority',
#                                                                                                        'valid', 'Time', 'TicketStatus',
#                                                                                                        'via',
#                                                                                                        'CreatedFor', 'Fam', 'Note',
#                                                                                                        'follow', 'termtype',
#                                                                                                        'localgovt', 'location',
#                                                                                                        'FaAssignTime', 'FaTime').order_by(
#                             '-Time')
#                         ticketsCount = TicketsModel.objects.filter(
#                             IssueDescription__icontains=Word).count()

#                 elif SFilter == "AL":
#                     print('this print')
#                     getdata = TicketsModel.objects.filter(Q(localgovt__icontains=Word) | Q(IssueCategory__icontains=Word) | Q(TicketId__icontains=Word) | Q(via__icontains=Word) | Q(ContactNo__icontains=Word) | Q(IssueDescription__icontains=Word)).values('TicketId',
#                                                                                                                                                                                                                                                               'IssueName',
#                                                                                                                                                                                                                                                               'IssueCategory',
#                                                                                                                                                                                                                                                               'IssueDescription',
#                                                                                                                                                                                                                                                               'Priority',
#                                                                                                                                                                                                                                                               'valid', 'Time',
#                                                                                                                                                                                                                                                               'TicketStatus',
#                                                                                                                                                                                                                                                               'via',
#                                                                                                                                                                                                                                                               'CreatedFor', 'Fam',
#                                                                                                                                                                                                                                                               'Note',
#                                                                                                                                                                                                                                                               'follow', 'termtype',
#                                                                                                                                                                                                                                                               'localgovt',
#                                                                                                                                                                                                                                                               'location',
#                                                                                                                                                                                                                                                               'FaAssignTime',
#                                                                                                                                                                                                                                                               'FaTime').order_by(
#                         '-Time')
#                     ticketsCount = TicketsModel.objects.filter(Q(localgovt__icontains=Word) | Q(
#                         IssueCategory__icontains=Word) | Q(TicketId__icontains=Word) | Q(via__icontains=Word)).count()

#         except:
#             print('error in ticket filter')

#         page = request.GET.get('page', pageno)
#         paginator = Paginator(getdata, size)
#         try:
#             employees = paginator.page(page)
#         except PageNotAnInteger:
#             employees = paginator.page(request.POST['page'])
#         except EmptyPage:
#             employees = paginator.page(paginator.num_pages)

#         all = []
#         for i in list(employees):
#             if i['valid'] == '0':
#                 Time = i['Time']
#                 daydata = IssueCategoryBucketing.objects.filter(
#                     IssueCategory="unassigned").values('Threshold')
#                 Threshold = Thresholdcalculate(daydata[0]['Threshold'], Time)
#                 i['Threshold'] = Threshold
#             elif i['valid'] == '1':
#                 daydata = IssueCategoryBucketing.objects.filter(IssueCategory=i["IssueCategory"]).values(
#                     'Threshold')
#                 Time = i['FaAssignTime']
#                 Threshold = Thresholdcalculate(daydata[0]['Threshold'], Time)
#                 i['Threshold'] = Threshold
#             elif i['valid'] == '2' and i['TicketStatus'] == '0':
#                 daydata = IssueCategoryBucketing.objects.filter(
#                     IssueCategory="completed").values('Threshold')
#                 Time = i['FaTime']
#                 Threshold = Thresholdcalculate(daydata[0]['Threshold'], Time)
#                 i['Threshold'] = Threshold
#             else:
#                 i['Threshold'] = 0

#                 # print('threshold',Threshold)

#             public = i.get('CreatedFor', None)
#             if public:
#                 public = User.objects.filter(pk=public).first()
#                 pub_mobile = public.email
#                 i['CreatedFor'] = pub_mobile
#             fams = i.get('Fam', None)
#             if fams:
#                 Fam = ''
#                 for index, fam in enumerate(fams):
#                     user = User.objects.filter(pk=fam).first()
#                     Fam += user.username + ' - ' + user.mobile
#                     if index != fams.__len__() - 1:
#                         Fam = Fam + '\n'
#                 i['Fam'] = Fam
#             else:
#                 i['Fam'] = 'Not Assigned'

#             # get no of agent remarks for particular tickets
#             ticketId = i.get('TicketId', None)
#             agentRemarksCount = AgentRemarks.objects.filter(
#                 Ticket_id=int(ticketId)).values('Remarks').count()
#             i['RemarksCount'] = agentRemarksCount
#             all.append(i)
#         # return Response({'data':all, 'Status': 1},
#         #                     status=status.HTTP_200_OK)

#         return Response(
#             {'message': "successfully Retrive", "data": {'ticketsData': all, 'ticketsCount': ticketsCount}, "status": "pass"}, status=status.HTTP_200_OK)


def searchFieldAgent(Word, ValidId, ticketStatusval):
    FieldAgentIds = User.objects.filter(
        username__icontains=Word, role='FA').values('id')

    totalTickets = []
    for data in FieldAgentIds:
        tickets = TicketsModel.objects.filter(
            Fam__contains=int(data['id']), valid=ValidId, TicketStatus=ticketStatusval).values('TicketId', 'IssueName',
                                                                                               'IssueCategory',
                                                                                               'IssueDescription', 'Priority',
                                                                                               'valid', 'Time', 'TicketStatus',
                                                                                               'via',
                                                                                               'CreatedFor', 'Fam', 'Note',
                                                                                               'follow', 'termtype',
                                                                                               'localgovt', 'location',
                                                                                               'FaAssignTime', 'FaTime').order_by(
            '-Time')
        totalTickets.append(tickets)
    return totalTickets


@permission_classes((AllowAny,))
class FilterSearchPaginatorForTickets(APIView):
    def get(self, request, pageno, size, Filter, SFilter):
        # print('data comming')
        Word = self.request.query_params.get('word', None)
        # print('word',Word)
        try:
            if Filter == "Unassigned" or Filter == "Pending":
                ValidId = "0"
                if Filter == "Pending":
                    ValidId = "1"
                if SFilter != "AL":
                    if SFilter == "TicketId":
                        getdata = TicketsModel.objects.filter(TicketId=int(Word), valid=ValidId).values('TicketId', 'IssueName', 'IssueCategory',
                                                                                                        'IssueDescription', 'Priority',
                                                                                                        'valid', 'Time', 'TicketStatus', 'via',
                                                                                                        'CreatedFor', 'Fam', 'Note', 'follow', 'termtype',
                                                                                                        'localgovt', 'location', 'FaAssignTime', 'FaTime').order_by('-Time')
                        ticketsCount = TicketsModel.objects.filter(
                            TicketId=int(Word), valid=ValidId).count()
                    elif SFilter == "IssueCategory":
                        getdata = TicketsModel.objects.filter(IssueCategory__icontains=Word, valid=ValidId).values('TicketId', 'IssueName',
                                                                                                                   'IssueCategory',
                                                                                                                   'IssueDescription', 'Priority',
                                                                                                                   'valid', 'Time', 'TicketStatus',
                                                                                                                   'via',
                                                                                                                   'CreatedFor', 'Fam', 'Note',
                                                                                                                   'follow', 'termtype',
                                                                                                                   'localgovt', 'location',
                                                                                                                   'FaAssignTime', 'FaTime').order_by(
                            '-Time')
                        ticketsCount = TicketsModel.objects.filter(
                            IssueCategory__icontains=Word, valid=ValidId).count()
                    elif SFilter == "localgovt":
                        getdata = TicketsModel.objects.filter(localgovt__icontains=Word, valid=ValidId).values('TicketId', 'IssueName',
                                                                                                               'IssueCategory',
                                                                                                               'IssueDescription', 'Priority',
                                                                                                               'valid', 'Time', 'TicketStatus',
                                                                                                               'via',
                                                                                                               'CreatedFor', 'Fam', 'Note',
                                                                                                               'follow', 'termtype',
                                                                                                               'localgovt', 'location',
                                                                                                               'FaAssignTime', 'FaTime').order_by(
                            '-Time')
                        ticketsCount = TicketsModel.objects.filter(
                            localgovt__icontains=Word, valid=ValidId).count()
                    elif SFilter == "via":
                        getdata = TicketsModel.objects.filter(via__icontains=Word, valid=ValidId).values('TicketId', 'IssueName',
                                                                                                         'IssueCategory',
                                                                                                         'IssueDescription', 'Priority',
                                                                                                         'valid', 'Time', 'TicketStatus',
                                                                                                         'via',
                                                                                                         'CreatedFor', 'Fam', 'Note',
                                                                                                         'follow', 'termtype',
                                                                                                         'localgovt', 'location',
                                                                                                         'FaAssignTime', 'FaTime').order_by(
                            '-Time')
                        ticketsCount = TicketsModel.objects.filter(
                            via__icontains=Word, valid=ValidId).count()

                    elif SFilter == "ContactNo":
                        getdata = TicketsModel.objects.filter(ContactNo__icontains=Word, valid=ValidId).values('TicketId', 'IssueName',
                                                                                                               'IssueCategory',
                                                                                                               'IssueDescription', 'Priority',
                                                                                                               'valid', 'Time', 'TicketStatus',
                                                                                                               'via',
                                                                                                               'CreatedFor', 'Fam', 'Note',
                                                                                                               'follow', 'termtype',
                                                                                                               'localgovt', 'location',
                                                                                                               'FaAssignTime', 'FaTime').order_by(
                            '-Time')
                        ticketsCount = TicketsModel.objects.filter(
                            ContactNo__icontains=Word, valid=ValidId).count()

                    elif SFilter == "IssueDescription":
                        getdata = TicketsModel.objects.filter(IssueDescription__icontains=Word, valid=ValidId).values('TicketId', 'IssueName',
                                                                                                                      'IssueCategory',
                                                                                                                      'IssueDescription', 'Priority',
                                                                                                                      'valid', 'Time', 'TicketStatus',
                                                                                                                      'via',
                                                                                                                      'CreatedFor', 'Fam', 'Note',
                                                                                                                      'follow', 'termtype',
                                                                                                                      'localgovt', 'location',
                                                                                                                      'FaAssignTime', 'FaTime').order_by(
                            '-Time')
                        ticketsCount = TicketsModel.objects.filter(
                            IssueDescription__icontains=Word, valid=ValidId).count()
                        print('total tickets', getdata)

                    # field agent search
                    elif SFilter == "Fam":
                        # get filed agent queryset from array
                        #ticketstatus ="0"
                        getdata = searchFieldAgent(
                            Word, ValidId, "0")[0]
                        ticketsCount = len(getdata)

                elif SFilter == "AL":
                    print('this print')
                    getdata = TicketsModel.objects.filter(Q(localgovt__icontains=Word) | Q(IssueCategory__icontains=Word) | Q(TicketId__icontains=Word) | Q(via__icontains=Word), valid=ValidId).values('TicketId',
                                                                                                                                                                                                        'IssueName',
                                                                                                                                                                                                        'IssueCategory',
                                                                                                                                                                                                        'IssueDescription',
                                                                                                                                                                                                        'Priority',
                                                                                                                                                                                                        'valid', 'Time',
                                                                                                                                                                                                        'TicketStatus',
                                                                                                                                                                                                        'via',
                                                                                                                                                                                                        'CreatedFor', 'Fam',
                                                                                                                                                                                                        'Note',
                                                                                                                                                                                                        'follow', 'termtype',
                                                                                                                                                                                                        'localgovt',
                                                                                                                                                                                                        'location',
                                                                                                                                                                                                        'FaAssignTime',
                                                                                                                                                                                                        'FaTime').order_by(
                        '-Time')
                    ticketsCount = TicketsModel.objects.filter(Q(localgovt__icontains=Word) | Q(
                        IssueCategory__icontains=Word) | Q(TicketId__icontains=Word) | Q(via__icontains=Word), valid=ValidId).count()

            elif Filter == "Completed" or Filter == "Closed":

                ValidId = "2"
                ticketStatusval = "0"
                if Filter == "Closed":
                    ValidId = "2"
                    ticketStatusval = "1"

                if SFilter != "AL":
                    if SFilter == "TicketId":
                        getdata = TicketsModel.objects.filter(TicketId=int(Word), valid=ValidId, TicketStatus=ticketStatusval).values('TicketId', 'IssueName', 'IssueCategory',
                                                                                                                                      'IssueDescription', 'Priority',
                                                                                                                                      'valid', 'Time', 'TicketStatus', 'via',
                                                                                                                                      'CreatedFor', 'Fam', 'Note', 'follow', 'termtype',
                                                                                                                                      'localgovt', 'location', 'FaAssignTime', 'FaTime').order_by('-Time')
                        ticketsCount = TicketsModel.objects.filter(TicketId=int(
                            Word), valid=ValidId, TicketStatus=ticketStatusval).count()
                    elif SFilter == "IssueCategory":
                        getdata = TicketsModel.objects.filter(IssueCategory__icontains=Word, valid=ValidId, TicketStatus=ticketStatusval).values('TicketId', 'IssueName',
                                                                                                                                                 'IssueCategory',
                                                                                                                                                 'IssueDescription', 'Priority',
                                                                                                                                                 'valid', 'Time', 'TicketStatus',
                                                                                                                                                 'via',
                                                                                                                                                 'CreatedFor', 'Fam', 'Note',
                                                                                                                                                 'follow', 'termtype',
                                                                                                                                                 'localgovt', 'location',
                                                                                                                                                 'FaAssignTime', 'FaTime').order_by(
                            '-Time')
                        ticketsCount = TicketsModel.objects.filter(
                            IssueCategory__icontains=Word, valid=ValidId, TicketStatus=ticketStatusval).count()
                    elif SFilter == "localgovt":
                        getdata = TicketsModel.objects.filter(localgovt__icontains=Word, valid=ValidId, TicketStatus=ticketStatusval).values('TicketId', 'IssueName',
                                                                                                                                             'IssueCategory',
                                                                                                                                             'IssueDescription', 'Priority',
                                                                                                                                             'valid', 'Time', 'TicketStatus',
                                                                                                                                             'via',
                                                                                                                                             'CreatedFor', 'Fam', 'Note',
                                                                                                                                             'follow', 'termtype',
                                                                                                                                             'localgovt', 'location',
                                                                                                                                             'FaAssignTime', 'FaTime').order_by(
                            '-Time')
                        ticketsCount = TicketsModel.objects.filter(
                            localgovt__icontains=Word, valid=ValidId, TicketStatus=ticketStatusval).count()
                    elif SFilter == "via":
                        getdata = TicketsModel.objects.filter(via__icontains=Word, valid=ValidId, TicketStatus=ticketStatusval).values('TicketId', 'IssueName',
                                                                                                                                       'IssueCategory',
                                                                                                                                       'IssueDescription', 'Priority',
                                                                                                                                       'valid', 'Time', 'TicketStatus',
                                                                                                                                       'via',
                                                                                                                                       'CreatedFor', 'Fam', 'Note',
                                                                                                                                       'follow', 'termtype',
                                                                                                                                       'localgovt', 'location',
                                                                                                                                       'FaAssignTime', 'FaTime').order_by(
                            '-Time')
                        ticketsCount = TicketsModel.objects.filter(
                            via__icontains=Word, valid=ValidId, TicketStatus=ticketStatusval).count()
                    elif SFilter == "ContactNo":
                        getdata = TicketsModel.objects.filter(ContactNo__icontains=Word, valid=ValidId, TicketStatus=ticketStatusval).values('TicketId', 'IssueName',
                                                                                                                                             'IssueCategory',
                                                                                                                                             'IssueDescription', 'Priority',
                                                                                                                                             'valid', 'Time', 'TicketStatus',
                                                                                                                                             'via',
                                                                                                                                             'CreatedFor', 'Fam', 'Note',
                                                                                                                                             'follow', 'termtype',
                                                                                                                                             'localgovt', 'location',
                                                                                                                                             'FaAssignTime', 'FaTime').order_by(
                            '-Time')
                        ticketsCount = TicketsModel.objects.filter(
                            ContactNo__icontains=Word, valid=ValidId, TicketStatus=ticketStatusval).count()

                    elif SFilter == "IssueDescription":
                        getdata = TicketsModel.objects.filter(IssueDescription__icontains=Word, valid=ValidId, TicketStatus=ticketStatusval).values('TicketId', 'IssueName',
                                                                                                                                                    'IssueCategory',
                                                                                                                                                    'IssueDescription', 'Priority',
                                                                                                                                                    'valid', 'Time', 'TicketStatus',
                                                                                                                                                    'via',
                                                                                                                                                    'CreatedFor', 'Fam', 'Note',
                                                                                                                                                    'follow', 'termtype',
                                                                                                                                                    'localgovt', 'location',
                                                                                                                                                    'FaAssignTime', 'FaTime').order_by(
                            '-Time')
                        ticketsCount = TicketsModel.objects.filter(
                            IssueDescription__icontains=Word, valid=ValidId, TicketStatus=ticketStatusval).count()
                    elif SFilter == "Fam":
                        # get filed agent queryset from array
                        getdata = searchFieldAgent(
                            Word, ValidId, ticketStatusval)[0]
                        ticketsCount = len(getdata)
                elif SFilter == "AL":
                    getdata = TicketsModel.objects.filter(Q(localgovt__icontains=Word) | Q(IssueCategory__icontains=Word) | Q(TicketId__icontains=Word) | Q(via__icontains=Word), valid=ValidId, TicketStatus=ticketStatusval).values('TicketId',
                                                                                                                                                                                                                                      'IssueName',
                                                                                                                                                                                                                                      'IssueCategory',
                                                                                                                                                                                                                                      'IssueDescription',
                                                                                                                                                                                                                                      'Priority',
                                                                                                                                                                                                                                      'valid', 'Time',
                                                                                                                                                                                                                                      'TicketStatus',
                                                                                                                                                                                                                                      'via',
                                                                                                                                                                                                                                      'CreatedFor', 'Fam',
                                                                                                                                                                                                                                      'Note',
                                                                                                                                                                                                                                      'follow', 'termtype',
                                                                                                                                                                                                                                      'localgovt',
                                                                                                                                                                                                                                      'location',
                                                                                                                                                                                                                                      'FaAssignTime',
                                                                                                                                                                                                                                      'FaTime').order_by(
                        '-Time')
                    ticketsCount = TicketsModel.objects.filter(Q(localgovt__icontains=Word) | Q(IssueCategory__icontains=Word) | Q(
                        TicketId__icontains=Word) | Q(via__icontains=Word), valid=ValidId, TicketStatus=ticketStatusval).count()

            elif Filter == "Invalid":
                ValidId = "3"
                if SFilter != "AL":
                    if SFilter == "TicketId":
                        getdata = TicketsModel.objects.filter(TicketId=int(Word), valid=ValidId).values('TicketId', 'IssueName', 'IssueCategory',
                                                                                                        'IssueDescription', 'Priority',
                                                                                                        'valid', 'Time', 'TicketStatus', 'via',
                                                                                                        'CreatedFor', 'Fam', 'Note', 'follow', 'termtype',
                                                                                                        'localgovt', 'location', 'FaAssignTime', 'FaTime').order_by('-Time')
                        ticketsCount = TicketsModel.objects.filter(
                            TicketId=int(Word), valid=ValidId).count()
                    elif SFilter == "IssueCategory":
                        getdata = TicketsModel.objects.filter(IssueCategory__icontains=Word, valid=ValidId).values('TicketId', 'IssueName',
                                                                                                                   'IssueCategory',
                                                                                                                   'IssueDescription', 'Priority',
                                                                                                                   'valid', 'Time', 'TicketStatus',
                                                                                                                   'via',
                                                                                                                   'CreatedFor', 'Fam', 'Note',
                                                                                                                   'follow', 'termtype',
                                                                                                                   'localgovt', 'location',
                                                                                                                   'FaAssignTime', 'FaTime').order_by(
                            '-Time')
                        ticketsCount = TicketsModel.objects.filter(
                            IssueCategory__icontains=Word, valid=ValidId).count()
                    elif SFilter == "localgovt":
                        getdata = TicketsModel.objects.filter(localgovt__icontains=Word, valid=ValidId).values('TicketId', 'IssueName',
                                                                                                               'IssueCategory',
                                                                                                               'IssueDescription', 'Priority',
                                                                                                               'valid', 'Time', 'TicketStatus',
                                                                                                               'via',
                                                                                                               'CreatedFor', 'Fam', 'Note',
                                                                                                               'follow', 'termtype',
                                                                                                               'localgovt', 'location',
                                                                                                               'FaAssignTime', 'FaTime').order_by(
                            '-Time')
                        ticketsCount = TicketsModel.objects.filter(
                            localgovt__icontains=Word, valid=ValidId).count()
                    elif SFilter == "via":
                        getdata = TicketsModel.objects.filter(via__icontains=Word, valid=ValidId).values('TicketId', 'IssueName',
                                                                                                         'IssueCategory',
                                                                                                         'IssueDescription', 'Priority',
                                                                                                         'valid', 'Time', 'TicketStatus',
                                                                                                         'via',
                                                                                                         'CreatedFor', 'Fam', 'Note',
                                                                                                         'follow', 'termtype',
                                                                                                         'localgovt', 'location',
                                                                                                         'FaAssignTime', 'FaTime').order_by(
                            '-Time')
                        ticketsCount = TicketsModel.objects.filter(
                            via__icontains=Word, valid=ValidId).count()
                    elif SFilter == "ContactNo":
                        getdata = TicketsModel.objects.filter(ContactNo__icontains=Word, valid=ValidId).values('TicketId', 'IssueName',
                                                                                                               'IssueCategory',
                                                                                                               'IssueDescription', 'Priority',
                                                                                                               'valid', 'Time', 'TicketStatus',
                                                                                                               'via',
                                                                                                               'CreatedFor', 'Fam', 'Note',
                                                                                                               'follow', 'termtype',
                                                                                                               'localgovt', 'location',
                                                                                                               'FaAssignTime', 'FaTime').order_by(
                            '-Time')
                        ticketsCount = TicketsModel.objects.filter(
                            ContactNo__icontains=Word, valid=ValidId).count()

                    elif SFilter == "IssueDescription":
                        getdata = TicketsModel.objects.filter(IssueDescription__icontains=Word, valid=ValidId).values('TicketId', 'IssueName',
                                                                                                                      'IssueCategory',
                                                                                                                      'IssueDescription', 'Priority',
                                                                                                                      'valid', 'Time', 'TicketStatus',
                                                                                                                      'via',
                                                                                                                      'CreatedFor', 'Fam', 'Note',
                                                                                                                      'follow', 'termtype',
                                                                                                                      'localgovt', 'location',
                                                                                                                      'FaAssignTime', 'FaTime').order_by(
                            '-Time')
                        ticketsCount = TicketsModel.objects.filter(
                            IssueDescription__icontains=Word, valid=ValidId).count()
                    elif SFilter == "Fam":
                        # get filed agent queryset from array
                        # ticketStatusval="0"
                        getdata = searchFieldAgent(Word, ValidId, "0")[0]
                        ticketsCount = len(getdata)
                elif SFilter == "AL":
                    print('this print')
                    getdata = TicketsModel.objects.filter(Q(localgovt__icontains=Word) | Q(IssueCategory__icontains=Word) | Q(TicketId__icontains=Word) | Q(via__icontains=Word), valid=ValidId).values('TicketId',
                                                                                                                                                                                                        'IssueName',
                                                                                                                                                                                                        'IssueCategory',
                                                                                                                                                                                                        'IssueDescription',
                                                                                                                                                                                                        'Priority',
                                                                                                                                                                                                        'valid', 'Time',
                                                                                                                                                                                                        'TicketStatus',
                                                                                                                                                                                                        'via',
                                                                                                                                                                                                        'CreatedFor', 'Fam',
                                                                                                                                                                                                        'Note',
                                                                                                                                                                                                        'follow', 'termtype',
                                                                                                                                                                                                        'localgovt',
                                                                                                                                                                                                        'location',
                                                                                                                                                                                                        'FaAssignTime',
                                                                                                                                                                                                        'FaTime').order_by(
                        '-Time')
                    ticketsCount = TicketsModel.objects.filter(Q(localgovt__icontains=Word) | Q(
                        IssueCategory__icontains=Word) | Q(TicketId__icontains=Word) | Q(via__icontains=Word), valid=ValidId).count()

            elif Filter == "AL":
                if SFilter != "AL":
                    if SFilter == "TicketId":
                        getdata = TicketsModel.objects.filter(TicketId=int(Word)).values('TicketId', 'IssueName', 'IssueCategory',
                                                                                         'IssueDescription', 'Priority',
                                                                                         'valid', 'Time', 'TicketStatus', 'via',
                                                                                         'CreatedFor', 'Fam', 'Note', 'follow', 'termtype',
                                                                                         'localgovt', 'location', 'FaAssignTime', 'FaTime').order_by('-Time')
                        ticketsCount = TicketsModel.objects.filter(
                            TicketId=int(Word)).count()
                    elif SFilter == "IssueCategory":
                        getdata = TicketsModel.objects.filter(IssueCategory__icontains=Word).values('TicketId', 'IssueName',
                                                                                                    'IssueCategory',
                                                                                                    'IssueDescription', 'Priority',
                                                                                                    'valid', 'Time', 'TicketStatus',
                                                                                                    'via',
                                                                                                    'CreatedFor', 'Fam', 'Note',
                                                                                                    'follow', 'termtype',
                                                                                                    'localgovt', 'location',
                                                                                                    'FaAssignTime', 'FaTime').order_by(
                            '-Time')
                        ticketsCount = TicketsModel.objects.filter(
                            IssueCategory__icontains=Word).count()
                    elif SFilter == "localgovt":
                        getdata = TicketsModel.objects.filter(localgovt__icontains=Word).values('TicketId', 'IssueName',
                                                                                                'IssueCategory',
                                                                                                'IssueDescription', 'Priority',
                                                                                                'valid', 'Time', 'TicketStatus',
                                                                                                'via',
                                                                                                'CreatedFor', 'Fam', 'Note',
                                                                                                'follow', 'termtype',
                                                                                                'localgovt', 'location',
                                                                                                'FaAssignTime', 'FaTime').order_by(
                            '-Time')
                        ticketsCount = TicketsModel.objects.filter(
                            localgovt__icontains=Word).count()
                    elif SFilter == "via":
                        getdata = TicketsModel.objects.filter(via__icontains=Word).values('TicketId', 'IssueName',
                                                                                          'IssueCategory',
                                                                                          'IssueDescription', 'Priority',
                                                                                          'valid', 'Time', 'TicketStatus',
                                                                                          'via',
                                                                                          'CreatedFor', 'Fam', 'Note',
                                                                                          'follow', 'termtype',
                                                                                          'localgovt', 'location',
                                                                                          'FaAssignTime', 'FaTime').order_by(
                            '-Time')
                        ticketsCount = TicketsModel.objects.filter(
                            via__icontains=Word).count()
                    elif SFilter == "ContactNo":
                        getdata = TicketsModel.objects.filter(ContactNo__icontains=Word).values('TicketId', 'IssueName',
                                                                                                'IssueCategory',
                                                                                                'IssueDescription', 'Priority',
                                                                                                'valid', 'Time', 'TicketStatus',
                                                                                                'via',
                                                                                                'CreatedFor', 'Fam', 'Note',
                                                                                                'follow', 'termtype',
                                                                                                'localgovt', 'location',
                                                                                                'FaAssignTime', 'FaTime').order_by(
                            '-Time')
                        ticketsCount = TicketsModel.objects.filter(
                            ContactNo__icontains=Word).count()

                    elif SFilter == "IssueDescription":
                        getdata = TicketsModel.objects.filter(IssueDescription__icontains=Word).values('TicketId', 'IssueName',
                                                                                                       'IssueCategory',
                                                                                                       'IssueDescription', 'Priority',
                                                                                                       'valid', 'Time', 'TicketStatus',
                                                                                                       'via',
                                                                                                       'CreatedFor', 'Fam', 'Note',
                                                                                                       'follow', 'termtype',
                                                                                                       'localgovt', 'location',
                                                                                                       'FaAssignTime', 'FaTime').order_by(
                            '-Time')
                        ticketsCount = TicketsModel.objects.filter(
                            IssueDescription__icontains=Word).count()

                    elif SFilter == "Fam":
                        FieldAgentIds = User.objects.filter(
                            username__icontains=Word, role='FA').values('id')
                        totalTickets = []
                        for data in FieldAgentIds:
                            # print('filed agent id', data['id'])
                            tickets = TicketsModel.objects.filter(
                                Fam__contains=int(data['id'])).values('TicketId', 'IssueName',
                                                                      'IssueCategory',
                                                                      'IssueDescription', 'Priority',
                                                                      'valid', 'Time', 'TicketStatus',
                                                                      'via',
                                                                      'CreatedFor', 'Fam', 'Note',
                                                                      'follow', 'termtype',
                                                                      'localgovt', 'location',
                                                                      'FaAssignTime', 'FaTime').order_by(
                                '-Time')
                            totalTickets.append(tickets)

                        getdata = totalTickets[0]
                        ticketsCount = len(getdata)
                elif SFilter == "AL":
                    print('this print')
                    getdata = TicketsModel.objects.filter(Q(localgovt__icontains=Word) | Q(IssueCategory__icontains=Word) | Q(TicketId__icontains=Word) | Q(via__icontains=Word)).values('TicketId',
                                                                                                                                                                                         'IssueName',
                                                                                                                                                                                         'IssueCategory',
                                                                                                                                                                                         'IssueDescription',
                                                                                                                                                                                         'Priority',
                                                                                                                                                                                         'valid', 'Time',
                                                                                                                                                                                         'TicketStatus',
                                                                                                                                                                                         'via',
                                                                                                                                                                                         'CreatedFor', 'Fam',
                                                                                                                                                                                         'Note',
                                                                                                                                                                                         'follow', 'termtype',
                                                                                                                                                                                         'localgovt',
                                                                                                                                                                                         'location',
                                                                                                                                                                                         'FaAssignTime',
                                                                                                                                                                                         'FaTime').order_by(
                        '-Time')
                    ticketsCount = TicketsModel.objects.filter(Q(localgovt__icontains=Word) | Q(
                        IssueCategory__icontains=Word) | Q(TicketId__icontains=Word) | Q(via__icontains=Word)).count()

        except Exception as e:
            print('error in ticket filter', e)

        page = request.GET.get('page', pageno)
        paginator = Paginator(getdata, size)
        try:
            employees = paginator.page(page)
        except PageNotAnInteger:
            employees = paginator.page(request.POST['page'])
        except EmptyPage:
            employees = paginator.page(paginator.num_pages)

        all = []
        for i in list(employees):
            if i['valid'] == '0':
                Time = i['Time']
                daydata = IssueCategoryBucketing.objects.filter(
                    IssueCategory="unassigned").values('Threshold')
                Threshold = Thresholdcalculate(daydata[0]['Threshold'], Time)
                i['Threshold'] = Threshold
            elif i['valid'] == '1':
                daydata = IssueCategoryBucketing.objects.filter(IssueCategory=i["IssueCategory"]).values(
                    'Threshold')
                Time = i['FaAssignTime']
                Threshold = Thresholdcalculate(daydata[0]['Threshold'], Time)
                i['Threshold'] = Threshold
            elif i['valid'] == '2' and i['TicketStatus'] == '0':
                daydata = IssueCategoryBucketing.objects.filter(
                    IssueCategory="completed").values('Threshold')
                Time = i['FaTime']
                Threshold = Thresholdcalculate(daydata[0]['Threshold'], Time)
                i['Threshold'] = Threshold
            else:
                i['Threshold'] = 0

                # print('threshold',Threshold)

            public = i.get('CreatedFor', None)
            if public:
                public = User.objects.filter(pk=public).first()
                pub_mobile = public.email
                i['CreatedFor'] = pub_mobile
            fams = i.get('Fam', None)
            if fams:
                Fam = ''
                for index, fam in enumerate(fams):
                    user = User.objects.filter(pk=fam).first()
                    Fam += user.username + ' - ' + user.mobile
                    if index != fams.__len__() - 1:
                        Fam = Fam + '\n'
                i['Fam'] = Fam
            else:
                i['Fam'] = 'Not Assigned'

            # get no of agent remarks for particular tickets
            ticketId = i.get('TicketId', None)
            agentRemarksCount = AgentRemarks.objects.filter(
                Ticket_id=int(ticketId)).values('Remarks').count()
            i['RemarksCount'] = agentRemarksCount
            all.append(i)
        # return Response({'data':all, 'Status': 1},
        #                     status=status.HTTP_200_OK)

        return Response(
            {'message': "successfully Retrive", "data": {'ticketsData': all, 'ticketsCount': ticketsCount}, "status": "pass"}, status=status.HTTP_200_OK)
