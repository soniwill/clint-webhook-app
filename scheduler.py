from apscheduler.schedulers.background import BackgroundScheduler
from webhook_handler import check_and_notify_old_leads, cleanup_old_leads
import logging

logger = logging.getLogger(__name__)

def start_scheduler():
    scheduler = BackgroundScheduler()
    
    # Verificar leads antigos a cada 6 horas
    scheduler.add_job(check_and_notify_old_leads, 'interval', hours=6)
    
    # Limpar leads muito antigos uma vez por dia
    scheduler.add_job(cleanup_old_leads, 'interval', days=1)
    
    scheduler.start()
    logger.info("Agendador iniciado com sucesso")
    
    return scheduler
