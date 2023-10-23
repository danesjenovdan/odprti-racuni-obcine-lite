(function () {
  let codeToName = {};
  let codeKeys = new Set();
  let data = [];
  let selectedColumnIndex = 1;

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

  function capFirstIfAllCaps(string) {
    if (!string) {
      return string;
    }
    if (string === string.toUpperCase()) {
      return string.charAt(0).toUpperCase() + string.slice(1).toLowerCase();
    }
    return string;
  }

  function fetchChartData(searchString, hashString) {
    const url = new URL(
      window.__COMPARISON_CHART_DATA_URL__,
      window.location.origin
    );
    url.search = searchString;

    const [, code] = hashString.slice(1).split(";");
    if (code) {
      url.searchParams.set("code", code);
    }

    // only show loader if it takes more than 0.5s
    const loaderTimeout = setTimeout(() => {
      document.querySelector(".loader-bg").classList.remove("hidden-sac");
    }, 500);

    const hideLoader = () => {
      clearTimeout(loaderTimeout);
      document.querySelector(".loader-bg").classList.add("hidden-sac");
    };

    fetch(url)
      .then(
        (res) => {
          hideLoader();
          if (!res.ok) {
            console.error(res);
            return { error: res.status };
          }
          return res.json();
        },
        (error) => {
          hideLoader();
          console.error(error);
          return { error: error.message };
        }
      )
      .then((responseData) => {
        prepareData(responseData);
        populateLegendOptions();
        renderChart();
      });
  }

  fetchChartData(window.location.search, window.location.hash);

  function prepareData(responseData) {
    codeToName = {};
    codeKeys = new Set();
    data = [];

    data = Object.keys(responseData.years_data).map((year, i) => {
      if (year === responseData.year) {
        selectedColumnIndex = i;
      }

      const yearData = responseData.years_data[year]
        .map((d) => {
          const codeKey = `code_${d.code}`;
          if (!codeKeys.has(codeKey)) {
            codeKeys.add(codeKey);
            codeToName[codeKey] = d.name;
          }
          return {
            [codeKey]: Number(d.amount || d.planned || 0),
          };
        })
        .reduce((acc, cur) => {
          return { ...acc, ...cur };
        }, {});

      return {
        year: year,
        ...yearData,
      };
    });

    data.forEach((d) => {
      codeKeys.forEach((codeKey) => {
        if (!d[codeKey]) {
          d[codeKey] = 0;
        }
      });
    });
  }

  function renderChart() {
    // remove any old chart contents and clone element to remove all old event listeners
    const oldElem = document.querySelector("#js-comparison-chart");
    oldElem.innerHTML = "";
    const newElem = oldElem.cloneNode(true);
    oldElem.parentNode.replaceChild(newElem, oldElem);

    // Set the dimensions and margins of the graph
    const margin = { top: 20, right: 20, bottom: 30, left: 70 };
    const width = 640 - margin.left - margin.right;
    const height = 480 - margin.top - margin.bottom;

    let hiddenKeys = {};
    let stackedData = d3.stack().keys(Array.from(codeKeys))(data);

    // Define the scales for the x and y axes
    const xScale = d3
      .scaleBand()
      .domain(data.map((d) => d.year))
      .range([0, width]);

    const yScale = d3
      .scaleLinear()
      .domain([0, d3.max(stackedData, (d) => d3.max(d, (d) => d[1]))])
      .range([height, 0]);

    // Set up the SVG container and dimensions
    const svg = d3
      .select("#js-comparison-chart")
      .append("svg")
      .attr(
        "viewBox",
        `0 0 ${width + margin.left + margin.right} ${
          height + margin.top + margin.bottom
        }`
      )
      // .attr("width", width + margin.left + margin.right)
      // .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    const areaSvg = svg
      .append("g")
      .attr("class", "area")
      .attr("transform", `translate(${xScale.bandwidth() / 2},0)`);

    const dotsSvg = svg
      .append("g")
      .attr("class", "dots")
      .attr("transform", `translate(${xScale.bandwidth() / 2},0)`);

    // Add the Y gridlines
    svg
      .append("g")
      .attr("class", "grid")
      .attr("color", "#0001")
      .call(d3.axisLeft(yScale).tickSize(-width).tickFormat(""))
      .call((g) => g.select(".domain").remove());

    // Add the X gridlines
    areaSvg
      .append("g")
      .attr("class", "grid")
      .attr("color", "#0001")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(xScale).tickSize(-height).tickFormat(""))
      .call((g) => g.select(".domain").remove());

    // Create the stacked area generator function using d3.area()
    const areaForAnimation = (zero) =>
      d3
        .area()
        .x((d, i) => xScale(d.data.year))
        .y0((d) => (zero ? yScale(0) : yScale(d[0])))
        .y1((d) => (zero ? yScale(0) : yScale(d[1])))
        .curve(d3_stepMiddle);

    // Draw the stacked area chart
    const areasGroup = areaSvg.append("g").attr("class", "areas");
    function updateArea(animateFromZero = false) {
      let tmp = areasGroup
        .selectAll("path")
        .data(stackedData)
        .join("path")
        .attr("data-key", (d) => d.key)
        .attr("fill", (d, i) => `${getColor(i)}44`);

      if (animateFromZero) {
        tmp = tmp.attr("d", areaForAnimation(true));
      }

      tmp = tmp
        .transition("loadGrow")
        .duration(2000)
        .attr("d", areaForAnimation(false));
    }
    updateArea(true);

    const lineForAnimation = (zero) =>
      d3
        .line()
        .x((d, i) => xScale(d.data.year))
        .y((d, i) => (zero ? yScale(0) : yScale(d[1])))
        .curve(d3_stepMiddle);

    // Draw the lines
    const linesGroup = areaSvg.append("g").attr("class", "lines");
    function updateLines(animateFromZero = false) {
      let tmp = linesGroup
        .selectAll("path")
        .data(stackedData)
        .join("path")
        .attr("data-key", (d) => d.key)
        .attr("fill", "none")
        .attr("stroke", (d, i) => getColor(i));

      if (animateFromZero) {
        tmp = tmp.attr("d", lineForAnimation(true));
      }

      tmp = tmp
        .transition("loadGrow")
        .duration(2000)
        .attr("d", lineForAnimation(false));
    }
    updateLines(true);

    // Draw the dots
    const dots = [];
    const dotsGroups = data.map((d, i) =>
      dotsSvg.append("g").attr("class", `dots-${i}`)
    );
    function updateDots(animateFromZero = false) {
      data.forEach((datum, index) => {
        let tmp = dotsGroups[index]
          .selectAll("circle")
          .data(stackedData)
          .join("circle")
          .attr("data-key", (d) => d.key)
          .attr("cx", (d, i) => xScale(d[index].data.year))
          .attr("r", 3)
          .attr("fill", (d, i) => getColor(i))
          .attr("stroke", "none");

        if (animateFromZero) {
          tmp = tmp.attr("cy", (d, i) => yScale(0));
          dots[index] = tmp;
        }

        tmp
          .transition("loadGrow")
          .duration(2000)
          .attr("cy", (d, i) => yScale(d[index][1]));
      });
    }
    updateDots(true);

    // Draw the box around selected year
    const selectedOutlineGroup = svg.append("g").attr("class", "selection");
    let selectedOutlineElement;
    function updateSelectedOutline(animateFromZero = false) {
      if (animateFromZero) {
        let tmp = selectedOutlineGroup
          .append("rect")
          .attr("id", "selectedYear")
          .attr("fill", "none")
          .attr("stroke", "#000")
          .attr("stroke-width", "2")
          .attr("x", () => xScale.step() * selectedColumnIndex)
          .attr("width", () => xScale.bandwidth())
          .attr("y", yScale(0))
          .attr("height", 0);

        selectedOutlineElement = tmp;
      }

      selectedOutlineElement
        .transition("loadGrow")
        .duration(2000)
        .attr("y", () => {
          const maxValue = d3.max(
            stackedData,
            (d) => d[selectedColumnIndex][1]
          );
          return yScale(maxValue);
        })
        .attr("height", () => {
          const maxValue = d3.max(
            stackedData,
            (d) => d[selectedColumnIndex][1]
          );
          const maxScaleValue = yScale(maxValue);
          const minScaleValue = yScale(yScale.domain()[0]);
          return minScaleValue - maxScaleValue;
        });
    }
    updateSelectedOutline(true);

    const yAxis = d3.axisLeft().scale(yScale);
    const xAxis = d3.axisBottom().scale(xScale);

    // add the X Axis
    svg.append("g").attr("transform", `translate(0,${height})`).call(xAxis);

    // add the Y Axis
    svg.append("g").call(yAxis);

    svg.call(mouseHovered);

    function mouseHovered(elem) {
      const bisectYear = d3.bisector((d) => d.year).center;

      function scaleBandInvert(scale) {
        var domain = scale.domain();
        var paddingOuter = scale(domain[0]);
        var eachBand = scale.step();
        return function (value) {
          var index = Math.floor((value - paddingOuter) / eachBand);
          return domain[Math.max(0, Math.min(index, domain.length - 1))];
        };
      }

      let lastHoveredDot = null;

      elem
        .on("mousemove", (e) => {
          const [pointerX, pointerY] = d3.pointer(e, elem.node());
          const xValue = scaleBandInvert(xScale)(pointerX);
          const yValue = yScale.invert(pointerY);
          const columnIndex = bisectYear(data, xValue);
          const columnValues = stackedData.map((d) => d[columnIndex][1]);
          const valueIndex = columnValues.findIndex((v) => yValue < v);

          if (columnIndex >= dots.length) {
            return;
          }

          const dot = dots[columnIndex].filter((d, i) => i === valueIndex);

          if (lastHoveredDot !== dot.node()) {
            updateTooltip(dot);
            lastHoveredDot = dot.node();

            dots.forEach((dotsCol, index) => {
              dotsCol
                .interrupt("hoverDot")
                .attr("r", 3)
                .attr("fill", (d, i) => getColor(i))
                .attr("stroke", "none");
            });

            dot
              .interrupt("hoverDot")
              .transition("hoverDot")
              .duration(150)
              .attr("r", 6)
              .attr("fill", "white")
              .attr("stroke", (d, i) => getColor(valueIndex))
              .attr("stroke-width", 2);
          }
        })
        .on("mouseleave", (e) => {
          updateTooltip(null);
          lastHoveredDot = null;

          dots.forEach((dotsCol, index) => {
            dotsCol
              .interrupt("hoverDot")
              .attr("r", 3)
              .attr("fill", (d, i) => getColor(i))
              .attr("stroke", "none");
          });
        });
    }

    // Legend checkboxes check/uncheck listener
    const optionsElem = document.querySelector("#js-comparison-options");
    optionsElem.addEventListener("change", (e) => {
      console.log(e.target);
      console.log(e.target.checked);

      const code = e.target.value;
      const checked = e.target.checked;

      if (!checked) {
        hiddenKeys[`code_${code}`] = {};
      }

      data.forEach((v) => {
        if (checked) {
          v[`code_${code}`] = hiddenKeys[`code_${code}`][v.year];
        } else {
          hiddenKeys[`code_${code}`][v.year] = v[`code_${code}`];
          v[`code_${code}`] = 0;
        }
      });

      if (checked) {
        delete hiddenKeys[`code_${code}`];
      }

      stackedData = d3.stack().keys(Array.from(codeKeys))(data);

      d3.selectAll(`[data-key]`).attr("opacity", 1);

      Object.keys(hiddenKeys).forEach((key) => {
        d3.selectAll(`[data-key="${key}"]`)
          .transition()
          .delay(1750)
          .duration(150)
          .attr("opacity", 0);
      });

      updateArea();
      updateLines();
      updateDots();
      updateSelectedOutline();
    });
  }

  function populateLegendOptions() {
    // reset contents to empty old data and clone element to remove all old event listeners
    const oldElem = document.querySelector("#js-comparison-options");
    oldElem.innerHTML = "";
    const newElem = oldElem.cloneNode(true);
    oldElem.parentNode.replaceChild(newElem, oldElem);

    // populate with new data
    [...codeKeys].forEach((codeKey, i) => {
      const code = codeKey.replace("code_", "");
      const name = codeToName[codeKey];
      const template = `
        <div class="chart-legend-option">
          <div class="form-check">
            <input class="form-check-input" type="checkbox" value="${code}" id="checkbox_${code}" checked>
            <label class="form-check-label" for="checkbox_${code}">
              <i class="icon icon-circle" style="background-color: ${getColor(
                i
              )};"></i>
              <span>${capFirstIfAllCaps(name)}</span>
            </label>
          </div>
        </div>
      `;
      newElem.insertAdjacentHTML("beforeend", template);
    });
  }

  function updateTooltip(dot) {
    const chart = document.querySelector("#js-comparison-chart");
    const tooltip = document.querySelector("#js-comparison-chart-tooltip");

    if (!dot) {
      tooltip.style.display = "none";
      return;
    }

    if (dot && dot._groups[0].length > 0) {
      tooltip.style.display = "block";
      svg = chart.querySelector("svg");
      const point = svg.createSVGPoint();
      point.x = dot.attr("cx");
      point.y = dot.attr("cy");
      const matrix = dot.node().getScreenCTM();
      const inverse = matrix.inverse();
      const cursorPoint = point.matrixTransform(matrix);
      tooltip.style.left = `${cursorPoint.x}px`;
      tooltip.style.top = `${cursorPoint.y - 16}px`;

      const d = dot.datum();
      const codeKey = d.key;
      const name = codeToName[codeKey];
      const columnIndex = dot._parents[0].classList[0].split("-")[1];
      const year = data[columnIndex].year;
      const value = data[columnIndex][d.key];

      const formattedName = capFirstIfAllCaps(name);

      const formatter = new Intl.NumberFormat("sl-SI", {
        style: "currency",
        currency: "EUR",
        currencyDisplay: "code",
      });
      const formattedValue = formatter.format(value);

      tooltip.querySelector(".tooltip-name").innerText = formattedName;
      tooltip.querySelector(".tooltip-year").innerText = year;
      tooltip.querySelector(".tooltip-value").innerText = formattedValue;
    }
  }

  window.addEventListener("hashchange", () => {
    fetchChartData(window.location.search, window.location.hash);
  });
})();
