import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
 
load_dotenv()
def get_engine():
    url = (
        f"postgresql+psycopg2://{os.getenv('PG_USER')}:{os.getenv('PG_PASSWORD')}"
        f"@{os.getenv('PG_HOST', 'localhost')}:{os.getenv('PG_PORT', '5432')}"
        f"/{os.getenv('PG_DB', 'kedaibuku')}"
    )
    return create_engine(url)
