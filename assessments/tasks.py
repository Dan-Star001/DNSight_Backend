"""
Assessments — Celery Background Tasks
========================================
Defines asynchronous tasks offloaded from the request-response cycle.

Tasks:
    generate_ai_treatment_suggestion — Calls the OpenRouter LLM API to produce
    a clinical treatment recommendation and writes it back to the Assessment.
"""

import requests
from celery import shared_task
from django.conf import settings
from google import genai
from google.genai import types

MAX_RETRIES = 3
RETRY_BACKOFF = True


@shared_task(
    bind=True,
    max_retries=MAX_RETRIES,
    default_retry_delay=10,
    retry_backoff=RETRY_BACKOFF,
    retry_backoff_max=120,
    acks_late=True,
)
def generate_ai_treatment_suggestion(self, assessment_id: int):
    """Fetch the Assessment, build a clinical context prompt, call the
    OpenRouter LLM API, and persist the generated suggestion.

    Args:
        assessment_id: Primary key of the Assessment to enrich.
    """
    from assessments.models import Assessment  # Late import to avoid circular deps

    # 1. Load the assessment with related patient data (single query)
    try:
        assessment = (
            Assessment.objects
            .select_related('patient', 'doctor')
            .get(id=assessment_id)
        )
    except Assessment.DoesNotExist:
        return

    # 2. Build the clinical context prompt
    patient = assessment.patient
    clinical = assessment.clinical_data

    prompt = (
        f"You are a specialist diabetologist AI assistant. Based on the following "
        f"clinical data for a patient, provide a detailed, evidence-based treatment "
        f"suggestion for managing diabetic neuropathy risk.\n\n"
        f"Patient: {patient.first_name} {patient.last_name}, "
        f"Age: {clinical.get('AGE', 'N/A')}, "
        f"Gender: {patient.gender}\n"
        f"BMI: {clinical.get('BMI', 'N/A')}, "
        f"HbA1c: {clinical.get('HbA1c', 'N/A')}%, "
        f"Systolic BP: {clinical.get('SP', 'N/A')}, "
        f"Diastolic BP: {clinical.get('BP', 'N/A')}\n"
        f"Fasting Plasma Sugar: {clinical.get('FPS', 'N/A')}, "
        f"Postprandial Sugar: {clinical.get('PPS', 'N/A')}\n"
        f"Family History of Diabetes: {'Yes' if clinical.get('FAMILY_HO') else 'No'}, "
        f"Smoking: {'Yes' if clinical.get('SMOKING') else 'No'}\n"
        f"Diabetes Duration: {clinical.get('AGE', 0) - clinical.get('ONSET_AGE', 0):.0f} years\n\n"
        f"Predicted Risk Score (Fusion): {assessment.risk_score}/100 ({assessment.risk_level})\n"
        f"KNN Model Score: {assessment.knn_score}/100\n"
        f"GNB Model Score: {assessment.gnb_score}/100\n"
        f"Confidence: {assessment.prediction_confidence:.1%}\n\n"
        f"Please provide a single combined list covering:\n"
        f"Key risk factors, lifestyle modifications, pharmacological interventions, "
        f"follow-up schedule, and screening tests. Do not use headings."
    )

    # 3. Call Google Generative AI using the new SDK
    model_name = getattr(settings, 'LLM_MODEL', 'gemini-2.0-flash')
    try:
        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=(
                    'You are a medical AI assistant specializing in diabetic '
                    'neuropathy. Provide professional, evidence-based treatment '
                    'suggestions. Be concise but thorough. '
                    'CRITICAL INSTRUCTION: Do NOT use any Markdown formatting (no asterisks, no hash symbols, no bold, no italics). Use ONLY plain text. Format your response strictly as a series of short, single-sentence bullet points separated by newlines. Start each bullet point with a hyphen (-). '
                    'ALWAYS start your response with: '
                    '"I am an AI, not a doctor. Consult a professional for advice."'
                ),
                temperature=0.4,
                max_output_tokens=1024,
            )
        )
        
        suggestion = response.text
        
        if not suggestion:
            suggestion = "Error: The AI model returned an empty response."

    except Exception as exc:
        suggestion = f"Failed to generate AI suggestion. Error: {str(exc)}"

    # 4. Persist the suggestion — atomic field update
    Assessment.objects.filter(id=assessment_id).update(
        ai_treatment_suggestion=suggestion,
    )
