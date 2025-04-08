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
            existing_lead.in_stage_one = True  # Garantir que está marcado como na etapa 1
            existing_lead.moved_at = None      # Resetar a data de movimentação
            db.commit()
        else:
            # Criar novo lead
            new_lead = Lead(
                name=data['name'],
                email=data['email'],
                phone=data['phone'],
                in_stage_one=True,  # Explicitamente marcar como na etapa 1
                moved_at=None
            )
            db.add(new_lead)
            db.commit()
            logger.info(f"Novo lead adicionado: {data['email']}")
        
        return True
    
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {str(e)}")
        return False

def process_stage_change_webhook(data):
    """Processa um webhook recebido quando um lead muda de etapa"""
    try:
        # Validar dados recebidos
        required_fields = ['email', 'new_stage']
        if not all(field in data for field in required_fields):
            logger.error(f"Dados incompletos recebidos para mudança de etapa: {data}")
            return False
        
        # Verificar se é uma mudança da etapa 1
        if 'previous_stage' in data and data['previous_stage'] == 1:
            # Buscar o lead no banco de dados
            db = get_db()
            lead = db.query(Lead).filter(Lead.email == data['email']).first()
            
            if lead:
                # Atualizar o status do lead
                lead.in_stage_one = False
                lead.moved_at = datetime.utcnow()
                db.commit()
                logger.info(f"Lead {data['email']} movido da etapa 1 para etapa {data['new_stage']}")
                return True
            else:
                logger.warning(f"Lead não encontrado para mudança de etapa: {data['email']}")
                return False
        else:
            # Se não for uma mudança da etapa 1, apenas registrar e retornar sucesso
            logger.info(f"Mudança de etapa não relevante para monitoramento: {data}")
            return True
    
    except Exception as e:
        logger.error(f"Erro ao processar webhook de mudança de etapa: {str(e)}")
        return False

def check_and_notify_old_leads():
    """Verifica leads antigos e envia notificações quando necessário"""
    try:
        db = get_db()
        # Calcular a data limite (7 dias atrás)
        threshold_date = datetime.utcnow() - timedelta(days=Config.LEAD_RETENTION_DAYS)
        
        # Buscar leads que estão há mais de 7 dias na etapa 1, ainda não foram notificados,
        # e ainda estão na etapa 1
        old_leads = db.query(Lead).filter(
            and_(
                Lead.created_at <= threshold_date,
                Lead.notified == False,
                Lead.in_stage_one == True  # Adicionado este filtro
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
        current_time = datetime.utcnow()
        
        # Remover leads que já foram notificados e estão há mais de 30 dias no sistema
        very_old_date = current_time - timedelta(days=30)
        
        # Leads que foram notificados e estão há mais de 30 dias no sistema
        old_notified_leads = db.query(Lead).filter(
            and_(
                Lead.created_at <= very_old_date,
                Lead.notified == True
            )
        )
        
        # Leads que foram movidos da etapa 1 há mais de 15 dias
        moved_date_threshold = current_time - timedelta(days=15)
        old_moved_leads = db.query(Lead).filter(
            and_(
                Lead.in_stage_one == False,
                Lead.moved_at <= moved_date_threshold
            )
        )
        
        # Contar quantos leads serão removidos
        notified_count = old_notified_leads.count()
        moved_count = old_moved_leads.count()
        
        # Excluir os leads
        old_notified_leads.delete(synchronize_session=False)
        old_moved_leads.delete(synchronize_session=False)
        
        db.commit()
        logger.info(f"Removidos {notified_count} leads notificados antigos e {moved_count} leads movidos antigos")
        return notified_count + moved_count
    
    except Exception as e:
        logger.error(f"Erro ao limpar leads antigos: {str(e)}")
        return 0
