# Instruções para Desabilitar Solicitação de Permissão do Google/Chrome

Quando você clica no botão "Gerar link da consulta" no ComexStat, o Google Chrome pode solicitar permissão para acessar a área de transferência (clipboard). Existem duas formas de resolver isso:

## Opção 1: Permitir Automaticamente (Recomendado)

O código já está configurado para clicar automaticamente no botão "Permitir" quando aparecer. Se isso não funcionar, você pode seguir a Opção 2.

## Opção 2: Configurar Chrome para Sempre Permitir (Manual)

### Passo a Passo:

1. **Abra o Chrome e vá para Configurações:**
   - Clique nos três pontos (⋮) no canto superior direito
   - Selecione "Configurações"

2. **Acesse Configurações de Site:**
   - Role para baixo e clique em "Privacidade e segurança"
   - Clique em "Configurações do site"

3. **Configure Permissões de Área de Transferência:**
   - Procure por "Área de transferência" ou "Clipboard"
   - Clique nessa opção
   - Selecione "Permitir que os sites leiam e alterem texto na área de transferência"

4. **Ou configure por site específico:**
   - Na mesma página de "Configurações do site"
   - Procure por "Permissões" → "Área de transferência"
   - Adicione `https://comexstat.mdic.gov.br` à lista de sites permitidos

### Alternativa: Usar Perfil de Usuário do Chrome

Se você quiser criar um perfil específico para automação:

1. **Criar novo perfil:**
   - Vá para `chrome://settings/manageProfile`
   - Clique em "Adicionar"
   - Crie um novo perfil chamado "Automação" ou similar

2. **Configurar permissões no novo perfil:**
   - Siga os passos acima para permitir acesso à área de transferência
   - Use este perfil apenas para automação

### Configuração via Linha de Comando (Avançado)

Se você quiser configurar via argumentos do Chrome, adicione estas flags ao iniciar o Chrome:

```
--disable-web-security
--disable-features=ClipboardReadWrite
--enable-clipboard-read-write
```

**Nota:** O código já tenta usar algumas dessas configurações automaticamente.

## Opção 3: Usar Modo Não-Headless Temporariamente

Se as opções acima não funcionarem, você pode executar o scraper em modo visível (não-headless) para clicar manualmente no "Permitir" na primeira vez:

```python
scraper.baixar_dados_por_link(
    link_consulta="https://comexstat.mdic.gov.br/pt/geral/142608",
    headless=False,  # Modo visível
    preferir_csv=True
)
```

Após clicar em "Permitir" uma vez, o Chrome geralmente lembra dessa escolha para o site.

## Verificação

Para verificar se está funcionando:

1. Execute o script de teste
2. Observe se o botão "Permitir" aparece
3. O código deve clicar automaticamente nele
4. Se não funcionar, siga a Opção 2 acima

## Problemas Comuns

- **"Permitir" não aparece:** Pode ser que o Chrome já tenha a permissão configurada. Verifique nas configurações.
- **Permissão não persiste:** Tente usar um perfil de usuário específico para automação.
- **Erro ao clicar:** O código tenta múltiplos métodos. Se falhar, use modo não-headless para clicar manualmente.


