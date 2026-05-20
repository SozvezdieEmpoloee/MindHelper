from dataclasses import dataclass
import re


class SafetyRiskLevel:
    LOW = "low"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


ASQ_QUESTIONS = {
    1: "За последние несколько недель вам хотелось, чтобы вы были мертвы?",
    2: "За последние несколько недель вам казалось, что вам или вашей семье было бы лучше, если бы вас не было?",
    3: "За последнюю неделю у вас появлялись мысли о том, чтобы покончить с собой?",
    4: "Были ли у вас когда-либо попытки покончить с собой?",
    5: "Есть ли у вас мысли о том, чтобы покончить с собой прямо сейчас?",
}

YES_ANSWERS = {"да", "ага", "угу", "есть", "yes", "y"}
NO_ANSWERS = {"нет", "неа", "нету", "no", "n"}

CRITICAL_PATTERNS = (
    r"\b(убью себя|покончу с собой|суицид)\b",
    r"\b(не хочу жить|хочу умереть)\b",
    r"\b(прямо сейчас|сегодня|этой ночью).*(убью себя|покончу с собой|наврежу себе)\b",
    r"\b(есть план|уже подготовил|уже подготовила).*(умереть|покончить с собой)\b",
    r"\b(kill myself|suicide)\b",
    r"\b(i do not want to live|i want to die)\b",
    r"\b(right now|tonight|today).*(kill myself|harm myself)\b",
    r"\b(i have a plan|already prepared).*(die|kill myself)\b",
)

SELF_REFERENCE_PATTERNS = (
    r"\b(я|мне|меня|мной|сам|сама|себя|с собой|для себя)\b",
)

THIRD_PARTY_CONTEXT_PATTERNS = (
    r"\b(он|она|они|друг|подруга|брат|сестра|мама|папа|герой|персонаж|кто-то другой|в фильме|в книге|новость|новости)\b",
)

SUICIDE_IDEATION_PATTERNS = (
    r"\b(мысли о смерти|мысли о самоубийстве|мысли о суициде)\b",
    r"\b(думаю о самоубийстве|думаю о суициде|думаю умереть)\b",
    r"\b(не хочу жить|жить не хочу|хочу умереть|хочу сдохнуть)\b",
    r"\b(лучше бы меня не было|семье было бы лучше без меня)\b",
    r"\b(хочу исчезнуть|лучше исчезнуть|не вижу смысла жить|не просыпаться)\b",
    r"\b(как можно было бы умереть|как бы умереть)\b",
    r"\b(закончить с собой|причинить себе вред|уйти совсем)\b",
    r"\b(thoughts of suicide|thoughts about killing myself|wish i were dead)\b",
    r"\b(better off without me|do not see a reason to live)\b",
)

SELF_HARM_METHOD_PATTERNS = (
    r"\b(под поезд|на рельс\w*|поезд.*переехал|переехал поезд)\b",
    r"\b(прыгну|спрыгну).*(с крыши|с моста|из окна)\b",
    r"\b(шагну|полезу|брошусь).*(с крыши|с моста|из окна|под поезд|под электричк\w*|под машину)\b",
    r"\b(повешусь|петл\w* на шею|веревк\w* на шею)\b",
    r"\b(вскрою вены|порежу себя|резать себя|лезвием по рукам)\b",
    r"\b(выпью все таблетки|напьюсь таблеток|передоз\w*)\b",
    r"\b(утоплюсь|брошусь под машину|прыгну под поезд)\b",
    r"\b(go under a train|jump off a roof|jump from a bridge|overdose|hang myself|cut my wrists)\b",
)

INTENT_PATTERNS = (
    r"\b(пойду|собираюсь|планирую|намерен|намерена|решил|решила|хочу)\b",
    r"\b(сделаю это|доведу до конца|не передумаю)\b",
    r"\b(i am going to|i plan to|i am about to|i want to)\b",
)

IMMEDIACY_PATTERNS = (
    r"\b(прямо сейчас|сейчас|сегодня|этой ночью|вечером|в ближайшее время|скоро)\b",
    r"\b(right now|today|tonight|soon|in a moment)\b",
)

PREPARATION_PATTERNS = (
    r"\b(уже подготовил|уже подготовила|подготовил всё|подготовила всё|собрал таблетки|собрала таблетки|подготовил таблетки|подготовила таблетки)\b",
    r"\b(выбрал место|выбрала место|написал записку|написала записку|написал прощальное сообщение|написала прощальное сообщение|попрощался|попрощалась)\b",
    r"\b(already prepared|picked a place|wrote a note|said goodbye)\b",
)

