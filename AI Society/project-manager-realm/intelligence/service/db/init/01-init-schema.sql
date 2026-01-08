-- Initial database schema for Intelligence Service

-- Create tables for cost tracking
CREATE TABLE IF NOT EXISTS workspaces (
    id SERIAL PRIMARY KEY,
    workspace_id UUID UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cost_budgets (
    id SERIAL PRIMARY KEY,
    workspace_id UUID NOT NULL REFERENCES workspaces(workspace_id),
    monthly_budget_cents INTEGER NOT NULL DEFAULT 100000, -- $1000
    alert_threshold_percent INTEGER NOT NULL DEFAULT 80,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(workspace_id)
);

CREATE TABLE IF NOT EXISTS llm_costs (
    id SERIAL PRIMARY KEY,
    workspace_id UUID NOT NULL REFERENCES workspaces(workspace_id),
    provider VARCHAR(50) NOT NULL, -- gemini, claude, gpt4
    model VARCHAR(100) NOT NULL,
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    cost_cents DECIMAL(10, 4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_workspace_created (workspace_id, created_at),
    INDEX idx_provider_created (provider, created_at)
);

CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    conversation_id UUID UNIQUE NOT NULL,
    workspace_id UUID NOT NULL REFERENCES workspaces(workspace_id),
    channel_id VARCHAR(255),
    thread_ts VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_workspace_id (workspace_id),
    INDEX idx_created_at (created_at)
);

CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    message_id UUID UNIQUE NOT NULL,
    conversation_id UUID NOT NULL REFERENCES conversations(conversation_id),
    role VARCHAR(50), -- user, assistant, system
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_created_at (created_at)
);

-- Create materialized view for monthly cost aggregation
CREATE MATERIALIZED VIEW IF NOT EXISTS monthly_cost_summary AS
SELECT 
    workspace_id,
    DATE_TRUNC('month', created_at)::DATE as month,
    provider,
    SUM(cost_cents) as total_cost_cents,
    SUM(prompt_tokens) as total_prompt_tokens,
    SUM(completion_tokens) as total_completion_tokens
FROM llm_costs
GROUP BY workspace_id, DATE_TRUNC('month', created_at), provider;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_monthly_cost_workspace ON monthly_cost_summary(workspace_id);
CREATE INDEX IF NOT EXISTS idx_monthly_cost_month ON monthly_cost_summary(month);

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_stat_statements for monitoring
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Create role-based access control functions for multi-tenancy
CREATE OR REPLACE FUNCTION set_workspace_id(workspace_uuid UUID) RETURNS void AS $$
BEGIN
    PERFORM set_config('app.workspace_id', workspace_uuid::text, false);
END;
$$ LANGUAGE plpgsql;

-- Add RLS policies for workspaces
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE cost_budgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE llm_costs ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Create policies for workspace isolation (placeholder - adjust based on auth system)
-- These are basic examples; real implementation depends on your auth system
CREATE POLICY workspace_isolation_workspaces ON workspaces
    USING (workspace_id::text = COALESCE(current_setting('app.workspace_id'), ''));

CREATE POLICY workspace_isolation_costs ON llm_costs
    USING (workspace_id::text = COALESCE(current_setting('app.workspace_id'), ''));

CREATE POLICY workspace_isolation_conversations ON conversations
    USING (workspace_id::text = COALESCE(current_setting('app.workspace_id'), ''));

-- Create table for health checks
CREATE TABLE IF NOT EXISTS health_checks (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL, -- healthy, degraded, unhealthy
    last_check_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details JSONB,
    INDEX idx_service_checked (service_name, last_check_at)
);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO intelligence;
