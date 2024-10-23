// javascript/controllers/response_time_graph_controller.js
import { Controller } from "@hotwired/stimulus";
import * as d3 from "d3";

export default class extends Controller {
  static values = {
    data: Array
  };

  connect() {
    requestAnimationFrame(() => {
      this.renderGraph();
    });
  }

  renderGraph() {
    const data = this.dataValue;

    const containerWidth = this.element.offsetWidth;
    const height = 100;
    const margin = { top: 10, right: 30, bottom: 40, left: 60 };
    const width = containerWidth - margin.left - margin.right;

    d3.select(this.element).selectAll("svg").remove();

    const svg = d3.select(this.element)
      .append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    const x = d3.scaleTime()
      .domain(d3.extent(data, d => new Date(d.timestamp)))
      .range([0, width]);

    // Adjust y domain to start at 0 and end at a nice round number
    const yMax = d3.max(data, d => d.response_time);
    const niceMax = this.getNiceRoundNumber(yMax);

    const y = d3.scaleLinear()
      .domain([0, niceMax])
      .range([height, 0]);

    const line = d3.line()
      .x(d => x(new Date(d.timestamp)))
      .y(d => y(d.response_time))
      .curve(d3.curveMonotoneX);

    // Calculate tick values for 6 equally spaced round number labels
    const yTickValues = this.generateRoundTickValues(niceMax, 6);

    // Add grid lines
    const yGridAxis = d3.axisLeft(y)
      .tickValues(yTickValues)
      .tickSize(-width)
      .tickFormat("");

    svg.append("g")
      .attr("class", "grid")
      .attr("opacity", 0.1)
      .call(yGridAxis);

    // Add X axis
    svg.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(
        d3.axisBottom(x)
          .ticks(6)
          .tickFormat(d3.timeFormat("%H:%M"))
      )
      .selectAll("text")
      .style("text-anchor", "end")
      .attr("dx", "-.8em")
      .attr("dy", ".15em")
      .attr("transform", "rotate(-45)")
      .style("font-size", "12px");

    // Add Y axis with 6 round number labels
    svg.append("g")
      .call(
        d3.axisLeft(y)
          .tickValues(yTickValues)
          .tickFormat(d => `${d}ms`)
      )
      .style("font-size", "12px");

    // Add line path
    svg.append("path")
      .datum(data)
      .attr("fill", "none")
      .attr("stroke", "#6366f1")
      .attr("stroke-width", 2)
      .attr("d", line);
  }

  getNiceRoundNumber(num) {
    const exponent = Math.floor(Math.log10(num));
    const factor = Math.pow(10, exponent);
    const normalized = num / factor;

    if (normalized < 1.5) return 1.5 * factor;
    if (normalized < 2) return 2 * factor;
    if (normalized < 3) return 3 * factor;
    if (normalized < 5) return 5 * factor;
    return 10 * factor;
  }

  generateRoundTickValues(max, count) {
    const step = max / (count - 1);
    const roundStep = this.getNiceRoundNumber(step);
    return d3.range(0, max + roundStep, roundStep).slice(0, count);
  }

  initialize() {
    this.resizeObserver = new ResizeObserver(() => {
      this.renderGraph();
    });
    this.resizeObserver.observe(this.element);
  }

  disconnect() {
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }
  }
}
