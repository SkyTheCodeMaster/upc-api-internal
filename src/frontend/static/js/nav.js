fetch("/sup/navbar")
.then(res => res.text())
.then(text => {
  let oldelem = document.querySelector("script#replace_with_navbar");
  let newelem = document.createElement("div");
  newelem.innerHTML = text;
  oldelem.replaceWith(newelem);
  get_user_area();
});
fetch("/sup/footer")
.then(res => res.text())
.then(text => {
  let oldelem = document.querySelector("div#replace_with_footer");
  let newelem = document.createElement("div");
  newelem.innerHTML = text;
  oldelem.replaceWith(newelem);
})