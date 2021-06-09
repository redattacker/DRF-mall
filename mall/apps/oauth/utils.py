
'''

QQ_APP_ID = '101474184'
QQ_APP_KEY = 'c6ce949e04e12ecc909ae6a8b09b637c'
QQ_REDIRECT_URL = 'http://www.meiduo.site:8080/oauth_callback.html'
QQ_STATE = '/'

'''
import json

from django.conf import settings
from urllib.parse import urlencode,parse_qs

import requests
class OAuthQQ(object):
    """
    QQ认证辅助工具类
    """

    def __init__(self,app_id=None,app_key=None,redirect_uri=None,state=None):
        self.app_id=app_id or settings.QQ_APP_ID
        self.app_key=app_key or settings.QQ_APP_KEY
        self.redirect_uri=redirect_uri or settings.QQ_REDIRECT_URL
        self.state=state or settings.QQ_STATE

    # 构造QQ登录页面的url  Step1：获取Authorization Code
    def get_url(self):

        params={
            'response_type':'code',
            'client_id':self.app_id,
            'redirect_uri':self.redirect_uri,
            'state':self.state
        }

        url='https://graph.qq.com/oauth2.0/authorize?'+urlencode(params)

        return url

    #Step2：通过Authorization Code获取Access Token

    def get_access_token(self,code):

        params = {
            'grant_type':'authorization_code',
            'client_id': self.app_id,
            'client_secret':self.app_key,
            'redirect_uri': self.redirect_uri,
            'code': code
        }

        url='https://graph.qq.com/oauth2.0/token?'+urlencode(params)

        # 后端发送请求
        try:
            response=requests.get(url)
            # 返回数据形式 access_token=FE04************************CCE2&expires_in=7776000&refresh_token=88E4************************BE14
            data=response.text
            data_dict=parse_qs(data)
        except:
            raise Exception('QQ请求失败')

        access_token=data_dict.get('access_token',None)
        if not access_token:
            raise Exception('access_token获取失败')

        return access_token[0]

    #Step3：通过Access Token获取Openid

    def get_openid(self,access_token):

        url = 'https://graph.qq.com/oauth2.0/me?access_token='+access_token
        # 后端发送请求
        try:
            response = requests.get(url)
            # 返回数据形式 callback( {"client_id":"YOUR_APPID","openid":"YOUR_OPENID"} );
            data = response.text
            data_dict=json.loads(data[10:-3])
        except:
            raise Exception('QQ请求失败')
        # 提取openid
        openid=data_dict.get('openid',None)
        if not openid:
            raise Exception('aopenid获取失败')

        return openid

