from django.contrib import admin
from main.models import VariableClassifcation, AccessAttempts, AccessAttempts_TEST
from oauth2_provider.models import get_application_model, Grant, AccessToken, RefreshToken
from oauth2_provider.admin import RawIDAdmin

class AccessAttemptsView(admin.ModelAdmin):
    list_display = ('id', 'client_id', 'customer_ip', 'path_hit', 'response_time', 'country', 'lat', 'long', 'city', 'region', 'date')

class AccessAttempts_TESTView(admin.ModelAdmin):
    list_display = ('id', 'client_id', 'customer_ip', 'path_hit', 'response_time', 'country', 'lat', 'long', 'city', 'region', 'date')
    
class VariableClassifcationView(admin.ModelAdmin):
    list_display = ('id', 'varName', 'desc', 'tags')

admin.site.register(AccessAttempts, AccessAttemptsView)
admin.site.register(AccessAttempts_TEST, AccessAttempts_TESTView)
admin.site.register(VariableClassifcation, VariableClassifcationView)

# ------------------- FOR BELOW CODE, UNREGISTER ALREADY REGISTERED MODELS FIRST -------------------
    
Application = get_application_model()

admin.site.unregister(Application)
admin.site.unregister(Grant)
admin.site.unregister(AccessToken)
admin.site.unregister(RefreshToken)

class ApplicationView(RawIDAdmin):
    list_display = ('name', 'client_id', 'client_secret')
    
class GrantView(RawIDAdmin):
    list_display = ('code', 'application', 'expires')
    
class AccessTokenView(RawIDAdmin):
    list_display = ('token', 'application', 'expires')
    
class RefreshTokenView(RawIDAdmin):
    list_display = ('token', 'application', 'access_token')

admin.site.register(Application, ApplicationView)
admin.site.register(Grant, GrantView)
admin.site.register(AccessToken, AccessTokenView)
admin.site.register(RefreshToken, RefreshTokenView)

# ------------------- CUSTOMIZED ADMIN PAGE -------------------
    
class AdminSiteView(admin.AdminSite):
    site_header = 'Think Analytics'
    site_title = 'Admin Page'
    site_url = 'http://www.algo360.com/'
    index_title = 'Algo360 Consumption API'

admin_site = AdminSiteView(name='divyansh_agicha')  # for basic_admin

admin_site.register(Application)
admin_site.register(Grant)
admin_site.register(AccessToken)
admin_site.register(RefreshToken)

admin_site.register(AccessAttempts)
admin_site.register(VariableClassifcation)