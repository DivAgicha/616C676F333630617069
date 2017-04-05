from django.contrib.gis.geoip2 import GeoIP2
from main.models import AccessAttempts
from oauth2_provider.models import Application
from main.thread import ThreadBuilderUtility, ThreadDetails
from main import log
from django.utils.deprecation import MiddlewareMixin
import os, json, time

clear = lambda: os.system('cls')
logger = log.getTimedLogger()

_request_tracker = None

def clear_screen():
    global clear
    clear()
        
def get_client_id(req, path=None):
    try:
        if not path:
            app = Application.objects.get(accesstoken__token__exact=req.META['HTTP_AUTHORIZATION'].split()[1])
            return app.name
        else:
            if path.startswith('/api/client'):
                app_check = Application.objects.filter(client_id__exact=req.POST.get('client_id'), client_secret__exact=req.POST.get('client_secret'))
                return app_check[0].name if app_check else "BadRequestForForgotToken"
            elif path.startswith('/o/token'):
                if req.POST.get('grant_type', '')=='authorization_code':
                    app_check = Application.objects.filter(client_id__exact=req.POST.get('client_id'), client_secret__exact=req.POST.get('client_secret'), grant__code__exact=req.POST.get('code'), grant__redirect_uri__exact=req.POST.get('redirect_uri'))
                    return app_check[0].name if app_check else "BadRequestForGrantToken"
                elif req.POST.get('grant_type', '')=='refresh_token':
                    app_check = Application.objects.filter(client_id__exact=req.POST.get('client_id'), client_secret__exact=req.POST.get('client_secret'), refreshtoken__token__exact=req.POST.get('refresh_token'))
                    return app_check[0].name if app_check else "BadRequestForRefreshToken"
                else:
                    raise Exception('Invalid Request for Grant/Refresh Token')
            elif path.startswith('/o/revoke_token'):
                app_check = Application.objects.filter(client_id__exact=req.POST.get('client_id'), client_secret__exact=req.POST.get('client_secret'), accesstoken__token__exact=req.POST.get('token'))
                return app_check[0].name if app_check else "BadRequestForRevokeToken"
    except Exception as e:
        logger.error("token error: "+str(e))
        if 'Grant/Refresh' not in str(e):
            return "AuthenticationFailed"
        else:
            return str(e)
    
def startMailThread(msg, new_credentials=False):
    try:
        mailDetails = {
            'subj': 'API Accessed - LOCALHOST',
            'msg': msg,
            'from': 'Algo360API',
            'to': [
                'divyansh@thinkanalytics.in'
            ]
        }
        
        if new_credentials:
            mailDetails['subj'] += ' - (New Credentials)'
            
        t = ThreadBuilderUtility(**ThreadDetails('accessed', mailDetails))
        t.setDaemonType
        logger.info('Initiating thread...'+str(type(t))+' as '+t.getName())
        t.start()
    except Exception as e:
        logger.error("email error: "+str(e))
        pass
    
