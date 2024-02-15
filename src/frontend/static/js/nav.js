fetch("/sup/navbar")
.then(res => res.text())
.then(text => {
  let oldelem = document.querySelector("script#replace_with_navbar");
  let newelem = document.createElement("div");
  newelem.innerHTML = text;
  oldelem.replaceWith(newelem);
});
fetch("/sup/footer")
.then(res => res.text())
.then(text => {
  let oldelem = document.querySelector("div#replace_with_footer");
  let newelem = document.createElement("div");
  newelem.innerHTML = text;
  oldelem.replaceWith(newelem);

  // Now that footer exists, we can fill in the details
  fetch("/api/database/get/")
    .then(res => res.json())
    .then(data => {
      const footer_frontend_p = document.getElementById("footer_frontend_p");
      const footer_backend_p = document.getElementById("footer_backend_p");
      footer_frontend_p.innerText = format(footer_frontend_p.innerText, data["frontend_version"]);
      footer_backend_p.innerText = format(footer_backend_p.innerText, data["api_version"]);
    })
})