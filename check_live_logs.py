#!/usr/bin/env python3
"""بررسی لاگ های زنده سرور پروداکشن"""

import paramiko

HOST = 'srv1203549.hstgr.cloud'
USER = 'root'
PASSWORD = 'u0;74KWyoEydh5g.Q9)s'
PROJECT_PATH = '/opt/ArtinSmartRealty'

print('📡 اتصال به سرور...\n')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=10)
print('✅ متصل شد\n')

print('=' * 70)
print('🔍 لاگ های استارت آپ:')
print('=' * 70)
stdin, stdout, stderr = ssh.exec_command(f'cd {PROJECT_PATH} && docker-compose logs --tail=30 backend')
logs = stdout.read().decode('utf-8', errors='replace')
print(logs)

print('\n' + '=' * 70)
print('✅ تایید فیکس در کد:')
print('=' * 70)
stdin, stdout, stderr = ssh.exec_command(f'grep -c "goal_buttons" {PROJECT_PATH}/backend/brain.py')
count = stdout.read().decode('utf-8', errors='replace').strip()
print(f'تعداد goal_buttons در کد: {count} بار')

stdin, stdout, stderr = ssh.exec_command(f'grep -n "Show buttons as backup" {PROJECT_PATH}/backend/brain.py')
fix_line = stdout.read().decode('utf-8', errors='replace')
if fix_line:
    print(f'\n✅ کامنت فیکس پیدا شد در خط:')
    print(fix_line)

print('\n' + '=' * 70)
print('📊 وضعیت کانتینر:')
print('=' * 70)
stdin, stdout, stderr = ssh.exec_command(f'cd {PROJECT_PATH} && docker-compose ps backend')
status = stdout.read().decode('utf-8', errors='replace')
print(status)

print('\n' + '=' * 70)
print('🔍 آخرین ارور ها (اگر هست):')
print('=' * 70)
stdin, stdout, stderr = ssh.exec_command(f'cd {PROJECT_PATH} && docker-compose logs --tail=100 backend | grep -i error')
errors = stdout.read().decode('utf-8', errors='replace').strip()
if errors:
    print(errors)
else:
    print('✅ هیچ ارور جدیدی نیست!')

print('\n' + '=' * 70)
print('⏰ تایم استمپ فایل:')
print('=' * 70)
stdin, stdout, stderr = ssh.exec_command(f'ls -lh {PROJECT_PATH}/backend/brain.py')
timestamp = stdout.read().decode('utf-8', errors='replace')
print(timestamp)

ssh.close()

print('\n' + '=' * 70)
print('🧪 حالا توی بات تست کن:')
print('=' * 70)
print('1. @TaranteenrealstateBot')
print('2. /start')
print('3. سلام من ارزو هستم، شماره‌م 09177105840')
print('4. باید 3 دکمه ببینی: 🏡 خرید | 💰 سرمایه‌گذاری | 🛂 اقامت')
