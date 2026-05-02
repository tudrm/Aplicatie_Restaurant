from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "parola_foarte_grea_de_ghicit"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///restaurant.db"

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    nume = db.Column(db.String(100), nullable = False)
    email = db.Column(db.String(120), unique = True, nullable = False)
    parola = db.Column(db.String(25), nullable = False)
    telefon = db.Column(db.String(12), nullable = False)
    este_admin = db.Column(db.Boolean, default = False)

    def __repr__(self):
        return f"User('{self.nume}', '{self.email}')"

class Rezervare(db.Model):
    id_rezervare = db.Column(db.Integer, primary_key = True)
    id_user_rezervare = db.Column(db.Integer, db.ForeignKey("user.id"), nullable = False)
    data = db.Column(db.String(30), nullable = False)
    ora = db.Column(db.String(6), nullable = False)
    numar_persoane = db.Column(db.Integer, nullable = False)
    numar_masa = db.Column(db.Integer, nullable = False)

with app.app_context():
    db.create_all()

@app.route("/")
def acasa():
    return render_template("index.html")

@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "POST":
        email_introdus = request.form.get("email")
        parola_introdusa = request.form.get("parola")

        toti_userii = User.query.all()

        for dosar in toti_userii:
            if dosar.email == email_introdus:
                if dosar.parola == parola_introdusa:
                    session["user_id"] = dosar.id
                    if dosar.este_admin == True:
                        return redirect("/panou_admin")
                    return redirect("/rezervare")
                else:
                    return render_template("login.html", eroare = "Parola introdusa este incorecta !")    
                        
        return render_template("login.html", eroare = "Nu exista niciun cont cu aceasta adresa de email !")
              
    return render_template("login.html")

@app.route("/register", methods = ["GET", "POST"])
def register():
    if request.method == "POST":
        nume_nou = request.form.get("nume")
        email_nou = request.form.get("email")
        parola_noua = request.form.get("parola")
        telefon_nou = request.form.get("telefon")

        toti_userii = User.query.all()

        for dosar in toti_userii:
            if email_nou == dosar.email:
                return render_template("register.html", eroare = "Exista deja un cont cu aceasta adresa de email !")
    
        user_nou = User(nume = nume_nou , email = email_nou, parola = parola_noua, telefon = telefon_nou)

        db.session.add(user_nou)
        db.session.commit()

        session["user_id"] = user_nou.id

        return  redirect ("/rezervare")

    return render_template("register.html")

@app.route("/rezervare", methods = ["GET", "POST"])
def rezervare():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        data = request.form.get("data")
        ora = request.form.get("ora")
        numar_persoane = request.form.get("numar_persoane")
        numar_masa = request.form.get("numar_masa") 

        toate_rezervarile = Rezervare.query.all()

        for dosar in toate_rezervarile:
            if data == dosar.data and ora == dosar.ora and str(dosar.numar_masa) == str(numar_masa):
                return render_template("rezervare.html", eroare = f"Masa {numar_masa} este deja ocupată la data și ora selectată!")
            
        rezervare_noua = Rezervare(id_user_rezervare = session["user_id"], data = data, ora = ora, numar_persoane = numar_persoane, numar_masa=int(numar_masa))

        db.session.add(rezervare_noua)
        db.session.commit()

        return redirect("/istoric_rezervari")

    return render_template("rezervare.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect("/")

@app.route("/istoric_rezervari", methods=["GET", "POST"])
def istoric_rezervari():
    if "user_id" not in session:
        return redirect("/login")
    
    query = Rezervare.query.filter_by(id_user_rezervare=session["user_id"])

    if request.method == "POST":
        an = request.form.get("an")
        luna = request.form.get("luna")
        if an and luna:
            search_pattern = f"{an}-{luna}-%"
            query = query.filter(Rezervare.data.like(search_pattern))

    rezervarile_mele = query.all()

    return render_template("istoric_rezervari.html", rezervari_trimise=rezervarile_mele)

@app.route("/delete_rezervare/<int:id_legatura>")
def delete_rezervare(id_legatura):
    if "user_id" not in session:
        return redirect("/login")
        
    rezervare_stearsa = Rezervare.query.get(id_legatura)
    if rezervare_stearsa != None:
        db.session.delete(rezervare_stearsa)
        db.session.commit()

    id_curent = session["user_id"]
    dosar_curent = User.query.get(id_curent)

    if dosar_curent.este_admin == True:
        return redirect("/panou_admin")
    return redirect("/istoric_rezervari")

@app.route("/panou_admin", methods=["GET", "POST"])
def panou_admin():
    if "user_id" not in session:
      return redirect("/login") 
      
    id_curent = session["user_id"]
    dosar_curent = User.query.get(id_curent)

    if dosar_curent.este_admin is not True:
        return redirect("/istoric_rezervari")
    
    query = db.session.query(Rezervare, User).join(User, Rezervare.id_user_rezervare == User.id)

    if request.method == "POST":
        an = request.form.get("an")
        luna = request.form.get("luna")
        if an and luna:
            search_pattern = f"{an}-{luna}-%"
            query = query.filter(Rezervare.data.like(search_pattern))

    rezervarile_tuturor = query.all()

    return render_template("panou_admin.html", rezervari_trimise=rezervarile_tuturor)

@app.route("/edit_rezervare/<int:id_rezervare>", methods=["GET", "POST"])
def edit_rezervare(id_rezervare):
    if "user_id" not in session:
        return redirect("/login")
    
    rezervare_curenta = Rezervare.query.get(id_rezervare)
    
    if not rezervare_curenta:
        return redirect("/istoric_rezervari")

    user_curent = User.query.get(session["user_id"])
    if user_curent.este_admin == False and rezervare_curenta.id_user_rezervare != user_curent.id:
        return redirect("/istoric_rezervari")

    if request.method == "POST":
        data_noua = request.form.get("data")
        ora_noua = request.form.get("ora")
        persoane_noi = request.form.get("numar_persoane")
        masa_noua = request.form.get("numar_masa")

        suprapunere = Rezervare.query.filter(
            Rezervare.data == data_noua,
            Rezervare.ora == ora_noua,
            Rezervare.numar_masa == int(masa_noua),
            Rezervare.id_rezervare != id_rezervare
        ).first()

        if suprapunere:
            return render_template("edit_rezervare.html", rezervare=rezervare_curenta, eroare=f"Masa {masa_noua} este deja ocupată la data și ora selectată!")

        rezervare_curenta.data = data_noua
        rezervare_curenta.ora = ora_noua
        rezervare_curenta.numar_persoane = persoane_noi
        rezervare_curenta.numar_masa = int(masa_noua)

        db.session.commit()

        if user_curent.este_admin:
            return redirect("/panou_admin")
        return redirect("/istoric_rezervari")

    return render_template("edit_rezervare.html", rezervare=rezervare_curenta)

if __name__== "__main__":
    app.run(debug=True)