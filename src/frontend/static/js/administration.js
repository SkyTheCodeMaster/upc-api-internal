function set_cookie(name, value, expire) {
  const d = new Date();
  d.setTime(d.getTime() + (expire*24*60*60*1000));
  let expires = "expires="+ d.toUTCString();
  document.cookie = name + "=" + value + ";" + expires + ";path=/";
}

function get_cookie(name) {
  var nameEQ = name + "=";
  var ca = document.cookie.split(';');
  for(let i=0;i < ca.length;i++) {
      var c = ca[i];
      while (c.charAt(0)==' ') c = c.substring(1,c.length);
      if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
  }
  return null;
}

function login() {
  if (!get_cookie("Authorization")) {
    var username = prompt("Enter your username");
    var password = prompt("Enter your password");
    var authentication = username + ":" + password;
    set_cookie("Authorization",authentication,1);
  }
}

function db_backup() {
  login();
  var backup_request = new XMLHttpRequest();
  backup_request.open("POST","/api/admin/backup/");
  backup_request.send();
  backup_request.onload = function() {
    if (backup_request.status == 200) {
      window.location = "/database";
    }
  }
}

function clear_misses() {
  login();
  var clearmisses_request = new XMLHttpRequest();
  clearmisses_request.open("POST","/api/admin/clearmisses/");
  clearmisses_request.send();
  clearmisses_request.onload = function() {
    if (clearmisses_request.status == 200) {
      window.location = "/misses";
    }
  }
}