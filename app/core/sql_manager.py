import os
import sqlite3
from typing import Dict, Any, List

class LogSQLManager:
    """
    Dedicated Relational Storage Layer mapped directly to SSMS [BICS].[dbo].[Job] schema.
    Handles SQL initialization and parameterized table lookups independently.
    """
    def __init__(self, db_dir: str = os.path.join("data", "vector_store"), db_name: str = "job_registry.db"):
        self.db_dir = db_dir
        self.db_path = os.path.join(self.db_dir, db_name)
        os.makedirs(self.db_dir, exist_ok=True)
        self._init_sql_database()

    def _init_sql_database(self):
        """Initializes a local database to perfectly mimic the SSMS production table layout."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build table matching your exact production schema column naming selections
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Job (
                ID TEXT PRIMARY KEY,
                CreateDate TEXT,
                CreateLogin TEXT,
                CreateUser TEXT,
                UpdateDate TEXT,
                UpdateLogin TEXT,
                UpdateUser TEXT,
                Name TEXT,
                Description TEXT,
                JobTypeID INTEGER,
                JobGroupID INTEGER,
                Priority INTEGER,
                Enabled INTEGER,
                OldJobID TEXT,
                Author TEXT,
                CompanyID INTEGER,
                DataSetID INTEGER,
                SourceTypeID INTEGER
            )
        """)
        
        # Populate realistic mock data fitting your test job identifiers
        mock_jobs = [
            ("1234", "2026-08-16 12:00:00", "srv_ops", "Automator", "2026-08-16 14:00:00", "srv_ops", "Automator", 
             "PaymentGatewaySync", "Core microservice financial token ledger settlement sync job", 1, 10, 1, 1, "OLD_J_99", "Faysal", 100, 500, 2),
            ("55201", "2026-08-16 11:30:00", "srv_ops", "Dispatcher", "2026-08-16 11:45:00", "srv_ops", "Dispatcher", 
             "PayloadIngestionDispatcher", "Ingests raw event telemetry webhooks into message clusters", 2, 10, 2, 1, None, "Admin", 100, 501, 2),
            ("99482", "2026-08-16 10:00:00", "srv_ops", "Scheduler", "2026-08-16 10:15:00", "srv_ops", "Scheduler", 
             "BulkMatrixAggregationJob", "Aggregates transactional database matrix entries over storage volumes", 1, 12, 3, 1, "OLD_J_44", "DevTeam", 102, 600, 1)
        ]
        
        cursor.executemany("""
            INSERT OR REPLACE INTO Job (
                ID, CreateDate, CreateLogin, CreateUser, UpdateDate, UpdateLogin, UpdateUser, 
                Name, Description, JobTypeID, JobGroupID, Priority, Enabled, OldJobID, Author, 
                CompanyID, DataSetID, SourceTypeID
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, mock_jobs)
        
        conn.commit()
        conn.close()

    def query_sql_job_details(self, job_id: str) -> Dict[str, Any]:
        """Executes a parameterized SQL query lookup against the persistent local database file."""
        if not job_id:
            return {}
            
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM Job WHERE ID = ?", (str(job_id),))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return {}

    def format_sql_audit_report(self, job_id: str, sql_data: Dict[str, Any]) -> str:
        """Generates an explicit metadata report string displaying the SSMS table record values."""
        return (
            f"## 🗄️ SSMS Database Record: [BICS].[dbo].[Job]\n"
            f"Surfaced matching record details for **ID: {job_id}**\n\n"
            f"| Database Column | Registered Record Value |\n"
            f"| :--- | :--- |\n"
            f"| **ID** | `{sql_data.get('ID')}` |\n"
            f"| **Name** | **{sql_data.get('Name')}** |\n"
            f"| **Description** | *{sql_data.get('Description')}* |\n"
            f"| **Author** | `{sql_data.get('Author')}` |\n"
            f"| **CreateDate** | `{sql_data.get('CreateDate')}` |\n"
            f"| **CreateUser** | `{sql_data.get('CreateUser')}` |\n"
            f"| **UpdateDate** | `{sql_data.get('UpdateDate')}` |\n"
            f"| **Priority** | `{sql_data.get('Priority')}` |\n"
            f"| **Enabled** | `{sql_data.get('Enabled')}` (True) |\n"
            f"| **JobTypeID** | `{sql_data.get('JobTypeID')}` |\n"
            f"| **JobGroupID** | `{sql_data.get('JobGroupID')}` |\n"
            f"| **OldJobID** | `{sql_data.get('OldJobID') or 'NULL'}` |\n"
            f"| **CompanyID** | `{sql_data.get('CompanyID')}` |\n"
            f"| **DataSetID** | `{sql_data.get('DataSetID')}` |\n"
            f"| **SourceTypeID** | `{sql_data.get('SourceTypeID')}` |\n"
        )
