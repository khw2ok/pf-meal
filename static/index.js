/**
 * Add or update url parameters.
 * If url doesn't has any params, return "?key=value"
 * Else url has 1 or more params, return "&key=value"
 * And if url already has key, func update key to value.
 * @param {*} key
 * @param {*} value
 * @returns {string}
 */
function updateUrl(key, value){
  var href = window.location.href;
  var regex = new RegExp("[&\\?]" + key + "=");
  if(regex.test(href)){
    regex = new RegExp("([&\\?])" + key + "=[^&]*");
    return href.replace(regex, "$1" + key + "=" + value);
  } else {
    return (href.indexOf("?") > -1) ? href + "&" + key + "=" + value : href + "?" + key + "=" + value;
  }
};

window.onload = function(){
  if ($(document).width() >= 350){
    $("#main>div").css("min-width", 330)
  } else {
    $("#main>div").css("min-width", $("#main").width())
  }
}
