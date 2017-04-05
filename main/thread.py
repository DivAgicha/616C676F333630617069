import threading, time
from django.core.mail import send_mail
from main import log
        
logger = log.getTimedLogger()
ThreadDetails = lambda type,accessedDetails=None: getThreadDetails(type, accessedDetails)
    
def getThreadDetails(type, accessedDetails):
    if type=='ftp':
        return {'name': 'FTP', 'target': ThreadBuilderUtility.ftpConnect, 'setDaemon': True, 'args': ['replace_with_host', 'replace_with_port', 'replace_with_user', 'replace_with_password']}
    elif type=='email':
        return {'name': 'Email', 'target': ThreadBuilderUtility.emailDetails, 'setDaemon': True, 'args': ['replace_with_TO', 'replace_with_type']}
    elif type=='accessed':
        return {'name': 'ForwardClientDetails', 'target': ThreadBuilderUtility.forwardDetails, 'setDaemon': True, 'args': [accessedDetails]}
    else:
        return {'name': 'Error', 'target': ThreadBuilderUtility.noInfoProvided, 'setDaemon': False, 'args': ['No Action Specified']}

class ThreadBuilderUtility(threading.Thread):

    daemon_type = False

    def __init__(self, name=None, target=None, setDaemon=False, args=None):
        #**kwargs   and     logger.info('name: '+kwargs['name']+'\ntarget: '+kwargs['target']+'\nargs: '+str(kwargs['args']))
        
        temp = [self]
        if args:
            for val in args:
                temp.append(val)
        
        threading.Thread.__init__(self, name=name, target=target, args=tuple(temp))
        logger.info('Thread Created')
                
        #self.args = tuple(temp)
        #logger.info("args: "+str(temp))
        
        self.daemon_type = setDaemon or False
        
        return
        
    @property
    def setDaemonType(self):
        #logger.info('setting daemon type as: '+str(self.daemon_type))
        if self.daemon_type:
            self.setDaemon(self.daemon_type)
    
    def run(self):
        #logger.info('inside run()...')
        self._target(*self._args, **self._kwargs)
        
    def ftpConnect(self, host, port, user, password):
        logger.info('FTP')
        
    def emailDetails(self, to, type):
        logger.info('Email')
        
    def forwardDetails(self, details):
        try:
            logger.info("sending mail...")
            send_mail(details['subj'], details['msg'], details['from'], details['to'], fail_silently=False)
            logger.info("DONE")
        except Exception as e:
            logger.error("FAILED-("+str(e)+")")
        
    def noInfoProvided(self, msg='ERROR MESSAGE'):
        logger.info(msg)
        for i in range(1,4):
            logger.info(i)
            time.sleep(1)