def register_client_details(req):
    authorization = req.META.get('HTTP_AUTHORIZATION', "-")
    remote_address = req.META.get('REMOTE_ADDR', "-")
    x_forwarded_for = req.META.get('HTTP_X_FORWARDED_FOR', None)    
    x_forwarded_host = req.META.get('HTTP_X_FORWARDED_HOST', "-")       
    x_forwarded_server = req.META.get('HTTP_X_FORWARDED_SERVER', "-")       
    host = req.META.get('HTTP_HOST', "-")
    ip = x_forwarded_for.split(',')[0] if x_forwarded_for else remote_address
    path_hit = req.META.get('PATH_INFO', "-")
    client = ''
    
    msg_string_for_mail = None
    access_attempts_obj = None
    try:
        g = GeoIP2()
        
        logger.info('-------------------------------------------------------------------------------------------------------------------')
                
        logger.info("REMOTE_ADDR: "+remote_address)
        logger.info("HTTP_X_FORWARDED_FOR: "+str(x_forwarded_for))
        logger.info("HTTP_X_FORWARDED_HOST: "+x_forwarded_host)
        logger.info("HTTP_X_FORWARDED_SERVER: "+x_forwarded_server)
        logger.info("path hit: "+path_hit)
        
        details = g.city(ip)
        details['ip'] = ip
        logger.info("CLIENT DETAILS: "+str(details))  
        
        if not path_hit.startswith('/o/token') and not path_hit.startswith('/o/revoke_token') and not path_hit.startswith('/api/client'):
            client = 'HomePage' if path_hit=='/' else get_client_id(req)
            msg_string_for_mail = 'AUTHORIZATION: '+authorization+'\nREMOTE_ADDR: '+remote_address+'\nHTTP_X_FORWARDED_FOR: '+str(x_forwarded_for)+'\nHTTP_X_FORWARDED_HOST: '+x_forwarded_host+'\nHTTP_X_FORWARDED_SERVER: '+x_forwarded_server+'\nHTTP_HOST: '+host+'\n\nCLIENT_ID: '+client+'\nCUSTOMER_IP: '+ip+'\nPATH_HIT: '+path_hit+'\nCOUNTRY: '+str(details['country_name'])+'\nCITY: '+str(details['city'])
        else:
            logger.info('POST_BODY: '+str(req.POST))
            client = get_client_id(req, path_hit)
            msg_string_for_mail = 'AUTHORIZATION: '+authorization+'\nREMOTE_ADDR: '+remote_address+'\nHTTP_X_FORWARDED_FOR: '+str(x_forwarded_for)+'\nHTTP_X_FORWARDED_HOST: '+x_forwarded_host+'\nHTTP_X_FORWARDED_SERVER: '+x_forwarded_server+'\nHTTP_HOST: '+host+'\n\nCLIENT_ID: '+client+'\nCUSTOMER_IP: '+ip+'\nPATH_HIT: '+path_hit+'\nCOUNTRY: '+str(details['country_name'])+'\nCITY: '+str(details['city'])+'\n\nPOST_BODY: '+str(req.POST)            
    except Exception as e:
        logger.error("error while fetching client details: "+str(e))
        msg_string_for_mail = 'AUTHORIZATION: '+authorization+'\nREMOTE_ADDR: '+remote_address+'\nHTTP_X_FORWARDED_FOR: '+str(x_forwarded_for)+'\nHTTP_X_FORWARDED_HOST: '+x_forwarded_host+'\nHTTP_X_FORWARDED_SERVER: '+x_forwarded_server+'\nHTTP_HOST: '+host+'\n\nCUSTOMER_IP: '+str(ip)+'\nPATH_HIT: '+str(path_hit)+'\nerror: '+str(e)
    else:
        #access_attempts_obj = AccessAttempts.objects.create(client_id = client, customer_ip = ip, path_hit = path_hit, country = details['country_name'], lat = details['latitude'], long = details['longitude'], city = details['city'], country_code = details['country_code'], postal_code = details['postal_code'], region = details['region'], dma_code = details['dma_code'])
        pass
        
    return msg_string_for_mail, access_attempts_obj

class Algo360Middleware(MiddlewareMixin):
    def process_request(self, request):
        global _request_tracker
        
        #clear_screen()
        if request.META.get('PATH_INFO', '')=='/' or request.META.get('PATH_INFO', '').startswith('/api') or request.META.get('PATH_INFO', '').startswith('/o/token') or request.META.get('PATH_INFO', '').startswith('/o/revoke_token'):
            _request_tracker['msg_string_for_mail'], _request_tracker['access_attempts_obj'] = register_client_details(request)
        else:
            _request_tracker['msg_string_for_mail'], _request_tracker['access_attempts_obj'] = None, None

class RequestTimeTracker(MiddlewareMixin):
    def process_request(self, request):
        global _request_tracker
        
        if not _request_tracker:
            _request_tracker = {}
            _request_tracker['start_time'] = time.time()

    def process_response(self, request, response):
        global _request_tracker
        
        try:                
            if _request_tracker['msg_string_for_mail']:
                response_time = str(int((time.time()-_request_tracker['start_time']) * 1000))+' ms'
                logger.info('RESPONSE TIME: '+response_time)
                startMailThread(_request_tracker['msg_string_for_mail']+'\n\nRESPONSE_TIME: '+response_time)
            
                if _request_tracker['access_attempts_obj']:
                    _request_tracker['access_attempts_obj'].response_time = response_time
                    _request_tracker['access_attempts_obj'].save()
                #else:
                #    _request_tracker['access_attempts_obj'] = AccessAttempts.objects.create(client_id = 'test entry', customer_ip = 'test entry', path_hit = 'test entry', response_time = response_time)
        except Exception as e:
            logger.error('request_tracker error: '+str(e))
        finally:
            _request_tracker = None
            
        try:
            if request.META.get('PATH_INFO', '').startswith('/o/token') and response.status_code==200:
                json_response = json.loads(str(response.content.decode("utf-8")))
                logger.info('New Credentials: \''+str(json_response)+'\'')
                startMailThread('CLIENT_ID: '+Application.objects.get(accesstoken__token__exact=json_response['access_token']).name+'\nACCESS_TOKEN: '+json_response['access_token']+'\nREFRESH_TOKEN: '+json_response['refresh_token'], True)
        except Exception as e:
            logger.error("new credentials error: "+str(e))
            
        return response
        