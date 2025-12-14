# 🛡️ Service Level Agreement (SLA) & Maintenance Specifications
## ArtinSmartRealty Platform - Enterprise Contract Terms

**Document Version:** 2.0  
**Effective Date:** November 28, 2025  
**Review Cycle:** Quarterly  
**Target Audience:** Enterprise Clients, Legal Teams, Procurement Departments

---

## 1. Service Level Commitments

### 1.1 Uptime Guarantee

**Service Availability:** 99.9% monthly uptime

**Calculation Method:**
```
Uptime % = ((Total Minutes in Month - Downtime Minutes) / Total Minutes in Month) × 100

Example (30-day month):
Total minutes: 43,200
Allowed downtime: 43.2 minutes (0.1%)
Actual downtime: 28 minutes
Uptime: 99.935% ✅ (Exceeds SLA)
```

**Exclusions from Uptime Calculation:**
- Scheduled maintenance windows (announced 72 hours in advance)
- Force majeure events (natural disasters, acts of war)
- Client-side infrastructure failures
- Third-party API outages (Telegram, Gemini AI) exceeding 15 minutes
- DDoS attacks mitigated within 30 minutes

**SLA Credits (Compensation):**

| Actual Uptime | Service Credit |
|---------------|----------------|
| 99.0% - 99.89% | 10% of monthly fee |
| 95.0% - 98.99% | 25% of monthly fee |
| < 95.0% | 50% of monthly fee |

**Credit Claim Process:**
1. Client submits SLA violation report within 7 days of incident
2. ArtinSmartRealty validates claim within 48 hours
3. Credit applied to next invoice (no cash refunds)

---

### 1.2 Response Time Performance

**Target: < 2 seconds per AI reply** (95th percentile)

**Measurement Points:**

| Request Type | Target Response Time | Actual Performance (Nov 2025) |
|--------------|---------------------|-------------------------------|
| **Text Message** | < 2s | 1.2s average, 1.8s p95 ✅ |
| **Voice Transcription (30s audio)** | < 5s | 3.8s average, 4.5s p95 ✅ |
| **Image Analysis** | < 6s | 4.5s average, 5.2s p95 ✅ |
| **Cached FAQ Response** | < 500ms | 280ms average ✅ |
| **PDF ROI Generation** | < 10s | 7.2s average ✅ |

**Performance Degradation Handling:**

If response times exceed targets for > 10 minutes:
1. **Auto-scaling triggered** - Deploy additional FastAPI instances
2. **Fallback to cached responses** - Serve pre-generated answers for common FAQs
3. **Queue management** - Prioritize VIP tenant requests
4. **Incident notification** - Email + SMS to client admins

**Monitoring & Transparency:**
- Real-time performance dashboard: https://status.artinsmartrealty.com
- Weekly performance reports emailed to clients
- Public status page with 90-day history

---

### 1.3 Data Backup & Recovery

**Backup Schedule:**

| Backup Type | Frequency | Retention Period | Storage Location |
|-------------|-----------|-----------------|------------------|
| **Database Full Backup** | Daily @ 2 AM UTC | 30 days | AWS S3 (Multi-region) |
| **Incremental Backup** | Every 6 hours | 7 days | AWS S3 |
| **Redis Session Snapshot** | Hourly | 24 hours | Local + S3 |
| **Configuration Files** | On change | 90 days | Git + S3 |

**Recovery Time Objectives (RTO):**

| Scenario | Target RTO | Tested Recovery Time |
|----------|-----------|---------------------|
| **Database corruption** | < 4 hours | 2.5 hours (Q4 2024 test) |
| **Complete data center failure** | < 8 hours | 6.2 hours (Q3 2024 drill) |
| **Accidental lead deletion** | < 1 hour | 35 minutes (Point-in-time recovery) |
| **Redis session loss** | < 5 minutes | Automatic (new session creation) |

**Recovery Point Objective (RPO):** 6 hours maximum data loss

**Disaster Recovery Testing:**
- Quarterly full disaster recovery drills
- Annual third-party DR audit
- Results published in transparency report

---

## 2. Support Tiers & Response Times

### 2.1 Support Level Matrix

#### **Tier 1: Standard Support (Included in Starter/Professional Plans)**

**Channels:**
- Email: support@artinsmartrealty.com
- In-app ticketing system
- Knowledge base: docs.artinsmartrealty.com

**Response Times:**

| Issue Severity | Initial Response | Resolution Target |
|----------------|-----------------|-------------------|
| **P1 - Critical** (Service down) | 2 hours | 8 hours |
| **P2 - High** (Major feature broken) | 8 hours | 48 hours |
| **P3 - Medium** (Minor bug, workaround available) | 24 hours | 5 business days |
| **P4 - Low** (Feature request, cosmetic issue) | 48 hours | Best effort |

