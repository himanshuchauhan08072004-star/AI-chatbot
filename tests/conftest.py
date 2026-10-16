import os
import tempfile

# Must be set before app modules are imported
os.environ["CHAT_DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ.pop("ANTHROPIC_API_KEY", None)
