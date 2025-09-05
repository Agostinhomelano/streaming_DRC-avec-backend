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

class Administracteurs(db.Model):
    id= db.Column(db.Integer,primary_key=True)
    nom=db.Column(db.String(30),nullable=False)
    mdp=db.Column(db.String(200),nullable=False)

class Commentaire(db.Model):
    id= db.Column(db.Integer,primary_key=True)
    nom=db.Column(db.String(30),nullable=False)
    tel=db.Column(db.String(30),nullable=False)
    message=db.Column(db.String(500),nullable=False)
    date_post=db.Column(db.DateTime,default=datetime.utcnow)

class Abonnements(db.Model):
    id= db.Column(db.Integer,primary_key=True)
    utilisateur_id=db.Column(db.Integer,db.ForeignKey('utilisateurs.id'),nullable=False)
    service=db.Column(db.String(30),nullable=False)
    statut=db.Column(db.Boolean, default=False)
    date_debut=db.Column(db.DateTime,default=datetime.utcnow)
    date_fin=db.Column(db.DateTime)
    utilisateur=db.relationship('Utilisateurs',backref=db.backref("abonnements",lazy=True))

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
            return redirect(next_page or url_for("accueil"))
        else:
            return render_template("users/inscription.html", erreur="Identifiants incorrects", show_register=False)
    return render_template("users/inscription.html", show_register=False)

@app.route("/connexion_admin",methods=["POST","GET"])
def connexion_admin():
    if request.method =="POST":
        nom= request.form['nom']
        mdp = request.form['mdp']
        if not mdp or not nom:
            return render_template("admin/inscription.html", erreur="Vous n'avez pas rempli tous les champs", show_register=True)
        else:
            admin=Administracteurs.query.filter_by(nom=nom).first()
        if admin and admin.mdp == mdp :
            session['nom']=admin.nom
            session['id']=admin.id
            next_page=request.args.get("next")
            return redirect(next_page or url_for("accueil_admin"))
        else:
            return render_template("admin/inscription.html", erreur="Identifiants incorrects vous n'etes pas administracteur", show_register=False)
    return render_template("admin/inscription.html", show_register=False)

CODE_ADMIN="001701"
@app.route("/inscription_admin", methods=["GET", "POST"])
def inscription_admin():
    if request.method == "POST":
        nom=request.form['nom']
        mdp = request.form['mdp']
        code_admin= request.form['code_admin']
        if not mdp or not nom or not code_admin:
                return render_template("admin/inscription.html", erreur="Vous n'avez pas rempli tous les champs", show_register=True)
        if code_admin!=CODE_ADMIN:
            return render_template("admin/inscription.html", erreur="informations incorrects vous n'ete pas administracteur", show_register=True)
        else:
            administrateurs_existant=Administracteurs.query.filter_by(nom=nom).first()
            if administrateurs_existant:
                return render_template("admin/inscription.html", erreur="cet utilisateur est deja utilise", show_register=True)
            nouvel_admin = Administracteurs(nom=nom, mdp=mdp)
            db.session.add(nouvel_admin)
            db.session.commit()
            session['nom']=nom
            retour = url_for('accueil_admin')
            return redirect(retour)
    return render_template("admin/inscription.html")

@app.route("/deconnexion_admin",methods=['POST','GET'])
def deconnexion_admin():
    session.clear()
    return render_template("users/index.html")

@app.route("/deconnexion",methods=['POST','GET'])
def deconnexion():
    session.clear()
    return render_template("users/index.html")

@app.route("/accueil")
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
    if 'id' not in session:
        return redirect(url_for('connexion', next=url_for('mon_abonnement')))
    abonnements=Abonnements.query.filter_by(utilisateurs_id=session["id"]).all()
    return render_template("users/mon_abonnement.html",abonnements=abonnements, session=session)

@app.route("/Contact",methods=['POST','GET'])
def contacts():
    if request.method =="POST":
        nom= request.form.get('nom')
        tel = request.form['tel']
        message= request.form['message']
        # next_page=request.args.get("next"),next_page=next_page
        nouveau_commentaire = Commentaire(nom=nom, tel=tel,message=message)
        db.session.add(nouveau_commentaire)
        db.session.commit()
        return render_template("users/confirmation.html")
    return render_template("users/contact.html")

@app.route("/confirmation")
def confirmation():
    return render_template("users/confirmation.html", session=session)

@app.route("/admin")
def accueil_admin():
    if 'nom' not in session:
        return redirect(url_for('connexion_admin', next=url_for('accueil_admin')))
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
    abonnements = Abonnements.query.all()
    return render_template("admin/list_abonnement.html", abonnements=abonnements)

@app.route("/acheter/<service>")
def acheter(service):
    if "id" not in session:
        return redirect(url_for("connexion", next=url_for("acheter", service=service)))
    # Exemple : abonnement d’un mois
    nouvel_abonnement = Abonnements(
        utilisateur_id=session["id"],
        service=service,
        date_fin=datetime.utcnow().replace(month=datetime.utcnow().month + 1)
    )
    db.session.add(nouvel_abonnement)
    db.session.commit()
    return redirect(url_for("mon_abonnement"))

@app.route("/admin/liste_commentaires")
def liste_commentaires():
    commentaires=Commentaire.query.all()
    return render_template("admin/commentaire.html",commentaires=commentaires)

@app.route("/admin/liste_commentaires/supprimer_commentaire/<int:id>",methods=["POST" , "GET"])
def supprimer_commentaire(id):
    commentaires=Commentaire.query.get(id)
    if commentaires:
        db.session.delete(commentaires)
        db.session.commit()
    return redirect(url_for('liste_commentaires'))

if __name__=='__main__':
    init_base()
    app.run(debug=True)
