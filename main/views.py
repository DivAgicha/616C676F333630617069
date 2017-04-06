from django.http import Http404
import os, csv, time
from datetime import datetime as dt
from django.utils import timezone

from main.models import VariableClassifcation
from main.boto_resources import boto_for_s3, boto_for_dynamodb
from main.response import JSONResponse
from main import log

from rest_framework import views
from oauth2_provider.ext.rest_framework import OAuth2Authentication
from oauth2_provider.models import Application, RefreshToken, AccessToken

clear = lambda: os.system('cls')
logger = log.getTimedLogger()

def clear_screen():
    global clear
    clear()

def generateRegex(urlTags):
    return urlTags.replace("/all", "/[a-z]+")

def put_file_contents_as_json(json_data, s3_file_list):
    try:
        DbLevelData_columns = ['latitude', 'longitude', 'username', 'road']
        
        for s3_file in s3_file_list:
            csv_string = s3_file.get()['Body'].read().decode('utf-8')
            reader = csv.reader(csv_string.splitlines(), delimiter='|')
            lines = list(reader)
            logger.info(s3_file.key+" (storing "+str(len(lines))+" lines as json...)")
            
            for columnNum in range(0,len(lines[0])):
                if "var" in lines[0][columnNum].lower() or lines[0][columnNum].lower() in DbLevelData_columns:
                    for i in range (1,len(lines)):
                        if lines[i][columnNum]!="" and lines[i][columnNum]!="NA":
                            if "Entity" in s3_file.key:
                                json_temp = {lines[0][columnNum]+"_"+str(i) : lines[i][columnNum]}
                            else:
                                json_temp = {lines[0][columnNum] : lines[i][columnNum]}
                            #logger.info(json_temp)
                            json_data['result']['data'].append(json_temp)
    except Exception as e:
        logger.error("s3 file list error: "+str(e))

def put_file_contents_as_json_containing_vars(json_data, s3_file_list, var_list, forSpagoBI=False):
    try:
        DbLevelData_columns = ['latitude', 'longitude', 'username', 'road']
        
        for s3_file in s3_file_list:
            csv_string = s3_file.get()['Body'].read().decode('utf-8')
            reader = csv.reader(csv_string.splitlines(), delimiter='|')
            lines = list(reader)
            logger.info(s3_file.key+" (storing "+str(len(lines))+" lines as json...)")
            
            if not forSpagoBI:
                for columnNum in range(0,len(lines[0])):
                    if lines[0][columnNum].lower() in var_list or lines[0][columnNum].lower() in DbLevelData_columns:
                        for i in range (1,len(lines)):
                            if lines[i][columnNum]!="" and lines[i][columnNum]!="NA":
                                if "Entity" in s3_file.key:
                                    json_temp = {lines[0][columnNum]+"_"+str(i) : lines[i][columnNum]}
                                else:
                                    json_temp = {lines[0][columnNum] : lines[i][columnNum]}
                                #logger.info(json_temp)
                                json_data['result']['data'].append(json_temp)
            else:
                typeOfData = s3_file.key.split('/')[-1].split('_',2)[2].split('.')[0].strip()
                json_data['result']['data'][typeOfData] = []
                
                for i in range (1,len(lines)):
                    json_temp = {}
                    for columnNum in range(0,len(lines[0])):
                        if lines[0][columnNum].lower() in var_list:
                            if lines[i][columnNum]!="" and lines[i][columnNum]!="NA":
                                if "Entity" in s3_file.key:
                                    json_temp[lines[0][columnNum]+"_"+str(i)] = lines[i][columnNum]
                                else:
                                    json_temp[lines[0][columnNum]] = lines[i][columnNum]
                    if len(json_temp)>0:
                        json_data['result']['data'][typeOfData].append(json_temp)
                        
                if len(json_data['result']['data'][typeOfData]) == 0:
                    del json_data['result']['data'][typeOfData]
    except Exception as e:
        logger.error("s3 file list error: "+str(e))


def default(request):
    clear_screen()
    raise Http404
    
