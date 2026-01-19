import os
import json
from openai import AzureOpenAI
from flask import current_app


class LLMService:
    def __init__(self):
        self._client = None
        self._system_prompt = None

    @property
    def client(self):
        if self._client is None:
            endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
            api_key = os.getenv('AZURE_OPENAI_API_KEY')
            api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')

            if endpoint and api_key:
                self._client = AzureOpenAI(
                    azure_endpoint=endpoint,
                    api_key=api_key,
                    api_version=api_version
                )
        return self._client

    @property
    def system_prompt(self):
        if self._system_prompt is None:
            prompt_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'prompts',
                'system_prompt.txt'
            )
            try:
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    self._system_prompt = f.read()
            except FileNotFoundError:
                self._system_prompt = self._get_default_prompt()
        return self._system_prompt

    def _get_default_prompt(self):
        return """Sen Oracle EBS R12.2.9 uzmanı bir asistansın. Kullanıcıların Oracle E-Business Suite hakkındaki sorularını analiz edip,
        uygun veritabanı sorgularını çalıştırarak yanıt veriyorsun.

        Desteklenen kontrol alanları:
        - concurrent_manager: Concurrent Manager durumu ve işleri
        - workflow: Oracle Workflow durumu
        - invalid_objects: Invalid veritabanı objeleri
        - tablespace: Tablespace kullanım durumu
        - general: Genel EBS soruları
        """

    def is_configured(self):
        return self.client is not None

    def analyze_question(self, question: str) -> dict:
        """Analyze user question and detect intent"""
        if not self.client:
            return self._fallback_intent_detection(question)

        try:
            deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4')

            response = self.client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": self._get_intent_prompt()},
                    {"role": "user", "content": question}
                ],
                temperature=0.1,
                max_tokens=500
            )

            content = response.choices[0].message.content
            result = json.loads(content)
            result['success'] = True
            return result

        except Exception as e:
            print(f"LLM intent detection error: {e}")
            return self._fallback_intent_detection(question)

    def _get_intent_prompt(self):
        return """Kullanıcının Oracle EBS sorusunu analiz et ve aşağıdaki JSON formatında yanıt ver:

{
    "intent": "concurrent_manager|workflow|invalid_objects|tablespace|general",
    "entities": {
        "manager_name": "optional - specific manager name if mentioned",
        "schema_name": "optional - specific schema if mentioned",
        "status_filter": "optional - status filter like RUNNING, ERROR, etc."
    },
    "confidence": 0.0-1.0
}

Intent açıklamaları:
- concurrent_manager: Concurrent Manager, concurrent request, job, schedule ile ilgili sorular
- workflow: Oracle Workflow, WF, iş akışı ile ilgili sorular
- invalid_objects: Invalid object, compile, geçersiz obje ile ilgili sorular
- tablespace: Tablespace, disk, alan, storage ile ilgili sorular
- general: Diğer genel EBS soruları

Sadece JSON döndür, başka bir şey yazma."""

    def _fallback_intent_detection(self, question: str) -> dict:
        """Simple keyword-based intent detection as fallback"""
        question_lower = question.lower()

        intents = {
            'concurrent_manager': ['concurrent', 'manager', 'request', 'job', 'schedule', 'fnd_concurrent', 'icm', 'running request'],
            'workflow': ['workflow', 'wf_', 'iş akışı', 'stuck', 'notification'],
            'invalid_objects': ['invalid', 'geçersiz', 'compile', 'dba_objects'],
            'tablespace': ['tablespace', 'disk', 'alan', 'storage', 'space', 'dolu']
        }

        for intent, keywords in intents.items():
            if any(keyword in question_lower for keyword in keywords):
                return {
                    'success': True,
                    'intent': intent,
                    'entities': {},
                    'confidence': 0.7
                }

        return {
            'success': True,
            'intent': 'general',
            'entities': {},
            'confidence': 0.5
        }

    def format_response(self, question: str, intent: str, db_result: dict) -> str:
        """Format database results into natural language response"""
        if not self.client:
            return self._fallback_format_response(intent, db_result)

        try:
            deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4')

            context = f"""Kullanıcı sorusu: {question}
Tespit edilen intent: {intent}
Veritabanı sonucu: {json.dumps(db_result, ensure_ascii=False, default=str) if db_result else 'Sorgu çalıştırılmadı'}"""

            response = self.client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.3,
                max_tokens=1000
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"LLM response formatting error: {e}")
            return self._fallback_format_response(intent, db_result)

    def _fallback_format_response(self, intent: str, db_result: dict) -> str:
        """Simple response formatting as fallback"""
        if not db_result:
            return "Veritabanı sorgusu çalıştırılamadı. Lütfen bağlantı ayarlarını kontrol edin."

        if db_result.get('error'):
            return f"Sorgu hatası: {db_result['error']}"

        data = db_result.get('data', [])
        columns = db_result.get('columns', [])

        if not data:
            return f"{intent} kontrolü tamamlandı. Herhangi bir sorun tespit edilmedi."

        response_lines = [f"**{intent.replace('_', ' ').title()} Sonuçları:**\n"]
        response_lines.append(f"Toplam {len(data)} kayıt bulundu.\n")

        # Show first 10 results
        for i, row in enumerate(data[:10]):
            row_info = " | ".join(f"{col}: {val}" for col, val in zip(columns, row))
            response_lines.append(f"{i+1}. {row_info}")

        if len(data) > 10:
            response_lines.append(f"\n... ve {len(data) - 10} kayıt daha.")

        return "\n".join(response_lines)
