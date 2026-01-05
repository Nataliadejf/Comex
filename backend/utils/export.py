"""
Utilitários para exportação de relatórios.
"""
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from loguru import logger

# Import opcional - não disponível no Render
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("pandas não disponível - exportação Excel/CSV limitada")

from config import settings


class ReportExporter:
    """Classe para exportação de relatórios."""
    
    def __init__(self):
        self.exports_dir = settings.data_dir / "exports"
        self.exports_dir.mkdir(parents=True, exist_ok=True)
    
    def export_to_excel(
        self,
        data: List[Dict[str, Any]],
        filename: str = None
    ) -> Path:
        """
        Exporta dados para Excel.
        
        Args:
            data: Lista de dicionários com os dados
            filename: Nome do arquivo (opcional)
        
        Returns:
            Caminho do arquivo gerado
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"relatorio_{timestamp}.xlsx"
        
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'
        
        filepath = self.exports_dir / filename
        
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas e openpyxl são necessários para exportação em Excel. Instale com: pip install pandas openpyxl")
        
        try:
            df = pd.DataFrame(data)
            df.to_excel(filepath, index=False, engine='openpyxl')
            logger.info(f"Relatório Excel exportado: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Erro ao exportar para Excel: {e}")
            raise
    
    def export_to_csv(
        self,
        data: List[Dict[str, Any]],
        filename: str = None
    ) -> Path:
        """
        Exporta dados para CSV.
        
        Args:
            data: Lista de dicionários com os dados
            filename: Nome do arquivo (opcional)
        
        Returns:
            Caminho do arquivo gerado
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"relatorio_{timestamp}.csv"
        
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        filepath = self.exports_dir / filename
        
        if not PANDAS_AVAILABLE:
            # Fallback: CSV simples sem pandas
            import csv
            if data:
                with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                logger.info(f"Relatório CSV exportado (sem pandas): {filepath}")
                return filepath
            else:
                raise ValueError("Nenhum dado para exportar")
        
        try:
            df = pd.DataFrame(data)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            logger.info(f"Relatório CSV exportado: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Erro ao exportar para CSV: {e}")
            raise
    
    def export_to_pdf(
        self,
        data: List[Dict[str, Any]],
        filename: str = None,
        title: str = "Relatório Comex Analyzer"
    ) -> Path:
        """
        Exporta dados para PDF.
        
        Args:
            data: Lista de dicionários com os dados
            filename: Nome do arquivo (opcional)
            title: Título do relatório
        
        Returns:
            Caminho do arquivo gerado
        """
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"relatorio_{timestamp}.pdf"
            
            if not filename.endswith('.pdf'):
                filename += '.pdf'
            
            filepath = self.exports_dir / filename
            
            # Criar documento PDF
            doc = SimpleDocTemplate(str(filepath), pagesize=A4)
            elements = []
            
            # Estilos
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#1890ff'),
                spaceAfter=30,
            )
            
            # Título
            elements.append(Paragraph(title, title_style))
            elements.append(Spacer(1, 0.2 * inch))
            
            # Preparar dados da tabela
            if data:
                # Cabeçalho
                headers = list(data[0].keys())
                table_data = [headers]
                
                # Dados
                for row in data[:100]:  # Limitar a 100 linhas para PDF
                    table_data.append([str(row.get(key, '')) for key in headers])
                
                # Criar tabela
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                ]))
                
                elements.append(table)
            
            # Construir PDF
            doc.build(elements)
            logger.info(f"Relatório PDF exportado: {filepath}")
            return filepath
        
        except ImportError:
            logger.warning("reportlab não instalado. Instale com: pip install reportlab")
            raise ImportError("reportlab é necessário para exportação em PDF")
        except Exception as e:
            logger.error(f"Erro ao exportar para PDF: {e}")
            raise

