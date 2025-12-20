#!/usr/bin/env python3
"""بررسی لاگ های مکالمه اخیر با یوزر"""

import paramiko

HOST = 'srv1203549.hstgr.cloud'
USER = 'root'
PASSWORD = 'u0;74KWyoEydh5g.Q9)s'
PROJECT_PATH = '/opt/ArtinSmartRealty'

print('🔍 بررسی لاگ های مکالمه اخیر...\n')
print('=' * 80)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=10)

# لاگ های 200 خط اخیر
print('📋 لاگ های کامل مکالمه (200 خط آخر):')
print('=' * 80)
stdin, stdout, stderr = ssh.exec_command(
    f'cd {PROJECT_PATH} && docker-compose logs --tail=200 backend | grep -E "(Lead|brain|telegram_bot|ERROR|WARNING|بودجه|Voice|voice|callback)"'
)
logs = stdout.read().decode('utf-8', errors='replace')
print(logs)

print('\n' + '=' * 80)
print('🎤 لاگ های مربوط به ویس:')
print('=' * 80)
stdin, stdout, stderr = ssh.exec_command(
    f'cd {PROJECT_PATH} && docker-compose logs --tail=300 backend | grep -i "voice"'
)
voice_logs = stdout.read().decode('utf-8', errors='replace')
if voice_logs.strip():
    print(voice_logs)
else:
    print('❌ هیچ لاگ ویسی پیدا نشد!')

print('\n' + '=' * 80)
print('💰 لاگ های مربوط به بودجه:')
print('=' * 80)
stdin, stdout, stderr = ssh.exec_command(
    f'cd {PROJECT_PATH} && docker-compose logs --tail=300 backend | grep -E "(budget|بودجه|buy_budget)"'
)
budget_logs = stdout.read().decode('utf-8', errors='replace')
if budget_logs.strip():
    print(budget_logs)
else:
    print('⚠️ هیچ لاگ بودجه ای پیدا نشد!')

print('\n' + '=' * 80)
print('🔘 لاگ های callback button:')
print('=' * 80)
stdin, stdout, stderr = ssh.exec_command(
    f'cd {PROJECT_PATH} && docker-compose logs --tail=300 backend | grep -E "callback_data|Callback"'
)
callback_logs = stdout.read().decode('utf-8', errors='replace')
if callback_logs.strip():
    print(callback_logs[-3000:])  # آخرین 3000 کاراکتر
else:
    print('⚠️ هیچ callback لاگی پیدا نشد!')

print('\n' + '=' * 80)
print('❌ ارورها:')
print('=' * 80)
stdin, stdout, stderr = ssh.exec_command(
    f'cd {PROJECT_PATH} && docker-compose logs --tail=300 backend | grep -E "(ERROR|Exception|Traceback)"'
)
errors = stdout.read().decode('utf-8', errors='replace')
if errors.strip():
    print(errors[-2000:])  # آخرین 2000 کاراکتر
else:
    print('✅ هیچ ارور جدیدی نیست')

ssh.close()

print('\n' + '=' * 80)
print('🐛 مشکلات شناسایی شده از مکالمه:')
print('=' * 80)
print('1. دکمه بودجه کار نمیکنه - بعد از کلیک سکوت میکنه')
print('2. ویس message ها رو نمیفهمه (15 ثانیه و 5 ثانیه سکوت)')
print('3. پیام "الان تقاضا خیلی زیاده" نامناسب')
print('4. وقتی user میگه "اجاره" بات نمیفهمه منظورش rent است نه buy')
print('5. بعد از گرفتن بودجه باید property ها رو نشان بده نه سوال بپرسه')
print('6. دکمه ها کار نمیکنند و user مجبور به تایپ است')
