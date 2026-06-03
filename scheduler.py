"""
Busca automática agendada — roda em background.
Execute separado: python scheduler.py

Requer: pip install apscheduler
"""
import time
import logging
from apscheduler.schedulers.background import BackgroundScheduler
import database
import apis

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

def job_buscar():
    logging.info("Iniciando busca automática...")
    database.criar_banco()
    resultados = apis.buscar_tudo()
    total = 0
    for fonte, df in resultados.items():
        if not df.empty:
            database.salvar(df, fonte)
            total += len(df)
    logging.info(f"Busca concluída: {total} jogos salvos.")

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    # Roda imediatamente ao iniciar e depois a cada 6 horas
    job_buscar()
    scheduler.add_job(job_buscar, "interval", hours=6, id="busca_jogos")
    scheduler.start()
    logging.info("Agendador iniciado. Buscando a cada 6 horas. Ctrl+C para parar.")
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logging.info("Agendador encerrado.")