**Coverage Hours:** Monday-Friday, 9 AM - 6 PM GST (UAE time)

**Included Services:**
- ✅ Bug fixes and patches
- ✅ Security updates
- ✅ Platform updates (new features)
- ✅ Email support
- ❌ Custom development
- ❌ On-site training
- ❌ Dedicated account manager

---

#### **Tier 2: Premium Support (Enterprise Plan Add-On: +$500/month)**

**Channels:**
- All Tier 1 channels +
- Phone hotline: +971 4 XXX XXXX
- WhatsApp support: +971 50 XXX XXXX
- Dedicated Slack channel

**Response Times:**

| Issue Severity | Initial Response | Resolution Target |
|----------------|-----------------|-------------------|
| **P1 - Critical** | 30 minutes | 4 hours |
| **P2 - High** | 2 hours | 24 hours |
| **P3 - Medium** | 4 hours | 3 business days |
| **P4 - Low** | 8 hours | Best effort |

**Coverage Hours:** 24/7/365 (including weekends and UAE public holidays)

**Included Services:**
- ✅ All Tier 1 services +
- ✅ Dedicated account manager
- ✅ Monthly strategy review calls
- ✅ Priority feature requests
- ✅ Custom flow development (up to 10 hours/month)
- ✅ Quarterly on-site training (Dubai only)
- ✅ Advanced analytics consulting

**Escalation Path:**
```
Level 1: Support Engineer (Initial response)
    ↓
Level 2: Senior Technical Lead (Complex issues)
    ↓
Level 3: CTO (Architecture changes, P1 incidents)
    ↓
Executive: CEO (Contract disputes, SLA violations)
```

---

#### **Tier 3: Dedicated Infrastructure (Custom Pricing)**

**For clients requiring:**
- Single-tenant deployment (no shared resources)
- Custom geographical hosting (e.g., on-premise UAE servers)
- Custom compliance requirements (HIPAA, SOC 2, ISO 27001)

**Includes:**
- ✅ Dedicated servers (no multi-tenancy)
- ✅ Custom SLA (up to 99.99% uptime)
- ✅ White-label branding
- ✅ Source code escrow
- ✅ Dedicated DevOps engineer
- ✅ Unlimited support tickets

**Minimum Contract:** 12 months, annual prepayment

---

## 3. Maintenance Windows & Change Management

### 3.1 Scheduled Maintenance

**Standard Maintenance Window:**
- **Frequency:** Monthly (first Sunday of each month)
- **Time:** 2:00 AM - 4:00 AM GST (UAE time)
- **Duration:** Maximum 2 hours
- **Notification:** 72 hours advance notice via email + in-app banner

**Emergency Maintenance:**
- **Trigger:** Critical security patches, P1 production bugs
- **Notification:** 4 hours minimum notice (or immediate if zero-day exploit)
- **Compensation:** If exceeds 30 minutes, counts against uptime SLA

**Maintenance Activities:**
- Database schema migrations
- Dependency updates (Python packages, OS patches)
- Performance optimization (index rebuilds)
- Security certificate renewals
- Infrastructure scaling tests

---

### 3.2 Change Management Process

**Change Classification:**

| Change Type | Approval Required | Testing | Rollback Plan |
|-------------|------------------|---------|---------------|
| **Low Risk** (UI text, translations) | Product Manager | Manual QA | Instant (Git revert) |
| **Medium Risk** (New features, API changes) | CTO + Client approval | Staging + UAT | < 15 minutes |
| **High Risk** (Database migrations, auth changes) | CTO + Legal + Client | Full regression suite | < 1 hour |

**Deployment Strategy:**

```
┌─────────────────────────────────────────────────┐
│  BLUE-GREEN DEPLOYMENT (Zero Downtime)         │
└─────────────────────────────────────────────────┘

Step 1: Deploy to Blue environment (inactive)
Step 2: Run health checks + smoke tests
Step 3: Switch traffic to Blue (becomes active)
Step 4: Monitor for 30 minutes
Step 5: If stable, decommission Green
        If issues, instant rollback to Green
```

**Client Communication:**
- **Pre-deployment:** Release notes 48 hours before
- **During deployment:** Real-time status updates on status page
- **Post-deployment:** Summary report with performance metrics

---

## 4. Token Usage & Billing Policy

### 4.1 AI Token Consumption Model

