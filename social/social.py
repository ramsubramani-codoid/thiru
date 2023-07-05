from users.models import Chat, SocialUser, TicketsModel, User, verification
from twilio.rest import Client
from .messages import messages

host = 'http://205.147.97.85:9002'

def create_user(id,full_name,provider):
    # Creating Base User
    user = User()
    user.email = id
    user.username = full_name
    user.provider = provider
    user.role = 'public'
    user.save()
    # Verification for restricting other mode of registration
    verify = verification()
    verify.Phonenumber = id
    verify.OTP = '12345'
    verify.valid = True
    verify.save()
    # Creating Social User
    social_user = SocialUser()
    social_user.user = user
    social_user.save()
    return social_user

#Whatsapp Client
account_sid = 'AC27acddc040d11c1ce4ec89c1ecaa9bde'
auth_token = '00f0a79536128ab0b39d9d5efe827c75'
client = Client(account_sid, auth_token)


class SocialMessageHandler():
    social_user:SocialUser = None
    complaint:TicketsModel = None
    temp = []
    temp_text = ''
    splitter = '*/'

    def __init__(self):
        pass


    def send_message(self,text:str):
        pass


    def send_file(self,file_url):
        pass


    def get_user(self)-> User:
        return User.objects.get(pk = self.social_user.user.pk)


    def exit(self):
        self.send_message(self.get_message_text('exit'))
        self.set_state('enter_hi')

        
    def set_state(self,state:str):
        self.social_user.state = state
        self.social_user.save()


    def get_message_text(self,text:str)->str:
        return messages[text]


    def handle_message(self,message):
        if self.social_user:
            self.social_user = SocialUser.objects.filter(pk= self.social_user.pk).first()
        if message == None:
            self.send_message('Not Supported Format')
        if self.social_user.state == None:
            self.send_issue_confirmation(message)
        elif self.social_user.state == 'issue_confirmation':
            self.issue_confirmation(message)
        elif self.social_user.state == 'issue_enter_again':
            self.ticket_create(message)
        elif self.social_user.state == 'issue_analyzing':
            self.issue_analyzing(message)
        elif self.social_user.state == 'complaint_closed':
            self.complaint_closed(message)
        elif self.social_user.state == 'sent_complaint_options':
            self.sent_complaint_options(message)
        elif self.social_user.state == 'enter_old_ticket_no':
            self.enter_old_ticket_no(message)
        # elif self.social_user.state == 'old_tickets':
        #     self.old_tickets(message)
        # elif self.social_user.state == 'enter_hi':
        #     self.enter_hi(message)
        # elif self.social_user.state == 'entered_hi':
        #     self.entered_hi(message)
        
    def enter_old_ticket_no(self,message):
        pass

    # Old Complaints
    def old_tickets(self):
        text = ''
        tickets = None
        tickets = TicketsModel.objects.filter(CreatedFor = str(self.social_user.user.pk)).all()
        if(tickets):
            text = 'உங்கள் பழைய புகார்கள் / Your Old Tickets\n'
            for ticket in tickets:
                ticket: TicketsModel
                text += 'புகார் எண் / Ticket Number: {}\nபுகார் / Issue: {}\nநிலை / Status: '.format(ticket.TicketId,ticket.IssueDescription)
                if ticket.TicketStatus == '1':
                    text += 'சரி செய்யப்பட்டது / Completed\n'
                else:
                    text += 'நிலுவையில் உள்ளது / Pending\n'
            text += '\n'+self.get_message_text('select')+self.get_message_text('old_new')
        else:
            text = self.get_message_text('no_old')
        self.send_message(text)
        
    def sent_complaint_options(self,message):
        if message == '1':
            text = ''
            split_msg = self.social_user.temp.split(self.splitter)
            if split_msg.__len__()==1:
                text += str(split_msg[0])+'\n'
            else:
                self.send_file(split_msg[1])
            text += f'மேலே கொடுக்கப்பட்டுள்ளது உங்கள் புகாரா? / Is the above message your issue?\n'
            text += '1: ஆம் / Yes\n2: இல்லை / No\n'
            self.send_message(text)
            self.set_state('issue_confirmation')

        elif message == '2':
            self.old_tickets()

        else:
            text = self.get_message_text('wrong')+self.get_message_text('old_new')
            self.send_message(text)

    def complaint_closed(self,message):
        text = self.get_message_text('select')+self.get_message_text('old_new')
        self.send_message(text)
        self.social_user.temp = message
        self.set_state('sent_complaint_options')

    # Issue Confirmation Option
    def send_issue_confirmation(self,message):
        username = self.social_user.user.username
        text = f'நல்வரவு, {username} மேலே கொடுக்கப்பட்டுள்ளது உங்கள் புகாரா? / Welcome, {username} Is the above message your issue?\n'
        text += '1: Yes / ஆம்\n2: No / இல்லை\n'
        self.send_message(text)
        self.social_user.temp = message
        self.set_state('issue_confirmation')


    def issue_confirmation(self,message):
        #  Tamil is True and english is False
        if message == '1':
            self.ticket_create(self.social_user.temp) 

        elif message =='2':
            self.send_message(self.get_message_text('issue_enter_again'))
            self.set_state('issue_enter_again')

        else:
            text = 'தவறான தேர்வு / Wrong Option\n'
            split_msg = self.social_user.temp.split(self.splitter)
            if split_msg.__len__()==1:
                text += str(split_msg[0])+'\n'
            else:
                self.send_file(split_msg[1])
            text += f'மேலே கொடுக்கப்பட்டுள்ளது உங்கள் புகாரா? / Is the above message your issue?\n'
            text += '1: ஆம் / Yes\n2: இல்லை / No\n'
            self.send_message(text)


    def ticket_create(self,message):
        user = self.get_user()
        ticket:TicketsModel = TicketsModel()
        ticket.CreatedBy = user
        ticket.CreatedFor = user.pk
        ticket.ContactNo = user.email
        ticket.via = 'Whatsapp'
        ticket.save()
        self.save_by_msg(message,ticket)
        self.send_message(self.get_message_text('issue_analyzing'))
        self.set_state('issue_analyzing')


    def issue_analyzing(self, message):
        ticket = TicketsModel.objects.filter(CreatedFor = str(self.social_user.user.pk),TicketStatus='0').order_by('-Time').first()
        self.save_by_msg(message,ticket)
        self.send_message(self.get_message_text('got_message'))


    def save_by_msg(self,message,ticket):
        split_msg = message.split(self.splitter)
        chat:Chat = Chat()
        chat.ticket = ticket
        if split_msg.__len__()==1:
            chat.message = split_msg[0]
        else:
            chat.message = split_msg[1]
            chat.media_type = split_msg[0]
        chat.save()


