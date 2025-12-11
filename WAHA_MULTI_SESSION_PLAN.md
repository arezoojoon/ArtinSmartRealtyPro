# 🔧 Waha Multi-Session Setup for SaaS Platform

## 📋 مشکل فعلی:

```
❌ یک Waha container → یک session (default) → یک شماره واتساپ
```

این فقط برای **یک Tenant** کار می‌کنه!

---

## ✅ راه‌حل: Waha Multi-Session

```
✅ یک Waha container → N sessions → N شماره واتساپ (هر tenant جدا)

Tenant 1 → Session: "tenant_1" → WhatsApp: +971501234567
Tenant 2 → Session: "tenant_2" → WhatsApp: +971509876543  
Tenant 3 → Session: "tenant_3" → WhatsApp: +971505037158
...
Tenant N → Session: "tenant_N" → WhatsApp: +971...
```

---

## 🔨 تغییرات لازم:

### 1️⃣ اضافه کردن فیلد `waha_session_name` به Tenant

```sql
ALTER TABLE tenants ADD COLUMN waha_session_name VARCHAR(100) UNIQUE;
```

یا با Alembic migration:

```python
# backend/alembic/versions/add_waha_session.py
def upgrade():
    op.add_column('tenants', sa.Column('waha_session_name', sa.String(100), nullable=True))
    op.create_unique_constraint('uix_tenant_waha_session', 'tenants', ['waha_session_name'])
    
    # Auto-generate session names for existing tenants
    op.execute("""
        UPDATE tenants 
        SET waha_session_name = 'tenant_' || id::text 
        WHERE waha_session_name IS NULL
    """)
```

---

### 2️⃣ آپدیت `whatsapp_providers.py`

**قبل:**
```python
self.session = getattr(tenant, 'waha_session_name', 'default')
```

**بعد:**
```python
self.session = tenant.waha_session_name or f"tenant_{tenant.id}"
```

---

### 3️⃣ Dashboard API برای Connect WhatsApp

**Frontend Flow:**
```
1. Agent login → Dashboard
2. Settings → WhatsApp Integration
3. Click "Connect WhatsApp"
4. Backend creates Waha session: POST /api/{tenant_id}/whatsapp/connect
5. Returns QR code URL
6. Agent scans QR
7. Session status changes to WORKING
```

**Backend Endpoint:**

```python
@app.post("/api/tenants/{tenant_id}/whatsapp/connect")
async def connect_whatsapp(
    tenant_id: int,
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """
    Create Waha session for tenant and return QR code URL.
    Each tenant gets isolated WhatsApp session.
    """
    tenant = await verify_tenant_access(tenant_id, current_tenant, db)
    
    # Generate unique session name
    session_name = f"tenant_{tenant.id}"
    
    # API URL for Waha
    waha_api = os.getenv('WAHA_API_URL', 'http://waha:3000/api')
    api_key = os.getenv('WAHA_API_KEY', '')
    
    headers = {'X-Api-Key': api_key} if api_key else {}
    
    # Create/start session with webhook
    webhook_url = f"http://backend:8000/api/webhook/waha?tenant_id={tenant.id}"
    
    payload = {
        "name": session_name,
        "config": {
            "webhooks": [{
                "url": webhook_url,
                "events": ["message.any"]
            }]
        }
    }
    
    async with httpx.AsyncClient() as client:
        # Start session
        response = await client.post(
            f"{waha_api}/sessions/{session_name}/start",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            # Save session name to tenant
            tenant.waha_session_name = session_name
            await db.commit()
            
            # Return QR code URL
            qr_url = f"{waha_api}/sessions/{session_name}/auth/qr"
            if api_key:
                qr_url += f"?api_key={api_key}"
            
            return {
                "success": True,
                "qr_url": qr_url,
                "session": session_name,
                "message": "Scan QR code with your WhatsApp to connect"
            }
        else:
            raise HTTPException(500, f"Failed to create session: {response.text}")


@app.get("/api/tenants/{tenant_id}/whatsapp/status")
async def whatsapp_status(
    tenant_id: int,
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Check WhatsApp connection status for tenant."""
    tenant = await verify_tenant_access(tenant_id, current_tenant, db)
    
    if not tenant.waha_session_name:
        return {"connected": False, "message": "WhatsApp not configured"}
    
    waha_api = os.getenv('WAHA_API_URL', 'http://waha:3000/api')
    api_key = os.getenv('WAHA_API_KEY', '')
    headers = {'X-Api-Key': api_key} if api_key else {}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{waha_api}/sessions/{tenant.waha_session_name}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status')
            
            if status == 'WORKING':
                phone = data.get('me', {}).get('id', '').replace('@c.us', '')
                return {
                    "connected": True,
                    "status": status,
                    "phone": phone,
                    "session": tenant.waha_session_name
                }
            else:
                return {
                    "connected": False,
                    "status": status,
                    "message": "Scan QR code to connect"
                }
        else:
            return {"connected": False, "message": "Session not found"}


@app.post("/api/tenants/{tenant_id}/whatsapp/disconnect")
async def disconnect_whatsapp(
    tenant_id: int,
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Disconnect WhatsApp for tenant."""
    tenant = await verify_tenant_access(tenant_id, current_tenant, db)
    
    if not tenant.waha_session_name:
        return {"success": True, "message": "Already disconnected"}
    
    waha_api = os.getenv('WAHA_API_URL', 'http://waha:3000/api')
    api_key = os.getenv('WAHA_API_KEY', '')
    headers = {'X-Api-Key': api_key} if api_key else {}
    
    async with httpx.AsyncClient() as client:
        # Stop session
        await client.post(
            f"{waha_api}/sessions/{tenant.waha_session_name}/stop",
            headers=headers,
            timeout=10
        )
        
        # Clear from tenant
        tenant.waha_session_name = None
        await db.commit()
        
        return {"success": True, "message": "WhatsApp disconnected"}
```