**What Are Tokens?**
Tokens are the unit of measurement for AI processing. 1 token ≈ 4 characters in English, 1-2 characters in Arabic/Persian.

**Example Conversation Token Count:**
```
User: "I want a 2-bedroom apartment in Dubai Marina for 2M"
Tokens: ~15 tokens (input)

Bot: "Great! I have 3 properties matching your criteria..."
Tokens: ~50 tokens (output)

Total: 65 tokens per message exchange
```

**Average Conversation Metrics:**

| Conversation Type | Avg Messages | Avg Tokens | Cost per Conversation |
|-------------------|--------------|------------|---------------------|
| **Simple Inquiry** (FAQ only) | 3 messages | 150 tokens | $0.002 |
| **Partial Qualification** (Drops at budget) | 8 messages | 600 tokens | $0.008 |
| **Full Qualification** (Phone captured) | 15 messages | 1,200 tokens | $0.015 |
| **With Voice** (30s transcription) | 20 messages | 2,500 tokens | $0.030 |
| **With Image** (Vision API) | 18 messages | 3,000 tokens | $0.040 |

**Token Limit Policy:**

| Plan | Monthly Token Allowance | Overage Cost |
|------|------------------------|--------------|
| **Starter** | 500K tokens (~400 convos) | $0.02/1K tokens |
| **Professional** | 2M tokens (~1,600 convos) | $0.015/1K tokens |
| **Enterprise** | Unlimited | Included |

**Billing Transparency:**
- Real-time token usage dashboard
- Daily usage alerts at 80%, 90%, 100%
- Automatic overage billing (itemized invoice)
- Token rollover (unused tokens expire end of month)

---

### 4.2 Pricing Models

#### **Option A: Pay-Per-Conversation (Recommended for Startups)**

**Pricing:**
- $0.50 per qualified conversation (phone number captured)
- $0 for unqualified drop-offs
- No monthly minimum

**Pros:**
- ✅ Zero risk (only pay for results)
- ✅ Scales with business growth

**Cons:**
- ❌ Higher per-conversation cost
- ❌ No advanced features (CRM integration, analytics)

---

#### **Option B: Flat Monthly Fee (Best for Established Agencies)**

**Pricing Tiers:**

| Plan | Monthly Fee | Included Conversations | Overage Cost |
|------|------------|----------------------|--------------|
| **Starter** | $299 | 500 | $0.75/conversation |
| **Professional** | $799 | 2,000 | $0.50/conversation |
| **Enterprise** | Custom | Unlimited | $0 |

**Pros:**
- ✅ Predictable costs
- ✅ Advanced features included
- ✅ Lower per-conversation cost at scale

**Cons:**
- ❌ Minimum commitment (monthly payment even if low usage)

---

#### **Option C: Revenue Share (For Large Portfolios)**

**Pricing:**
- 3-5% of closed deal value (negotiable)
- Tracked via CRM webhook integration
- Minimum $2,000/month guarantee

**Example:**
```
Closed Deals in Month:
1. Villa - 8M AED → $1,200 (5% of $24,000 commission)
2. Apartment - 3M AED → $450
3. Penthouse - 12M AED → $1,800

Total Revenue Share: $3,450
```

**Pros:**
- ✅ Aligned incentives (we succeed when you succeed)
- ✅ No upfront costs

**Cons:**
- ❌ Requires CRM integration
- ❌ Complex contract negotiation

---

## 5. Data Privacy & Compliance

### 5.1 GDPR Compliance

**Data Subject Rights Supported:**

| Right | Implementation | Response Time |
|-------|----------------|---------------|
| **Right to Access** | API endpoint to download all user data | 48 hours |
| **Right to Erasure** | Permanent deletion of lead data | 24 hours |
| **Right to Rectification** | Edit lead info via dashboard | Instant |
| **Right to Data Portability** | Export to JSON/CSV | Instant |
| **Right to Object** | Opt-out of automated processing | Instant |

**Data Processing Agreement (DPA):**
- ArtinSmartRealty acts as **Data Processor**
- Client (agency) is **Data Controller**
- Signed DPA included in Enterprise contracts
- Sub-processor list: AWS (hosting), Google (AI), Telegram (messaging)

**Data Retention Policy:**
- Active leads: Retained indefinitely
- Inactive leads (no activity for 2 years): Auto-deleted (unless client opts out)
- Conversation logs: 90 days (configurable up to 2 years)
- Voice recordings: 30 days (GDPR requirement)
- Analytics data (anonymized): 5 years

---

### 5.2 UAE Data Protection Law (PDPL) Compliance

**Legal Framework:**
- UAE Federal Decree-Law No. 45 of 2021 (Personal Data Protection Law)
- Effective: September 2, 2023

