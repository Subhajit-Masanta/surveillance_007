"""Test harness: runs the REAL client pointed at the test server."""
import edu_admin
edu_admin.SERVER_HOSTS = ['127.0.0.1']
edu_admin.SERVER_PORT = 5556
edu_admin.run_client()
