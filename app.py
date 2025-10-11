from flask import Flask, render_template, request, redirect, url_for, session, jsonify,flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///base.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "1a6676b463603eaa5118f0a289721f25d52b7fb7be2afebccfadaa455b618b7f"
db = SQLAlchemy(app)

# -------------------- MODELES --------------------

class Utilisateurs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(30), nullable=False)
    mdp = db.Column(db.String(200), nullable=False)

    def _repr_(self):
        return f"base {self.nom}"

class Administracteurs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(30), nullable=False)
    mdp = db.Column(db.String(200), nullable=False)

class Commentaire(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(30), nullable=False)
    tel = db.Column(db.String(30), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    date_post = db.Column(db.DateTime, default=datetime.utcnow)

class Abonnements(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    service = db.Column(db.String(30), nullable=False)
    statut = db.Column(db.Boolean, default=True)  # actif à la création
    date_debut = db.Column(db.DateTime, default=datetime.utcnow)
    date_fin = db.Column(db.DateTime, nullable=False)

    utilisateur = db.relationship('Utilisateurs', backref=db.backref("abonnements", lazy=True))

    @property
    def est_actif(self) -> bool:
        return datetime.utcnow() <= (self.date_fin or datetime.utcnow())

    @property
    def jours_restants(self) -> int:
        if not self.date_fin:
            return 0
        delta = self.date_fin - datetime.utcnow()
        return max(delta.days, 0)

class Paiement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    service = db.Column(db.String(30), nullable=False)
    moyen = db.Column(db.String(20),nullable=False)
    nom_compte=db.Column(db.String(50), nullable=False)
    numero=db.Column(db.String(20), nullable=False)
    montant=db.Column(db.Float, nullable=False)
    statut = db.Column(db.Boolean, default=False)
    date_paiement = db.Column(db.DateTime, default=datetime.utcnow)
    utilisateur=db.relationship("Utilisateurs", backref="paiememts",lazy=True)

# -------------------- INIT DB --------------------

def init_base():
    with app.app_context():
        db.create_all()
        if Utilisateurs.query.first() is None:
            print("Taches initiales ajoutees.")
        else:
            print("La base contient deja des donnes.")
def page_precedentes():
    page_precedente= request.referrer or url_for('accueil')#permet de recuperer la page precedente pour le bouton retour   
    return page_precedente

# -------------------- PAGES PUBLIQUES --------------------

@app.route("/")
def introduction():
    return render_template("users/streaming_rdc.html")

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

# -------------------- AUTH UTILISATEUR --------------------

@app.route("/inscription", methods=["GET", "POST"])
def inscription():
    if request.method == "POST":
        nom = request.form['nom']
        mdp = request.form['mdp']
        if not mdp or not nom:
            return render_template("users/inscription.html", erreur="Vous n'avez pas rempli tous les champs", show_register=True)

        utilisateur_existant = Utilisateurs.query.filter_by(nom=nom).first()
        if utilisateur_existant:
            return render_template("users/inscription.html", erreur="Cet utilisateur existe déjà, veuillez choisir un autre nom.", show_register=True)

        nouvel_utilisateur = Utilisateurs(nom=nom, mdp=mdp)
        db.session.add(nouvel_utilisateur)
        db.session.commit()

        # 🔑 session utilisateur (séparée)
        session['user_id'] = nouvel_utilisateur.id
        session['nom'] = nouvel_utilisateur.nom  # conservé pour tes templates actuels
        return redirect(url_for('accueil'))
    return render_template("users/inscription.html")

@app.route("/connexion", methods=["POST", "GET"])
def connexion():
    if request.method == "POST":
        nom = request.form['nom']
        mdp = request.form['mdp']
        utilisateur = Utilisateurs.query.filter_by(nom=nom).first()
        if utilisateur and utilisateur.mdp == mdp:
            session['user_id'] = utilisateur.id
            session['nom'] = utilisateur.nom
            next_page = request.args.get("next")
            return redirect(next_page or url_for("accueil"))
        else:
            return render_template("users/inscription.html", erreur="Identifiants incorrects", show_register=False)
    return render_template("users/inscription.html", show_register=False)

@app.route("/deconnexion", methods=['POST','GET'])
def deconnexion():
    # ❌ on ne touche qu'aux clés user
    session.pop("user_id", None)
    session.pop("nom", None)
    return render_template("users/index.html")

# -------------------- AUTH ADMIN --------------------

CODE_ADMIN = "001701"

@app.route("/connexion_admin", methods=["POST", "GET"])
def connexion_admin():
    if request.method == "POST":
        nom = request.form['nom']
        mdp = request.form['mdp']
        if not mdp or not nom:
            return render_template("admin/inscription.html", erreur="Vous n'avez pas rempli tous les champs", show_register=True)
        admin = Administracteurs.query.filter_by(nom=nom).first()
        if admin and admin.mdp == mdp:
            session['admin_id'] = admin.id
            session['admin_nom'] = admin.nom  # séparé du 'nom' utilisateur
            next_page = request.args.get("next")
            return redirect(next_page or url_for("accueil_admin"))
        else:
            return render_template("admin/inscription.html", erreur="Identifiants incorrects vous n'etes pas administracteur", show_register=False)
    return render_template("admin/inscription.html", show_register=False)

@app.route("/inscription_admin", methods=["GET", "POST"])
def inscription_admin():
    if request.method == "POST":
        nom = request.form['nom']
        mdp = request.form['mdp']
        code_admin = request.form['code_admin']
        if not mdp or not nom or not code_admin:
            return render_template("admin/inscription.html", erreur="Vous n'avez pas rempli tous les champs", show_register=True)
        if code_admin != CODE_ADMIN:
            return render_template("admin/inscription.html", erreur="informations incorrects vous n'ete pas administracteur", show_register=True)

        administrateurs_existant = Administracteurs.query.filter_by(nom=nom).first()
        if administrateurs_existant:
            return render_template("admin/inscription.html", erreur="cet utilisateur est deja utilise", show_register=True)

        nouvel_admin = Administracteurs(nom=nom, mdp=mdp)
        db.session.add(nouvel_admin)
        db.session.commit()
        session['admin_id'] = nouvel_admin.id
        session['admin_nom'] = nouvel_admin.nom
        return redirect(url_for('accueil_admin'))
    return render_template("admin/inscription.html")

@app.route("/deconnexion_admin", methods=['POST','GET'])
def deconnexion_admin():
    # ❌ on ne touche qu'aux clés admin
    session.pop("admin_id", None)
    session.pop("admin_nom", None)
    return render_template("users/index.html")

# -------------------- ABONNEMENTS (USER) --------------------

@app.route("/Formulaire_de_paiement", methods=['POST','GET'])
def formulaire_paiement():
    h1="Merci pour votre confiance !"
    p1="Votre paiement a bien été envoyé."
    p2="Nous vous répondrons dans les plus brefs délais."
    m="Retour"
    if 'user_id' not in session:
        return redirect(url_for('connexion',next=url_for('formulaire_paiement')))
    service={
        "netflix":["Netflix classique","Netflix fidélité","Netflix economie","Netflix VIP"],
        "prime_video":["prime_video classique","prime_video fidélité","prime_video economie","prime_video VIP"],
        "iptv":["iptv pour 3 mois","iptv pour 6 mois","iptv pour 12 mois"],
    }
    if request.method == "POST":
        service=request.form['service']
        moyen=request.form['moyen']
        nom_compte=request.form['nom_compte']
        numero=request.form['numero']
        montant=request.form['montant']

         # Vérification : abonnement actif pour ce service ?
        abonnement_actif = Abonnements.query.filter(
            Abonnements.utilisateur_id == session["user_id"],
            Abonnements.service == service[0],  # service principal
            Abonnements.date_fin >= datetime.utcnow(),
            Abonnements.statut == True
        ).first()
        if abonnement_actif:
            erreur = "Vous avez déjà un abonnement actif pour ce service. Veuillez attendre la fin de votre abonnement actuel avant de payer à nouveau."
            return render_template("users/paiement.html", session=session, service=service, erreur=erreur)

        new_paiement= Paiement(
        utilisateur_id=session["user_id"],
        service=service,
        moyen=moyen,
        nom_compte=nom_compte,
        numero= numero,
        montant=montant,
        statut=True,
        date_paiement=datetime.now()
        )
        db.session.add(new_paiement)
        db.session.commit()
        return render_template("users/confirmation.html",h1=h1,p1=p1,p2=p2,retour=page_precedentes(), m=m)
    return render_template("users/paiement.html",session=session,service=service,retour=page_precedentes())

@app.route("/admin/valider_paiement/<int:id>", methods=["POST","GET"])
def valider_paiement(id):
    paiement=Paiement.query.get_or_404(id)
    nouvel_abonnement=Abonnements(
        utilisateur_id=paiement.utilisateur_id,
        service=paiement.service,
        date_debut=datetime.utcnow(),
        date_fin=datetime.utcnow()+timedelta(days=30),
        statut=True
        )
    db.session.add(nouvel_abonnement)
    db.session.delete(paiement)
    db.session.commit()
    print("c'est bon tout marche bien")
    return redirect(url_for('liste_paiement'))

@app.route("/admin/liste_paiement/supprimer_paiement/<int:id>", methods=["POST", "GET"])
def supprimer_paiement(id):
    paiement=Paiement.query.get(id)
    if not paiement:
      flash("Paiement introuvable","danger")
      return redirect(url_for("liste_paiement"))
    db.session.delete(paiement)
    db.session.commit()
    flash("paiement Suprimer")
    return redirect(url_for('liste_paiement'))

@app.route("/mon_abonnement")
def mon_abonnement():
    if 'user_id' not in session:
        return redirect(url_for('connexion', next=url_for('mon_abonnement')))
    abonnements = Abonnements.query.filter_by(utilisateur_id=session["user_id"]).order_by(Abonnements.date_fin.desc()).all()
    return render_template("users/mon_abonnement.html", abonnements=abonnements, session=session)

# -------------------- CONTACT --------------------

@app.route("/Contact", methods=['POST','GET'])
def contacts():
    h1="Merci pour votre commentaire !"
    p1="Votre message a bien été envoyé."
    p2="Nous vous répondrons dans les plus brefs délais."
    m="Ajouter encore un commentaire?"
    if request.method == "POST":
        nom = request.form.get('nom')
        tel = request.form['tel']
        message = request.form['message']
        nouveau_commentaire = Commentaire(nom=nom, tel=tel, message=message)
        db.session.add(nouveau_commentaire)
        db.session.commit()
        return render_template("users/confirmation.html",h1=h1,p1=p1,p2=p2,retour=page_precedentes(),m=m)
    return render_template("users/contact.html")

@app.route("/confirmation")
def confirmation():
    return render_template("users/confirmation.html", session=session)

# -------------------- ADMIN --------------------

@app.route("/admin")
def accueil_admin():
    if 'admin_id' not in session:
        return redirect(url_for('connexion_admin', next=url_for('accueil_admin')))
    return render_template("admin/index.html")

@app.route("/admin/utilisateurs")
def list_users():
    users = Utilisateurs.query.all()
    return render_template("admin/list_users.html", users=users)

@app.route("/admin/utilisateurs/Supprimer/<int:id>", methods=["POST"])
def supprimer_utilisateur(id):
    user = Utilisateurs.query.get(id)
    if user:
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for("list_users"))

@app.route("/liste_abonnements")
def list_abonnements():
    # route conservée telle quelle (ta page admin)
    num=1
    abonnements = Abonnements.query.order_by(Abonnements.date_fin.desc()).all()
    return render_template("admin/list_abonnement.html", abonnements=abonnements,num=num)

@app.route("/admin/liste_abonnements/supprimer_abonnement/<int:id>", methods=["POST", "GET"])
def supprimer_abonnement(id):
    abonnement = Abonnements.query.get_or_404(id)
    db.session.delete(abonnement)
    db.session.commit()
    flash("abonnement Suprimer")
    return redirect(url_for('list_abonnements'))

@app.route("/admin/liste_commentaires")
def liste_commentaires():
    commentaires = Commentaire.query.all()
    return render_template("admin/commentaire.html", commentaires=commentaires)

@app.route("/admin/liste_commentaires/supprimer_commentaire/<int:id>", methods=["POST", "GET"])
def supprimer_commentaire(id):
    commentaire = Commentaire.query.get(id)
    if commentaire:
        db.session.delete(commentaire)
        db.session.commit()
    return redirect(url_for('liste_commentaires'))

@app.route("/admin/liste_paiement")
def liste_paiement():
    paiements = Paiement.query.order_by(Paiement.date_paiement.desc()).all()
    return render_template("admin/liste_paiement.html", paiements=paiements)

@app.route("/admin/list_activite")
def list_activite():
    return render_template("admin/list_activite.html")

# -------------------- RUN --------------------

if __name__ == '__main__':
    init_base()
    app.run(debug=True)
    