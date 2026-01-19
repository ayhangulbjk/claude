from queries.ebs_queries import EBS_QUERIES


class QueryMapper:
    def __init__(self):
        self.queries = EBS_QUERIES

    def get_query(self, intent: str, entities: dict = None) -> dict:
        """Map intent to appropriate SQL query"""
        if intent not in self.queries:
            return None

        query_info = self.queries[intent].copy()

        # Handle dynamic parameters based on entities
        if entities:
            if entities.get('manager_name') and intent == 'concurrent_manager':
                query_info['query'] = self._add_manager_filter(
                    query_info['query'],
                    entities['manager_name']
                )
                query_info['params'] = {'manager_name': f"%{entities['manager_name']}%"}

            if entities.get('schema_name') and intent == 'invalid_objects':
                query_info['query'] = self._add_schema_filter(
                    query_info['query'],
                    entities['schema_name']
                )
                query_info['params'] = {'owner': entities['schema_name'].upper()}

            if entities.get('status_filter') and intent == 'workflow':
                query_info['query'] = self._add_workflow_status_filter(
                    query_info['query'],
                    entities['status_filter']
                )

        return query_info

    def _add_manager_filter(self, query: str, manager_name: str) -> str:
        """Add manager name filter to query"""
        if 'WHERE' in query.upper():
            return query.replace('WHERE', f"WHERE UPPER(fcq.CONCURRENT_QUEUE_NAME) LIKE UPPER(:manager_name) AND ")
        return query

    def _add_schema_filter(self, query: str, schema_name: str) -> str:
        """Add schema filter to query"""
        if 'WHERE' in query.upper():
            return query.replace('WHERE', f"WHERE owner = :owner AND ")
        return query

    def _add_workflow_status_filter(self, query: str, status: str) -> str:
        """Add workflow status filter"""
        status_upper = status.upper()
        if status_upper == 'STUCK':
            return query + " AND wi.end_date IS NULL AND wi.begin_date < SYSDATE - 7"
        elif status_upper == 'ACTIVE':
            return query + " AND wi.end_date IS NULL"
        elif status_upper == 'COMPLETED':
            return query + " AND wi.end_date IS NOT NULL"
        return query

    def get_available_intents(self) -> list:
        """Return list of supported intents"""
        return list(self.queries.keys())

    def get_query_description(self, intent: str) -> str:
        """Return description of what the query checks"""
        descriptions = {
            'concurrent_manager': 'Concurrent Manager durumunu ve çalışan işleri kontrol eder',
            'workflow': 'Oracle Workflow durumunu ve bekleyen iş akışlarını kontrol eder',
            'invalid_objects': 'Veritabanındaki geçersiz (invalid) objeleri listeler',
            'tablespace': 'Tablespace kullanım durumunu ve doluluk oranlarını kontrol eder',
            'concurrent_requests': 'Çalışan ve bekleyen concurrent request\'leri listeler',
            'alerts': 'Aktif alertleri ve uyarıları kontrol eder'
        }
        return descriptions.get(intent, 'Genel EBS kontrolü')
