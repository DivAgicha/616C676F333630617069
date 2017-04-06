import boto3, botocore
from main.config import config
from main import log

logger = log.getTimedLogger()

class boto_for_s3:
    s3_resource = None
    
    def __init__(self):
        self.s3_resource = None
    
    @property
    def initialise_resource(self):
        try:
            self.s3_resource = boto3.resource('s3', region_name=config.S3.REGION, aws_access_key_id=config.AWS.ACCESS_KEY_ID, aws_secret_access_key=config.AWS.SECRET_ACCESS_KEY)
        except Exception as e:
            logger.error("Error creating s3 resource: "+str(e))
            self.s3_resource = None
            pass

    def get_bucket(self):
        if self.s3_resource:
            return self.s3_resource.Bucket(config.S3.BUCKET)
        else:
            raise Exception("Bucket can't be accessed before initialising s3 resource")
            
    def get_file_list_from_bucket(self, bucket, client_id, tags, fileName, dirList = None):
        if bucket:
            file_list = []
            splitted_clientID = client_id.split('/', 1)
            
            if dirList and len(dirList)>0:
                for dir in dirList:
                    try:
                        for obj in bucket.objects.filter(Prefix=splitted_clientID[0]+"/"+dir+"/"+splitted_clientID[1]+"/"+fileName):
                            file_list.append(obj)
                            break
                    except Exception as e:
                        logger.error("s3 file not found in directory: "+str(e))
                        pass
            else:
                all = False
                prefix_dir = ""
                if tags.endswith("/u") or tags.endswith("/u/"):
                    prefix_dir += "/User/"
                elif tags.endswith("/e") or tags.endswith("/e/"):
                    prefix_dir += "/Entity/"
                else:
                    all = True
                    
                if not all:
                    for obj in bucket.objects.filter(Prefix=splitted_clientID[0]+prefix_dir+splitted_clientID[1]+"/"+fileName):
                        file_list.append(obj)
                        break
                else:
                    for obj in bucket.objects.filter(Prefix=splitted_clientID[0]+"/User/"+splitted_clientID[1]+"/"+fileName):
                        file_list.append(obj)
                        break
                    for obj in bucket.objects.filter(Prefix=splitted_clientID[0]+"/Entity/"+splitted_clientID[1]+"/"+fileName):
                        file_list.append(obj)
                        break
                        
                for obj in bucket.objects.filter(Prefix=splitted_clientID[0]+"/DbLevelData/"+splitted_clientID[1]+"/"+fileName):
                    file_list.append(obj)
                    break
                
            return file_list
        else:
            raise Exception("Bucket can't be empty")
            
    def delete_duplicates_from_bucket(self, bucket, client_id):
        if bucket:
            original_keys = []
            duplicate_keys = []
            count = 1
            try:
                for obj in bucket.object_versions.filter(Prefix=client_id+"/"):
                    if obj.key in original_keys:
                        duplicate_keys.append(obj.key)
                    else:
                        original_keys.append(obj.key)
                    """
                    delete = False
                    for duplicate in bucket.objects.filter(Prefix=obj.key):
                        if not delete:
                            delete = True
                        else:
                            #delete all duplicate files
                            delete_file = {'Key': duplicate.key}
                            duplicate_keys.append(delete_file)
                    """        
                    logger.info(str(count)+". success")
                    count += 1
            except Exception as e:
                logger.error("s3 file operation error: "+str(e))
                pass
            else:
                logger.info("no. of original keys: "+str(len(original_keys)))
                logger.info("no. of duplicate keys: "+str(len(duplicate_keys)))
                if len(duplicate_keys) > 0:
                    #response = bucket.delete_objects(Delete={'Objects': duplicate_keys})
                    pass
        else:
            raise Exception("Bucket can't be empty")

