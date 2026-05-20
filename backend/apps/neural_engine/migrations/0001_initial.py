import django.db.models.deletion
import uuid
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("chat", "0003_crisisevent_screening_fields"),
        ("platform_ops", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SafetyAuditLog",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("risk_level", models.CharField(choices=[("low", "Low"), ("elevated", "Elevated"), ("high", "High"), ("critical", "Critical")], max_length=16)),
                ("route_code", models.CharField(choices=[("low_support", "Low support"), ("elevated_support", "Elevated support"), ("immediate_emergency", "Immediate emergency"), ("start_screening", "Start screening"), ("repeat_screening", "Repeat screening"), ("screening_next_question", "Screening next question"), ("screening_negative", "Screening negative"), ("screening_high", "Screening high"), ("screening_critical", "Screening critical")], max_length=64)),
                ("escalation_action", models.CharField(choices=[("none", "None"), ("offer_specialist", "Offer specialist"), ("start_asq", "Start ASQ"), ("urgent_specialist", "Urgent specialist"), ("emergency_contacts", "Emergency contacts")], max_length=64)),
                ("human_review_flag", models.BooleanField(default=False)),
                ("generated_with_model", models.BooleanField(default=False)),
                ("policy_intervened", models.BooleanField(default=False)),
                ("model_provider", models.CharField(blank=True, max_length=64)),
                ("matched_rules", models.JSONField(blank=True, default=list)),
                ("action_note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("chat", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="safety_audit_logs", to="chat.userchat")),
                ("crisis_event", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="safety_audit_logs", to="chat.crisisevent")),
                ("message", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="safety_audit_logs", to="chat.chatmessage")),
                ("model_version", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="safety_audit_logs", to="platform_ops.neuralmodelversion")),
            ],
            options={
                "db_table": "safety_audit_log",
                "ordering": ("-created_at",),
            },
        ),
    ]
