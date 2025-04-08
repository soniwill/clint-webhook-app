import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configurações do banco de dados
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///leads.db')
    
    # Configurações do Clint CRM
    CLINT_CRM_WEBHOOK_URL = os.getenv('CLINT_CRM_WEBHOOK_URL')
    CLINT_CRM_API_KEY = os.getenv('CLINT_CRM_API_KEY')
    
    # Configurações da aplicação
    SECRET_KEY = os.getenv('SECRET_KEY', 'development_key')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Configuração do tempo de permanência (em dias)
    LEAD_RETENTION_DAYS = int(os.getenv('LEAD_RETENTION_DAYS', '7'))