class boto_for_dynamodb:
    dynamodb_client = None
    
    def __init__(self):
        self.dynamodb_client = None
    
    @property
    def initialise_client(self):
        try:
            self.dynamodb_client = boto3.client('dynamodb', region_name=config.DYNAMODB.REGION, aws_access_key_id=config.AWS.ACCESS_KEY_ID, aws_secret_access_key=config.AWS.SECRET_ACCESS_KEY)
        except Exception as e:
            logger.error("Error creating DynamoDB client: "+str(e))
            self.dynamodb_client = None
            pass
            
    def retrieve_alternative(self, cuid, ref_code):
        if self.dynamodb_client:
            if ref_code=='MYHBT':
                return self.dynamodb_client.scan(
                    TableName = config.DYNAMODB.TABLES.CLIENT_CUST,
                    ExpressionAttributeValues = {
                        ':cuid' : {
                            'S' : cuid
                        },
                    },
                    FilterExpression = '(CUID = :cuid OR referrer_user_id = :cuid) AND attribute_exists(created_at)',
                    ConsistentRead = True
                )
            else:
                return self.dynamodb_client.scan(
                    TableName = config.DYNAMODB.TABLES.CLIENT_CUST,
                    ExpressionAttributeValues = {
                        ':cuid' : {
                            'S' : cuid
                        },
                        ':ref_code' : {
                            'S' : ref_code
                        },
                    },
                    FilterExpression = '(CUID = :cuid OR referrer_user_id = :cuid) AND ref_code = :ref_code AND attribute_exists(created_at)',
                    ConsistentRead = True
                )
        else:
            raise Exception("Database can't be accessed before initialising DynamoDB client")
            
    def scan_db_for_customer(self, cuid, fromDate = None, toDate = None):
        if self.dynamodb_client:
            if fromDate and toDate:
                return self.dynamodb_client.scan(
                    TableName = config.DYNAMODB.TABLES.VERSIONS,
                    #Limit = 1,
                    ScanFilter = {
                        'CustomerID' : {
                            'AttributeValueList' : [
                                {
                                    'S' : cuid
                                }
                            ],
                            'ComparisonOperator' : 'EQ'
                        },
                        'TimeStamp' : {
                            'AttributeValueList' : [
                                {
                                    'N' : fromDate
                                },
                                {
                                    'N' : toDate
                                }
                            ],
                            'ComparisonOperator' : 'BETWEEN'
                        },
                        'Version' : {
                            'AttributeValueList' : [
                                {
                                    'N' : '0'
                                }
                            ],
                            'ComparisonOperator' : 'GE'
                        },
                        'EndTime' : {
                            'ComparisonOperator' : 'NOT_NULL'
                        }
                    },
                    ConsistentRead = True
                )
            else:
                return self.dynamodb_client.scan(
                    TableName = config.DYNAMODB.TABLES.VERSIONS,
                    #Limit = 1,
                    ScanFilter = {
                        'CustomerID' : {
                            'AttributeValueList' : [
                                {
                                    'S' : cuid
                                }
                            ],
                            'ComparisonOperator' : 'EQ'
                        },
                        'Version' : {
                            'AttributeValueList' : [
                                {
                                    'N' : '0'
                                }
                            ],
                            'ComparisonOperator' : 'GE'
                        },
                        'EndTime' : {
                            'ComparisonOperator' : 'NOT_NULL'
                        }
                    },
                    ConsistentRead = True
                )
        else:
            raise Exception("Database can't be accessed before initialising DynamoDB client")
            
    def scan_db_for_distinct_customers(self, ref_code, fromDate = None, toDate = None):
        if self.dynamodb_client:
            if ref_code=='MYHBT':
                return self.dynamodb_client.scan(
                    TableName = config.DYNAMODB.TABLES.CLIENT_CUST,
                    ScanFilter = {
                        'CUID' : {
                            'ComparisonOperator' : 'NOT_NULL'
                        },
                        'created_at' : {
                            'ComparisonOperator' : 'NOT_NULL'
                        },
                        'isProcessed' : {
                            'AttributeValueList' : [
                                {
                                    'N' : '1'
                                }
                            ],
                            'ComparisonOperator' : 'EQ'
                        }
                    },
                    ConsistentRead = True
                )
            elif fromDate and toDate:
                return self.dynamodb_client.scan(
                    TableName = config.DYNAMODB.TABLES.CLIENT_CUST,
                    ScanFilter = {
                        'CUID' : {
                            'ComparisonOperator' : 'NOT_NULL'
                        },
                        'created_at' : {
                            'AttributeValueList' : [
                                {
                                    'N' : fromDate
                                },
                                {
                                    'N' : toDate
                                }
                            ],
                            'ComparisonOperator' : 'BETWEEN'
                        },
                        'ref_code' : {
                            'AttributeValueList' : [
                                {
                                    'S' : ref_code
                                }
                            ],
                            'ComparisonOperator' : 'EQ'
                        },
                        'isProcessed' : {
                            'AttributeValueList' : [
                                {
                                    'N' : '1'
                                }
                            ],
                            'ComparisonOperator' : 'EQ'
                        }
                    },
                    ConsistentRead = True
                )
            else:
                return self.dynamodb_client.scan(
                    TableName = config.DYNAMODB.TABLES.CLIENT_CUST,
                    ScanFilter = {
                        'CUID' : {
                            'ComparisonOperator' : 'NOT_NULL'
                        },
                        'created_at' : {
                            'ComparisonOperator' : 'NOT_NULL'
                        },
                        'ref_code' : {
                            'AttributeValueList' : [
                                {
                                    'S' : ref_code
                                }
                            ],
                            'ComparisonOperator' : 'EQ'
                        },
                        'isProcessed' : {
                            'AttributeValueList' : [
                                {
                                    'N' : '1'
                                }
                            ],
                            'ComparisonOperator' : 'EQ'
                        }
                    },
                    ConsistentRead = True
                )
        else:
            raise Exception("Database can't be accessed before initialising DynamoDB client")
            
    def get_user_profile_json(self, cuid):
        if self.dynamodb_client:
            user_profile = self.dynamodb_client.scan(
                TableName = config.DYNAMODB.TABLES.PROFILE,
                ScanFilter = {
                    'CUID' : {
                        'AttributeValueList' : [
                            {
                                'S' : cuid
                            }
                        ],
                        'ComparisonOperator' : 'EQ'
                    },
                    'UUID' : {
                        'ComparisonOperator' : 'NOT_NULL'
                    }
                },
                ConsistentRead = True
            )
            
            user_details = {}
            if user_profile['Count'] > 0:
                for k, v in user_profile['Items'][0].items():
                    if not k.endswith('UID'):
                        user_details[k] = v['S']
                
            return user_details
        else:
            raise Exception("Database can't be accessed before initialising DynamoDB client")
            
            