---

### 4️⃣ آپدیت Webhook Handler

**قبل:**
```python
@app.post("/api/webhook/waha")
async def waha_webhook(payload: dict):
    # همه tenantها به یک webhook میان!
```

**بعد:**
```python
@app.post("/api/webhook/waha")
async def waha_webhook(
    payload: dict, 
    tenant_id: Optional[int] = None,  # از query parameter
    background_tasks: BackgroundTasks
):
    """
    Waha webhook - routes to correct tenant based on:
    1. tenant_id query param (preferred)
    2. session name in payload
    3. phone number lookup
    """
    
    # Method 1: Direct tenant_id from webhook URL
    if tenant_id:
        logger.info(f"📩 Waha webhook for tenant {tenant_id}")
    else:
        # Method 2: Extract from session name
        session = payload.get('session', 'default')
        if session.startswith('tenant_'):
            tenant_id = int(session.replace('tenant_', ''))
            logger.info(f"📩 Waha webhook - extracted tenant {tenant_id} from session")
        else:
            # Method 3: Lookup by phone number
            phone = payload.get('payload', {}).get('from', '').replace('@c.us', '')
            async with async_session() as db:
                result = await db.execute(
                    select(Tenant).join(Lead).where(Lead.whatsapp_phone == phone)
                )
                tenant = result.scalar_one_or_none()
                if tenant:
                    tenant_id = tenant.id
                    logger.info(f"📩 Waha webhook - found tenant {tenant_id} by phone lookup")
    
    if not tenant_id:
        logger.error("❌ Cannot determine tenant for Waha webhook")
        return {"status": "error", "message": "Tenant not found"}
    
    # Process webhook for specific tenant
    async def process_webhook():
        try:
            async with async_session() as db:
                result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
                tenant = result.scalar_one_or_none()
                
                if not tenant:
                    logger.error(f"Tenant {tenant_id} not found")
                    return
                
                # Get WhatsApp handler for this tenant
                handler = WhatsAppBotHandler(tenant)
                await handler.handle_webhook(payload)
                
        except Exception as e:
            logger.error(f"❌ Webhook processing error for tenant {tenant_id}: {e}")
    
    background_tasks.add_task(process_webhook)
    return {"status": "received", "tenant_id": tenant_id}
```

---

### 5️⃣ Frontend Component: WhatsApp Settings

```jsx
// frontend/src/components/WhatsAppSettings.jsx
import { useState, useEffect } from 'react';
import { Button, Card, Text, Image, Badge } from '@mantine/core';
import axios from 'axios';

export function WhatsAppSettings({ tenantId }) {
  const [status, setStatus] = useState(null);
  const [qrUrl, setQrUrl] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    const res = await axios.get(`/api/tenants/${tenantId}/whatsapp/status`);
    setStatus(res.data);
  };

  const connect = async () => {
    setLoading(true);
    const res = await axios.post(`/api/tenants/${tenantId}/whatsapp/connect`);
    setQrUrl(res.data.qr_url);
    setLoading(false);
    
    // Poll status every 3 seconds
    const interval = setInterval(async () => {
      const statusRes = await axios.get(`/api/tenants/${tenantId}/whatsapp/status`);
      if (statusRes.data.connected) {
        setStatus(statusRes.data);
        setQrUrl(null);
        clearInterval(interval);
      }
    }, 3000);
  };

  const disconnect = async () => {
    await axios.post(`/api/tenants/${tenantId}/whatsapp/disconnect`);
    setStatus({ connected: false });
    setQrUrl(null);
  };

  return (
    <Card shadow="sm" padding="lg">
      <Text size="xl" weight={700}>WhatsApp Integration</Text>
      
      {status?.connected ? (
        <>
          <Badge color="green">Connected</Badge>
          <Text>Phone: {status.phone}</Text>
          <Button color="red" onClick={disconnect}>Disconnect</Button>
        </>
      ) : qrUrl ? (
        <>
          <Text>Scan this QR code with WhatsApp:</Text>
          <Image src={qrUrl} alt="QR Code" width={300} />
        </>
      ) : (
        <Button onClick={connect} loading={loading}>Connect WhatsApp</Button>
      )}
    </Card>
  );
}
```

---

## 📊 خلاصه تغییرات:

| # | فایل | تغییر |
|---|------|-------|
| 1 | `database.py` | ➕ `waha_session_name` به Tenant model |
| 2 | Migration | ➕ Alembic migration برای add column |
| 3 | `main.py` | ➕ 3 endpoint: `/connect`, `/status`, `/disconnect` |
| 4 | `main.py` | 🔄 Webhook handler با tenant isolation |
| 5 | `whatsapp_providers.py` | 🔄 Use `tenant.waha_session_name` |
| 6 | Frontend | ➕ WhatsApp Settings component |

---

## 🎯 نتیجه نهایی:

```
Agent A Login → Connect WhatsApp → Scan QR → Session "tenant_5" created
Agent B Login → Connect WhatsApp → Scan QR → Session "tenant_12" created
Agent C Login → Connect WhatsApp → Scan QR → Session "tenant_3" created

همه روی یک Waha container ولی کاملاً جدا از هم! 🎉
```

---

**آماده‌ای که این تغییرات رو پیاده کنم؟** 🚀
