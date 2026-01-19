"""
Oracle EBS R12.2.9 SQL Queries for Diagora
"""

EBS_QUERIES = {
    'concurrent_manager': {
        'name': 'Concurrent Manager Status',
        'description': 'Concurrent Manager durumu ve calisan process sayisi',
        'query': """
            SELECT
                fcq.CONCURRENT_QUEUE_NAME AS manager_name,
                fcq.RUNNING_PROCESSES AS running,
                fcq.MAX_PROCESSES AS max_processes,
                DECODE(fcq.ENABLED_FLAG, 'Y', 'Enabled', 'Disabled') AS status,
                fcq.CONTROL_CODE,
                TO_CHAR(fcq.LAST_UPDATE_DATE, 'DD-MON-YYYY HH24:MI:SS') AS last_update
            FROM
                FND_CONCURRENT_QUEUES fcq,
                FND_APPLICATION fa
            WHERE
                fcq.APPLICATION_ID = fa.APPLICATION_ID
                AND fcq.ENABLED_FLAG = 'Y'
            ORDER BY
                fcq.RUNNING_PROCESSES DESC
        """,
        'params': {}
    },

    'concurrent_requests': {
        'name': 'Running Concurrent Requests',
        'description': 'Calisan ve bekleyen concurrent request listesi',
        'query': """
            SELECT
                fcr.REQUEST_ID,
                fcp.USER_CONCURRENT_PROGRAM_NAME AS program_name,
                fcr.PHASE_CODE,
                fcr.STATUS_CODE,
                fu.USER_NAME AS requested_by,
                TO_CHAR(fcr.REQUEST_DATE, 'DD-MON-YYYY HH24:MI:SS') AS request_date,
                TO_CHAR(fcr.ACTUAL_START_DATE, 'DD-MON-YYYY HH24:MI:SS') AS start_date,
                ROUND((SYSDATE - fcr.ACTUAL_START_DATE) * 24 * 60, 2) AS running_minutes
            FROM
                FND_CONCURRENT_REQUESTS fcr,
                FND_CONCURRENT_PROGRAMS_VL fcp,
                FND_USER fu
            WHERE
                fcr.CONCURRENT_PROGRAM_ID = fcp.CONCURRENT_PROGRAM_ID
                AND fcr.PROGRAM_APPLICATION_ID = fcp.APPLICATION_ID
                AND fcr.REQUESTED_BY = fu.USER_ID
                AND fcr.PHASE_CODE = 'R'
            ORDER BY
                fcr.ACTUAL_START_DATE
        """,
        'params': {}
    },

    'workflow': {
        'name': 'Workflow Status',
        'description': 'Oracle Workflow durumu ve stuck workflow listesi',
        'query': """
            SELECT
                wi.ITEM_TYPE,
                wit.DISPLAY_NAME AS workflow_name,
                COUNT(*) AS item_count,
                SUM(CASE WHEN wi.END_DATE IS NULL THEN 1 ELSE 0 END) AS active_count,
                SUM(CASE WHEN wi.END_DATE IS NULL AND wi.BEGIN_DATE < SYSDATE - 7 THEN 1 ELSE 0 END) AS stuck_count,
                MIN(wi.BEGIN_DATE) AS oldest_item
            FROM
                WF_ITEMS wi,
                WF_ITEM_TYPES_TL wit
            WHERE
                wi.ITEM_TYPE = wit.NAME
                AND wit.LANGUAGE = 'US'
            GROUP BY
                wi.ITEM_TYPE,
                wit.DISPLAY_NAME
            HAVING
                SUM(CASE WHEN wi.END_DATE IS NULL THEN 1 ELSE 0 END) > 0
            ORDER BY
                stuck_count DESC
        """,
        'params': {}
    },

    'workflow_stuck': {
        'name': 'Stuck Workflows Detail',
        'description': 'Stuck workflow detaylari',
        'query': """
            SELECT
                wi.ITEM_TYPE,
                wi.ITEM_KEY,
                wit.DISPLAY_NAME AS workflow_name,
                wi.USER_KEY,
                TO_CHAR(wi.BEGIN_DATE, 'DD-MON-YYYY HH24:MI:SS') AS begin_date,
                ROUND(SYSDATE - wi.BEGIN_DATE) AS days_stuck,
                wi.ROOT_ACTIVITY
            FROM
                WF_ITEMS wi,
                WF_ITEM_TYPES_TL wit
            WHERE
                wi.ITEM_TYPE = wit.NAME
                AND wit.LANGUAGE = 'US'
                AND wi.END_DATE IS NULL
                AND wi.BEGIN_DATE < SYSDATE - 7
            ORDER BY
                wi.BEGIN_DATE
            FETCH FIRST 100 ROWS ONLY
        """,
        'params': {}
    },

    'invalid_objects': {
        'name': 'Invalid Database Objects',
        'description': 'Invalid durumundaki veritabani objeleri',
        'query': """
            SELECT
                owner,
                object_name,
                object_type,
                status,
                TO_CHAR(created, 'DD-MON-YYYY') AS created_date,
                TO_CHAR(last_ddl_time, 'DD-MON-YYYY HH24:MI:SS') AS last_ddl
            FROM
                DBA_OBJECTS
            WHERE
                status = 'INVALID'
                AND owner IN ('APPS', 'AR', 'AP', 'GL', 'INV', 'ONT', 'PO', 'HR')
            ORDER BY
                owner,
                object_type,
                object_name
        """,
        'params': {}
    },

    'tablespace': {
        'name': 'Tablespace Usage',
        'description': 'Tablespace doluluk durumu',
        'query': """
            SELECT
                tablespace_name,
                ROUND(used_space * 8192 / 1024 / 1024 / 1024, 2) AS used_gb,
                ROUND(tablespace_size * 8192 / 1024 / 1024 / 1024, 2) AS total_gb,
                ROUND(used_percent, 2) AS used_percent,
                CASE
                    WHEN used_percent >= 90 THEN 'CRITICAL'
                    WHEN used_percent >= 80 THEN 'WARNING'
                    ELSE 'OK'
                END AS status
            FROM
                DBA_TABLESPACE_USAGE_METRICS
            ORDER BY
                used_percent DESC
        """,
        'params': {}
    },

    'tablespace_detail': {
        'name': 'Tablespace Detail',
        'description': 'Tablespace detayli bilgi',
        'query': """
            SELECT
                df.TABLESPACE_NAME,
                ROUND(SUM(df.BYTES) / 1024 / 1024 / 1024, 2) AS total_gb,
                ROUND(SUM(df.BYTES - NVL(fs.BYTES, 0)) / 1024 / 1024 / 1024, 2) AS used_gb,
                ROUND(NVL(SUM(fs.BYTES), 0) / 1024 / 1024 / 1024, 2) AS free_gb,
                ROUND((SUM(df.BYTES - NVL(fs.BYTES, 0)) / SUM(df.BYTES)) * 100, 2) AS used_pct,
                COUNT(df.FILE_ID) AS datafile_count
            FROM
                DBA_DATA_FILES df,
                (SELECT TABLESPACE_NAME, FILE_ID, SUM(BYTES) AS BYTES
                 FROM DBA_FREE_SPACE
                 GROUP BY TABLESPACE_NAME, FILE_ID) fs
            WHERE
                df.TABLESPACE_NAME = fs.TABLESPACE_NAME(+)
                AND df.FILE_ID = fs.FILE_ID(+)
            GROUP BY
                df.TABLESPACE_NAME
            ORDER BY
                used_pct DESC
        """,
        'params': {}
    },

    'alerts': {
        'name': 'Active Alerts',
        'description': 'Aktif sistem alertleri',
        'query': """
            SELECT
                alert_name,
                application_name,
                enabled_flag,
                frequency_type,
                TO_CHAR(start_date_active, 'DD-MON-YYYY') AS start_date,
                TO_CHAR(end_date_active, 'DD-MON-YYYY') AS end_date
            FROM
                ALR_ALERTS_V
            WHERE
                enabled_flag = 'Y'
                AND (end_date_active IS NULL OR end_date_active > SYSDATE)
            ORDER BY
                application_name,
                alert_name
        """,
        'params': {}
    },

    'profile_options': {
        'name': 'Profile Options',
        'description': 'Sistem profile option degerleri',
        'query': """
            SELECT
                fpo.PROFILE_OPTION_NAME,
                fpot.USER_PROFILE_OPTION_NAME,
                fpov.PROFILE_OPTION_VALUE,
                fpov.LEVEL_ID,
                DECODE(fpov.LEVEL_ID,
                    10001, 'Site',
                    10002, 'Application',
                    10003, 'Responsibility',
                    10004, 'User',
                    'Unknown') AS level_name
            FROM
                FND_PROFILE_OPTIONS fpo,
                FND_PROFILE_OPTIONS_TL fpot,
                FND_PROFILE_OPTION_VALUES fpov
            WHERE
                fpo.PROFILE_OPTION_ID = fpot.PROFILE_OPTION_ID
                AND fpo.PROFILE_OPTION_NAME = fpov.PROFILE_OPTION_NAME
                AND fpot.LANGUAGE = 'US'
                AND fpov.LEVEL_ID = 10001
            ORDER BY
                fpo.PROFILE_OPTION_NAME
        """,
        'params': {}
    },

    'user_sessions': {
        'name': 'Active User Sessions',
        'description': 'Aktif kullanici oturumlari',
        'query': """
            SELECT
                fu.USER_NAME,
                fr.RESPONSIBILITY_NAME,
                fls.START_TIME,
                ROUND((SYSDATE - fls.START_TIME) * 24, 2) AS session_hours,
                fls.LOGIN_ID
            FROM
                FND_LOGINS fl,
                FND_LOGIN_RESP_FORMS fls,
                FND_USER fu,
                FND_RESPONSIBILITY_TL fr
            WHERE
                fl.LOGIN_ID = fls.LOGIN_ID
                AND fl.USER_ID = fu.USER_ID
                AND fls.RESPONSIBILITY_ID = fr.RESPONSIBILITY_ID
                AND fls.END_TIME IS NULL
                AND fl.END_TIME IS NULL
            ORDER BY
                fls.START_TIME DESC
            FETCH FIRST 50 ROWS ONLY
        """,
        'params': {}
    }
}