class CustDetails(views.APIView):
    authentication_classes = [OAuth2Authentication]
    required_scopes = ['read']
    
    def get(self, request, cuid):
        clear_screen()
        logger.info("fetching details...")
        
        cid = 'none'
        cname = ''
        try:
            token = request.META['HTTP_AUTHORIZATION'].split()[1]
            logger.info("using Token: "+token)
            app = Application.objects.get(accesstoken__token__exact=token)
            cid = app.client_id
            cname = app.name
            logger.info("using ClientID: "+str(cid))
            logger.info("using ClientName: "+str(cname))
        except Exception as e:
            logger.error("token error: "+str(e))
            pass
        
        tags = '[a-z//]+'
        date = False
        if request.GET:
            if request.GET.get('tags'):
                tags = request.GET.get('tags')
                logger.info("found 'tags': "+tags)
            if request.GET.get('date'):
                fromDate = request.GET.get('date')+" 00:00:00"
                if request.GET.get('dateTo'):
                    toDate = request.GET.get('dateTo')+" 23:59:59"
                else:
                    toDate = request.GET.get('date')+" 23:59:59"
                date = True
                logger.info("found 'date': "+fromDate+" to "+toDate)
        tags = generateRegex(tags.lower())
        logger.info('tags Regex: '+tags)
        
        try:
            dynamo = boto_for_dynamodb()
            dynamo.initialise_client
            
            try:
                alternative = dynamo.retrieve_alternative(cuid, cname.upper())['Items'][0]
                logger.info("original: "+str(cuid)+", alternative: "+alternative['CUID']['S'])
                cuid = alternative['CUID']['S']
            except Exception as e:
                logger.error("alternative error: "+str(e))
                raise Http404
            
            if date:
                #date_heirarchy_for_s3 = str(dt.strptime(fromDate, "%d-%m-%Y %H:%M:%S")).split(" ",1)[0].split("-", 2)
                fromDate = time.mktime(dt.strptime(fromDate, "%d-%m-%Y %H:%M:%S").timetuple())
                toDate = time.mktime(dt.strptime(toDate, "%d-%m-%Y %H:%M:%S").timetuple())
                logger.info("altered 'date': "+str(fromDate)+" to "+str(toDate))
                runversion_data = dynamo.scan_db_for_customer(cuid, str(fromDate).split(".",1)[0], str(toDate).split(".",1)[0])
            else:
                runversion_data = dynamo.scan_db_for_customer(cuid)
            
            if not runversion_data['Count'] > 0:
                raise Http404
            else:
                try:
                    dynamoDate = str(dt.fromtimestamp(float(runversion_data['Items'][runversion_data['Count']-1]['EndTime']['N'])))
                    date_heirarchy_for_s3 = str(dt.strptime(dynamoDate, "%Y-%m-%d %H:%M:%S")).split(" ",1)[0].split("-", 2)
                except Exception as e:
                    logger.error("dynamoDate error: "+str(e))
                    date_heirarchy_for_s3 = [dt.now().year, dt.now().month, dt.now().day]
                
                
            max_ver = runversion_data['Items'][runversion_data['Count']-1]['Version']['N']
            max_ver_time = runversion_data['Items'][runversion_data['Count']-1]['TimeStamp']['N']
            logger.info("max_ver: "+str(max_ver)+"\tmax_ver_time: "+str(max_ver_time))
            
            s3 = boto_for_s3()
            s3.initialise_resource
            date_heirarchy_for_s3 = str(date_heirarchy_for_s3[0])+"/"+str(date_heirarchy_for_s3[1]).lstrip("0")+"/"+str(date_heirarchy_for_s3[2]).lstrip("0")
            logger.info("date_heirarchy_for_s3: "+date_heirarchy_for_s3)
            file_list = s3.get_file_list_from_bucket(s3.get_bucket(), "Output/"+date_heirarchy_for_s3, tags, cuid+"_"+max_ver)  #replace "COMMUNITY" with cid when live
            
            json_data = {
                'count': 1,
                'result': {
                    'status': 'success',
                    'data': []
                }
            }
            
            try:
                json_data['result']['customerid'] = alternative['referrer_user_id']['S']
            except Exception as e:
                json_data['result']['customerid'] = cuid
            
            if not tags=='[a-z//]+':
                var_list = []
                varClass_data = VariableClassifcation.objects.filter(tags__iregex=tags).values('varName')
                for var in varClass_data:
                    var_list.append(var['varName'].lower())
                logger.info("var_list length: "+str(len(var_list)))#+" "+str(var_list))
                put_file_contents_as_json_containing_vars(json_data, file_list, var_list)
            else:
                put_file_contents_as_json(json_data, file_list)
        except Exception as e:
            json_data = {
                'count': 0,
                'result': {
                    'status': 'failed'
                },
            }
            if len(str(e)) > 0:
                logger.error("error: "+str(e))
                json_data['error'] = 'Error encountered'
            else:
                logger.error("error: Customer Not Found-'"+str(e)+"'")
                json_data['error'] = 'Customer Not Found'
            
        return JSONResponse(json_data)

