# 🗺️ Mapeamento de Botões - Portal Comex Stat

Este documento descreve como mapear os botões do portal Comex Stat para automação.

## 📋 Passos para Mapear os Botões

### 1. Acessar o Portal
- URL: https://comexstat.mdic.gov.br
- Abrir DevTools (F12) no navegador

### 2. Identificar Elementos

#### A. Botão/Menu Principal de Dados
- **Localização**: Geralmente no topo ou menu lateral
- **Seletor CSS**: Inspecionar elemento e copiar seletor
- **Exemplo**: `button.download`, `a[href*="download"]`, `#download-btn`

#### B. Seleção de Tipo (Importação/Exportação)
- **Localização**: Dropdown ou botões de seleção
- **Seletor CSS**: `select[name="tipo"]`, `button[data-tipo="exportacao"]`
- **Valores**: "Importação" ou "Exportação"

#### C. Seleção de Período/Mês
- **Localização**: Calendário ou dropdown de mês/ano
- **Seletor CSS**: `input[type="date"]`, `select[name="mes"]`
- **Formato**: YYYY-MM (ex: "2025-01")

#### D. Botão de Download/Exportar
- **Localização**: Após selecionar tipo e período
- **Seletor CSS**: `button.download`, `a.btn-download`, `#export-btn`
- **Ação**: Clicar para iniciar download

### 3. Estrutura Típica do Site

```html
<!-- Exemplo de estrutura esperada -->
<div class="download-section">
  <select name="tipo">
    <option value="exportacao">Exportação</option>
    <option value="importacao">Importação</option>
  </select>
  
  <input type="month" name="periodo" value="2025-01">
  
  <button class="btn-download">Baixar CSV</button>
</div>
```

### 4. Seletores Comuns

#### Por ID
```python
driver.find_element(By.ID, "download-btn")
```

#### Por Classe
```python
driver.find_element(By.CLASS_NAME, "download-button")
```

#### Por XPath
```python
driver.find_element(By.XPATH, "//button[contains(text(), 'Download')]")
```

#### Por CSS Selector
```python
driver.find_element(By.CSS_SELECTOR, "button.download")
```

### 5. Exemplo de Código para Mapear

```python
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Aguardar página carregar
wait = WebDriverWait(driver, 10)

# 1. Selecionar tipo (Exportação)
tipo_select = wait.until(
    EC.presence_of_element_located((By.NAME, "tipo"))
)
tipo_select.select_by_value("exportacao")

# 2. Selecionar mês
mes_input = wait.until(
    EC.presence_of_element_located((By.NAME, "periodo"))
)
mes_input.clear()
mes_input.send_keys("2025-01")

# 3. Clicar em download
download_btn = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.download"))
)
download_btn.click()

# 4. Aguardar download
time.sleep(5)  # Ajustar conforme necessário
```

## 🔍 Como Encontrar os Seletores

1. **Abrir DevTools** (F12)
2. **Clicar no ícone de inspeção** (Ctrl+Shift+C)
3. **Clicar no elemento** desejado na página
4. **Copiar o seletor**:
   - Botão direito → Copy → Copy selector
   - Ou usar XPath: Copy → Copy XPath

## 📝 Checklist de Mapeamento

- [ ] URL do portal identificada
- [ ] Botão/menu de dados localizado
- [ ] Seletor de tipo (IMP/EXP) identificado
- [ ] Seletor de período/mês identificado
- [ ] Botão de download identificado
- [ ] Seletores testados manualmente
- [ ] Código de automação criado
- [ ] Testado com um mês de exemplo

## ⚠️ Observações Importantes

1. **Site pode mudar**: Os seletores podem mudar se o site for atualizado
2. **Rate limiting**: Adicionar delays entre requisições
3. **Captcha**: Alguns sites têm proteção contra bots
4. **Login**: Verificar se é necessário login
5. **Cookies**: Pode ser necessário aceitar cookies primeiro

## 🛠️ Ferramentas Úteis

- **Selenium IDE**: Gravar ações e exportar código
- **Playwright Codegen**: Gerar código automaticamente
- **Browser DevTools**: Inspecionar elementos
- **XPath Helper**: Extensão do Chrome para testar XPath

## 📚 Próximos Passos

Após mapear os botões:

1. Atualizar o arquivo `download_comex_automatico.py` com os seletores corretos
2. Testar com um mês de exemplo
3. Implementar tratamento de erros
4. Adicionar logs detalhados
5. Configurar agendamento mensal

---

**Última atualização**: Janeiro 2025



