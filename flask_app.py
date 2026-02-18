from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

global_user = None  # Variabile globale per memorizzare l'utente attuale

app = Flask(__name__)
app.secret_key = 'chiave_segreta'

# Connessione al database MySQL
mydb = mysql.connector.connect(
    host="Andrea06.mysql.pythonanywhere-services.com",
    user="Andrea06",
    password="informatica",
    database="Andrea06$gestione_spese_entrate"
)

def get_cursor():
    return mydb.cursor()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        password = request.form['password']
        
        cursor = get_cursor()
        cursor.execute("INSERT INTO utente (nome, email, password) VALUES (%s, %s, %s)", (nome, email, password))
        mydb.commit()
        cursor.close()

        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    global global_user
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = get_cursor()
        cursor.execute("SELECT id_utente, password FROM utente WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if user and user[1] == password:
            global_user = user[0]  # Salva l'ID utente nella variabile globale
            return redirect(url_for('dashboard'))  

        return "Credenziali errate"

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if global_user is None:
        return redirect(url_for('login'))

    # Calcolo delle entrate totali
    cursor = get_cursor()
    cursor.execute("SELECT SUM(importo) FROM voce WHERE tipo = 'entrata' AND id_utente = %s", (global_user,))
    total_income = cursor.fetchone()[0] or 0  # Se non ci sono entrate, assegna 0

    # Calcolo delle spese totali
    cursor.execute("SELECT SUM(importo) FROM voce WHERE tipo = 'spesa' AND id_utente = %s", (global_user,))
    total_expense = cursor.fetchone()[0] or 0  # Se non ci sono spese, assegna 0

    cursor.close()

    # Calcolo del saldo
    balance = total_income - total_expense

    # Passaggio dei dati alla vista dashboard.html
    return render_template('dashboard.html', total_income=total_income, total_expense=total_expense, balance=balance)

@app.route('/add_transaction', methods=['GET', 'POST'])
def add_transaction():
    if global_user is None:
        return redirect(url_for('login'))  

    if request.method == 'POST':
        importo = float(request.form['importo'])
        data = request.form['data']
        tipo = request.form['tipo']
        id_categoria = int(request.form['categoria'])  

        cursor = get_cursor()
        cursor.execute(
            "INSERT INTO voce (importo, data, tipo, id_utente, id_categoria) VALUES (%s, %s, %s, %s, %s)",
            (importo, data, tipo, global_user, id_categoria))
        mydb.commit()
        cursor.close()

        return redirect(url_for('transactions'))  # Redirige alla pagina delle transazioni

    cursor = get_cursor()
    cursor.execute("SELECT id_categoria, nome FROM categoria")
    categorie = cursor.fetchall()
    cursor.close()

    return render_template('add_transaction.html', categorie=categorie)

@app.route('/transactions')
def transactions():
    if global_user is None:
        return redirect(url_for('login'))

    cursor = get_cursor()
    cursor.execute("""
        SELECT voce.importo, voce.data, voce.tipo, categoria.nome 
        FROM voce 
        JOIN categoria ON voce.id_categoria = categoria.id_categoria 
        WHERE voce.id_utente = %s
        ORDER BY voce.data DESC
    """, (global_user,))

    transazioni = cursor.fetchall()

    cursor.execute("SELECT SUM(importo) FROM voce WHERE tipo = 'entrata' AND id_utente = %s", (global_user,))
    total_income = cursor.fetchone()[0] or 0  

    cursor.execute("SELECT SUM(importo) FROM voce WHERE tipo = 'spesa' AND id_utente = %s", (global_user,))
    total_expense = cursor.fetchone()[0] or 0  

    cursor.close()
    balance = total_income - total_expense  

    return render_template('transactions.html', transazioni=transazioni, total_income=total_income, total_expense=total_expense, balance=balance)

@app.route('/logout')
def logout():
    global global_user
    global_user = None
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)