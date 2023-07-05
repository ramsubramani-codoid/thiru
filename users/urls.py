from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('otp/', views.Verifications.as_view(), name='otp_view'),
    path('register/', views.Registerusers.as_view(), name='register_view'),
    path('login-otp/', views.LoginotpUser.as_view(), name='login_otp'),
    path('login-verify/', views.verfiyloginuser.as_view(), name='login_view'),
    path('adminuserreg/', views.Admincreateuser.as_view(), name='admin_reg_view'),
    path('backendlogin/', views.Backenduserlogin.as_view(),
         name='backend_login_view'),
    path('logout/', views.LogoutView.as_view(), name='logout_view'),
    path('user/', views.UserView.as_view(), name='user_view'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('getallissue/', views.GetAllissueDetails.as_view(), name='issue bucketing'),
    path('deleteissueCat/<cat>', views.GetAllissueDetails.as_view(),
         name='delete issue bucketing category'),
    path('TicketCreation/', views.TicketCreation.as_view(), name='Ticket creations'),
    path('Getparticularticketdetails/<id>', views.Getparticularticketdetails.as_view(),
         name='Get particular ticket details'),
    path('Fieldagentdata/<id>', views.Fieldagentdata.as_view(),
         name='Field agent data'),
    path('GetSpecicFieldagentdata/<name>',
         views.GetSpecicFieldagentdata.as_view(), name='Field agent data'),
    path('GetParticularUserTickets/<id>', views.GetParticularUserTickets.as_view(),
         name='Get Particular User Tickets'),

    path('GetParticularCCTickets/<id>', views.GetParticularCCTickets.as_view(),
         name='Get Particular CC Tickets'),
    path('GetOpenandCloseTicket/', views.GetOpenandCloseTicket.as_view(),
         name='Get Open and close ticket'),
    path('GetUserIdUsingMobileNo/<id>', views.GetUserIdUsingMobileNo.as_view(),
         name='Get UserId Using MobileNo'),
    # need threshold  remarks count
    path('GetSingleFieldAgentTicket/<id>', views.GetSingleFieldAgentTicket.as_view(),
         name='Get Single FieldAgent Ticket'),
    path('GetCategoryNameCount/', views.GetCategoryNameCount.as_view(),
         name='Get Category NameCount'),
    path('GetSpecificCategoryName/<cat>',
         views.GetSpecificCategoryName.as_view(), name='Get Specific Category Name'),
    path('GetAllAgentsData/<cat>', views.GetAllAgentsData.as_view(),
         name='Get Specific Category Name'),

    path('SearchAddress/<cat>', views.SearchAddress.as_view(), name='Search Address'),
    path('GetLatLongTickets/', views.GetLatLongTickets.as_view(),
         name='Get Lat Long Tickets'),

    path('PushNotificationKeyUpload/', views.PushNotificationKeyUpload.as_view(),
         name='Push Notification KeyUpload'),

    path('GetSpecificUserNotification/<id>', views.GetSpecificUserNotification.as_view(),
         name='Get Specific User Notification'),

    # path('GetSpecificUserDetails/<id>', views.GetSpecificUserDetails.as_view(), name='Get Specific UserDetails'),

    path('SegrigationTicketClose/', views.SegrigationTicketClose.as_view(),
         name='Segrigation Ticket Close'),
    path('GetMlaTickets/', views.GetMlaTickets.as_view(), name='Get Mla Tickets'),
    path('GetCatAccountByCal/', views.GetCatAccountByCal.as_view(),
         name='Get Cat Account ByCal'),
    path('FollowUp/', views.FollowUp.as_view(), name='Follow up increase by 1'),

    path('UpdateDeleteUserMedia/<user_media_id>',
         views.UpdateDeleteUserMedia.as_view(), name='Update Delete User Media'),
    path('DeleteAgentMedia/<agent_media_id>',
         views.UpdateDeleteAgentMedia.as_view(), name=' Delete Agent Media'),
    path('getAreaCategory/', views.GetAreaCategory.as_view(), name='area'),
    path('categorythreshold/', views.getCategoryThreshold.as_view(),
         name='categorythreshold'),



    # path('GetAllTicketsPaginator/<pageno>/<size>/<Filter>/<SFilter>', views.FilterSearchPaginatorForAdmin.as_view(), name='GetAllTicketsPaginator'),
    path('GetAllTicketsPaginator/<pageno>/<size>/<Filter>/<SFilter>',
         views.FilterSearchPaginatorForTickets.as_view(), name='GetAllTicketsPaginatorForCC'),


]
