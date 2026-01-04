"""
Script de diagnóstico completo para identificar problemas com bcrypt.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
import bcrypt

def diagnostico_completo():
    """Faz diagnóstico completo do sistema."""
    logger.info("=" * 60)
    logger.info("DIAGNÓSTICO COMPLETO DO SISTEMA")
    logger.info("=" * 60)
    
    # Teste 1: Verificar se bcrypt está instalado
    logger.info("\n1️⃣ Verificando instalação do bcrypt...")
    try:
        import bcrypt
        logger.info(f"   ✅ bcrypt instalado: {bcrypt.__version__ if hasattr(bcrypt, '__version__') else 'versão desconhecida'}")
    except ImportError as e:
        logger.error(f"   ❌ bcrypt não está instalado: {e}")
        return False
    
    # Teste 2: Verificar se passlib está instalado (não deveria estar)
    logger.info("\n2️⃣ Verificando se passlib está instalado...")
    try:
        import passlib
        logger.warning(f"   ⚠️ passlib AINDA ESTÁ INSTALADO: {passlib.__version__ if hasattr(passlib, '__version__') else 'versão desconhecida'}")
        logger.warning("   Execute: pip uninstall -y passlib")
    except ImportError:
        logger.info("   ✅ passlib não está instalado (correto)")
    
    # Teste 3: Testar hash de senha curta
    logger.info("\n3️⃣ Testando hash de senha curta (senha123)...")
    try:
        senha = "senha123"
        senha_bytes = senha.encode('utf-8')
        logger.info(f"   Tamanho: {len(senha_bytes)} bytes")
        hash_bytes = bcrypt.hashpw(senha_bytes, bcrypt.gensalt())
        hash_str = hash_bytes.decode('utf-8')
        logger.info(f"   ✅ Hash criado: {hash_str[:50]}...")
        
        # Verificar
        verificacao = bcrypt.checkpw(senha_bytes, hash_bytes)
        logger.info(f"   ✅ Verificação: {verificacao}")
    except Exception as e:
        logger.error(f"   ❌ Erro: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    
    # Teste 4: Testar hash de senha longa (> 72 bytes)
    logger.info("\n4️⃣ Testando hash de senha longa (> 72 bytes)...")
    try:
        senha_longa = "a" * 100  # 100 bytes
        senha_bytes = senha_longa.encode('utf-8')
        logger.info(f"   Tamanho original: {len(senha_bytes)} bytes")
        
        # Truncar para 72 bytes
        senha_bytes_truncada = senha_bytes[:72]
        logger.info(f"   Tamanho após truncamento: {len(senha_bytes_truncada)} bytes")
        
        hash_bytes = bcrypt.hashpw(senha_bytes_truncada, bcrypt.gensalt())
        hash_str = hash_bytes.decode('utf-8')
        logger.info(f"   ✅ Hash criado: {hash_str[:50]}...")
        
        # Verificar
        verificacao = bcrypt.checkpw(senha_bytes_truncada, hash_bytes)
        logger.info(f"   ✅ Verificação: {verificacao}")
    except Exception as e:
        logger.error(f"   ❌ Erro: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    
    # Teste 5: Verificar imports no auth.py
    logger.info("\n5️⃣ Verificando imports no auth.py...")
    try:
        auth_file = backend_dir / "auth.py"
        with open(auth_file, 'r', encoding='utf-8') as f:
            conteudo = f.read()
            if 'passlib' in conteudo.lower():
                logger.warning("   ⚠️ auth.py ainda contém referências a passlib!")
                logger.warning("   Verifique se há imports ou uso de passlib")
            else:
                logger.info("   ✅ auth.py não contém referências a passlib")
            
            if 'import bcrypt' in conteudo or 'from bcrypt' in conteudo:
                logger.info("   ✅ auth.py importa bcrypt diretamente")
            else:
                logger.warning("   ⚠️ auth.py não importa bcrypt diretamente")
    except Exception as e:
        logger.error(f"   ❌ Erro ao verificar auth.py: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ DIAGNÓSTICO CONCLUÍDO!")
    logger.info("=" * 60)
    
    return True

if __name__ == "__main__":
    diagnostico_completo()


