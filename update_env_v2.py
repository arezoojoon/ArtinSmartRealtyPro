#!/usr/bin/env python3
import paramiko

SERVER = "72.62.93.116"
USERNAME = "root"
PASSWORD = "u0;74KWyoEydh5g.Q9)s"

print("🔧 Updating .env file...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USERNAME, password=PASSWORD)
    
    # Read current .env
    stdin, stdout, stderr = ssh.exec_command("cat /opt/ArtinSmartRealty/.env")
    current_env = stdout.read().decode()
    
    # Remove old GEMINI_API_KEY lines
    lines = current_env.split('\n')
    new_lines = [line for line in lines if not line.startswith('GEMINI_API_KEY=') and not line.startswith('GEMINI_KEY_')]
    
    # Add new keys at the end of AI section
    ai_section_index = -1
    for i, line in enumerate(new_lines):
        if '# AI / GEMINI' in line:
            ai_section_index = i
            break
    
    if ai_section_index >= 0:
        # Insert after the AI comment
        new_lines.insert(ai_section_index + 1, 'GEMINI_KEY_1=AIzaSyD7H0oXK80-FE-wgBXyK-GxssrwwtgQtn0')
        new_lines.insert(ai_section_index + 2, 'GEMINI_KEY_2=AIzaSyDDJwP4_QNmUYz-AnxMtpQFPwD1alsb2AE')
        new_lines.insert(ai_section_index + 3, 'GEMINI_KEY_3=AIzaSyA6PYKu78XDthMXQL-3kK3c-GIna4mtcWs')
        new_lines.insert(ai_section_index + 4, 'GEMINI_API_KEY=AIzaSyD7H0oXK80-FE-wgBXyK-GxssrwwtgQtn0')
    else:
        # Append at end
        new_lines.extend([
            '',
            '# AI / GEMINI',
            'GEMINI_KEY_1=AIzaSyD7H0oXK80-FE-wgBXyK-GxssrwwtgQtn0',
            'GEMINI_KEY_2=AIzaSyDDJwP4_QNmUYz-AnxMtpQFPwD1alsb2AE',
            'GEMINI_KEY_3=AIzaSyA6PYKu78XDthMXQL-3kK3c-GIna4mtcWs',
            'GEMINI_API_KEY=AIzaSyD7H0oXK80-FE-wgBXyK-GxssrwwtgQtn0'
        ])
    
    new_env = '\n'.join(new_lines)
    
    # Write back
    # Escape special characters for bash
    escaped_env = new_env.replace("'", "'\\''")
    stdin, stdout, stderr = ssh.exec_command(f"echo '{escaped_env}' > /opt/ArtinSmartRealty/.env")
    stdout.read()
    
    print("✅ .env file updated!")
    
    # Verify
    stdin, stdout, stderr = ssh.exec_command("grep GEMINI /opt/ArtinSmartRealty/.env")
    print("\n📋 Gemini keys in .env:")
    print(stdout.read().decode())
    
    ssh.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
