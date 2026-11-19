import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'chave-temporaria-trocar-depois'

CAMINHO_BANCO = 'instance/hemera.db'

# Troque o texto abaixo pela senha que você quer para o administrador.
# Ela só é usada uma vez, quando o banco é criado.
SENHA_ADMIN = 'Hemera123'

def get_db():
    return sqlite3.connect(CAMINHO_BANCO)

def criar_banco():
    conexao = get_db()
    cursor = conexao.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            login TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS administrador (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL
        )
    ''')

    cursor.execute("SELECT * FROM administrador WHERE login = 'admin'")
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO administrador (login, senha) VALUES (?, ?)",
            ('admin', generate_password_hash(SENHA_ADMIN))
        )

    # Empresa de teste
    cursor.execute("SELECT * FROM empresas WHERE login = 'teste'")
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO empresas (nome, login, senha) VALUES (?, ?, ?)",
            ('Empresa Teste', 'teste', generate_password_hash('123'))
        )

    conexao.commit()
    conexao.close()

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/entrar', methods=['POST'])
def entrar():
    login_digitado = request.form['login']
    senha_digitada = request.form['senha']

    conexao = get_db()
    cursor = conexao.cursor()

    # Primeiro tenta como administrador
    cursor.execute(
        "SELECT * FROM administrador WHERE login = ?",
        (login_digitado,)
    )
    admin = cursor.fetchone()

    if admin and check_password_hash(admin[2], senha_digitada):
        session['usuario_id'] = admin[0]
        session['tipo'] = 'admin'
        session['nome'] = 'Administrador'
        conexao.close()
        return redirect(url_for('inicio'))

    # Depois tenta como empresa
    cursor.execute(
        "SELECT * FROM empresas WHERE login = ?",
        (login_digitado,)
    )
    empresa = cursor.fetchone()
    conexao.close()

    if empresa and check_password_hash(empresa[3], senha_digitada):
        session['usuario_id'] = empresa[0]
        session['tipo'] = 'empresa'
        session['nome'] = empresa[1]
        return redirect(url_for('inicio'))

    return redirect(url_for('login'))

@app.route('/inicio')
def inicio():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('inicio.html', nome=session['nome'])

@app.route('/lancamento')
def lancamento():
    if session.get('tipo') != 'empresa':
        return redirect(url_for('login'))
    return render_template('lancamento.html')

@app.route('/historico')
def historico():
    if session.get('tipo') != 'empresa':
        return redirect(url_for('login'))
    return render_template('historico.html')

@app.route('/complementares')
def complementares():
    if session.get('tipo') != 'empresa':
        return redirect(url_for('login'))
    return render_template('complementares.html')

@app.route('/sair')
def sair():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    criar_banco()
    app.run(debug=True)