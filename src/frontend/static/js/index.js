function load_item_count() {
  fetch("/api/database/get/")
    .then(res => res.json())
    .then(info => {
      const item_count_title = document.getElementById("item_count_title");
      item_count_title.innerText = format(item_count_title.innerText, info["items"]);
    })
}

function setup() {
  load_item_count();
}

document.addEventListener("DOMContentLoaded", setup);
if (document.readyState == "complete") {
  setup();
}