class WhatsappMessageHandler(SocialMessageHandler):
    def __init__(self,mobile):
        data = mobile.split('*/')
        recipient_id = data[0]
        user = User.objects.filter(provider='email',email=recipient_id).first()
        if user:
            send_whatsapp_message('நீங்கள் ஏற்கனவே கால் சென்டர் மூலம் புகாரை எழுப்பியுள்ளீர்கள். / You have already raised a complaint through Call Center.',recipient_id)
            return 'registered'
        else:
            social_user = SocialUser.objects.filter(user__email=recipient_id).first()
            if not social_user:
                full_name = data[1]
                self.social_user = create_user(recipient_id,full_name,'whatsapp')
            else:
                self.social_user = social_user


    def send_message(self,text):
        client.messages.create(
            from_='whatsapp:+14155238886',
            body=text,
            to='whatsapp:+91'+ self.social_user.user.email
        )


    def send_file(self,file_url):
        client.messages.create(
        from_='whatsapp:+14155238886',
        body = '',
        media_url=file_url,
        to='whatsapp:+91'+ self.social_user.user.email
        )


def send_whatsapp_message(text, mobile):
    client.messages.create(
        from_='whatsapp:+14155238886',
        body=text,
        to='whatsapp:+91'+ mobile
    )
    
def send_whatsapp_file_message(file_url, mobile):
    client.messages.create(
        from_='whatsapp:+14155238886',
        body='',
        media_url=file_url,
        to='whatsapp:+91'+ mobile
    )

def set_social_user_state(state, mobile):
    soc_user:SocialUser =  SocialUser.objects.filter(user__email=mobile).first()
    soc_user.state = state
    soc_user.save()

