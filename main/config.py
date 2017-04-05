class config:
    class AWS:
        ACCESS_KEY_ID = 'AKIAI7HTLZ65W6NGIANQ'
        SECRET_ACCESS_KEY = '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'
        pass

    class S3:
        REGION = 'ap-south-1'
        #BUCKET = 'intermediate-files'
        BUCKET = 'algo360-community'
        pass

    class DYNAMODB:
        REGION = 'ap-south-1'
        class TABLES:
            CLIENT_CUST = 'Client_Customer'
            VERSIONS = 'COMMUNITY_runversion'
            pass
        pass
        
    pass