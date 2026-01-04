"""
Script completo para popular o dashboard:
1. Verifica espaço em disco
2. Configura banco
3. Faz download dos arquivos
4. Processa os arquivos
"""
import sys
from pathlib import Path
import asyncio
import shutil

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from config import settings


def verificar_espaco_disco():
    """Verifica espaço disponível em disco."""
    logger.info("=" * 60)
    logger.info("VERIFICAÇÃO DE ESPAÇO EM DISCO")
    logger.info("=" * 60)
    
    try:
        # Verificar drive D:
        if Path("D:/").exists():
            disk_usage = shutil.disk_usage("D:/")
            free_gb = disk_usage.free / (1024**3)
            total_gb = disk_usage.total / (1024**3)
            used_gb = disk_usage.used / (1024**3)
            
            logger.info(f"Drive D:")
            logger.info(f"  Total: {total_gb:.2f} GB")
            logger.info(f"  Usado: {used_gb:.2f} GB")
            logger.info(f"  Livre: {free_gb:.2f} GB")
            
            # Estimar espaço necessário (cada arquivo CSV pode ter ~100-500MB)
            # 3 meses * 2 tipos (IMP/EXP) = 6 arquivos
            # Estimativa: 6 * 300MB = 1.8GB
            espaco_necessario_gb = 2.0
            
            if free_gb < espaco_necessario_gb:
                logger.error(f"❌ Espaço insuficiente! Necessário: {espaco_necessario_gb} GB, Disponível: {free_gb:.2f} GB")
                return False
            else:
                logger.info(f"✅ Espaço suficiente! Disponível: {free_gb:.2f} GB")
                return True
        else:
            logger.warning("⚠️  Drive D: não encontrado, usando diretório padrão")
            return True
            
    except Exception as e:
        logger.error(f"Erro ao verificar espaço: {e}")
        return True  # Continuar mesmo se não conseguir verificar


def verificar_capacidade_processamento():
    """Verifica capacidade de processamento."""
    logger.info("=" * 60)
    logger.info("VERIFICAÇÃO DE CAPACIDADE DE PROCESSAMENTO")
    logger.info("=" * 60)
    
    try:
        import psutil
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        logger.info(f"CPU: {cpu_percent:.1f}% de uso")
        
        # RAM
        ram = psutil.virtual_memory()
        ram_total_gb = ram.total / (1024**3)
        ram_livre_gb = ram.available / (1024**3)
        ram_percent = ram.percent
        
        logger.info(f"RAM Total: {ram_total_gb:.2f} GB")
        logger.info(f"RAM Livre: {ram_livre_gb:.2f} GB")
        logger.info(f"RAM Usada: {ram_percent:.1f}%")
        
        # Verificar se há RAM suficiente (mínimo 2GB livre)
        if ram_livre_gb < 2:
            logger.warning("⚠️  Pouca RAM livre disponível")
            return False
        else:
            logger.info("✅ Capacidade de processamento adequada")
            return True
            
    except ImportError:
        logger.warning("psutil não instalado, pulando verificação de capacidade")
        return True
    except Exception as e:
        logger.error(f"Erro ao verificar capacidade: {e}")
        return True


async def processar_arquivos_baixados():
    """Processa os arquivos CSV baixados."""
    logger.info("=" * 60)
    logger.info("PROCESSAMENTO DE ARQUIVOS")
    logger.info("=" * 60)
    
    try:
        from process_files import main_async
        await main_async()
        logger.info("✅ Processamento concluído")
    except Exception as e:
        logger.error(f"Erro no processamento: {e}")
        import traceback
        logger.error(traceback.format_exc())


async def main():
    """Função principal."""
    logger.info("=" * 60)
    logger.info("POPULAR DASHBOARD - PROCESSO COMPLETO")
    logger.info("=" * 60)
    logger.info("")
    
    # 1. Verificar espaço em disco
    if not verificar_espaco_disco():
        logger.error("❌ Processo interrompido: espaço em disco insuficiente")
        return
    
    logger.info("")
    
    # 2. Verificar capacidade de processamento
    if not verificar_capacidade_processamento():
        logger.warning("⚠️  Capacidade limitada, mas continuando...")
    
    logger.info("")
    
    # 3. Configurar banco
    logger.info("=" * 60)
    logger.info("CONFIGURAÇÃO DO BANCO")
    logger.info("=" * 60)
    try:
        from configurar_banco import configurar_banco
        configurar_banco()
    except Exception as e:
        logger.error(f"Erro ao configurar banco: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return
    
    logger.info("")
    
    # 4. Fazer download dos arquivos
    logger.info("=" * 60)
    logger.info("DOWNLOAD DE ARQUIVOS")
    logger.info("=" * 60)
    logger.info("")
    logger.info("⚠️  IMPORTANTE: Para download automático completo,")
    logger.info("   é necessário mapear os botões do site Comex Stat.")
    logger.info("   Por enquanto, use o método manual:")
    logger.info("   1. Acesse: https://comexstat.mdic.gov.br")
    logger.info("   2. Baixe os arquivos CSV manualmente")
    logger.info("   3. Salve em: D:\\comex\\2025\\ ou D:\\NatFranca\\raw\\")
    logger.info("")
    logger.info("Ou execute o script de download:")
    logger.info("   python scripts/download_comex_automatico.py")
    logger.info("")
    
    # Perguntar se deseja tentar download automático
    try:
        resposta = input("Deseja tentar download automático? (s/n): ").strip().lower()
        if resposta == 's':
            logger.info("Iniciando download automático...")
            from download_comex_automatico import main as download_main
            download_main()
    except KeyboardInterrupt:
        logger.info("Download cancelado pelo usuário")
    except Exception as e:
        logger.error(f"Erro no download automático: {e}")
        logger.info("Continuando com processamento de arquivos existentes...")
    
    logger.info("")
    
    # 5. Processar arquivos baixados
    logger.info("=" * 60)
    logger.info("PROCESSAMENTO DE ARQUIVOS")
    logger.info("=" * 60)
    await processar_arquivos_baixados()
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("PROCESSO COMPLETO FINALIZADO!")
    logger.info("=" * 60)
    
    # Verificar resultado final
    try:
        from database import get_db, OperacaoComex
        from sqlalchemy import func
        db = next(get_db())
        total = db.query(func.count(OperacaoComex.id)).scalar() or 0
        logger.info(f"Total de registros no banco: {total:,}")
    except Exception as e:
        logger.error(f"Erro ao verificar resultado: {e}")


if __name__ == "__main__":
    asyncio.run(main())



