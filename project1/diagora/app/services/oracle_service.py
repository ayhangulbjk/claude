import os


class OracleService:
    def __init__(self):
        self._connection = None

    def _get_connection(self):
        """Get Oracle database connection"""
        try:
            import cx_Oracle

            host = os.getenv('ORACLE_HOST')
            port = os.getenv('ORACLE_PORT', '1521')
            service = os.getenv('ORACLE_SERVICE_NAME')
            user = os.getenv('ORACLE_USER')
            password = os.getenv('ORACLE_PASSWORD')

            if not all([host, service, user, password]):
                return None

            dsn = cx_Oracle.makedsn(host, port, service_name=service)
            connection = cx_Oracle.connect(user, password, dsn)
            return connection

        except ImportError:
            print("cx_Oracle not installed. Running in demo mode.")
            return None
        except Exception as e:
            print(f"Oracle connection error: {e}")
            return None

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            conn = self._get_connection()
            if conn:
                conn.close()
                return True
            return False
        except Exception:
            return False

    def execute_query(self, query: str, params: dict = None) -> dict:
        """Execute SQL query and return results"""
        connection = self._get_connection()

        if not connection:
            # Return demo data when no connection
            return self._get_demo_data(query)

        try:
            cursor = connection.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            data = cursor.fetchall()

            cursor.close()
            connection.close()

            return {
                'success': True,
                'columns': columns,
                'data': data,
                'row_count': len(data)
            }

        except Exception as e:
            if connection:
                connection.close()
            return {
                'success': False,
                'error': str(e),
                'columns': [],
                'data': []
            }

    def _get_demo_data(self, query: str) -> dict:
        """Return demo data when no database connection"""
        query_lower = query.lower()

        if 'fnd_concurrent_queues' in query_lower:
            return {
                'success': True,
                'columns': ['CONCURRENT_QUEUE_NAME', 'RUNNING_PROCESSES', 'MAX_PROCESSES', 'ENABLED_FLAG'],
                'data': [
                    ('Standard Manager', 10, 20, 'Y'),
                    ('Conflict Resolution Manager', 1, 1, 'Y'),
                    ('Scheduler', 1, 1, 'Y'),
                    ('Workflow Mailer', 2, 5, 'Y'),
                    ('Output Post Processor', 3, 10, 'Y')
                ],
                'row_count': 5,
                'demo': True
            }

        elif 'wf_items' in query_lower:
            return {
                'success': True,
                'columns': ['ITEM_TYPE', 'ITEM_KEY', 'BEGIN_DATE', 'END_DATE', 'ROOT_ACTIVITY'],
                'data': [
                    ('OEOL', '12345', '2024-01-15', None, 'ORDER_LINE'),
                    ('POAPPRV', '67890', '2024-01-14', None, 'PO_APPROVAL'),
                    ('REQAPPRV', '11111', '2024-01-10', '2024-01-11', 'REQ_APPROVAL')
                ],
                'row_count': 3,
                'demo': True
            }

        elif 'dba_objects' in query_lower and 'invalid' in query_lower:
            return {
                'success': True,
                'columns': ['OWNER', 'OBJECT_NAME', 'OBJECT_TYPE', 'STATUS'],
                'data': [
                    ('APPS', 'XX_CUSTOM_PKG', 'PACKAGE BODY', 'INVALID'),
                    ('APPS', 'XX_TEST_VIEW', 'VIEW', 'INVALID')
                ],
                'row_count': 2,
                'demo': True
            }

        elif 'tablespace' in query_lower or 'dba_tablespace' in query_lower:
            return {
                'success': True,
                'columns': ['TABLESPACE_NAME', 'USED_PERCENT', 'USED_GB', 'MAX_GB'],
                'data': [
                    ('APPS_TS_TX_DATA', 75.5, 150.2, 200),
                    ('APPS_TS_TX_IDX', 68.3, 102.5, 150),
                    ('APPS_TS_MEDIA', 45.0, 45.0, 100),
                    ('SYSTEM', 82.1, 8.2, 10),
                    ('SYSAUX', 71.0, 14.2, 20)
                ],
                'row_count': 5,
                'demo': True
            }

        else:
            return {
                'success': True,
                'columns': ['INFO'],
                'data': [('Demo mode - no database connection',)],
                'row_count': 1,
                'demo': True
            }