HIGH_PATTERNS = (
    r"\b(мысли о смерти|мысли о самоубийстве|мысли о суициде)\b",
    r"\b(навредить себе|самоповреждени)\b",
    r"\b(лучше бы меня не было|семье было бы лучше без меня)\b",
    r"\b(thoughts of suicide|thoughts about killing myself|harm myself)\b",
    r"\b(better off without me|wish i were dead)\b",
)

ELEVATED_PATTERNS = (
    r"\b(сильн\w* тревог\w*|паник\w*|не могу успокоиться)\b",
    r"\b(не сплю|плохо сплю|бессонниц\w*|не могу спать)\b",
    r"\b(безнад[её]жн\w*|нет сил|очень тяжело)\b",
    r"\b(постоянный стресс|выгорание|внутреннее напряжение|сильное напряжение|тревожно|тяжело собраться)\b",
)

UNSAFE_RESPONSE_PATTERNS = (
    r"\b(я ставлю вам диагноз|это точно диагноз)\b",
    r"\b(у вас депрессия|у вас биполярное расстройство|у вас паническое расстройство)\b",
    r"\b(начните принимать|вам нужно принимать|пейте)\b.*\b(таблет|антидепрессант|лекарств)\w*",
    r"\b(вам не нужна помощь|никому не говорите|скройте это от близких)\b",
    r"\b(все точно будет хорошо|ничего страшного не происходит)\b",
)

SAFE_POLICY_FALLBACK = (
    "Я не могу ставить диагнозы, назначать лекарства или обещать, что риск отсутствует. "
    "Я могу помочь описать состояние, предложить безопасные следующие шаги и подсказать, где искать помощь."
)


@dataclass(slots=True)
class SafetyAssessment:
    risk_level: str
    risk_score: float
    requires_screening: bool
    immediate_emergency: bool
    matched_rules: list[str]


@dataclass(slots=True)
class SafetyFeatureSignals:
    self_reference: list[str]
    third_party_context: list[str]
    ideation: list[str]
    method: list[str]
    intent: list[str]
    immediacy: list[str]
    preparation: list[str]


SELF_REFERENCE_STEMS = ("я", "мне", "меня", "себя", "сам", "сама", "собой", "мой", "моя")
THIRD_PARTY_STEMS = ("друг", "подруг", "брат", "сестр", "мама", "папа", "геро", "персонаж", "фильм", "книга", "новост", "человек")
IDEATION_STEMS = (
    "самоуб",
    "суицид",
    "умер",
    "сдох",
    "исчез",
    "не просып",
    "не хочу жить",
    "без меня",
    "закончить с собой",
    "причинить себе вред",
    "уйти совсем",
)
METHOD_STEMS = (
    "рельс",
    "поезд",
    "электрич",
    "крыш",
    "мост",
    "окн",
    "петл",
    "верев",
    "вен",
    "лезви",
    "таблет",
    "передоз",
    "машин",
    "утоп",
)
INTENT_STEMS = ("пойду", "собира", "планир", "намер", "решил", "решила", "хочу", "сделаю", "полезу", "шагну", "брошусь")
IMMEDIACY_STEMS = ("сейчас", "сегодня", "ноч", "вечер", "скоро", "ближайш", "прямо")
PREPARATION_STEMS = ("подготов", "собрал", "собрала", "выбрал", "выбрала", "записк", "прощальн", "попрощ", "отложил")


def _matches_any(text: str, patterns: tuple[str, ...]) -> list[str]:
    return [pattern for pattern in patterns if re.search(pattern, text)]


def _normalize_message(content_text: str) -> str:
    return re.sub(r"\s+", " ", content_text.lower()).strip()


def _has_any(text: str, patterns: tuple[str, ...]) -> bool:
    return bool(_matches_any(text, patterns))


def _match_stems(text: str, stems: tuple[str, ...]) -> list[str]:
    matches: list[str] = []
    for stem in stems:
        if stem in text:
            matches.append(stem)
    return matches


def extract_safety_features(content_text: str) -> SafetyFeatureSignals:
    normalized = _normalize_message(content_text)
    return SafetyFeatureSignals(
        self_reference=_match_stems(normalized, SELF_REFERENCE_STEMS),
        third_party_context=_match_stems(normalized, THIRD_PARTY_STEMS),
        ideation=_match_stems(normalized, IDEATION_STEMS),
        method=_match_stems(normalized, METHOD_STEMS),
        intent=_match_stems(normalized, INTENT_STEMS),
        immediacy=_match_stems(normalized, IMMEDIACY_STEMS),
        preparation=_match_stems(normalized, PREPARATION_STEMS),
    )


