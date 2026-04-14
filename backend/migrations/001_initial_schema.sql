-- JSW ONE MSME WhatsApp Agent — Initial Schema

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── Leads ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS leads (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone            VARCHAR(20) UNIQUE NOT NULL,
    name             VARCHAR(200),
    language         VARCHAR(10) NOT NULL DEFAULT 'en',
    stage            VARCHAR(20) NOT NULL DEFAULT 'NEW',
    score            INT NOT NULL DEFAULT 0,
    project_type     VARCHAR(50),
    project_location VARCHAR(200),
    material_needed  VARCHAR(200),
    volume_mt        VARCHAR(50),
    timeline_days    INT,
    is_decision_maker BOOLEAN,
    sf_opportunity_id VARCHAR(100),
    sf_synced_at     TIMESTAMP,
    created_at       TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_leads_phone ON leads(phone);
CREATE INDEX IF NOT EXISTS idx_leads_stage ON leads(stage);

-- ─── Conversations ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS conversations (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id    UUID NOT NULL REFERENCES leads(id),
    channel    VARCHAR(20) NOT NULL DEFAULT 'whatsapp',
    status     VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_conversations_lead_id ON conversations(lead_id);
CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status);

-- ─── Messages ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS messages (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id   UUID NOT NULL REFERENCES conversations(id),
    direction         VARCHAR(3) NOT NULL,       -- IN | OUT
    body              TEXT NOT NULL,
    template_name     VARCHAR(100),
    wa_message_id     VARCHAR(100),
    created_at        TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);

-- ─── Handoff Queue ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS handoff_queue (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id  UUID NOT NULL UNIQUE REFERENCES conversations(id),
    agent_id         VARCHAR(36),
    trigger_reason   VARCHAR(50) NOT NULL,
    triggered_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    accepted_at      TIMESTAMP,
    resolved_at      TIMESTAMP,
    resolution_notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_handoff_pending ON handoff_queue(accepted_at) WHERE accepted_at IS NULL;

-- ─── Campaigns ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS campaigns (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name          VARCHAR(200) NOT NULL,
    template_name VARCHAR(100) NOT NULL,
    language      VARCHAR(10) NOT NULL DEFAULT 'en',
    status        VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
    scheduled_at  TIMESTAMP,
    started_at    TIMESTAMP,
    completed_at  TIMESTAMP,
    created_by    VARCHAR(36),
    created_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS campaign_contacts (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id   UUID NOT NULL REFERENCES campaigns(id),
    lead_id       UUID NOT NULL REFERENCES leads(id),
    sent_at       TIMESTAMP,
    delivered_at  TIMESTAMP,
    replied_at    TIMESTAMP,
    failed_at     TIMESTAMP,
    error_message TEXT
);
CREATE INDEX IF NOT EXISTS idx_cc_campaign_id ON campaign_contacts(campaign_id);
