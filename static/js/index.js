document.getElementById('burgerBtn').onclick = function() {
  document.getElementById('menuNav').classList.toggle('open');
};
document.addEventListener('click', function(e) {
  const menu = document.getElementById('menuNav');
  const burger = document.getElementById('burgerBtn');
  if (!menu.contains(e.target) && !burger.contains(e.target)) {
    menu.classList.remove('open');
  }
});
  function openModal(offre, prix) {
  document.getElementById("overlay").style.display = "flex";
  document.getElementById("offreChoisie").innerText = "Offre : " + offre + " - Prix : " + prix + "$";
  document.getElementById("inputService").value = offre;
  document.getElementById("inputPrix").value = prix;
  choix={ offre:offre,prix:prix}//initialisation du prix
  goToPage("page1");
}

function closeModal() {
  document.getElementById("overlay").style.display = "none";
}

function goToPage(id) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.getElementById(id).classList.add("active");
}

function nextPage(service) {
  if (service === "mpesa") goToPage("page-mpesa");
  if (service === "airtel") goToPage("page-airtel");
  if (service === "orange") goToPage("page-orange");
}

// Copier numéro
function copyToClipboard(el) {
  navigator.clipboard.writeText(el.innerText);
  alert("Numéro copié : " + el.innerText);
}

function submitPayment(formId){
  const form= document.getElementById(formId);
  if (form.checkValidity()){
    goToPage("page3");
  } else{
    alert("Veuillez remplir tous les champs.")
  }
}
let choix={};
function choisirPaiement(moyen){
  choix.moyenPaiement=moyen;
  choix.offre=document.getElementById("inputService").value;
  choix.prix=document.getElementById("inputPrix").value;
  if (moyen === "M-Pesa")goToPage("page-mpesa");
  if (moyen === "Airtel Money")goToPage("page-airtel");
  if (moyen === "Orange Money")goToPage("page-orange");
  document.getElementById("service-titre").innerText="service"+moyen;
}
document.getElementById("paiementForm").addEventListener("submit",
  function(e){
    e.preventDefault();
    let form=e.target;
    let data={
      offre:document.getElementById("inputService").value,
      prix:document.getElementById("inputPrix").value,
      moyenPaiement:choix.moyenPaiement,
      nom: form.nom.value,
      numero:form.numero.value,
      montant:form.montant.value
    };
    fetch("/valider_paiement",{
      method:"POST",
      headers:{"content-Type":"application/json"},
      body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(rep =>{
      alert("Paiement enregistre avec succes!");
      goToPage("page3");
      })
      .catch(err=> console.error(err));
});