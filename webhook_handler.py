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
        current_time = datetime.utcnow()
        
        # Calcular a data limite baseada no modo (teste ou produção)
        if Config.TEST_MODE:
            # Em modo de teste, usar minutos
            threshold_date = current_time - timedelta(minutes=Config.LEAD_RETENTION_MINUTES)
            logger.info(f"Modo de teste ativado: verificando leads mais antigos que {Config.LEAD_RETENTION_MINUTES} minutos")
        else:
            # Em modo normal, usar dias
            threshold_date = current_time - timedelta(days=Config.LEAD_RETENTION_DAYS)
            logger.info(f"Verificando leads mais antigos que {Config.LEAD_RETENTION_DAYS} dias")
        
        # Buscar leads que estão há mais tempo que o limite na etapa 1,
        # ainda não foram notificados, e ainda estão na etapa 1
        old_leads = db.query(Lead).filter(
            and_(
                Lead.created_at <= threshold_date,
                Lead.notified == False,
                Lead.in_stage_one == True
            )
        ).all()
        
        logger.info(f"Encontrados {len(old_leads)} leads para notificação")
        
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
    """
    Envia um webhook para o Clint CRM com apenas o e-mail do lead.
    Não requer autenticação via API key.
    """
    try:
        # Payload simplificado contendo apenas o e-mail do lead
        payload = {
            "email": lead.email
        }
        
        # Cabeçalho básico sem autenticação
        headers = {
            "Content-Type": "application/json"
        }
        
        logger.info(f"Enviando webhook para Clint CRM para o lead: {lead.email}")
        
        response = requests.post(
            Config.CLINT_CRM_WEBHOOK_URL,
            json=payload,
            headers=headers
        )
        
        if response.status_code in [200, 201, 202]:
            logger.info(f"Webhook enviado com sucesso para o lead: {lead.email}")
            return True
        else:
            logger.error(f"Erro ao enviar webhook: Código {response.status_code} - {response.text}")
            try:
                error_detail = response.json()
                logger.error(f"Detalhes do erro: {error_detail}")
            except:
                pass
            return False
    
    except Exception as e:
        logger.error(f"Exceção ao enviar webhook: {str(e)}")
        return False

def cleanup_old_leads():
    """Remove leads muito antigos do banco de dados"""
    try:
        db = get_db()
        current_time = datetime.utcnow()
        
        # Definir períodos baseados no modo (teste ou produção)
        if Config.TEST_MODE:
            # Em modo de teste, usar minutos
            very_old_date = current_time - timedelta(minutes=30)  # 30 minutos para leads notificados
            moved_date_threshold = current_time - timedelta(minutes=15)  # 15 minutos para leads movidos
            logger.info("Modo de teste: limpando leads notificados há mais de 30 minutos e movidos há mais de 15 minutos")
        else:
            # Em modo normal, usar dias
            very_old_date = current_time - timedelta(days=30)  # 30 dias para leads notificados
            moved_date_threshold = current_time - timedelta(days=15)  # 15 dias para leads movidos
            logger.info("Limpando leads notificados há mais de 30 dias e movidos há mais de 15 dias")
        
        # Leads que foram notificados e estão há mais tempo que o limite no sistema
        old_notified_leads = db.query(Lead).filter(
            and_(
                Lead.created_at <= very_old_date,
                Lead.notified == True
            )
        )
        
        # Leads que foram movidos da etapa 1 há mais tempo que o limite
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
