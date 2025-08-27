# -*- coding: utf-8 -*-
"""
Script principal do Sistema de Clipping Legislativo FACIAP
"""

import sys
import time
from datetime import datetime
from pathlib import Path

# Adiciona o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

from core.scrapers.camara_scraper import CamaraScraper
from core.scrapers.senado_scraper import SenadoScraper
from core.extractors.content_extractor import ContentExtractor
from core.scoring.news_scorer import news_scorer
from core.database.db_manager import db_manager
from utils.logger import logger

class ClippingSystem:
    """
    Sistema principal de clipping legislativo
    """
    
    def __init__(self):
        """Inicializa o sistema"""
        self.camara_scraper = CamaraScraper()
        self.senado_scraper = SenadoScraper()
        self.content_extractor = ContentExtractor()
        self.scorer = news_scorer
        self.db = db_manager
        
        logger.info("Sistema de Clipping FACIAP inicializado")
    
    def test_scrapers(self, max_pages: int = 3):
        """
        Testa os scrapers das duas fontes
        
        Args:
            max_pages: Número de páginas para testar
        """
        logger.info("🔧 INICIANDO TESTES DOS SCRAPERS...")
        
        # Testa Câmara
        logger.info("\n" + "="*50)
        logger.info("TESTANDO SCRAPER DA CÂMARA")
        logger.info("="*50)
        camara_results = self.camara_scraper.test_scraping(max_pages)
        
        # Testa Senado
        logger.info("\n" + "="*50)
        logger.info("TESTANDO SCRAPER DO SENADO")
        logger.info("="*50)
        senado_results = self.senado_scraper.test_scraping(max_pages)
        
        # Resumo
        logger.info("\n" + "="*50)
        logger.info("RESUMO DOS TESTES")
        logger.info("="*50)
        logger.info(f"Câmara: {camara_results['valid_news_found']} notícias válidas")
        logger.info(f"Senado: {senado_results['valid_news_found']} notícias válidas")
        logger.info(f"Total: {camara_results['valid_news_found'] + senado_results['valid_news_found']} notícias")
        
        return {
            'camara': camara_results,
            'senado': senado_results
        }
    
    def test_content_extraction(self, sample_urls: list = None):
        """
        Testa extração de conteúdo
        
        Args:
            sample_urls: URLs para teste (se None, coleta algumas automaticamente)
        """
        if not sample_urls:
            logger.info("Coletando URLs de exemplo...")
            # Coleta algumas URLs das primeiras páginas
            camara_news = self.camara_scraper.scrape_news(max_pages=2)
            senado_news = self.senado_scraper.scrape_news(max_pages=2)
            
            sample_urls = []
            for news in (camara_news + senado_news)[:5]:  # Pega 5 exemplos
                sample_urls.append(news['link'])
        
        if sample_urls:
            logger.info(f"🔧 TESTANDO EXTRAÇÃO DE CONTEÚDO ({len(sample_urls)} URLs)...")
            results = self.content_extractor.test_extraction(sample_urls)
            return results
        else:
            logger.warning("Nenhuma URL disponível para teste")
            return {}
    
    def test_scoring(self):
        """Testa sistema de scoring com casos de exemplo"""
        test_cases = [
            {
                'titulo': 'Projeto de Lei aumenta imposto sobre operações financeiras',
                'texto': 'O projeto de lei em tramitação na Câmara dos Deputados propõe aumento da alíquota do IOF para operações financeiras. A medida visa aumentar a arrecadação federal e equilibrar as contas públicas.'
            },
            {
                'titulo': 'Senado aprova resolução sobre processo legislativo',
                'texto': 'O Senado Federal aprovou nova resolução que modifica o processo legislativo para projetos de lei. A medida busca agilizar a tramitação de propostas no Congresso Nacional.'
            },
            {
                'titulo': 'Deputados discutem reforma tributária',
                'texto': 'A reforma tributária foi tema de debate na Câmara dos Deputados. Os parlamentares discutiram a criação do IVA e a simplificação do sistema tributário brasileiro.'
            }
        ]
        
        logger.info("🔧 TESTANDO SISTEMA DE SCORING...")
        results = self.scorer.test_scoring(test_cases)
        return results
    
    def run_full_collection(self, max_pages_camara: int = 10, max_pages_senado: int = 10):
        """
        Executa coleta completa de notícias
        
        Args:
            max_pages_camara: Páginas da Câmara
            max_pages_senado: Páginas do Senado
        """
        start_time = time.time()
        execution_log = {
            'data_execucao': datetime.now(),
            'noticias_coletadas': 0,
            'noticias_processadas': 0,
            'status': 'iniciado',
            'log_detalhes': {}
        }
        
        try:
            logger.info("🚀 INICIANDO COLETA COMPLETA...")
            
            # Coleta notícias
            logger.info("📰 Coletando notícias da Câmara...")
            camara_news = self.camara_scraper.scrape_news(max_pages_camara)
            
            logger.info("📰 Coletando notícias do Senado...")
            senado_news = self.senado_scraper.scrape_news(max_pages_senado)
            
            all_news = camara_news + senado_news
            execution_log['noticias_coletadas'] = len(all_news)
            
            if not all_news:
                logger.warning("Nenhuma notícia coletada")
                execution_log['status'] = 'sem_noticias'
                return execution_log
            
            logger.info(f"📊 Total coletado: {len(all_news)} notícias")
            
            # Salva notícias no banco
            logger.info("💾 Salvando notícias no banco de dados...")
            saved_count = 0
            
            for news in all_news:
                saved_news = self.db.save_noticia(news)
                if saved_news:
                    saved_count += 1
            
            logger.info(f"💾 Notícias salvas: {saved_count}")
            
            # Extrai conteúdo textual
            logger.info("📝 Extraindo conteúdo textual...")
            extraction_count = 0
            
            for news in all_news:
                if 'link' in news:
                    texto = self.content_extractor.extract_text(news['link'])
                    if texto:
                        # Busca a notícia no banco para atualizar
                        db_news = self.db.get_noticia_by_link(news['link'])
                        if db_news:
                            self.db.update_noticia_texto(
                                db_news.id, 
                                texto, 
                                len(texto.split())
                            )
                            extraction_count += 1
            
            logger.info(f"📝 Textos extraídos: {extraction_count}")
            
            # Calcula scores
            logger.info("🎯 Calculando scores...")
            scoring_count = 0
            
            # Busca notícias com texto para calcular scores
            noticias_db, _ = self.db.get_noticias(limit=1000)  # Pega todas recentes
            
            for noticia in noticias_db:
                if noticia.texto_completo:
                    score_data = self.scorer.calculate_scores(
                        noticia.texto_completo,
                        noticia.titulo
                    )
                    score_data['noticia_id'] = noticia.id
                    
                    saved_score = self.db.save_score(score_data)
                    if saved_score:
                        scoring_count += 1
            
            logger.info(f"🎯 Scores calculados: {scoring_count}")
            
            # Limpeza de dados antigos
            logger.info("🧹 Limpando dados antigos...")
            cleaned_count = self.db.cleanup_old_news()
            logger.info(f"🧹 Notícias antigas removidas: {cleaned_count}")
            
            # Finaliza execução
            execution_time = time.time() - start_time
            execution_log.update({
                'noticias_processadas': scoring_count,
                'tempo_execucao': execution_time,
                'status': 'sucesso',
                'log_detalhes': {
                    'camara_coletadas': len(camara_news),
                    'senado_coletadas': len(senado_news),
                    'salvas_banco': saved_count,
                    'textos_extraidos': extraction_count,
                    'scores_calculados': scoring_count,
                    'limpeza_antigas': cleaned_count
                }
            })
            
            # Salva log da execução
            self.db.save_execucao(execution_log)
            
            logger.info(f"✅ COLETA COMPLETA FINALIZADA em {execution_time:.1f}s")
            logger.info(f"📊 Resumo: {len(all_news)} coletadas, {scoring_count} processadas")
            
            return execution_log
            
        except Exception as e:
            execution_time = time.time() - start_time
            execution_log.update({
                'tempo_execucao': execution_time,
                'status': 'erro',
                'log_detalhes': {'erro': str(e)}
            })
            
            self.db.save_execucao(execution_log)
            logger.error(f"❌ Erro na coleta completa: {e}")
            raise
    
    def get_statistics(self):
        """Retorna estatísticas do sistema"""
        stats = self.db.get_stats()
        logger.info("📊 ESTATÍSTICAS DO SISTEMA:")
        logger.info(f"Total de notícias: {stats.get('total_noticias', 0)}")
        logger.info(f"Notícias favoritas: {stats.get('noticias_favoritas', 0)}")
        
        if 'por_fonte' in stats:
            logger.info("Distribuição por fonte:")
            for fonte, count in stats['por_fonte'].items():
                logger.info(f"  {fonte}: {count}")
        
        if 'por_categoria' in stats:
            logger.info("Distribuição por categoria:")
            for categoria, count in stats['por_categoria'].items():
                logger.info(f"  {categoria}: {count}")
        
        return stats
    
    def close(self):
        """Fecha recursos do sistema"""
        try:
            self.camara_scraper.close()
            self.senado_scraper.close()
            self.content_extractor.close()
            self.db.close()
            logger.info("Sistema fechado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao fechar sistema: {e}")

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sistema de Clipping Legislativo FACIAP')
    parser.add_argument('--test-scrapers', action='store_true', help='Testa scrapers')
    parser.add_argument('--test-extraction', action='store_true', help='Testa extração de conteúdo')
    parser.add_argument('--test-scoring', action='store_true', help='Testa sistema de scoring')
    parser.add_argument('--full-collection', action='store_true', help='Executa coleta completa')
    parser.add_argument('--stats', action='store_true', help='Mostra estatísticas')
    parser.add_argument('--pages-camara', type=int, default=10, help='Páginas da Câmara')
    parser.add_argument('--pages-senado', type=int, default=10, help='Páginas do Senado')
    
    args = parser.parse_args()
    
    system = ClippingSystem()
    
    try:
        if args.test_scrapers:
            system.test_scrapers(3)
        
        elif args.test_extraction:
            system.test_content_extraction()
        
        elif args.test_scoring:
            system.test_scoring()
        
        elif args.full_collection:
            system.run_full_collection(args.pages_camara, args.pages_senado)
        
        elif args.stats:
            system.get_statistics()
        
        else:
            # Execução padrão: testa todos os componentes
            logger.info("🔧 EXECUTANDO TESTES COMPLETOS...")
            
            # Testa scrapers
            system.test_scrapers(2)
            
            # Testa extração
            system.test_content_extraction()
            
            # Testa scoring
            system.test_scoring()
            
            # Mostra estatísticas
            system.get_statistics()
            
            logger.info("✅ TESTES COMPLETOS FINALIZADOS")
    
    finally:
        system.close()

if __name__ == "__main__":
    main()