**Compliance Measures:**
- ✅ Explicit consent obtained before data collection
- ✅ Data processing limited to specified purposes
- ✅ Data stored within UAE jurisdiction (optional)
- ✅ Breach notification within 72 hours
- ✅ Data Protection Officer (DPO) appointed

**Cross-Border Data Transfer:**
- Default: AWS Middle East (Bahrain) region
- Optional: AWS UAE (Dubai) region (+20% cost)
- Data residency certificate provided

---

### 5.3 Security Certifications

**Current Certifications:**
- ✅ ISO 27001:2022 (Information Security Management)
- ✅ SOC 2 Type II (Security, Availability, Confidentiality)
- 🔄 PCI DSS (In progress, Q2 2026) - For payment processing

**Annual Security Audit:**
- Independent third-party penetration testing
- Vulnerability scanning (monthly)
- Code security reviews (quarterly)
- Results shared with Enterprise clients under NDA

**Incident Response Plan:**
```
Data Breach Detection → Containment (< 1 hour) → Investigation → 
Client Notification (< 24 hours) → Remediation → Post-Incident Report
```

---

## 6. Professional Services

### 6.1 Onboarding & Implementation

**Included in All Plans:**

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| **1. Kickoff Call** | 1 hour | Requirements gathering, access credentials |
| **2. Bot Configuration** | 24 hours | Telegram bot setup, branding customization |
| **3. Data Import** | 48 hours | Import existing lead database (CSV) |
| **4. Team Training** | 2 hours | Dashboard walkthrough, best practices |
| **5. Go-Live** | 1 hour | Final testing, production deployment |

**Total Onboarding Time:** 5 business days

---

### 6.2 Custom Development Services

**Hourly Rate:** $150/hour (Enterprise clients), $200/hour (Standard)

**Common Customizations:**