def _is_third_party_report(*, normalized: str, features: SafetyFeatureSignals) -> bool:
    if not features.third_party_context:
        return False
    direct_self_risk = (
        bool(features.intent and (features.method or features.preparation or features.ideation))
        or bool(re.search(r"\b(я|себя|сам|сама)\b", normalized) and re.search(r"\b(умереть|покончить|убить себя|навредить себе)\b", normalized))
    )
    return not direct_self_risk


def has_self_harm_signal(content_text: str) -> bool:
    normalized = _normalize_message(content_text)
    self_reference_matches = _matches_any(normalized, SELF_REFERENCE_PATTERNS)
    third_party_matches = _matches_any(normalized, THIRD_PARTY_CONTEXT_PATTERNS)
    method_matches = _matches_any(normalized, SELF_HARM_METHOD_PATTERNS)
    intent_matches = _matches_any(normalized, INTENT_PATTERNS)
    preparation_matches = _matches_any(normalized, PREPARATION_PATTERNS)
    features = extract_safety_features(content_text)
    third_party_report = _is_third_party_report(normalized=normalized, features=features)

    if third_party_report:
        return False

    return any(
        (
            _has_any(normalized, CRITICAL_PATTERNS),
            _has_any(normalized, SUICIDE_IDEATION_PATTERNS),
            _has_any(normalized, HIGH_PATTERNS),
            preparation_matches,
            self_reference_matches and method_matches and not third_party_matches,
            (not third_party_matches) and method_matches and intent_matches,
            bool(features.ideation),
            bool(features.preparation),
            (not features.third_party_context) and bool(features.method) and bool(features.intent),
            bool(features.self_reference) and bool(features.method),
        )
    )


def assess_user_message(content_text: str) -> SafetyAssessment:
    normalized = _normalize_message(content_text)
    features = extract_safety_features(content_text)

    critical_matches = _matches_any(normalized, CRITICAL_PATTERNS)
    self_reference_matches = _matches_any(normalized, SELF_REFERENCE_PATTERNS)
    third_party_matches = _matches_any(normalized, THIRD_PARTY_CONTEXT_PATTERNS)
    ideation_matches = _matches_any(normalized, SUICIDE_IDEATION_PATTERNS)
    method_matches = _matches_any(normalized, SELF_HARM_METHOD_PATTERNS)
    intent_matches = _matches_any(normalized, INTENT_PATTERNS)
    immediacy_matches = _matches_any(normalized, IMMEDIACY_PATTERNS)
    preparation_matches = _matches_any(normalized, PREPARATION_PATTERNS)
    third_party_report = _is_third_party_report(normalized=normalized, features=features)

    if third_party_report:
        critical_matches = []
        ideation_matches = []
        method_matches = []
        preparation_matches = []

    derived_critical_matches: list[str] = []
    if self_reference_matches and method_matches and (intent_matches or immediacy_matches or preparation_matches):
        derived_critical_matches.extend(self_reference_matches)
        derived_critical_matches.extend(method_matches)
        derived_critical_matches.extend(intent_matches or immediacy_matches or preparation_matches)
    if not third_party_matches and method_matches and intent_matches and (immediacy_matches or preparation_matches):
        derived_critical_matches.extend(method_matches)
        derived_critical_matches.extend(intent_matches)
        derived_critical_matches.extend(immediacy_matches or preparation_matches)
    if not third_party_matches and preparation_matches and intent_matches:
        derived_critical_matches.extend(preparation_matches)
        derived_critical_matches.extend(intent_matches)
    if self_reference_matches and preparation_matches and (ideation_matches or method_matches):
        derived_critical_matches.extend(self_reference_matches)
        derived_critical_matches.extend(preparation_matches)
        derived_critical_matches.extend(ideation_matches or method_matches)
    if not features.third_party_context and features.method and features.intent and (features.immediacy or features.preparation):
        derived_critical_matches.extend(features.method)
        derived_critical_matches.extend(features.intent)
        derived_critical_matches.extend(features.immediacy or features.preparation)
    if features.self_reference and features.method and features.preparation:
        derived_critical_matches.extend(features.self_reference)
        derived_critical_matches.extend(features.method)
        derived_critical_matches.extend(features.preparation)
    if features.preparation and features.intent and (features.ideation or features.method) and not features.third_party_context:
        derived_critical_matches.extend(features.preparation)
        derived_critical_matches.extend(features.intent)
        derived_critical_matches.extend(features.ideation or features.method)

    if critical_matches or derived_critical_matches:
        return SafetyAssessment(
            risk_level=SafetyRiskLevel.CRITICAL,
            risk_score=0.98,
            requires_screening=False,
            immediate_emergency=True,
            matched_rules=critical_matches or derived_critical_matches,
        )

    high_matches = _matches_any(normalized, HIGH_PATTERNS)
    if third_party_report:
        high_matches = []
    derived_high_matches: list[str] = []
    if ideation_matches:
        derived_high_matches.extend(ideation_matches)
    if self_reference_matches and method_matches and not third_party_matches:
        derived_high_matches.extend(self_reference_matches)
        derived_high_matches.extend(method_matches)
    if not third_party_matches and method_matches:
        derived_high_matches.extend(method_matches)
    if preparation_matches:
        derived_high_matches.extend(preparation_matches)
    if features.ideation and not third_party_report:
        derived_high_matches.extend(features.ideation)
    if not third_party_report and features.method:
        derived_high_matches.extend(features.method)
    if features.preparation and not third_party_report:
        derived_high_matches.extend(features.preparation)

    if high_matches or derived_high_matches:
        return SafetyAssessment(
            risk_level=SafetyRiskLevel.HIGH,
            risk_score=0.86,
            requires_screening=True,
            immediate_emergency=False,
            matched_rules=high_matches or derived_high_matches,
        )

    elevated_matches = _matches_any(normalized, ELEVATED_PATTERNS)
    if elevated_matches:
        return SafetyAssessment(
            risk_level=SafetyRiskLevel.ELEVATED,
            risk_score=0.62,
            requires_screening=False,
            immediate_emergency=False,
            matched_rules=elevated_matches,
        )

    return SafetyAssessment(
        risk_level=SafetyRiskLevel.LOW,
        risk_score=0.18,
        requires_screening=False,
        immediate_emergency=False,
        matched_rules=[],
    )


