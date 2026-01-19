"""
Script para deletar usuários específicos do banco de dados.
Execute: python backend/scripts/deletar_usuarios.py
"""
import sys
from pathlib import Path
import os

backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

from database import SessionLocal
from database.models import Usuario, AprovacaoCadastro
from loguru import logger

def deletar_usuarios(emails: list):
    """Deleta usuários por lista de emails."""
    db = SessionLocal()
    try:
        logger.info("="*80)
        logger.info("DELETANDO USUÁRIOS")
        logger.info("="*80)
        
        deletados = []
        nao_encontrados = []
        
        for email in emails:
            try:
                usuario = db.query(Usuario).filter(Usuario.email == email).first()
                
                if not usuario:
                    logger.warning(f"⚠️ Usuário não encontrado: {email}")
                    nao_encontrados.append(email)
                    continue
                
                # Deletar aprovações associadas
                aprovacoes_deletadas = db.query(AprovacaoCadastro).filter(
                    AprovacaoCadastro.usuario_id == usuario.id
                ).delete(synchronize_session=False)
                
                # Deletar usuário
                db.delete(usuario)
                db.commit()
                
                logger.success(f"✅ Usuário deletado: {email} (ID: {usuario.id})")
                logger.info(f"   Aprovações deletadas: {aprovacoes_deletadas}")
                deletados.append(email)
                
            except Exception as e:
                logger.error(f"❌ Erro ao deletar {email}: {e}")
                db.rollback()
                continue
        
        logger.info("="*80)
        logger.info(f"✅ {len(deletados)} usuário(s) deletado(s)")
        if nao_encontrados:
            logger.warning(f"⚠️ {len(nao_encontrados)} usuário(s) não encontrado(s): {nao_encontrados}")
        logger.info("="*80)
        
        return deletados, nao_encontrados
        
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
        return [], emails
    finally:
        db.close()

if __name__ == "__main__":
    emails_para_deletar = [
        "daniel.borba@grupoht.com.br",
        "andre.rodrigues@grupoht.com.br"
    ]
    
    deletados, nao_encontrados = deletar_usuarios(emails_para_deletar)
    
    if deletados:
        print(f"\n✅ Usuários deletados: {deletados}")
    if nao_encontrados:
        print(f"\n⚠️ Usuários não encontrados: {nao_encontrados}")