# from pymessenger.bot import Bot
# from django.utils import timezone
# from django.core.files.storage import default_storage

# #Facebook Client
# token = 'EAAMoZCZB6eENYBAJqflDiZCFQB8ikCIYwka2xGZBu9mTJowpMpuYNQICa2bAfIRk6Y'
# token += 'fxAzDbqOBE4gZAPDk701Nc4Glgc3LLsE5ZBWHrcMloBfUlZBQGBbUwxWoDu'
# token += 'NJqx8WOXmsRNgXOeV0zFdTwA0nZCNGZAUdFyUxX713kZBcOqLoq0vIpFoIRt4'
# bot = Bot(token)


# # Welcome Message after registration
# def enter_hi(self,message):
#     if message.lower() == 'hi' or message=='வணக்கம்':
#         if self.get_language():
#             welcome_text = 'வணக்கம், {}.\n'.format(self.social_user.user.username) + 'பின்வரும் விருப்பங்களிலிருந்து தேர்வு செய்யவும்\n'
#             welcome_text = welcome_text + '1: புதிய புகார்\n' + '2: முந்தைய புகார்கள்\n' + '3: வெளியேறு.'
#         else:
#             welcome_text = 'Welcome, {}.\n'.format(self.social_user.user.username) + 'Choose from the following options\n'
#             welcome_text = welcome_text + '1: New Complaint\n' + '2: Previous Complaints\n' + '3: Exit.'
#         self.send_message(welcome_text)
#         self.set_state('entered_hi')

#     else:
#         self.send_message(self.get_message_text('exit'))

# def entered_hi(self,message):
#     if message == '1':
#         if self.get_language():
#             text = 'புகார் வகையைத் தேர்ந்தெடுக்கவும்.\n'

#         else:
#             text = 'Select Your Complaint Type\n'
            
#         self.send_message(text)
#         self.set_state('enter_complaint_category')

#     elif message == '2':
#         self.old_tickets()

#     elif message == '3':
#         self.exit()

#     else:
#         if self.get_language():
#             wrong_option = 'தவறான தேர்வு,\nபின்வரும் விருப்பங்களிலிருந்து தேர்வு செய்யவும்\n'
#             wrong_option += '1: புதிய புகார்\n2: முந்தைய புகார்கள்\n3: வெளியேறு.'
#         else:
#             wrong_option = 'Wrong Option,\nChoose from the following options\n'
#             wrong_option = wrong_option + '1: New Complaint\n2: Previous Complaints\n3: Exit'
#         self.send_message(wrong_option)
        

#     self.welcome_complaint_options()

# def welcome_complaint_options(self):
#     if self.get_language():
#         options = 'பின்வரும் விருப்பங்களிலிருந்து தேர்வு செய்யவும்\n'
#         options = options +'1: புதிய புகார்\n' + '2: முந்தைய புகார்கள்\n' + '3: வெளியேறு.'
#     else:
#         options = 'Choose from the following options\n'
#         options = options + '1: New Complaint\n' + '2: Previous Complaints\n' + '3: Exit'
#     self.send_message(options)
#     self.set_state('entered_hi')


# class FacebookMessageHandler(SocialMessageHandler):
#     def __init__(self,recipient_id):
#         social_user = SocialUser.objects.filter(user__email=recipient_id).first()
#         if not social_user:
#             user_info = bot.get_user_info(recipient_id)
#             full_name = user_info['first_name'] + ' ' + user_info['last_name']
#             self.social_user = create_user(recipient_id,full_name,'facebook')
#         else:
#             self.social_user = social_user

#     def send_message(self,text):
#         bot.send_text_message(self.social_user.user.email,text)

#     def send_file_message(self,file_url,type):
#         global host
#         if type == 'image':
#             # print(bot.send_image_url(self.social_user.recipient,host+file_url))
#             print(bot.send_image_url(self.social_user.recipient,
#             "https://homepages.cae.wisc.edu/~ece533/images/airplane.png"))

#         elif type == 'video':
#             print(bot.send_video_url(self.social_user.recipient,host+file_url))

#         else:
#             print(bot.send_attachment_url(self.social_user.recipient,'file',host+file_url))