| Service | Estimated Hours | Total Cost |
|---------|----------------|------------|
| **Custom CRM Integration** | 8-12 hours | $1,200 - $1,800 |
| **White-Label Branding** | 4-6 hours | $600 - $900 |
| **Custom AI Training** (Industry-specific) | 20-30 hours | $3,000 - $4,500 |
| **Additional Language Support** | 10-15 hours | $1,500 - $2,250 |
| **Voice Cloning (Agent's Voice)** | 8 hours + $500 licensing | $1,700 |

**Custom Development SLA:**
- Fixed-price quotes provided within 48 hours
- Work begins within 5 business days of approval
- Progress updates every 3 days
- Final delivery includes 30 days of bug fixes

---

### 6.3 Training & Consulting

**Training Packages:**

| Package | Duration | Price | Includes |
|---------|----------|-------|----------|
| **Basic** | 2 hours | Included | Dashboard tour, FAQ handling |
| **Advanced** | 4 hours | $500 | Conversation design, analytics interpretation |
| **Agency Certification** | 8 hours | $1,500 | Full platform mastery, best practices |

**Consulting Services:**
- Conversation flow optimization: $200/hour
- Lead qualification strategy: $200/hour
- Multi-agent workflow design: $250/hour

---

## 7. Contract Terms & Legal

### 7.1 Agreement Structure

**Contract Duration:**
- **Starter/Professional:** Month-to-month (cancel anytime with 30 days notice)
- **Enterprise:** 12-month minimum, auto-renewal

**Payment Terms:**
- Monthly plans: Billed on 1st of each month (advance payment)
- Annual plans: 10% discount, billed upfront
- Accepted methods: Credit card, wire transfer, Stripe

**Late Payment Policy:**
- Grace period: 5 days
- Late fee: 5% of invoice amount
- Service suspension: After 10 days overdue
- Data retention: 30 days after suspension (then permanent deletion)

---

### 7.2 Termination Conditions

**Client-Initiated Termination:**
- Notice period: 30 days
- Data export provided within 48 hours
- No refunds for current billing cycle
- API access revoked immediately after notice period

**ArtinSmartRealty-Initiated Termination:**
- Grounds: Non-payment, Terms of Service violation, illegal activity
- Notice period: 7 days (except immediate for illegal activity)
- Full refund of unused portion

**Data Destruction After Termination:**
- All lead data permanently deleted after 90 days
- Client receives final data export (JSON + CSV)
- Deletion certificate provided upon request

---

### 7.3 Liability & Indemnification

**Limitation of Liability:**
- Maximum liability: 12 months of fees paid
- Excludes: Gross negligence, willful misconduct, data breach due to our security failure

**Indemnification:**
- ArtinSmartRealty indemnifies client against IP infringement claims
- Client indemnifies ArtinSmartRealty against misuse of platform (e.g., spam, illegal content)

**Insurance Coverage:**
- Professional Liability: $5M
- Cyber Liability: $10M
- General Liability: $2M

---

## 8. Performance Monitoring & Reporting

### 8.1 Monthly Performance Reports

**Delivered on 1st of each month:**

```
┌─────────────────────────────────────────────────┐
│  ArtinSmartRealty - November 2025 Report        │
│  Client: Dubai Elite Properties                 │
└─────────────────────────────────────────────────┘

📊 Conversation Metrics:
- Total conversations: 1,245
- Qualified leads: 498 (40%)
- Phone numbers captured: 187 (15%)
- Average qualification time: 68 seconds

⚡ Performance:
- Average response time: 1.4s (Target: < 2s) ✅
- Uptime: 99.94% (Target: 99.9%) ✅
- API errors: 0.02% (Target: < 1%) ✅

💰 Business Impact:
- Estimated deals closed: 8 (based on CRM data)
- Revenue attributed: $180,000
- ROI: 225x (Platform cost: $799)

🔥 Top Performing Hours:
1. 8 PM - 10 PM GST (28% of conversations)
2. 12 PM - 2 PM GST (22% of conversations)
3. 6 PM - 8 PM GST (18% of conversations)

🌍 Top Languages:
1. Arabic: 45%
2. English: 35%
3. Persian: 18%
4. Russian: 2%
```

---

### 8.2 Quarterly Business Reviews (Enterprise Only)

**Format:** 60-minute video call with:
- Account Manager
- Senior Technical Lead
- Optional: CTO (for strategic accounts)

**Agenda:**
1. Performance deep dive (30 min)
2. Feature roadmap preview (15 min)
3. Optimization recommendations (10 min)
4. Q&A (5 min)

**Deliverables:**
- Custom analytics deck (PowerPoint)
- Competitive benchmark report
- Action plan with timelines

---

## 9. Acceptable Use Policy

### 9.1 Prohibited Activities

**Strictly Forbidden:**

❌ **Spam:** Sending unsolicited messages to users who didn't initiate contact  
❌ **Scraping:** Using bot to harvest contact information for external databases  
❌ **Illegal Content:** Promoting illegal properties, money laundering, fraud  
❌ **Impersonation:** Pretending to be government entities (Dubai Land Dept, etc.)  
❌ **Hate Speech:** Discriminatory messaging based on race, religion, nationality  
❌ **Competitive Intelligence:** Using platform to gather data on competitors  

**Violation Consequences:**
1. First offense: Warning + 24-hour suspension
2. Second offense: 7-day suspension
3. Third offense: Immediate termination (no refund)

---

### 9.2 Fair Usage Guidelines

**Conversation Quality Standards:**
- No bulk messaging (max 50 new conversations/day per agent)
- No automated lead generation (must be human-initiated)
- Response to user inquiries within 24 hours (agent takeover)

**API Rate Limits:**
- 100 requests/minute (Standard plans)
- 500 requests/minute (Enterprise plans)
- Burst allowance: 2x for 60 seconds

---

## 10. Contact & Escalation

### 10.1 Support Contacts

**Technical Support:**
- Email: support@artinsmartrealty.com
- Phone: +971 4 XXX XXXX (Premium/Enterprise only)
- Live chat: app.artinsmartrealty.com (9 AM - 6 PM GST)

**Account Management:**
- Email: accounts@artinsmartrealty.com
- Dedicated Slack (Enterprise only)

**Billing & Invoicing:**
- Email: billing@artinsmartrealty.com
- Portal: billing.artinsmartrealty.com

**Executive Escalations:**
- CTO: cto@artinsmartrealty.com (Technical issues only)
- CEO: ceo@artinsmartrealty.com (Contract disputes, SLA violations)

---

### 10.2 Service Status

**Real-Time Status Page:**
https://status.artinsmartrealty.com

**Incident History:**
- Last 90 days: 2 incidents (both < 15 minutes)
- P1 incidents (2025): 0
- Planned maintenance: 11 windows (all completed on time)

**Subscribe to Updates:**
- Email alerts: status.artinsmartrealty.com/subscribe
- SMS alerts: Premium/Enterprise only
- Slack integration: Enterprise only

---

**Document Version:** 2.0  
**Last Updated:** November 28, 2025  
**Next Review:** February 28, 2026  

**Acceptance:**
This SLA is automatically incorporated into all service contracts. Custom SLA terms available for Enterprise clients upon request.

---

**© 2025 ArtinSmartRealty. All rights reserved.**