class CustomerCount(views.APIView):
    authentication_classes = [OAuth2Authentication]
    required_scopes = ['read']
    
    def get(self, request):
        clear_screen()
        logger.info("fetching list...")
        
        cid = 'none'
        cname = ''
        try:
            token = request.META['HTTP_AUTHORIZATION'].split()[1]
            logger.info("using Token: "+token)
            app = Application.objects.get(accesstoken__token__exact=token)
            cid = app.client_id
            cname = app.name
            logger.info("using ClientID: "+str(cid))
            logger.info("using ClientName: "+str(cname))
        except Exception as e:
            logger.error("token error: "+str(e))
            pass
            
        date = False
        if request.GET:
            if request.GET.get('date'):
                fromDate = request.GET.get('date')+" 00:00:00"
                if request.GET.get('dateTo'):
                    toDate = request.GET.get('dateTo')+" 23:59:59"
                else:
                    toDate = request.GET.get('date')+" 23:59:59"
                date = True
                logger.info("found 'date': "+fromDate+" to "+toDate)
        
        try:
            dynamo = boto_for_dynamodb()
            dynamo.initialise_client
            
            if date:
                fromDate = time.mktime(dt.strptime(fromDate, "%d-%m-%Y %H:%M:%S").timetuple())
                toDate = time.mktime(dt.strptime(toDate, "%d-%m-%Y %H:%M:%S").timetuple())
                logger.info("altered 'date': "+str(fromDate)+" to "+str(toDate))
                runversion_data = dynamo.scan_db_for_distinct_customers(cname.upper(), str(fromDate).split(".",1)[0], str(toDate).split(".",1)[0])
            else:
                runversion_data = dynamo.scan_db_for_distinct_customers(cname.upper())
            
            json_data = {
                'count': 0,
                'result': {
                    'status': 'success',
                    'customerids': [],
                }
            }
            
            distinct_customerids = []
            if runversion_data['Count'] > 0:
                for cust in runversion_data['Items']:
                    if cust['CUID']['S'] not in distinct_customerids:
                        try:
                            if cname.upper()=='MYHBT':
                                id = {'id': cust['CUID']['S']}
                            else:
                                id = {'id': cust['referrer_user_id']['S']}
                        except Exception as e:
                            id = {'id': cust['CUID']['S']}
                        json_data['result']['customerids'].append(id)
                        distinct_customerids.append(cust['CUID']['S'])
                    
            json_data['count'] = len(json_data['result']['customerids'])
            logger.info('distinct IDs count: '+str(json_data['count'] ))
        except Exception as e:
            logger.error("error: "+str(e))
            json_data = {
                'count': 0,
                'result': {
                    'status': 'failed'
                },
                'error': str(e)
            }       
            
        return JSONResponse(json_data)

