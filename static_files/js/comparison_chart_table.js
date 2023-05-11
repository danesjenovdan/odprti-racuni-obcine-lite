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
    tableContainerElem.addEventListener("click", onTableRowClick);
    fetchTable(window.location.search, window.location.hash);
  }

  window.addEventListener("hashchange", onHashChange);

  function onTableRowClick(event) {
    const row = event.target.closest("tbody tr");
    if (row) {
      const link = row.querySelector(".bar-chart-name a");
      if (link) {
        event.stopPropagation();
        console.log(link);
        window.location.hash = link.hash;
        return;
      }
    } else {
      const backLink = event.target.closest(".bar-chart-title a");
      if (backLink) {
        event.stopPropagation();
        console.log(backLink);
        window.location.hash = backLink.hash;
        return;
      } else {
        const legend = event.target.closest(".chart-legend-option");
        if (legend && event.target.tagName === "INPUT") {
          event.stopPropagation();
          {
            const chart = window.comparisonChart;
            chart.data.datasets.forEach((dataset, i) => {
              if (dataset.__comparison_code === `code_${event.target.value}`) {
                const meta = chart.getDatasetMeta(i);
                meta.hidden = !event.target.checked;
              }
            });
            chart.update();
          }
          return;
        }
      }
    }
  }

  function onHashChange(event) {
    fetchTable(window.location.search, window.location.hash);
  }

  function fetchTable(searchString, hashString) {
    const url = new URL(
      window.__COMPARISON_CHART_TABLE_URL__,
      window.location.origin
    );
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
        setInnerHTMLAndExecuteScripts(tableContainerElem, text);
        onTableLoad();
        if (scrollOnLoad && scrollToElem) {
          scrollToElem.scrollIntoView({
            behavior: "instant",
            block: "start",
            inline: "start",
          });
        }
      });
  }

  function setInnerHTMLAndExecuteScripts(elem, html) {
    elem.innerHTML = html;
    elem.querySelectorAll("script").forEach((script) => {
      const newScript = document.createElement("script");
      newScript.innerHTML = script.innerHTML;
      script.parentNode.replaceChild(newScript, script);
    });
  }

  function onTableLoad() {
    const budgetData = window.__CHART_DATA__;

    const years = Object.keys(budgetData).sort();

    const dataByCode = {};
    years.forEach((year) => {
      const yearData = budgetData[year];
      yearData.forEach((d) => {
        if (dataByCode["code_" + d.code] == undefined) {
          dataByCode["code_" + d.code] = [];
        }
        dataByCode["code_" + d.code].push({
          ...d,
          year,
        });
      });
    });

    const data = [];
    Object.keys(dataByCode).forEach((code) => {
      const codeData = dataByCode[code];
      const dataValues = [];

      codeData.forEach((d) => {
        dataValues[years.indexOf(d.year)] = Number(d.planned) || Number(d.amount);
      });

      data.push({
        code,
        label: codeData[0].name,
        values: dataValues,
      });
    });

    console.log(data);

    // -----------------------------------------------------------------------------

    const colors = [
      "#64507d",
      "#8c70ae",
      "#c9a2f9",
      "#efe2fd",
      "#101a34",
      "#283c78",
      "#3756ae",
      "#899acd",
      "#c3cce6",
    ];

    function getColor(i) {
      return colors[i % colors.length];
    }

    function isLastSegment(ctx) {
      const dataSize = ctx.chart.data.datasets[ctx.datasetIndex].data.length;
      return ctx.p1DataIndex === dataSize - 1;
    }

    Chart.Tooltip.positioners.center = function (elements, eventPosition) {
      if (elements.length) {
        const { x, y, base } = elements[0].element;
        const height = !base ? 0 : base - y;
        return { x, y: y + height / 2 };
      }
      return false;
    };

    const chartElem = document.getElementById("comparison_chart");

    window.comparisonChart = new Chart(chartElem, {
      type: "line",
      data: {
        labels: years,
        datasets: data.map((dataset, i) => {
          return {
            __comparison_code: dataset.code,
            stepped: "middle",
            label: dataset.label,
            fill: i === 0 ? "origin" : "-1",
            backgroundColor: `${getColor(i)}aa`,
            borderColor: getColor(i),
            data: dataset.values,
            segment: {
              backgroundColor: (ctx) =>
                isLastSegment(ctx) ? `${getColor(i)}88` : undefined,
              borderColor: (ctx) =>
                isLastSegment(ctx) ? `${getColor(i)}aa` : undefined,
            },
          };
        }),
      },
      options: {
        animation: true,
        elements: {
          point: {
            pointStyle: "circle",
            pointRadius: 3,
            pointHoverRadius: 6,
            borderWidth: 0,
            hoverBorderWidth: 2,
            pointHoverBackgroundColor: "#fff",
          },
          line: {
            borderWidth: 2,
            borderDash: [],
            spanGaps: true,
          },
        },
        plugins: {
          tooltip: { position: "center" },
          legend: { display: false },
        },
        scales: {
          y: { stacked: true },
        },
        interaction: {
          intersect: false,
          mode: "nearest",
          axis: "xy",
        },
      },
    });
  }
})();
