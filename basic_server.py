#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Gestao de Projetos - Servidor Full-Stack
Servidor HTTP com banco de dados SQLite, autenticacao JWT e APIs RESTful
"""

import http.server
import socketserver
import json
import sqlite3
import hashlib
import jwt
import re
import os
import urllib.request
import urllib.parse
import base64
import mimetypes
from datetime import datetime, timedelta, timezone

PORT = 8000
SECRET_KEY = "projeto_fullstack_2024_secret_key"
DB_NAME = "sistema_gestao.db"

# Rate limiting simples (IP: timestamp)
login_attempts = {}
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_TIME = 300  # 5 minutos em segundos

class ProjectHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=".", **kwargs)
    
    def send_cors_headers(self):
        """Envia headers CORS"""
        # CORS específico para localhost (mais seguro que *)
        origin = self.headers.get('Origin', f'http://localhost:{PORT}')
        if 'localhost' in origin or '127.0.0.1' in origin:
            self.send_header('Access-Control-Allow-Origin', origin)
        else:
            self.send_header('Access-Control-Allow-Origin', f'http://localhost:{PORT}')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Allow-Credentials', 'true')
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
    
    def get_request_data(self):
        """Le dados da requisicao"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                return json.loads(post_data.decode('utf-8'))
            return {}
        except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
            return {}
    
    def send_json_response(self, data, status=200):
        """Envia resposta JSON"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def verify_token(self):
        """Verifica token JWT"""
        auth_header = self.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            return payload.get('user_id')
        except (jwt.InvalidTokenError, jwt.DecodeError, jwt.ExpiredSignatureError):
            return None
    
    def hash_password(self, password):
        """Criptografa senha"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def do_POST(self):
        """Handle POST requests"""
        path = urllib.parse.urlparse(self.path).path
        
        if path == '/api/register':
            self.handle_register()
        elif path == '/api/login':
            self.handle_login()
        elif path == '/api/lists':
            self.handle_create_project()
        else:
            self.send_json_response({'error': 'Endpoint nao encontrado'}, 404)
    
    def do_GET(self):
        """Handle GET requests"""
        path = urllib.parse.urlparse(self.path).path
        
        if path == '/api/lists':
            self.handle_get_projects()
        elif path.startswith('/api/cep/'):
            cep = path.split('/')[-1]
            self.handle_get_cep(cep)
        elif path == '/api/quotes':
            self.handle_get_quotes()
        else:
            super().do_GET()
    
    def do_PUT(self):
        """Handle PUT requests"""
        path = urllib.parse.urlparse(self.path).path
        
        if path.startswith('/api/lists/') and path != '/api/lists/reorder':
            project_id = path.split('/')[-1]
            self.handle_update_project(project_id)
        elif path == '/api/lists/reorder':
            self.handle_reorder_projects()
        else:
            self.send_json_response({'error': 'Endpoint nao encontrado'}, 404)
    
    def do_DELETE(self):
        """Handle DELETE requests"""
        path = urllib.parse.urlparse(self.path).path
        
        if path == '/api/lists':
            # Deletar todos os projetos do usuário
            self.handle_delete_all_projects()
        elif path.startswith('/api/lists/'):
            project_id = path.split('/')[-1]
            self.handle_delete_project(project_id)
        else:
            self.send_json_response({'error': 'Endpoint nao encontrado'}, 404)
    
    def handle_register(self):
        """Cadastro de usuario"""
        data = self.get_request_data()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        print(f"[DEBUG] /api/register recebido username={username} email={email} len(password)={len(password)}")
        
        if not username or not email or not password:
            self.send_json_response({'error': 'Dados obrigatorios faltando'}, 400)
            return
        
        # Validar formato de email
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            self.send_json_response({'error': 'Email invalido'}, 400)
            return
        
        # Validar username (alfanumérico)
        if not re.match(r'^[a-zA-Z0-9_]{3,30}$', username):
            self.send_json_response({'error': 'Username deve ter 3-30 caracteres (apenas letras, numeros e _)'}, 400)
            return
        
        if len(password) < 6:
            self.send_json_response({'error': 'Senha deve ter pelo menos 6 caracteres'}, 400)
            return
        
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            # Verifica se usuario ja existe
            cursor.execute('SELECT id FROM users WHERE email = ? OR username = ?', (email, username))
            if cursor.fetchone():
                self.send_json_response({'error': 'Usuario ja existe'}, 400)
                return
            
            # Cadastra usuario
            hashed_password = self.hash_password(password)
            cursor.execute(
                'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                (username, email, hashed_password)
            )
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Gera token
            token = jwt.encode({
                'user_id': user_id,
                'username': username,
                'exp': datetime.now(timezone.utc) + timedelta(days=7)
            }, SECRET_KEY, algorithm='HS256')
            
            self.send_json_response({
                'success': True,
                'token': token,
                'user': {'id': user_id, 'username': username, 'email': email}
            })
            print(f"[DEBUG] /api/register sucesso id={user_id}")
            
        except Exception as e:
            print(f"[DEBUG] /api/register erro: {e}")
            self.send_json_response({'error': f'Erro interno: {str(e)}'}, 500)
    
    def handle_login(self):
        """Login de usuario"""
        # Rate limiting por IP
        client_ip = self.client_address[0]
        current_time = datetime.now().timestamp()
        
        # Limpar tentativas antigas
        if client_ip in login_attempts:
            login_attempts[client_ip] = [
                t for t in login_attempts[client_ip] 
                if current_time - t < LOCKOUT_TIME
            ]
        
        # Verificar se excedeu tentativas
        if client_ip in login_attempts and len(login_attempts[client_ip]) >= MAX_LOGIN_ATTEMPTS:
            self.send_json_response({
                'error': f'Muitas tentativas de login. Tente novamente em {LOCKOUT_TIME//60} minutos.'
            }, 429)
            return
        
        data = self.get_request_data()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        print(f"[DEBUG] /api/login recebido email={email} len(password)={len(password)}")
        
        if not email or not password:
            self.send_json_response({'error': 'Email e senha obrigatorios'}, 400)
            return
        
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            hashed_password = self.hash_password(password)
            cursor.execute(
                'SELECT id, username, email FROM users WHERE email = ? AND password = ?',
                (email, hashed_password)
            )
            user = cursor.fetchone()
            conn.close()
            
            if not user:
                print(f"[DEBUG] /api/login falha: usuario nao encontrado")
                # Registrar tentativa falhada
                if client_ip not in login_attempts:
                    login_attempts[client_ip] = []
                login_attempts[client_ip].append(current_time)
                self.send_json_response({'error': 'Email ou senha incorretos'}, 401)
                return
            
            # Limpar tentativas de login em caso de sucesso
            if client_ip in login_attempts:
                del login_attempts[client_ip]
            
            # Gera token
            token = jwt.encode({
                'user_id': user[0],
                'username': user[1],
                'exp': datetime.now(timezone.utc) + timedelta(days=7)
            }, SECRET_KEY, algorithm='HS256')
            
            self.send_json_response({
                'success': True,
                'token': token,
                'user': {'id': user[0], 'username': user[1], 'email': user[2]}
            })
            print(f"[DEBUG] /api/login sucesso user_id={user[0]}")
            
        except Exception as e:
            print(f"[DEBUG] /api/login erro: {e}")
            self.send_json_response({'error': f'Erro interno: {str(e)}'}, 500)
    
    def handle_create_project(self):
        """Criar projeto"""
        user_id = self.verify_token()
        if not user_id:
            self.send_json_response({'error': 'Token invalido'}, 401)
            return
        
        data = self.get_request_data()
        texto = data.get('texto', '').strip()
        description = data.get('description', '').strip()
        priority = data.get('priority', 'medium')
        image_path = data.get('image_path', '')
        pinned = 1 if data.get('pinned') else 0
        
        # Validações de segurança
        if not texto or len(texto) < 3:
            self.send_json_response({'error': 'Titulo deve ter pelo menos 3 caracteres'}, 400)
            return
        
        if len(texto) > 500:
            self.send_json_response({'error': 'Titulo não pode ter mais de 500 caracteres'}, 400)
            return
        
        if len(description) > 1000:
            self.send_json_response({'error': 'Descrição muito longa'}, 400)
            return
        
        # Validar priority
        if priority not in ['low', 'medium', 'high']:
            priority = 'medium'
        
        # Validar tamanho da imagem (2MB em base64 ≈ 2.7MB)
        if image_path and len(image_path) > 2700000:
            self.send_json_response({'error': 'Imagem muito grande (max 2MB)'}, 400)
            return
        
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            # Pega proximo order_index
            cursor.execute('SELECT MAX(order_index) FROM projects WHERE user_id = ?', (user_id,))
            max_order = cursor.fetchone()[0] or 0
            
            cursor.execute('''
                INSERT INTO projects (user_id, texto, description, priority, image_path, pinned, order_index) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, texto, description, priority, image_path, pinned, max_order + 1))
            
            project_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            self.send_json_response({
                'success': True,
                'id': project_id,
                'message': 'Projeto criado com sucesso'
            })
            
        except Exception as e:
            self.send_json_response({'error': f'Erro interno: {str(e)}'}, 500)
    
    def handle_get_projects(self):
        """Listar projetos"""
        user_id = self.verify_token()
        if not user_id:
            self.send_json_response({'error': 'Token invalido'}, 401)
            return
        
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, texto, description, priority, image_path, pinned, order_index, created_at 
                FROM projects WHERE user_id = ? ORDER BY pinned DESC, order_index ASC
            ''', (user_id,))
            
            projects = []
            for row in cursor.fetchall():
                projects.append({
                    'id': row[0],
                    'texto': row[1],
                    'description': row[2],
                    'priority': row[3],
                    'image_path': row[4],
                    'pinned': bool(row[5]),
                    'order_index': row[6],
                    'created_at': row[7]
                })
            
            conn.close()
            self.send_json_response({'success': True, 'items': projects})
            
        except Exception as e:
            self.send_json_response({'error': f'Erro interno: {str(e)}'}, 500)
    
    def handle_update_project(self, project_id):
        """Atualizar projeto"""
        user_id = self.verify_token()
        if not user_id:
            self.send_json_response({'error': 'Token invalido'}, 401)
            return
        
        data = self.get_request_data()
        texto = data.get('texto', '').strip()
        description = data.get('description', '').strip()
        priority = data.get('priority', 'medium')
        image_path = data.get('image_path', '')
        pinned = 1 if data.get('pinned') else 0
        order_index = data.get('order_index')
        
        # Validações de segurança
        if not texto or len(texto) < 3:
            self.send_json_response({'error': 'Titulo deve ter pelo menos 3 caracteres'}, 400)
            return
        
        if len(texto) > 500:
            self.send_json_response({'error': 'Titulo muito longo'}, 400)
            return
        
        if len(description) > 1000:
            self.send_json_response({'error': 'Descrição muito longa'}, 400)
            return
        
        if priority not in ['low', 'medium', 'high']:
            priority = 'medium'
        
        if image_path and len(image_path) > 2700000:
            self.send_json_response({'error': 'Imagem muito grande'}, 400)
            return
        
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            # Atualizar com ou sem order_index
            if order_index is not None:
                cursor.execute('''
                    UPDATE projects SET texto = ?, description = ?, priority = ?, image_path = ?, pinned = ?, order_index = ?
                    WHERE id = ? AND user_id = ?
                ''', (texto, description, priority, image_path, pinned, order_index, project_id, user_id))
            else:
                cursor.execute('''
                    UPDATE projects SET texto = ?, description = ?, priority = ?, image_path = ?, pinned = ?
                    WHERE id = ? AND user_id = ?
                ''', (texto, description, priority, image_path, pinned, project_id, user_id))
            
            if cursor.rowcount == 0:
                self.send_json_response({'error': 'Projeto nao encontrado'}, 404)
                return
            
            conn.commit()
            conn.close()
            
            self.send_json_response({'success': True, 'message': 'Projeto atualizado'})
            
        except Exception as e:
            self.send_json_response({'error': f'Erro interno: {str(e)}'}, 500)
    
    def handle_delete_project(self, project_id):
        """Deletar projeto"""
        user_id = self.verify_token()
        if not user_id:
            self.send_json_response({'error': 'Token invalido'}, 401)
            return
        
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM projects WHERE id = ? AND user_id = ?', (project_id, user_id))
            
            if cursor.rowcount == 0:
                self.send_json_response({'error': 'Projeto nao encontrado'}, 404)
                return
            
            conn.commit()
            conn.close()
            
            self.send_json_response({'success': True, 'message': 'Projeto deletado'})
            
        except Exception as e:
            self.send_json_response({'error': f'Erro interno: {str(e)}'}, 500)
    
    def handle_delete_all_projects(self):
        """Deletar todos os projetos do usuário"""
        user_id = self.verify_token()
        if not user_id:
            self.send_json_response({'error': 'Token invalido'}, 401)
            return
        
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM projects WHERE user_id = ?', (user_id,))
            deleted_count = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            self.send_json_response({
                'success': True, 
                'message': f'{deleted_count} projeto(s) deletado(s)'
            })
            
        except Exception as e:
            self.send_json_response({'error': f'Erro interno: {str(e)}'}, 500)
    
    def handle_reorder_projects(self):
        """Reordenar projetos"""
        user_id = self.verify_token()
        if not user_id:
            self.send_json_response({'error': 'Token invalido'}, 401)
            return
        
        data = self.get_request_data()
        order = data.get('order', [])
        
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            for index, project_id in enumerate(order):
                cursor.execute(
                    'UPDATE projects SET order_index = ? WHERE id = ? AND user_id = ?',
                    (index, project_id, user_id)
                )
            
            conn.commit()
            conn.close()
            
            self.send_json_response({'success': True, 'message': 'Ordem atualizada'})
            
        except Exception as e:
            self.send_json_response({'error': f'Erro interno: {str(e)}'}, 500)
    
    def handle_get_cep(self, cep):
        """Consultar CEP via ViaCEP"""
        # Remove caracteres nao numericos
        cep = ''.join(filter(str.isdigit, cep))
        
        if len(cep) != 8:
            self.send_json_response({'error': 'CEP deve ter 8 digitos'}, 400)
            return
        
        try:
            # Consulta ViaCEP
            url = f'https://viacep.com.br/ws/{cep}/json/'
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            if 'erro' in data:
                self.send_json_response({'error': 'CEP nao encontrado'}, 404)
            else:
                self.send_json_response({'success': True, 'data': data})
                
        except Exception as e:
            # Fallback para dados simulados
            self.send_json_response({
                'success': True,
                'data': {
                    'cep': f'{cep[:5]}-{cep[5:]}',
                    'logradouro': 'Endereco de exemplo',
                    'bairro': 'Bairro de exemplo',
                    'localidade': 'Sao Paulo',
                    'uf': 'SP'
                }
            })
    
    def handle_get_quotes(self):
        """Buscar citacoes motivacionais"""
        import random
        
        quotes = [
            "O sucesso é a soma de pequenos esforços repetidos dia após dia.",
            "A persistência é o caminho do êxito.",
            "Grandes realizações requerem grandes ambições.",
            "O único impossível é aquilo que não tentamos realizar.",
            "A disciplina é a ponte entre objetivos e conquistas.",
            "Sua carreira jamais irá acordar de manhã para dizer que não a ama mais. - Lady Gaga",
            "O céu é o limite... para algumas pessoas. Mire mais alto. Nada é impossível. - Demi Lovato"
        ]
        
        quote = random.choice(quotes)
        self.send_json_response({'success': True, 'quote': quote})

def main():
    print("Sistema de Gestao de Projetos - Servidor Full-Stack")
    print("=" * 60)
    print(f"Servidor rodando em: http://localhost:{PORT}")
    print(f"Banco de dados: {DB_NAME}")
    print(f"Frontend: http://localhost:{PORT}/lista.html")
    print()
    print("Funcionalidades:")
    print("  • Autenticacao JWT")
    print("  • CRUD de projetos")
    print("  • APIs externas (ViaCEP)")
    print("  • Dashboard integrado")
    print("  • Sistema responsivo")
    print()
    print("Pressione Ctrl+C para parar o servidor")
    print("=" * 60)
    
    try:
        # Inicializa banco na primeira execucao
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Tabela de usuarios
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Tabela de projetos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            texto TEXT NOT NULL,
            description TEXT,
            priority TEXT DEFAULT 'medium',
            image_path TEXT,
            pinned INTEGER DEFAULT 0,
            order_index INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )''')
        
        conn.commit()
        conn.close()
        
        with socketserver.TCPServer(("", PORT), ProjectHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServidor parado com sucesso!")
    except Exception as e:
        print(f"Erro no servidor: {e}")
        print("Verifique se a porta 8000 está disponível.")

if __name__ == "__main__":
    main()