class SpagoDetails(views.APIView):
    authentication_classes = [OAuth2Authentication]
    required_scopes = ['read']
    
    def post(self, request, cuid):
        clear_screen()
        logger.info("fetching details...")
        
        cid = 'none'
        cname = ''
        try:
            token = request.META['HTTP_AUTHORIZATION'].split()[1]
            logger.info("using Token: "+token)
            app = Application.objects.get(accesstoken__token__exact=token)
            cid = app.client_id
            cname = app.name
            logger.info("using ClientID: "+str(cid))
            logger.info("using ClientName: "+str(cname))
        except Exception as e:
            logger.error("token error: "+str(e))
            pass
        
        var_list = []
        dir_list = []
        date = False
        if request.POST:
            if request.POST.get('var_list'):
                str_list = request.POST.get('var_list')
                var_list = str_list.split(",")
                logger.info("found 'var_list': "+str(type(var_list))+": "+str(var_list))
            if request.POST.get('dir_list'):
                str_list = request.POST.get('dir_list')
                dir_list = str_list.split(",")
                logger.info("found 'var_list': "+str(type(dir_list))+": "+str(dir_list))
            if request.POST.get('date'):
                fromDate = request.POST.get('date')+" 00:00:00"
                toDate = request.POST.get('date')+" 23:59:59"
                date = True
                logger.info("found 'date': "+fromDate+" to "+toDate)
        
        try:
            dynamo = boto_for_dynamodb()
            dynamo.initialise_client
            
            try:
                alternative = dynamo.retrieve_alternative(cuid, cname.upper())['Items'][0]
                logger.info("original: "+str(cuid)+", alternative: "+alternative['CUID']['S'])
                cuid = alternative['CUID']['S']
            except Exception as e:
                logger.error("alternative error: "+str(e))
                raise Http404
            
            if date:
                #date_heirarchy_for_s3 = str(dt.strptime(fromDate, "%d-%m-%Y %H:%M:%S")).split(" ",1)[0].split("-", 2)
                fromDate = time.mktime(dt.strptime(fromDate, "%d-%m-%Y %H:%M:%S").timetuple())
                toDate = time.mktime(dt.strptime(toDate, "%d-%m-%Y %H:%M:%S").timetuple())
                logger.info("altered 'date': "+str(fromDate)+" to "+str(toDate))
                runversion_data = dynamo.scan_db_for_customer(cuid, str(fromDate).split(".",1)[0], str(toDate).split(".",1)[0])
            else:
                runversion_data = dynamo.scan_db_for_customer(cuid)
            
            if not runversion_data['Count'] > 0:
                raise Http404
            else:
                try:
                    dynamoDate = str(dt.fromtimestamp(float(runversion_data['Items'][runversion_data['Count']-1]['EndTime']['N'])))
                    date_heirarchy_for_s3 = str(dt.strptime(dynamoDate, "%Y-%m-%d %H:%M:%S")).split(" ",1)[0].split("-", 2)
                except Exception as e:
                    logger.error("dynamoDate error: "+str(e))
                    date_heirarchy_for_s3 = [dt.now().year, dt.now().month, dt.now().day]
                
            max_ver = runversion_data['Items'][runversion_data['Count']-1]['Version']['N']
            max_ver_time = runversion_data['Items'][runversion_data['Count']-1]['TimeStamp']['N']
            logger.info("max_ver: "+str(max_ver)+"\tmax_ver_time: "+str(max_ver_time))
            
            s3 = boto_for_s3()
            s3.initialise_resource
            date_heirarchy_for_s3 = str(date_heirarchy_for_s3[0])+"/"+str(date_heirarchy_for_s3[1]).lstrip("0")+"/"+str(date_heirarchy_for_s3[2]).lstrip("0")
            logger.info("date_heirarchy_for_s3: "+date_heirarchy_for_s3)
            file_list = s3.get_file_list_from_bucket(s3.get_bucket(), "Output/"+date_heirarchy_for_s3, '[a-z//]+', cuid+"_"+max_ver, dir_list)  #replace "COMMUNITY" with cid when live
            
            json_data = {
                'count': 1,
                'result': {
                    'status': 'success',
                    'customerid': cuid,
                    'data': {}
                }
            }
            
            logger.info("var_list length: "+str(len(var_list)))#+" "+str(var_list))
            put_file_contents_as_json_containing_vars(json_data, file_list, var_list, True)
            
            try:
                if request.POST.get('user_profile') and (str(request.POST.get('user_profile'))=='True' or str(request.POST.get('user_profile'))=='true'):
                    logger.info('requesting User Profile...')
                    user_profile_data = dynamo.get_user_profile_json(cuid)
                    if len(user_profile_data) > 0:
                        logger.info('PROFILE RECIEVED')
                        json_data['result']['data']['UserProfile'] = [user_profile_data]
                    else:
                        logger.info('NOT FOUND')
            except Exception as e:
                logger.error("error: User Profile could not be received='"+str(e)+"'")
        except Exception as e:
            json_data = {
                'count': 0,
                'result': {
                    'status': 'failed'
                },
            }
            if len(str(e)) > 0:
                logger.error("error: "+str(e))
                json_data['error'] = str(e)
            else:
                logger.error("error: Customer Not Found-'"+str(e)+"'")
                json_data['error'] = 'Customer Not Found'
            
        return JSONResponse(json_data)

class RetrieveRefreshToken(views.APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        clear_screen()
        logger.info("fetching token...")
        
        cid = None
        csk = None
        
        try:
            cid = request.POST.get('client_id')
            logger.info("found 'clientID': "+cid)
            csk = request.POST.get('client_secret')
            logger.info("found 'clientSecret': "+csk)
        except Exception as e:
            logger.error("error: "+str(e))
            raise Http404
        else:
            if cid and csk:
                try:
                    refresh = RefreshToken.objects.get(application__client_id__exact = cid, application__client_secret__exact = csk)
                except Exception as e:
                    logger.error("error: "+str(e))
                    json_data = {
                        'detail': 'Authentication failed'
                    }
                else:
                    now = str(timezone.now())
                    token_expiration_date = str(AccessToken.objects.get(token__exact=str(refresh.access_token)).expires)
                    json_data = {
                        'detail': 'token',
                        'refresh_token': str(refresh.token),
                        'access_token': str(refresh.access_token),
                        'access_token_status': 'active' if token_expiration_date > now else 'expired'
                    }
                    
                return JSONResponse(json_data)
            else:
                logger.info("error: Information not provided")
                raise Http404
            