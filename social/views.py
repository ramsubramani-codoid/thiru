from users.serializers import ChatSerializer
from users.models import AgentUpload_media, Chat, TicketsModel, User
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from .social import SocialMessageHandler, WhatsappMessageHandler, client, host

splitter = '*/'
def whatsapp_attachments_filter(data):
    try:
        media_type:str = data['MediaContentType0']
        url = data['MediaUrl0']
        body = data['Body']
        if body =='':
            if media_type.__contains__('video'):
                return 'video'+splitter+url
            elif media_type.__contains__('audio'):
                return 'audio'+splitter+url
            else:
                return 'image'+splitter+url
        else:
            return f'doc'+splitter+url
    except:
        latitude = data['Latitude']
        longitude = data['Longitude']
        return 'map'+splitter+latitude+','+longitude


class WhatsappView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    clients = {'test':'hello'}
    
    def post(self, request):
        body = None
        data = request.data
        mobile = data['From'][12:]+splitter+data['ProfileName']
        try:
            body = whatsapp_attachments_filter(data)
        except:
            try:
                body = data['Body']
            except:
                body = None
        client:WhatsappMessageHandler = self.clients.get(mobile,None)
        handle_client(self,client,mobile,body,WhatsappMessageHandler)
        return Response('Success',200)
        
# function to handle both facebook and whatsapp clients
def handle_client(self,client,recipient,message,handler:SocialMessageHandler):
    if client:
        res = client.handle_message(message)
        if res=='none':
            handler = handler(recipient)
            client = self.clients[recipient] = handler
            client.handle_message(message)
    else:
        try:
            client = self.clients[recipient] = handler(recipient)
            client.handle_message(message)
        except:
            pass


class ChatView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, id):
        chats = Chat.objects.filter(ticket=id).all()
        chats = ChatSerializer(instance=chats, many=True)
        return Response({"data":chats.data},200)

    def post(self,request):
        data = request.data
        files = request.FILES
        ticketId = data['ticket_id']
        sender = data.get('sender',None)
        try:
            ticket:TicketsModel = TicketsModel.objects.get(pk=ticketId)
            if ticket.via == 'Whatsapp':
                if not files:
                    message = data['message']
                    user:User = User.objects.filter(id=ticket.CreatedFor).first()
                    if sender=='MLA':
                        message = 'Message from MLA: '+ message
                    client.messages.create(
                        from_='whatsapp:+14155238886',
                        body=message,
                        to='whatsapp:+91'+user.email
                    )
                    chat = Chat()
                    chat.ticket = ticket
                    chat.message = message
                    if sender:
                        chat.sender = sender
                    else:
                        chat.sender = 'agent'
                    chat.save()
                else:
                    images = files.getlist('images',None)
                    audios = files.getlist('audios',None)
                    videos = files.getlist('videos',None)
                    docs = files.getlist('docs',None)
                    if images:
                        media_handle(images,'image',ticket,sender)
                    if videos:
                        media_handle(videos,'video',ticket,sender)
                    if audios:
                        media_handle(audios,'audio',ticket,sender)
                    if docs:
                        media_handle(docs,'doc',ticket,sender)
                return Response({'message':'Sent Message'},200)
            else:
                return Response({'message':'Ticket not from whatsapp so cannot send message.'},500)
        except:
            return Response({'message':'Cannot Send Message'},500)


def media_handle(medias,type,ticket:TicketsModel,sender):
    user:User = User.objects.filter(id=ticket.CreatedFor).first()
    if sender =='MLA' and (type=='audio' or type=='doc'):
        client.messages.create(
        from_='whatsapp:+14155238886',
        body = 'Message from MLA',
        to='whatsapp:+91'+user.email,
        )
        
    for media in medias:
        agentMedia = AgentUpload_media()
        agentMedia.Agent_media_type = type
        agentMedia.Ticket_creation_in = ticket.TicketId
        agentMedia.Agent_media = media
        agentMedia.save()
        url = host+'/media/'+str(agentMedia.Agent_media)
        if sender == 'MLA' and (type=='image' or type=='video'):
            body = 'Message from MLA'
        else:
            body = ''
        client.messages.create(
        from_='whatsapp:+14155238886',
        body = body,
        media_url=url,
        to='whatsapp:+91'+user.email,
        )
        chat = Chat()
        chat.message = 'media/'+str(agentMedia.Agent_media)
        if sender:
            chat.sender = sender
        else:
            chat.sender = 'agent'
        chat.media_type = type
        chat.ticket = ticket
        chat.save()

# class FacebookView(APIView):
#     authentication_classes = []
#     permission_classes = [AllowAny]
#     clients = {}

#     def post(self, request):
#         data = request.data
#         messaging = data['entry'][0]['messaging'][0]
#         recipient_id = messaging['sender']['id']
#         message = messaging['message']['text']
#         client:FacebookMessageHandler = self.clients.get(recipient_id,None)
#         handle_client(self,client,recipient_id,message,FacebookMessageHandler)

#         return Response('Success',200)

#     def get(self, request):
#         VERIFY_TOKEN = "123456"
#         mode = request.query_params['hub.mode']
#         token = request.query_params['hub.verify_token'];
#         challenge = request.query_params['hub.challenge'];
#         if (mode and token):
#             if (mode == 'subscribe' and token == VERIFY_TOKEN):  
#                 challenge = str(challenge)
#                 return response.HttpResponse(challenge)   
#         else:
#             return Response('Forbidden',status=status.HTTP_403_FORBIDDEN)  