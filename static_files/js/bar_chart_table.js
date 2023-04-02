(function () {
  const hash = window.location.hash.slice(1);
  const [elemName] = hash.split(";");

  const scrollToElem = document.querySelector(`a[name="${elemName}"]`);
  if (scrollToElem) {
    scrollToElem.scrollIntoView({
      behavior: "instant",
      block: "start",
      inline: "start",
    });
  }

  const tableContainerElem = document.getElementById("js-table-container");
  if (tableContainerElem) {
    tableContainerElem.style.minHeight = "60vh";
    tableContainerElem.addEventListener("click", onTableRowClick, true);
    fetchTable(window.location.search, window.location.hash);
  }

  window.addEventListener("hashchange", onHashChange);

  function onTableRowClick(event) {
    const row = event.target.closest("tbody tr");
    if (row) {
      const link = row.querySelector(".bar-chart-name a");
      if (link) {
        window.location.hash = link.hash;
        return;
      }
    } else {
      const backLink = event.target.closest(".bar-chart-title a");
      if (backLink) {
        window.location.hash = backLink.hash;
        return;
      }
    }
  }

  function onHashChange(event) {
    fetchTable(window.location.search, window.location.hash);
  }

  function fetchTable(searchString, hashString) {
    const url = new URL(window.__BAR_CHART_TABLE_URL__, window.location.origin);
    url.search = searchString;
    let scrollOnLoad = false;

    const [, code] = hashString.slice(1).split(";");
    if (code) {
      url.searchParams.set("code", code);
      scrollOnLoad = true;
    }

    return fetch(url)
      .then(
        (res) => {
          if (!res.ok) {
            console.error(res);
            return `<div class="alert alert-warning">${res.statusText}</div>`;
          }
          return res.text();
        },
        (error) => {
          console.error(error);
          return `<div class="alert alert-danger">${error.message}</div>`;
        }
      )
      .then((text) => {
        tableContainerElem.innerHTML = text;
        if (scrollOnLoad && scrollToElem) {
          scrollToElem.scrollIntoView({
            behavior: "instant",
            block: "start",
            inline: "start",
          });
        }
      });
  }
})();
