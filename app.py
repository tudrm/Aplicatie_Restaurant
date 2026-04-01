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
        return [f"User('{self.nume}', '{self.email}')"]

class Rezervare(db.Model):
    id_rezervare = db.Column(db.Integer, primary_key = True)
    id_user_rezervare = db.Column(db.Integer, db.ForeignKey("user.id"), nullable = False)
    data = db.Column(db.String(30), nullable = False)
    ora = db.Column(db.String(6), nullable = False)
    numar_persoane = db.Column(db.Integer, nullable = False)

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
    if request.method == "POST":
        data = request.form.get("data")
        ora = request.form.get("ora")
        numar_persoane = request.form.get("numar_persoane")

        toate_rezervarile = Rezervare.query.all()

        for dosar in toate_rezervarile:
            if data == dosar.data and ora == dosar.ora:
                return render_template("rezervare.html", eroare = "Ora selectata este rezervata !")
            
        rezervare_noua = Rezervare(id_user_rezervare = session["user_id"],data = data, ora = ora, numar_persoane = numar_persoane)

        db.session.add(rezervare_noua)
        db.session.commit()

        return redirect("/istoric_rezervari")

    return render_template("rezervare.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect("/")

@app.route("/istoric_rezervari")
def istoric_rezervari():

    if "user_id" not in session:
        return redirect("/login")
    
    rezervarile_mele = Rezervare.query.filter_by(id_user_rezervare = session["user_id"]).all()

    return render_template("istoric_rezervari.html", rezervari_trimise = rezervarile_mele)

@app.route("/delete_rezervare/<int:id_legatura>")
def delete_rezervare(id_legatura):
    if session["user_id"] == None:
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

@app.route("/panou_admin")
def panou_admin():
    if session["user_id"] == None:
      return redirect("/login") 
      
    id_curent = session["user_id"]
    dosar_curent = User.query.get(id_curent)

    if dosar_curent.este_admin is not True:
        return redirect("/istoric_rezervari")
    rezervarile_tuturor = Rezervare.query.all()

    return render_template("panou_admin.html", rezervari_trimise = rezervarile_tuturor)


if __name__== "__main__":
    app.run(debug=True)