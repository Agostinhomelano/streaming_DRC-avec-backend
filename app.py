from flask import Flask,render_template,request , redirect , url_for ,session 
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import datetime,date
import os

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///base.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.secret_key="1a6676b463603eaa5118f0a289721f25d52b7fb7be2afebccfadaa455b618b7f"
db=SQLAlchemy(app)

class Utilisateurs(db.Model):#creation d'une table dans la db model represente une table dans la db c'est une class, ici elle herite de sqlalchemy pour fontionner
    id= db.Column(db.Integer,primary_key=True)# numero unique de chaque utilisateur
    nom=db.Column(db.String(30),nullable=False)
    mdp=db.Column(db.String(200),nullable=False)

    def __repr__(self):
            return f"base {self.nom}"

class Commentaire(db.Model):
    id= db.Column(db.Integer,primary_key=True)
    nom=db.Column(db.String(30),nullable=False)
    tel=db.Column(db.String(30),nullable=False)
    message=db.Column(db.String(500),nullable=False)
    date_post=db.Column(db.DateTime,default=datetime.utcnow)

def init_base():
    with app.app_context():#contexte d'application pour savoir quelle application appeler
        db.create_all()
    #verification si il y a deja des taches
        if Utilisateurs.query.first() is None:
            print("Taches initiales ajoutees.")
        else:
            print("La base contient deja des donnes.")
@app.route("/")
def introduction():
    return render_template("streaming_rdc.html")

@app.route("/inscription", methods=["GET", "POST"])
def inscription():
    if request.method == "POST":
        nom=request.form['nom']
        mdp = request.form['mdp']
        if not mdp or not nom:
            return render_template("inscription.html", erreur="Vous n'avez pas rempli tous les champs", show_register=True)
        utilisateur_existant=Utilisateurs.query.filter_by(nom=nom).first()
        if utilisateur_existant:
            return render_template("inscription.html", erreur="Cet utilisateur existe déjà, veuillez choisir un autre nom.", show_register=True)
        nouvel_utilisateur = Utilisateurs(nom=nom, mdp=mdp)
        db.session.add(nouvel_utilisateur)
        db.session.commit()
        retour = url_for('accueil')
        return redirect(retour)
    return render_template("inscription.html")

@app.route("/connexion",methods=["POST","GET"])
def connexion():
    if request.method =="POST":
        nom= request.form['nom']
        mdp = request.form['mdp']
        utilisateur=Utilisateurs.query.filter_by(nom=nom).first()
        if utilisateur and utilisateur.mdp == mdp :
            session['nom']=utilisateur.nom
            session['id']=utilisateur.id
            next_page=request.args.get("next")
            return redirect(next_page or url_for("accueil"))
        else:
            return render_template("inscription.html", erreur="Identifiants incorrects", show_register=False)
    return render_template("inscription.html", show_register=False)

@app.route("/deconnexion",methods=['POST','GET'])
def deconnexion():
    session.clear()
    return redirect(url_for('accueil'))

@app.route("/Accueil")
def accueil():
    return render_template("index.html", session=session)

@app.route("/iptv")
def iptv():
    return render_template("iptv.html", session=session)

@app.route("/netflix")
def netflix():
    return render_template("netflix.html", session=session)

@app.route("/Prime video")
def prime_video():
    return render_template("prime.html", session=session)

@app.route("/Netflix et Prime video")
def net_prime():
    return render_template("netflix_prime.html", session=session)

@app.route("/Contact",methods=['POST','GET'])
def contacts():
    if request.method =="POST":
        nom= request.form.get('nom')
        tel = request.form['tel']
        message= request.form['message']
        next_page=request.args.get("next")
        nouveau_commentaire = Commentaire(nom=nom, tel=tel,message=message)
        db.session.add(nouveau_commentaire)
        db.session.commit()
        return redirect(next_page or url_for("accueil"))
    return render_template("contact.html")

if __name__=='__main__':
    init_base()
    app.run(debug=True)
