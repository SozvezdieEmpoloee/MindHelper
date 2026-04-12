-- MindSupport test data
-- Safe to run multiple times (fixed UUIDs + ON CONFLICT DO NOTHING)

BEGIN;

-- Users
INSERT INTO user_account (
    id, email, password_hash, display_name, status, is_staff, is_superuser, created_at, last_login_at
)
VALUES
    ('00000000-0000-0000-0000-000000000001', 'admin@mindhelper.local', '$2b$12$admin_placeholder_hash', 'System Admin', 'active', true, true, now(), now()),
    ('00000000-0000-0000-0000-000000000002', 'user1@mindhelper.local', '$2b$12$user_placeholder_hash', 'Anna K', 'active', false, false, now(), now())
ON CONFLICT (id) DO NOTHING;

-- Roles
INSERT INTO role (id, code, name)
VALUES
    ('00000000-0000-0000-0000-000000000011', 'admin', 'Administrator'),
    ('00000000-0000-0000-0000-000000000012', 'user', 'User')
ON CONFLICT (id) DO NOTHING;

-- User-role mapping
INSERT INTO user_role (id, user_id, role_id, assigned_at)
VALUES
    ('00000000-0000-0000-0000-000000000021', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000011', now()),
    ('00000000-0000-0000-0000-000000000022', '00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000012', now())
ON CONFLICT (id) DO NOTHING;

-- Linked channels
INSERT INTO channel_account (id, user_id, channel_type, external_user_id, external_chat_id, linked_at, is_active)
VALUES
    ('00000000-0000-0000-0000-000000000031', '00000000-0000-0000-0000-000000000002', 'web', 'web-user-anna', null, now(), true),
    ('00000000-0000-0000-0000-000000000032', '00000000-0000-0000-0000-000000000002', 'telegram', 'tg-user-anna', 'tg-chat-anna', now(), true)
ON CONFLICT (id) DO NOTHING;

-- Model versions
INSERT INTO neural_model_version (id, version_tag, model_name, provider, safety_profile, is_active, deployed_at, created_by_admin_user_id)
VALUES
    ('00000000-0000-0000-0000-000000000101', 'v0.9.0', 'MindSupport-RU', 'local', 'strict-v1', false, now() - interval '20 days', '00000000-0000-0000-0000-000000000001'),
    ('00000000-0000-0000-0000-000000000102', 'v1.0.0', 'MindSupport-RU', 'local', 'strict-v2', true, now() - interval '3 days', '00000000-0000-0000-0000-000000000001')
ON CONFLICT (id) DO NOTHING;

-- One chat per user
INSERT INTO user_chat (id, user_id, model_version_id, status, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000000201', '00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000102', 'active', now() - interval '2 days', now())
ON CONFLICT (id) DO NOTHING;

-- Chat messages
INSERT INTO chat_message (id, chat_id, sender_role, content_text, risk_score, created_at)
VALUES
    ('00000000-0000-0000-0000-000000000301', '00000000-0000-0000-0000-000000000201', 'user', 'Lately I feel very anxious and cannot sleep.', 0.55000, now() - interval '1 day'),
    ('00000000-0000-0000-0000-000000000302', '00000000-0000-0000-0000-000000000201', 'bot', 'Thank you for sharing this. Can you rate anxiety from 1 to 10?', 0.15000, now() - interval '1 day' + interval '1 minute'),
    ('00000000-0000-0000-0000-000000000303', '00000000-0000-0000-0000-000000000201', 'user', 'I had thoughts that scare me. I may need urgent help.', 0.93000, now() - interval '2 hours')
ON CONFLICT (id) DO NOTHING;

-- Emergency resources
INSERT INTO emergency_resource (id, region_code, service_name, contact_phone, contact_url, is_active)
VALUES
    ('00000000-0000-0000-0000-000000000401', 'RU-VOR', 'Regional Emergency Mental Health Hotline', '+7-800-000-00-00', 'https://example.org/help', true)
ON CONFLICT (id) DO NOTHING;

-- Crisis event
INSERT INTO crisis_event (
    id, chat_id, trigger_message_id, emergency_resource_id, risk_level, status, action_note, detected_at, resolved_at
)
VALUES
    (
        '00000000-0000-0000-0000-000000000501',
        '00000000-0000-0000-0000-000000000201',
        '00000000-0000-0000-0000-000000000303',
        '00000000-0000-0000-0000-000000000401',
        'critical',
        'open',
        'Escalated to emergency hotline recommendation.',
        now() - interval '2 hours',
        null
    )
ON CONFLICT (id) DO NOTHING;

-- Assessment templates and questions
INSERT INTO assessment_template (id, code, title, is_active)
VALUES
    ('00000000-0000-0000-0000-000000000601', 'WELLBEING_BASIC_V1', 'Basic Wellbeing Check', true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO assessment_question (id, template_id, question_text, response_format, min_value, max_value, order_index)
VALUES
    ('00000000-0000-0000-0000-000000000611', '00000000-0000-0000-0000-000000000601', 'How anxious did you feel this week?', 'scale', 0, 10, 1),
    ('00000000-0000-0000-0000-000000000612', '00000000-0000-0000-0000-000000000601', 'How was your sleep quality?', 'scale', 0, 10, 2),
    ('00000000-0000-0000-0000-000000000613', '00000000-0000-0000-0000-000000000601', 'How much energy did you have?', 'scale', 0, 10, 3)
ON CONFLICT (id) DO NOTHING;

INSERT INTO assessment_session (
    id, user_id, chat_id, template_id, status, total_score, severity_level, started_at, completed_at
)
VALUES
    (
        '00000000-0000-0000-0000-000000000701',
        '00000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000201',
        '00000000-0000-0000-0000-000000000601',
        'completed',
        18.0000,
        'moderate',
        now() - interval '6 hours',
        now() - interval '5 hours 50 minutes'
    )
ON CONFLICT (id) DO NOTHING;

INSERT INTO assessment_answer (id, session_id, question_id, answer_value, answer_text, answered_at)
VALUES
    ('00000000-0000-0000-0000-000000000711', '00000000-0000-0000-0000-000000000701', '00000000-0000-0000-0000-000000000611', 8, null, now() - interval '5 hours 59 minutes'),
    ('00000000-0000-0000-0000-000000000712', '00000000-0000-0000-0000-000000000701', '00000000-0000-0000-0000-000000000612', 4, null, now() - interval '5 hours 56 minutes'),
    ('00000000-0000-0000-0000-000000000713', '00000000-0000-0000-0000-000000000701', '00000000-0000-0000-0000-000000000613', 6, null, now() - interval '5 hours 53 minutes')
ON CONFLICT (id) DO NOTHING;

-- Specialists and appointment
INSERT INTO specialist (id, full_name, profession, license_number, is_verified, rating_avg)
VALUES
    ('00000000-0000-0000-0000-000000000801', 'Dr. Elena Petrova', 'psychologist', 'PSY-77-123456', true, 4.80)
ON CONFLICT (id) DO NOTHING;

INSERT INTO specialist_location (
    id, specialist_id, address_line, city, latitude, longitude, consultation_price, currency, is_active
)
VALUES
    ('00000000-0000-0000-0000-000000000811', '00000000-0000-0000-0000-000000000801', 'Lenina st. 10, office 5', 'Voronezh', 51.661500, 39.200200, 2500.00, 'RUB', true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO appointment (id, user_id, specialist_id, location_id, start_at, end_at, status, created_at)
VALUES
    (
        '00000000-0000-0000-0000-000000000901',
        '00000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000801',
        '00000000-0000-0000-0000-000000000811',
        now() + interval '2 days',
        now() + interval '2 days 1 hour',
        'confirmed',
        now()
    )
ON CONFLICT (id) DO NOTHING;

-- Admin features
INSERT INTO moderation_case (id, chat_id, message_id, reason, status, opened_by_admin_user_id, opened_at, closed_at)
VALUES
    (
        '00000000-0000-0000-0000-000000001001',
        '00000000-0000-0000-0000-000000000201',
        '00000000-0000-0000-0000-000000000303',
        'High-risk wording detected in user message.',
        'in_review',
        '00000000-0000-0000-0000-000000000001',
        now() - interval '2 hours',
        null
    )
ON CONFLICT (id) DO NOTHING;

INSERT INTO site_content (
    id, content_type, slug, title, body, is_published, updated_by_admin_user_id, updated_at
)
VALUES
    (
        '00000000-0000-0000-0000-000000001101',
        'announcement',
        'service-safety-notice',
        'Service Safety Notice',
        'This service provides preliminary support and is not a replacement for emergency medical care.',
        true,
        '00000000-0000-0000-0000-000000000001',
        now()
    ),
    (
        '00000000-0000-0000-0000-000000001102',
        'faq',
        'how-private-is-my-data',
        'How private is my data?',
        'We process personal data according to policy and restrict admin access by role.',
        true,
        '00000000-0000-0000-0000-000000000001',
        now()
    )
ON CONFLICT (id) DO NOTHING;

COMMIT;
