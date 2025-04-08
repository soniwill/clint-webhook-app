# tests/test_webhook.py
import unittest
import json
from datetime import datetime, timedelta
from app import app
from database import Lead, get_db, init_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import Config

class TestWebhooks(unittest.TestCase):
    def setUp(self):
        # Configurar banco de dados de teste
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Usar banco de dados em memória para testes
        test_engine = create_engine('sqlite:///:memory:')
        init_db(test_engine)
        self.TestSessionLocal = sessionmaker(bind=test_engine)
        
        # Criar alguns leads de teste
        self.create_test_leads()
    
    def tearDown(self):
        self.app_context.pop()
    
    def create_test_leads(self):
        db = self.TestSessionLocal()
        
        # Lead na etapa 1 há menos de 7 dias
        lead1 = Lead(
            name="Teste Um",
            email="teste1@example.com",
            phone="11999999999",
            created_at=datetime.utcnow() - timedelta(days=3),
            in_stage_one=True
        )
        
        # Lead na etapa 1 há mais de 7 dias
        lead2 = Lead(
            name="Teste Dois",
            email="teste2@example.com",
            phone="11988888888",
            created_at=datetime.utcnow() - timedelta(days=10),
            in_stage_one=True
        )
        
        db.add_all([lead1, lead2])
        db.commit()
        db.close()
    
    def test_stage_change_webhook(self):
        """Testa o webhook de mudança de etapa"""
        # Dados do webhook
        webhook_data = {
            "email": "teste1@example.com",
            "previous_stage": 1,
            "new_stage": 2
        }
        
        # Enviar webhook
        response = self.app.post(
            '/webhook/clint/stage-change',
            data=json.dumps(webhook_data),
            content_type='application/json'
        )
        
        # Verificar resposta
        self.assertEqual(response.status_code, 200)
        
        # Verificar se o lead foi atualizado no banco de dados
        db = self.TestSessionLocal()
        lead = db.query(Lead).filter(Lead.email == "teste1@example.com").first()
        
        self.assertIsNotNone(lead)
        self.assertFalse(lead.in_stage_one)
        self.assertIsNotNone(lead.moved_at)
        
        db.close()
    
    def test_notification_for_moved_leads(self):
        """Testa que leads movidos não são notificados"""
        # Primeiro, mover um lead
        webhook_data = {
            "email": "teste2@example.com",
            "previous_stage": 1,
            "new_stage": 2
        }
        
        self.app.post(
            '/webhook/clint/stage-change',
            data=json.dumps(webhook_data),
            content_type='application/json'
        )
        
        # Simular verificação de leads antigos
        from webhook_handler import check_and_notify_old_leads
        notified_count = check_and_notify_old_leads()
        
        # Verificar que nenhum lead foi notificado (o único lead antigo foi movido)
        self.assertEqual(notified_count, 0)
        
        # Verificar no banco de dados
        db = self.TestSessionLocal()
        lead = db.query(Lead).filter(Lead.email == "teste2@example.com").first()
        
        self.assertIsNotNone(lead)
        self.assertFalse(lead.in_stage_one)
        self.assertFalse(lead.notified)  # Não deve ter sido notificado
        
        db.close()

if __name__ == '__main__':
    unittest.main()
