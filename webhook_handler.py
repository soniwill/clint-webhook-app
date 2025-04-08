import requests
import logging
from datetime import datetime, timedelta
from sqlalchemy import and_
from database import Lead, get_db
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_incoming_webhook(data):
    """Processa um webhook recebido do Clint CRM"""
    try:
        # Validar dados recebidos
        required_fields = ['name', 'email', 'phone']
        if not all(field in data for field in required_fields):
            logger.error(f"Dados incompletos recebidos: {data}")
            return False
        
        # Verificar se o lead já existe
        db = get_db()
        existing_lead = db.query(Lead).filter(Lead.email == data['email']).first()
        
        if existing_lead:
            logger.info(f"Lead já existe: {data['email']}")
            # Atualizar a data de criação para reiniciar a contagem
            existing_lead.created_at = datetime.utcnow()
            existing_lead.notified = False
            db.commit()
        else:
            # Criar novo lead
            new_lead = Lead(
                name=data['name'],
                email=data['email'],
                phone=data['phone']
            )
            db.add(new_lead)
            db.commit()
            logger.info(f"Novo lead adicionado: {data['email']}")
        
        return True
    
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {str(e)}")
        return False

def check_and_notify_old_leads():
    """Verifica leads antigos e envia notificações quando necessário"""
    try:
        db = get_db()
        # Calcular a data limite (7 dias atrás)
        threshold_date = datetime.utcnow() - timedelta(days=Config.LEAD_RETENTION_DAYS)
        
        # Buscar leads que estão há mais de 7 dias na etapa 1 e ainda não foram notificados
        old_leads = db.query(Lead).filter(
            and_(
                Lead.created_at <= threshold_date,
                Lead.notified == False
            )
        ).all()
        
        for lead in old_leads:
            # Enviar webhook para o Clint CRM
            success = send_webhook_to_clint(lead)
            if success:
                # Marcar como notificado
                lead.notified = True
                db.commit()
                logger.info(f"Lead notificado com sucesso: {lead.email}")
            else:
                logger.error(f"Falha ao notificar lead: {lead.email}")
        
        return len(old_leads)
    
    except Exception as e:
        logger.error(f"Erro ao verificar leads antigos: {str(e)}")
        return 0

def send_webhook_to_clint(lead):
    """Envia um webhook para o Clint CRM"""
    try:
        payload = {
            "name": lead.name,
            "email": lead.email,
            "phone": lead.phone,
            "retention_days": Config.LEAD_RETENTION_DAYS
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {Config.CLINT_CRM_API_KEY}"
        }
        
        response = requests.post(
            Config.CLINT_CRM_WEBHOOK_URL,
            json=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            return True
        else:
            logger.error(f"Erro ao enviar webhook: {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        logger.error(f"Exceção ao enviar webhook: {str(e)}")
        return False

def cleanup_old_leads():
    """Remove leads muito antigos do banco de dados"""
    try:
        db = get_db()
        # Remover leads que já foram notificados e estão há mais de 30 dias no sistema
        very_old_date = datetime.utcnow() - timedelta(days=30)
        old_leads = db.query(Lead).filter(
            and_(
                Lead.created_at <= very_old_date,
                Lead.notified == True
            )
        ).all()
        
        for lead in old_leads:
            db.delete(lead)
        
        db.commit()
        logger.info(f"Removidos {len(old_leads)} leads antigos do banco de dados")
        return len(old_leads)
    
    except Exception as e:
        logger.error(f"Erro ao limpar leads antigos: {str(e)}")
        return 0
