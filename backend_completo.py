import sys
import os
from pathlib import Path

# Adiciona o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'Clipping Legislativo FACIAP',
        'version': '1.0.0'
    })

@app.route('/api/status')
def status():
    return jsonify({
        'frontend': 'Funcionando',
        'backend': 'Funcionando',
        'coleta': 'Disponível',
        'sistema': 'Operacional'
    })

@app.route('/api/noticias')
def get_noticias():
    try:
        from core.database.db_manager import db_manager
        
        # Buscar notícias do banco
        noticias, total = db_manager.get_noticias(limit=100)
        
        # Converter para dicionário
        noticias_dict = []
        for noticia in noticias:
            noticias_dict.append({
                'id': noticia.id,
                'titulo': noticia.titulo,
                'fonte': noticia.fonte,
                'link': noticia.link,
                'data_publicacao': noticia.data_publicacao.isoformat() if noticia.data_publicacao else None,
                'resumo': noticia.texto_completo[:200] + '...' if noticia.texto_completo and len(noticia.texto_completo) > 200 else noticia.texto_completo,
                'favorita': noticia.favorita
            })
        
        return jsonify({
            'noticias': noticias_dict,
            'total': total
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'noticias': [],
            'total': 0
        }), 500

if __name__ == '__main__':
    print('🚀 Iniciando Backend Flask...')
    print('📍 Acesse: http://localhost:5000/health' )
    print('📰 Notícias: http://localhost:5000/api/noticias' )
    app.run(host='0.0.0.0', port=5000, debug=True)
