// Home page "search everything" box: opens the built-in site search.
// Temporary: later this box will call an AI-powered search (embeddings over the site's search index).
document.addEventListener("DOMContentLoaded", function () {
  var box = document.getElementById("home-search");
  if (!box) return;
  function openSearch() {
    var toggle = document.getElementById("__search");
    var input = document.querySelector("[data-md-component='search-query']");
    if (toggle) toggle.checked = true;
    if (input) input.focus();
  }
  box.addEventListener("focus", openSearch);
  box.addEventListener("click", openSearch);
});
