#!/usr/bin/env python3
"""
Check what code is actually running inside the container
"""
import paramiko

SERVER = "72.62.93.116"
USERNAME = "root"
PASSWORD = "u0;74KWyoEydh5g.Q9)s"

print("🐳 Checking code inside RUNNING container...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD)
    
    # Check the ACTUAL brain.py being used
    print("1️⃣ Checking lines 2785-2840 in container's brain.py:")
    stdin, stdout, stderr = ssh.exec_command(
        "docker exec artinrealty-backend sed -n '2785,2840p' /app/brain.py"
    )
    
    code = stdout.read().decode()
    print(code)
    
    if "CRITICAL FIX" in code:
        print("\n✅ NEW CODE is in the file!")
    else:
        print("\n❌ OLD CODE is in the file!")
    
    # Check if Python actually loaded it
    print("\n2️⃣ Checking Python's loaded module:")
    stdin, stdout, stderr = ssh.exec_command(
        """docker exec artinrealty-backend python3 -c "
import sys
sys.path.insert(0, '/app')
with open('/app/brain.py', 'r') as f:
    content = f.read()
    if 'CRITICAL FIX' in content:
        print('✅ File contains fix')
        # Find the line
        for i, line in enumerate(content.split('\\n'), 1):
            if 'CRITICAL FIX' in line:
                print(f'   Found at line {i}')
                break
    else:
        print('❌ File does NOT contain fix')
"
"""
    )
    
    result = stdout.read().decode()
    print(result)
    
    # Check __pycache__
    print("\n3️⃣ Checking for cached .pyc files:")
    stdin, stdout, stderr = ssh.exec_command(
        "docker exec artinrealty-backend find /app -name 'brain*.pyc' -exec ls -lh {} \\;"
    )
    
    pyc = stdout.read().decode()
    if pyc:
        print(pyc)
        print("\n⚠️ Found cached bytecode! This might be the problem.")
    else:
        print("No .pyc files found")
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
