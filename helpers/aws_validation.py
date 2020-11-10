# -*- coding: utf-8 -*-

# http://docs.aws.amazon.com/general/latest/gr/signature-v4-examples.html#signature-v4-examples-python

import datetime, hashlib, hmac
from urllib.request import Request, urlopen
from urllib.error import HTTPError

class AwsValidation:
    METHOD = 'POST'
    SERVICE = 'sts'
    REGION = 'us-east-1'
    HOST = 'sts.amazonaws.com'
    ENDPOINT = 'https://sts.amazonaws.com'
    REQUEST_PARAMETERS = 'Action=GetCallerIdentity&Version=2011-06-15'
    CANONICAL_URI = '/'
    SIGNED_HEADERS = 'host;x-amz-date'
    PAYLOAD_HASH = hashlib.sha256(('').encode('utf-8')).hexdigest()
    ALGORITHM = 'AWS4-HMAC-SHA256'

    def __init__(self, aws_access_key_id, aws_secret_access_key):
        self.access_key = aws_access_key_id
        self.secret_key = aws_secret_access_key

    @staticmethod
    def __sign(key, msg):
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

    @classmethod
    def __get_signature_key(cls, key, date_stamp, region_name, service_name):
        k_date = cls.__sign(('AWS4' + key).encode('utf-8'), date_stamp)
        k_region = cls.__sign(k_date, region_name)
        k_service = cls.__sign(k_region, service_name)
        return cls.__sign(k_service, 'aws4_request')

    def __get_request_url_and_headers(self):
        t = datetime.datetime.utcnow()
        amzdate = t.strftime('%Y%m%dT%H%M%SZ')
        datestamp = t.strftime('%Y%m%d')

        canonical_querystring = self.REQUEST_PARAMETERS

        canonical_headers = '\n'.join(
            [f'host:{self.HOST}', f'x-amz-date:{amzdate}', '']
        )

        canonical_request = '\n'.join(
            [
                self.METHOD,
                self.CANONICAL_URI,
                canonical_querystring,
                canonical_headers,
                self.SIGNED_HEADERS,
                self.PAYLOAD_HASH,
            ]
        )

        credential_scope = '/'.join(
            [datestamp, self.REGION, self.SERVICE, 'aws4_request']
        )

        string_to_sign = '\n'.join(
            [
                self.ALGORITHM,
                amzdate,
                credential_scope,
                hashlib.sha256(canonical_request.encode('utf-8')).hexdigest(),
            ]
        )

        signing_key = self.__get_signature_key(
            self.secret_key, datestamp, self.REGION, self.SERVICE
        )

        signature = hmac.new(
            signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256
        ).hexdigest()

        authorization_header = (
            '{} Credential={}/{}, SignedHeaders={}, Signature={}'.format(
                self.ALGORITHM,
                self.access_key,
                credential_scope,
                self.SIGNED_HEADERS,
                signature,
            )
        )

        headers = {'x-amz-date': amzdate, 'Authorization': authorization_header}
        request_url = '?'.join([self.ENDPOINT, canonical_querystring])

        return request_url, headers

    def validate_credentials(self):
        request_url, headers = self.__get_request_url_and_headers()
        req = Request(request_url, headers=headers, method='POST')

        try:
            with urlopen(req) as res:
                if res.status == 200:
                    return True
                else:
                    return False
        except HTTPError as e:
            return False


