from django.conf import settings
from django.core.mail import send_mail

from celery_tasks.main import app


@app.task(name='send_email')
def send_emailc_code(email,verify_url):
    msg='<p>尊敬的用户您好！</p>' \
                   '<p>感谢您使用美多商城。</p>' \
                   '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                   '<p><a href="%s">%s<a></p>' % (email, verify_url, verify_url)
    send_mail('美多商城验证','',settings.EMAIL_FROM,[email],html_message=msg)