def parse_yes_no_answer(content_text: str) -> bool | None:
    normalized = re.sub(r"[^a-zа-яё ]+", " ", content_text.lower()).strip()
    tokens = normalized.split()
    if normalized in YES_ANSWERS or (tokens and tokens[0] in YES_ANSWERS):
        return True
    if normalized in NO_ANSWERS or (tokens and tokens[0] in NO_ANSWERS):
        return False
    return None


def get_asq_question(question_index: int) -> str:
    return ASQ_QUESTIONS[question_index]


def build_asq_prompt(question_index: int) -> str:
    return (
        "Чтобы аккуратно оценить уровень риска, мне нужно задать несколько прямых вопросов.\n\n"
        f"{get_asq_question(question_index)}\n\n"
        'Пожалуйста, ответьте коротко: "да" или "нет".'
    )


def build_asq_repeat_prompt(question_index: int) -> str:
    return (
        "Для этого шага мне нужен короткий ответ «да» или «нет».\n\n"
        f"{get_asq_question(question_index)}"
    )


def build_negative_screen_reply() -> str:
    return (
        "Спасибо, что ответили на вопросы. По этому короткому скринингу признаки немедленного "
        "суицидального риска не подтверждаются. Мы можем продолжить разговор о вашем состоянии, "
        "а если напряжение сохраняется, лучше обсудить его со специалистом очно."
    )


def build_non_acute_positive_reply(resources_text: str) -> str:
    return (
        "Спасибо, что ответили честно. Скрининг показывает, что вам нужна более серьёзная поддержка "
        "и очная оценка состояния специалистом как можно скорее. Пожалуйста, свяжитесь с близким "
        "человеком, не оставайтесь с этим состоянием в одиночку и воспользуйтесь контактами помощи:\n\n"
        f"{resources_text}"
    )


def build_acute_positive_reply(resources_text: str) -> str:
    return (
        "Сейчас важнее всего безопасность. Пожалуйста, не оставайтесь в одиночестве, уберите от себя "
        "опасные предметы и срочно свяжитесь с экстренной помощью или близким человеком рядом.\n\n"
        f"{resources_text}"
    )


def apply_response_policy(content_text: str) -> str:
    normalized = re.sub(r"\s+", " ", content_text.lower()).strip()
    if any(re.search(pattern, normalized) for pattern in UNSAFE_RESPONSE_PATTERNS):
        return SAFE_POLICY_FALLBACK
    return content_text.strip()
