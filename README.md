# JSW ONE MSME — WhatsApp AI Sales Agent (Priya)

AI-powered WhatsApp sales qualification agent for JSW ONE MSME. Priya auto-qualifies inbound steel and cement leads, triggers human handoffs at the right moment, and gives inside sales a single dashboard for their daily work queue.

---

## Architecture

```
WhatsApp Business API (Meta)
        ↕
   FastAPI (port 8000)  ←→  Claude claude-sonnet-4-6 (Priya)
        ↕
   PostgreSQL 15  +  Redis 7 (session cache)
        ↕
   Celery Workers (campaigns, follow-ups, Salesforce sync)
        ↕
   React Dashboard (port 3000)
        ↕
   Salesforce (optional — Opportunity upsert on handoff resolve)
```

---

## Quick Start

### 1. Clone and configure

```bash
git clone <repo-url>
cd jsw-msme-wa-agent
cp .env.example .env
# Edit .env — add ANTHROPIC_API_KEY and META_* credentials at minimum
```

### 2. Start all services

```bash
docker-compose up --build
```

Services started:
| Service | URL |
|---------|-----|
| FastAPI API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| React Dashboard | http://localhost:3000 |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

Database schema and seed data are applied automatically from `backend/migrations/`.

### 3. Configure WhatsApp Business Account

1. Go to [Meta for Developers](https://developers.facebook.com/) → your WhatsApp Business app
2. Set webhook URL: `https://your-domain.com/webhook`
3. Set **Verify Token** to match `META_VERIFY_TOKEN` in your `.env`
4. Subscribe to the `messages` webhook field
5. Add your test number to the allowed list under **Phone Numbers**

To test locally:
```bash
# Install ngrok, then:
ngrok http 8000
# Use the https URL as your webhook in Meta dashboard
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key for Claude |
| `META_WHATSAPP_TOKEN` | Yes | WhatsApp Cloud API bearer token |
| `META_PHONE_NUMBER_ID` | Yes | Meta phone number ID |
| `META_VERIFY_TOKEN` | Yes | Webhook verification token (you choose) |
| `META_APP_SECRET` | Recommended | For signature verification |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `SALESFORCE_CLIENT_ID` | Optional | SF connected app client ID |
| `SALESFORCE_CLIENT_SECRET` | Optional | SF connected app secret |
| `SALESFORCE_INSTANCE_URL` | Optional | e.g. `https://yourorg.salesforce.com` |
| `SALESFORCE_ENABLED` | Optional | Set `true` to enable SF sync |
| `BUSINESS_HOURS_START` | Optional | IST hour (default: 9) |
| `BUSINESS_HOURS_END` | Optional | IST hour (default: 19) |
| `HANDOFF_SLA_MINUTES` | Optional | Target acceptance SLA (default: 30) |

---

## First Campaign Walkthrough

1. Open the dashboard at http://localhost:3000
2. Go to **Campaigns** → **+ New Campaign**
3. Fill in:
   - **Name**: `April TMT Offer`
   - **Template name**: your Meta-approved template name (e.g. `jsw_tmt_offer_v1`)
   - **Language**: Hindi
4. Click **Create**
5. Click **Upload CSV** — upload a file with a `phone` column (E.164 format, e.g. `919876543210`)
6. Click **Send Now** — Celery will dispatch template messages to all contacts

---

## Bot Qualification Flow

Priya collects these fields, one question at a time:

| # | Field | Example |
|---|-------|---------|
| 1 | Project type | residential / commercial / infrastructure |
| 2 | Project location | Mumbai, Pune, Hyderabad |
| 3 | Material needed | TMT Fe500, JSW Cement OPC 53 |
| 4 | Volume | 100 MT, 500 bags |
| 5 | Timeline | 2 weeks, next month |
| 6 | Decision maker | Yes / No |

**Scoring** (0–100):
- Volume ≥ 50 MT → +30
- Timeline ≤ 30 days → +25
- Decision maker confirmed → +20
- Commercial/infrastructure project → +15
- Name known → +10

**Score ≥ 70 → automatic handoff to human agent.**

---

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest
```

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/webhook` | Meta webhook verification |
| POST | `/webhook` | Inbound WhatsApp messages |
| GET | `/dashboard/metrics` | KPI metrics (leads, handoffs, SLA) |
| GET | `/dashboard/leads` | Lead list with filters |
| GET | `/dashboard/conversations/{id}/messages` | Conversation thread |
| GET | `/handoff/queue` | Pending handoff queue |
| POST | `/handoff/{id}/accept` | Agent accepts a handoff |
| POST | `/handoff/{id}/resolve` | Agent resolves a handoff |
| POST | `/handoff/{id}/send` | Agent sends a message |
| GET | `/campaigns` | List campaigns |
| POST | `/campaigns` | Create campaign |
| POST | `/campaigns/{id}/contacts` | Upload contact CSV |
| POST | `/campaigns/{id}/send` | Trigger campaign send |
| GET | `/campaigns/{id}/stats` | Delivery stats |

---

## Supported Languages

Priya detects and responds in: Hindi, Marathi, Gujarati, Telugu, Kannada, Tamil, English.

---

## What This Does NOT Handle

- Pricing / quotes — handled by jswonemsme.com and the sales team
- Email flows — handled by MoEngage
- Generic CRM — handled by Salesforce
- JSW One Homes or other business units
