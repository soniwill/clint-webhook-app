from apscheduler.schedulers.background import BackgroundScheduler
from webhook_handler import check_and_notify_old_leads, cleanup_old_leads
import logging
from config import Config

logger = logging.getLogger(__name__)

def start_scheduler():
    scheduler = BackgroundScheduler()
    
    # Definir intervalo baseado no modo (teste ou produção)
    if Config.TEST_MODE:
        # Em modo de teste, verificar a cada minuto
        logger.info("Iniciando agendador em modo de teste (verificação a cada minuto)")
        scheduler.add_job(check_and_notify_old_leads, 'interval', minutes=1)
    else:
        # Em modo normal, verificar a cada 6 horas
        logger.info("Iniciando agendador em modo normal (verificação a cada 6 horas)")
        scheduler.add_job(check_and_notify_old_leads, 'interval', hours=6)
    
    # Limpar leads muito antigos uma vez por dia
    scheduler.add_job(cleanup_old_leads, 'interval', days=1)
    
    scheduler.start()
    logger.info("Agendador iniciado com sucesso")
    
    return scheduler
