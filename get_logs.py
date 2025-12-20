import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('srv1203549.hstgr.cloud', username='root', password='u0;74KWyoEydh5g.Q9)s', timeout=20)

print("=" * 80)
print("LOGS - Last 150 lines:")
print("=" * 80)
stdin, stdout, stderr = ssh.exec_command('cd /opt/ArtinSmartRealty && docker-compose logs --tail=150 backend')
logs = stdout.read().decode('utf-8', errors='replace')
print(logs)

ssh.close()
