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
            PROFILE = 'customer_profile'
            FORM_DATA = 'cust_form_data'
            pass
        pass
        
        class TABLES_TEST:
            CLIENT_CUST = 'test_Client_Customer'
            VERSIONS = 'test_runversion'
            PROFILE = 'test_customer_profile'
            FORM_DATA = 'test_cust_form_data'
            pass
        pass
        
    pass