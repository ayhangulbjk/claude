from flask import Blueprint, render_template, request, jsonify
from app.services.llm_service import LLMService
from app.services.oracle_service import OracleService
from app.services.query_mapper import QueryMapper

main_bp = Blueprint('main', __name__)

llm_service = LLMService()
oracle_service = OracleService()
query_mapper = QueryMapper()


@main_bp.route('/')
def index():
    return render_template('index.html')


@main_bp.route('/api/ask', methods=['POST'])
def ask():
    try:
        data = request.get_json()
        question = data.get('question', '').strip()

        if not question:
            return jsonify({'error': 'Soru boş olamaz'}), 400

        # Step 1: Analyze question with LLM to detect intent
        intent_result = llm_service.analyze_question(question)

        if not intent_result.get('success'):
            return jsonify({
                'answer': 'Sorunuzu anlayamadım. Lütfen Oracle EBS ile ilgili bir soru sorun.',
                'intent': 'unknown',
                'query_executed': False
            })

        intent = intent_result.get('intent', 'general')
        entities = intent_result.get('entities', {})

        # Step 2: Map intent to SQL query
        query_info = query_mapper.get_query(intent, entities)

        db_result = None
        if query_info:
            # Step 3: Execute Oracle query
            db_result = oracle_service.execute_query(
                query_info['query'],
                query_info.get('params', {})
            )

        # Step 4: Format response with LLM
        response = llm_service.format_response(question, intent, db_result)

        return jsonify({
            'answer': response,
            'intent': intent,
            'query_executed': db_result is not None,
            'row_count': len(db_result.get('data', [])) if db_result else 0
        })

    except Exception as e:
        return jsonify({
            'error': f'Bir hata oluştu: {str(e)}',
            'answer': 'İsteğiniz işlenirken bir hata oluştu. Lütfen tekrar deneyin.'
        }), 500


@main_bp.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    db_status = oracle_service.test_connection()
    return jsonify({
        'status': 'healthy',
        'database': 'connected' if db_status else 'disconnected',
        'llm': 'configured' if llm_service.is_configured() else 'not configured'
    })
