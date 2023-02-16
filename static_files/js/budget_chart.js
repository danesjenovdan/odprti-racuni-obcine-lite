const budgetData = window.__BUDGET_DATA__;

const years = Object.keys(budgetData).sort();

const dataByCode = {};
years.forEach((year) => {
  const yearData = budgetData[year];
  yearData.forEach((d) => {
    dataByCode[d.code] = dataByCode[d.code] || [];
    dataByCode[d.code].push({
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
    dataValues[years.indexOf(d.year)] = Number(d.amount);
  });

  data.push({
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

function isLastColumn(ctx) {
  const dataSize = ctx.chart.data.datasets[ctx.datasetIndex].data.length;
  return ctx.dataIndex === dataSize - 1;
}

Chart.Tooltip.positioners.center = function (elements, eventPosition) {
  if (elements.length) {
    const { x, y, base } = elements[0].element;
    const height = !base ? 0 : base - y;
    return { x, y: y + height / 2 };
  }
  return false;
};

const chartElem1 = document.getElementById("budget_chart1");
const chartElem2 = document.getElementById("budget_chart2");

const budgetChart1 = new Chart(chartElem1, {
  type: "line",
  data: {
    labels: years,
    datasets: data.map((dataset, i) => {
      return {
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
          borderDash: (ctx) => (isLastSegment(ctx) ? [6, 6] : undefined),
        },
      };
    }),
  },
  options: {
    responsive: false,
    animation: false,
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
      },
    },
    plugins: {
      tooltip: {
        position: "center",
      },
      legend: {
        position: "left",
      },
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

const budgetChart2 = new Chart(chartElem2, {
  type: "bar",
  data: {
    labels: years,
    datasets: data.map((dataset, i) => {
      return {
        label: dataset.label,
        backgroundColor: (ctx) => {
          if (isLastColumn(ctx)) {
            return pattern.draw("diagonal", `${getColor(i)}88`, `#0006`, 16);
          }
          return `${getColor(i)}aa`;
        },
        data: dataset.values,
      };
    }),
  },
  options: {
    responsive: false,
    animation: false,
    elements: {
      bar: {
        borderWidth: 1,
        borderColor: "#444",
      },
    },
    plugins: {
      tooltip: {
        position: "center",
      },
      legend: {
        position: "left",
      },
    },
    scales: {
      y: { stacked: true },
      x: { stacked: true },
    },
  },
});
