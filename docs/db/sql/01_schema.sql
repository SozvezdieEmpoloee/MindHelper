-- MindHelper PostgreSQL schema
-- Updated to match current Django models and migrations.
-- PostgreSQL 14+.

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS user_account (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email varchar(254) NOT NULL UNIQUE,
    password_hash varchar(255) NOT NULL,
    display_name varchar(120) NOT NULL,
    status varchar(32) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'blocked', 'deleted')),
    is_staff boolean NOT NULL DEFAULT false,
    is_superuser boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    last_login_at timestamptz
);

CREATE TABLE IF NOT EXISTS role (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(32) NOT NULL UNIQUE,
    name varchar(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS user_role (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES user_account(id) ON DELETE CASCADE,
    role_id uuid NOT NULL REFERENCES role(id) ON DELETE CASCADE,
    assigned_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_user_role UNIQUE (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS channel_account (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES user_account(id) ON DELETE CASCADE,
    channel_type varchar(32) NOT NULL
        CHECK (channel_type IN ('web', 'telegram')),
    external_user_id varchar(255) NOT NULL,
    external_chat_id varchar(255),
    bot_message_log jsonb NOT NULL DEFAULT '[]'::jsonb,
    linked_at timestamptz NOT NULL DEFAULT now(),
    is_active boolean NOT NULL DEFAULT true,
    CONSTRAINT uq_channel_external_user UNIQUE (channel_type, external_user_id)
);

CREATE TABLE IF NOT EXISTS neural_model_version (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    version_tag varchar(64) NOT NULL UNIQUE,
    model_name varchar(120) NOT NULL,
    provider varchar(120) NOT NULL,
    safety_profile varchar(64) NOT NULL,
    is_active boolean NOT NULL DEFAULT false,
    deployed_at timestamptz,
    created_by_admin_user_id uuid NOT NULL REFERENCES user_account(id) ON DELETE RESTRICT
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_single_active_model
    ON neural_model_version ((is_active))
    WHERE is_active = true;

CREATE TABLE IF NOT EXISTS user_chat (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL UNIQUE REFERENCES user_account(id) ON DELETE CASCADE,
    model_version_id uuid REFERENCES neural_model_version(id) ON DELETE SET NULL,
    status varchar(32) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'archived', 'blocked')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chat_message (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id uuid NOT NULL REFERENCES user_chat(id) ON DELETE CASCADE,
    sender_role varchar(16) NOT NULL
        CHECK (sender_role IN ('user', 'bot', 'system')),
    content_text text NOT NULL,
    risk_score numeric(6,5)
        CHECK (risk_score IS NULL OR (risk_score >= 0 AND risk_score <= 1)),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS emergency_resource (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    region_code varchar(16) NOT NULL,
    service_name varchar(255) NOT NULL,
    contact_phone varchar(64) NOT NULL DEFAULT '',
    contact_url varchar(512) NOT NULL DEFAULT '',
    is_active boolean NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS crisis_event (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id uuid NOT NULL REFERENCES user_chat(id) ON DELETE CASCADE,
    trigger_message_id uuid REFERENCES chat_message(id) ON DELETE SET NULL,
    emergency_resource_id uuid REFERENCES emergency_resource(id) ON DELETE SET NULL,
    risk_level varchar(16) NOT NULL
        CHECK (risk_level IN ('low', 'elevated', 'high', 'critical')),
    status varchar(32) NOT NULL
        CHECK (status IN ('open', 'resolved', 'dismissed')),
    screening_status varchar(24) NOT NULL DEFAULT 'not_required'
        CHECK (screening_status IN ('not_required', 'pending', 'completed')),
    screening_question_index smallint NOT NULL DEFAULT 0
        CHECK (screening_question_index >= 0),
    screening_answers jsonb NOT NULL DEFAULT '[]'::jsonb,
    action_note text NOT NULL DEFAULT '',
    detected_at timestamptz NOT NULL DEFAULT now(),
    resolved_at timestamptz
);

CREATE TABLE IF NOT EXISTS assessment_template (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(64) NOT NULL UNIQUE,
    title varchar(255) NOT NULL,
    is_active boolean NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS assessment_question (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id uuid NOT NULL REFERENCES assessment_template(id) ON DELETE CASCADE,
    question_text text NOT NULL,
    response_format varchar(32) NOT NULL
        CHECK (response_format IN ('scale', 'text', 'number')),
    min_value numeric(8,2),
    max_value numeric(8,2),
    order_index int NOT NULL,
    CONSTRAINT uq_template_question_order UNIQUE (template_id, order_index)
);

CREATE TABLE IF NOT EXISTS assessment_session (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES user_account(id) ON DELETE CASCADE,
    chat_id uuid REFERENCES user_chat(id) ON DELETE SET NULL,
    template_id uuid NOT NULL REFERENCES assessment_template(id) ON DELETE RESTRICT,
    status varchar(32) NOT NULL
        CHECK (status IN ('started', 'completed', 'cancelled')),
    total_score numeric(10,4),
    severity_level varchar(32) NOT NULL DEFAULT '',
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz
);

CREATE TABLE IF NOT EXISTS assessment_answer (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id uuid NOT NULL REFERENCES assessment_session(id) ON DELETE CASCADE,
    question_id uuid NOT NULL REFERENCES assessment_question(id) ON DELETE RESTRICT,
    answer_value numeric(10,4),
    answer_text text NOT NULL DEFAULT '',
    answered_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_session_question UNIQUE (session_id, question_id)
);

CREATE TABLE IF NOT EXISTS specialist (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name varchar(255) NOT NULL,
    profession varchar(32) NOT NULL
        CHECK (profession IN ('psychologist', 'psychiatrist')),
    license_number varchar(64) NOT NULL DEFAULT '',
    is_verified boolean NOT NULL DEFAULT false,
    rating_avg numeric(3,2)
        CHECK (rating_avg IS NULL OR (rating_avg >= 0 AND rating_avg <= 5))
);

CREATE TABLE IF NOT EXISTS specialist_location (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    specialist_id uuid NOT NULL REFERENCES specialist(id) ON DELETE CASCADE,
    address_line varchar(512) NOT NULL,
    city varchar(120) NOT NULL,
    latitude numeric(9,6) NOT NULL,
    longitude numeric(9,6) NOT NULL,
    consultation_price numeric(10,2),
    currency varchar(3) NOT NULL DEFAULT 'RUB',
    is_active boolean NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS appointment (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES user_account(id) ON DELETE CASCADE,
    specialist_id uuid NOT NULL REFERENCES specialist(id) ON DELETE RESTRICT,
    location_id uuid REFERENCES specialist_location(id) ON DELETE SET NULL,
    start_at timestamptz NOT NULL,
    end_at timestamptz NOT NULL,
    status varchar(32) NOT NULL
        CHECK (status IN ('requested', 'confirmed', 'completed', 'cancelled')),
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_appointment_time CHECK (end_at > start_at)
);

CREATE TABLE IF NOT EXISTS moderation_case (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id uuid NOT NULL REFERENCES user_chat(id) ON DELETE CASCADE,
    message_id uuid REFERENCES chat_message(id) ON DELETE SET NULL,
    reason text NOT NULL,
    status varchar(32) NOT NULL
        CHECK (status IN ('open', 'in_review', 'closed')),
    opened_by_admin_user_id uuid NOT NULL REFERENCES user_account(id) ON DELETE RESTRICT,
    opened_at timestamptz NOT NULL DEFAULT now(),
    closed_at timestamptz
);

CREATE TABLE IF NOT EXISTS site_content (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    content_type varchar(64) NOT NULL
        CHECK (content_type IN ('faq', 'announcement', 'help_page', 'legal')),
    slug varchar(255) NOT NULL UNIQUE,
    title varchar(255) NOT NULL,
    body text NOT NULL,
    is_published boolean NOT NULL DEFAULT false,
    updated_by_admin_user_id uuid NOT NULL REFERENCES user_account(id) ON DELETE RESTRICT,
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS safety_audit_log (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id uuid NOT NULL REFERENCES user_chat(id) ON DELETE CASCADE,
    message_id uuid REFERENCES chat_message(id) ON DELETE SET NULL,
    crisis_event_id uuid REFERENCES crisis_event(id) ON DELETE SET NULL,
    model_version_id uuid REFERENCES neural_model_version(id) ON DELETE SET NULL,
    risk_level varchar(16) NOT NULL
        CHECK (risk_level IN ('low', 'elevated', 'high', 'critical')),
    route_code varchar(64) NOT NULL
        CHECK (
            route_code IN (
                'low_support',
                'elevated_support',
                'immediate_emergency',
                'start_screening',
                'repeat_screening',
                'screening_next_question',
                'screening_negative',
                'screening_high',
                'screening_critical'
            )
        ),
    escalation_action varchar(64) NOT NULL
        CHECK (
            escalation_action IN (
                'none',
                'offer_specialist',
                'start_asq',
                'urgent_specialist',
                'emergency_contacts'
            )
        ),
    human_review_flag boolean NOT NULL DEFAULT false,
    generated_with_model boolean NOT NULL DEFAULT false,
    policy_intervened boolean NOT NULL DEFAULT false,
    model_provider varchar(64) NOT NULL DEFAULT '',
    matched_rules jsonb NOT NULL DEFAULT '[]'::jsonb,
    action_note text NOT NULL DEFAULT '',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_user_role_user_id ON user_role(user_id);
CREATE INDEX IF NOT EXISTS ix_channel_account_user_id ON channel_account(user_id);
CREATE INDEX IF NOT EXISTS ix_user_chat_model_version_id ON user_chat(model_version_id);
CREATE INDEX IF NOT EXISTS ix_chat_message_chat_id_created_at ON chat_message(chat_id, created_at);
CREATE INDEX IF NOT EXISTS ix_crisis_event_chat_id ON crisis_event(chat_id);
CREATE INDEX IF NOT EXISTS ix_assessment_question_template_id ON assessment_question(template_id);
CREATE INDEX IF NOT EXISTS ix_assessment_session_user_id ON assessment_session(user_id);
CREATE INDEX IF NOT EXISTS ix_assessment_answer_session_id ON assessment_answer(session_id);
CREATE INDEX IF NOT EXISTS ix_specialist_location_specialist_id ON specialist_location(specialist_id);
CREATE INDEX IF NOT EXISTS ix_appointment_user_id ON appointment(user_id);
CREATE INDEX IF NOT EXISTS ix_moderation_case_chat_id ON moderation_case(chat_id);
CREATE INDEX IF NOT EXISTS ix_site_content_type_published ON site_content(content_type, is_published);
CREATE INDEX IF NOT EXISTS ix_safety_audit_log_chat_id ON safety_audit_log(chat_id);
CREATE INDEX IF NOT EXISTS ix_safety_audit_log_message_id ON safety_audit_log(message_id);
CREATE INDEX IF NOT EXISTS ix_safety_audit_log_crisis_event_id ON safety_audit_log(crisis_event_id);
CREATE INDEX IF NOT EXISTS ix_safety_audit_log_model_version_id ON safety_audit_log(model_version_id);

COMMIT;
