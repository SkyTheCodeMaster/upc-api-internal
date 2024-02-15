"use strict";

/*
<tr>
  <td>{{ row.upc }}</td>
  <td>{{ row.name }}</td>
  <td>{{ row.quantity }}{{ row.quantity_unit }}</td>
  <td><button class="button is-success is-small" onclick="window.location='/lookup#{{ row.upc }}'">View</button></td>
  <td><button class="button is-link is-small" onclick="window.location='/publish#{{ row.upc }}'">Edit</button></td>
</tr>
*/

function generate_table_row(row) {
  // Take in object of upc, name, quanity, and quantity_unit (output from API)
  // Create all the elements
  let tr = document.createElement("tr");
  let td_paste = document.createElement("td");
  let a_paste = document.createElement("a");
  a_paste.href = "https://paste.skystuff.cc/"+row["paste"];
  a_paste.innerText = row["paste"];
  td_paste.appendChild(a_paste);
  let td_date = document.createElement("td");
  td_date.innerText = row["date"];
  
  // Nest elements
  tr.append(td_paste);
  tr.append(td_date);

  return tr;
}

function fill_table(backups) {
  // This is the resp["backups"] part of API response.
  let table_body = document.getElementById("backup_table_tbody");

  for (let item of backups) {
    let tr = generate_table_row(item);
    table_body.appendChild(tr);
  }
}

function fill_page_selector(data) {
  let current_page = Number(window.location.hash.slice(1));
  let visible_page = current_page+1; // This is for showing the user.
  let total_pages = Math.ceil(data["total"]/50);
  let pagination_list = document.getElementById("pagination_list");
  let pagination_next = document.getElementById("pagination_next");
  let pagination_previous = document.getElementById("pagination_previous");


  // Make buttons work.
  pagination_previous.onclick = function() { window.location.hash = current_page-1; window.location.reload(); }
  pagination_next.onclick = function() { window.location.hash = current_page+1; window.location.reload(); }

  if (current_page == 0) {
    // We don't need a previous if the page is 0.
    pagination_previous.classList.add("is-disabled");
    pagination_previous.setAttribute("disabled", true);
    pagination_previous.onclick = function() {};
  }
  if (current_page == total_pages-1) {
    pagination_next.classList.add("is-disabled");
    pagination_next.setAttribute("disabled", true)
    pagination_next.onclick = function() {};
  }

  // For the list, we want to show:
  // 1 ... current_page-1, current_page, current_page+1 ... total_pages
  // and hide the (... current_page+-1) if that is 1 or total_pages.
  // Build the two end elements.
  let li_goto_one = document.createElement("li");
  let button_goto_one = document.createElement("a");
  button_goto_one.classList.add("pagination-link");
  button_goto_one.innerText = "1";
  button_goto_one.onclick = function() { window.location.hash = 0; window.location.reload(); }
  li_goto_one.appendChild(button_goto_one);

  // Make the ellipsis elements.
  let li_ellipsis = document.createElement("li");
  let span_ellipsis = document.createElement("span");
  span_ellipsis.classList.add("pagination-ellipsis");
  span_ellipsis.innerHTML = "&hellip;"
  li_ellipsis.appendChild(span_ellipsis)

  // Make the last page element
  let li_goto_end = document.createElement("li");
  let button_goto_end = document.createElement("a");
  button_goto_end.classList.add("pagination-link");
  button_goto_end.innerText = total_pages;
  button_goto_end.onclick = function() { window.location.hash = total_pages-1; window.location.reload(); }
  li_goto_end.appendChild(button_goto_end);

  // Previous page
  let li_previous_page = document.createElement("li");
  let button_previous_page = document.createElement("a");
  button_previous_page.classList.add("pagination-link");
  button_previous_page.innerText = visible_page-1;
  button_previous_page.onclick = function() { window.location.hash = current_page-1; window.location.reload(); }
  li_previous_page.appendChild(button_previous_page);

  // Current page. Clicking it does nothing.
  let li_current_page = document.createElement("li");
  let button_current_page = document.createElement("a");
  button_current_page.classList.add("pagination-link", "is-current");
  button_current_page.innerText = visible_page;
  li_current_page.appendChild(button_current_page);

  // Next page.
  let li_next_page = document.createElement("li");
  let button_next_page = document.createElement("a");
  button_next_page.classList.add("pagination-link");
  button_next_page.innerText = visible_page+1;
  button_next_page.onclick = function() { window.location.hash = current_page+1; window.location.reload(); }
  li_next_page.appendChild(button_next_page);

  console.log(current_page, total_pages);
  if (current_page != 0) {
    // Also, if the current page is 0, no sense in showing the first button.
    pagination_list.appendChild(li_goto_one);
  }
  if (current_page != 0 && current_page-1 != 0) {
    // The previous page is not the first, so show the side.
    pagination_list.appendChild(li_ellipsis);
    pagination_list.appendChild(li_previous_page);
  }

  pagination_list.appendChild(li_current_page);

  if (current_page != total_pages-1) {
    pagination_list.appendChild(li_next_page);
  }
  if (current_page+1 != total_pages && current_page+1 != total_pages-1) {
    pagination_list.appendChild(li_ellipsis);
    pagination_list.appendChild(li_goto_end);
  }

}

function fill_all() {
  let page = Number(window.location.hash.slice(1));
  let offset = page*50;
  fetch("/api/database/backups/list/?offset="+offset)
    .then(res => res.json())
    .then(data => {
      let backups = data["backups"];
      fill_table(backups);
      // Fill the showing_x_of_y_backups_p element.
      let showing_x_of_y_backups_h1 = document.getElementById("showing_x_of_y_backups_h1");
      showing_x_of_y_backups_h1.innerText = format(showing_x_of_y_backups_h1.innerText, data["returned"], data["total"]);
      let page_x_of_y_backups_h1 = document.getElementById("page_x_of_y_backups_h1");
      let current_page = page+1;
      let total_pages = Math.ceil(data["total"]/50);
      page_x_of_y_backups_h1.innerText = format(page_x_of_y_backups_h1.innerText, current_page, total_pages);

      fill_page_selector(data)
    })
  fetch("/api/database/get/")
    .then(res => res.json())
    .then(data => {
      let database_info_items = document.getElementById("database_info_items");
      let database_info_total_backups = document.getElementById("database_info_total_backups");
      let database_info_database_size = document.getElementById("database_info_database_size");

      database_info_items.innerText = format(database_info_items.innerText, data["items"]);
      database_info_total_backups.innerText = format(database_info_total_backups.innerText, data["backups"]);
      database_info_database_size.innerText = format(database_info_database_size.innerText, data["db_size"]);
    })
}

function setup() {
  let current_page = Number(window.location.hash.slice(1));
  if (isNaN(current_page)) {
    window.location.hash = "0";
    window.location.reload();
  }
  fill_all();
}

document.addEventListener("DOMContentLoaded", setup);
if (document.readyState == "complete") {
  setup();
}