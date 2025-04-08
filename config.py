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
    PORT = os.getenv('PORT', '5000')
    
    # Modo de teste (5 minutos em vez de 7 dias)
    TEST_MODE = os.getenv('TEST_MODE', 'False').lower() == 'true'
    
    # Configuração do tempo de permanência
    LEAD_RETENTION_DAYS = int(os.getenv('LEAD_RETENTION_DAYS', '7'))
    
    # Tempo em minutos para teste (usado quando TEST_MODE=True)
    LEAD_RETENTION_MINUTES = int(os.getenv('LEAD_RETENTION_MINUTES', '5'))
