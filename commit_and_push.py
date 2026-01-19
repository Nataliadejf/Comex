"""
Script para fazer commit e push das mudanças.
Execute: python commit_and_push.py
"""
import subprocess
import sys
from pathlib import Path

projeto_dir = Path(__file__).parent

def run_command(cmd, description):
    """Executa um comando e exibe resultado."""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=str(projeto_dir),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr and result.returncode != 0:
            print(f"⚠️ Erros: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Erro ao executar comando: {e}")
        return False

def main():
    """Executa commit e push."""
    print("\n🚀 INICIANDO COMMIT E PUSH DAS MUDANÇAS\n")
    
    # 1. Adicionar todos os arquivos
    if not run_command("git add -A", "Adicionando arquivos ao stage"):
        print("❌ Falha ao adicionar arquivos")
        return False
    
    # 2. Verificar status
    run_command("git status --short", "Status do repositório")
    
    # 3. Fazer commit
    commit_msg = """Remove senhas expostas, ajusta Dashboard mobile, adiciona endpoint deletar usuário

- Remove senhas expostas dos arquivos .md
- Ajusta Dashboard para mobile (cards, gráficos, tabelas responsivos)
- Adiciona endpoint POST /admin/usuarios/deletar-por-email
- Cria script deletar_usuarios.py para deletar usuários específicos
- Corrige render.yaml removendo duplicação"""
    
    if not run_command(f'git commit -m "{commit_msg}"', "Fazendo commit"):
        print("❌ Falha ao fazer commit")
        return False
    
    # 4. Fazer push
    if not run_command("git push origin main", "Fazendo push para GitHub"):
        print("❌ Falha ao fazer push")
        return False
    
    print("\n" + "="*60)
    print("✅ COMMIT E PUSH CONCLUÍDOS COM SUCESSO!")
    print("="*60)
    print("\n📡 O Render vai detectar as mudanças e fazer deploy automaticamente.")
    print("   Acompanhe o deploy em: https://dashboard.render.com")
    print("\n")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
