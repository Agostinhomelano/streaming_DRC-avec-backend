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

class Abonnements(db.Model):
    id= db.Column(db.Integer,primary_key=True)
    nom=db.Column(db.String(30),nullable=False)
    service=db.Column(db.String(30),nullable=False)
    statut=db.Column(db.Boolean, default=False)
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
    return render_template("users/streaming_rdc.html")

@app.route("/inscription", methods=["GET", "POST"])
def inscription():
    if request.method == "POST":
        nom=request.form['nom']
        mdp = request.form['mdp']
        if not mdp or not nom:
            return render_template("users/inscription.html", erreur="Vous n'avez pas rempli tous les champs", show_register=True)
        utilisateur_existant=Utilisateurs.query.filter_by(nom=nom).first()
        if utilisateur_existant:
            return render_template("users/inscription.html", erreur="Cet utilisateur existe déjà, veuillez choisir un autre nom.", show_register=True)
        nouvel_utilisateur = Utilisateurs(nom=nom, mdp=mdp)
        db.session.add(nouvel_utilisateur)
        db.session.commit()
        retour = url_for('accueil')
        return redirect(retour)
    return render_template("users/inscription.html")

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
            return redirect(next_page or url_for("users/accueil"))
        else:
            return render_template("users/inscription.html", erreur="Identifiants incorrects", show_register=False)
    return render_template("users/inscription.html", show_register=False)

@app.route("/deconnexion",methods=['POST','GET'])
def deconnexion():
    session.clear()
    return redirect(url_for('users/accueil'))

@app.route("/Accueil")
def accueil():
    return render_template("users/index.html", session=session)

@app.route("/iptv")
def iptv():
    return render_template("users/iptv.html", session=session)

@app.route("/netflix")
def netflix():
    return render_template("users/netflix.html", session=session)

@app.route("/Prime video")
def prime_video():
    return render_template("users/prime.html", session=session)

@app.route("/Netflix et Prime video")
def net_prime():
    return render_template("users/netflix_prime.html", session=session)

@app.route("/mon_abonnement")
def mon_abonnement():
    if 'nom' not in session:
        return redirect(url_for('users/connexion', next=url_for('mon_abonnement')))
    return render_template("users/mon_abonnement.html", session=session)

@app.route("/Contact",methods=['POST','GET'])
def contacts():
    if request.method =="POST":
        nom= request.form.get('nom')
        tel = request.form['tel']
        message= request.form['message']
        next_page=request.args.get("next")
        nouveau_commentaire = Commentaire(nom=nom, tel=tel,message=message,next_page=next_page)
        db.session.add(nouveau_commentaire)
        db.session.commit()
        return render_template("users/confirmation.html")
    return render_template("users/contact.html")

@app.route("/confirmation")
def confirmation():
    return render_template("users/confirmation.html", session=session)

@app.route("/admin")
def accueil_admin():
    return render_template("admin/index.html")

@app.route("/admin/utilisateurs")
def list_users():
    users=Utilisateurs.query.all()
    return render_template("admin/list_users.html",users=users)

@app.route("/admin/utilisateurs/Supprimer/<int:id>",methods=["POST"])
def supprimer_utilisateur(id):
    users=Utilisateurs.query.get(id)
    if users:
        db.session.delete(users)
        db.session.commit()
    return redirect(url_for("list_users"))

@app.route("/liste_abonnements")
def list_abonnements():
    return render_template("admin/list_abonnement.html")

@app.route("/admin/liste_commentaires")
def liste_commentaires():
    commentaires=Commentaire.query.all()
    return render_template("admin/commentaire.html",commentaires=commentaires)

@app.route("/admin/liste_commentaires/Supprimer/<int:id>",methods=["POST" , "GET"])
def supprimer_commentaire(id):
    commentaires=Commentaire.query.get(id)
    if commentaires:
        db.session.delete(commentaires)
        db.session.commit()
    return redirect('admin/liste_commentaires')

if __name__=='__main__':
    init_base()
    app.run(debug=True)
