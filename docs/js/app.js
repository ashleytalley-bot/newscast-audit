var __defProp = Object.defineProperty;
var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __publicField = (obj, key, value) => {
  __defNormalProp(obj, typeof key !== "symbol" ? key + "" : key, value);
  return value;
};
import { LOADING_MESSAGES } from "./modules/config.js";
import { ChartRenderer } from "./modules/ChartRenderer.js";
import { TableRenderer } from "./modules/TableRenderer.js";
import { DataExporter } from "./modules/DataExporter.js";
import { CommentRenderer } from "./modules/CommentRenderer.js";
import { PyodideService } from "./services/PyodideService.js";
class NewscastAuditApp {
  constructor() {
    __publicField(this, "pyodideService");
    __publicField(this, "processedData", null);
    __publicField(this, "jsonData", null);
    // Raw Excel data
    __publicField(this, "isInitializingSlider", false);
    __publicField(this, "dom");
    __publicField(this, "chartRenderer");
    __publicField(this, "tableRenderer");
    __publicField(this, "commentRenderer");
    __publicField(this, "exporter");
    console.log("NewscastAuditApp constructor called");
    this.pyodideService = new PyodideService();
    this.dom = {
      uploadSection: document.getElementById("upload-section"),
      resultsSection: document.getElementById("results-section"),
      dropZone: document.getElementById("drop-zone"),
      fileInput: document.getElementById("file-input"),
      loadingIndicator: document.getElementById("loading-indicator"),
      loadingText: document.getElementById("loading-text"),
      errorMessage: document.getElementById("error-message")
    };
    this.validateDom();
    this.chartRenderer = new ChartRenderer();
    this.tableRenderer = new TableRenderer();
    this.commentRenderer = new CommentRenderer();
    this.exporter = new DataExporter();
  }
  validateDom() {
    for (const [key, element] of Object.entries(this.dom)) {
      if (!element) {
        console.error(`CRITICAL: DOM element '${key}' not found!`);
        const errDiv = document.getElementById("error-message");
        if (errDiv) {
          errDiv.classList.remove("hidden");
          errDiv.textContent = `Error: DOM element '${key}' missing. Page structure incorrect.`;
        }
      }
    }
  }
  /**
   * Initialize the application
   */
  init() {
    console.log("Newscast Audit App v2.2.3 - Deployed: 2026-01-18");
    this.setupEventListeners();
  }
  /**
   * Set up all event listeners
   */
  setupEventListeners() {
    this.dom.dropZone.addEventListener("click", () => this.dom.fileInput.click());
    this.dom.fileInput.addEventListener("change", (e) => this.handleFileSelect(e));
    this.dom.dropZone.addEventListener("dragover", (e) => this.handleDragOver(e));
    this.dom.dropZone.addEventListener("dragleave", (e) => this.handleDragLeave(e));
    this.dom.dropZone.addEventListener("drop", (e) => this.handleDrop(e));
    document.getElementById("btn-export-excel")?.addEventListener("click", () => this.exportExcel());
    document.getElementById("btn-export-pptx")?.addEventListener("click", () => this.exportPowerPoint());
    document.getElementById("btn-new-file")?.addEventListener("click", () => this.resetToUpload());
    document.getElementById("btn-copy-comments")?.addEventListener("click", () => this.copyCommentsToClipboard());
  }
  async applyDateFilter() {
    const startInput = document.getElementById("filter-start-date");
    const endInput = document.getElementById("filter-end-date");
    const start = startInput?.value;
    const end = endInput?.value;
    console.log(`Apply Filter Triggered: [${start}] to [${end}]`);
    if (!this.jsonData)
      return;
    this.showLoading("Applying filters...");
    try {
      const options = {
        filter_start_date: start || null,
        filter_end_date: end || null
      };
      const result = await this.pyodideService.processData(this.jsonData, options);
      if (result.success) {
        this.processedData = result;
        this.renderResults();
      } else {
        errorUI.showError(result);
      }
    } catch (e) {
      console.error(e);
      errorUI.showError("Failed to apply filter");
    } finally {
      this.hideLoading();
    }
  }
  async copyCommentsToClipboard() {
    if (!this.processedData || !this.processedData.comments)
      return;
    const comments = this.processedData.comments;
    if (comments.length === 0) {
      alert("No comments to copy.");
      return;
    }
    const text = comments.map((c) => `[${c.date}] ${c.newscast}: ${c.text}`).join("\n");
    try {
      await navigator.clipboard.writeText(text);
      const btn = document.getElementById("btn-copy-comments");
      if (btn) {
        const originalText = btn.innerHTML;
        btn.innerHTML = "Copied!";
        setTimeout(() => {
          btn.innerHTML = originalText;
        }, 2e3);
      }
    } catch (err) {
      console.error("Failed to copy comments: ", err);
      alert("Failed to copy to clipboard.");
    }
  }
  /**
   * Initialize date range slider
   */
  initializeDateFilters(result) {
    let minTimestamp;
    let maxTimestamp;
    let pChartDates = [];
    if (result.charts?.date_range?.min) {
      minTimestamp = new Date(result.charts.date_range.min).getTime();
      maxTimestamp = new Date(result.charts.date_range.max).getTime();
      console.log("Using raw daily date range:", result.charts.date_range);
    } else if (result.charts?.weekly?.full_dates) {
      pChartDates = result.charts.weekly.full_dates.sort();
      if (pChartDates.length > 0) {
        minTimestamp = new Date(pChartDates[0]).getTime();
        maxTimestamp = new Date(pChartDates[pChartDates.length - 1]).getTime();
      }
    }
    if (minTimestamp && maxTimestamp) {
      const minDateObj = new Date(minTimestamp);
      const minDate = Date.UTC(minDateObj.getUTCFullYear(), minDateObj.getUTCMonth(), minDateObj.getUTCDate());
      const maxDateObj = new Date(maxTimestamp);
      const maxDate = Date.UTC(maxDateObj.getUTCFullYear(), maxDateObj.getUTCMonth(), maxDateObj.getUTCDate());
      const DAY_MS = 864e5;
      const totalDays = Math.round((maxDate - minDate) / DAY_MS);
      console.log("Slider Setup (UTC):", {
        minDateStr: new Date(minDate).toISOString().split("T")[0],
        maxDateStr: new Date(maxDate).toISOString().split("T")[0],
        totalDays
      });
      const slider = document.getElementById("date-slider");
      const startInput = document.getElementById("filter-start-date");
      const endInput = document.getElementById("filter-end-date");
      if (!slider)
        return;
      let dayStart = 0;
      let dayEnd = totalDays;
      if (startInput && startInput.value && endInput && endInput.value) {
        const sDate = new Date(startInput.value);
        const curStart = Date.UTC(sDate.getUTCFullYear(), sDate.getUTCMonth(), sDate.getUTCDate());
        const eDate = new Date(endInput.value);
        const curEnd = Date.UTC(eDate.getUTCFullYear(), eDate.getUTCMonth(), eDate.getUTCDate());
        if (!isNaN(curStart) && !isNaN(curEnd)) {
          dayStart = Math.max(0, Math.round((curStart - minDate) / DAY_MS));
          dayEnd = Math.min(totalDays, Math.round((curEnd - minDate) / DAY_MS));
        }
      }
      if (slider.noUiSlider) {
        slider.noUiSlider.destroy();
      }
      this.isInitializingSlider = true;
      try {
        noUiSlider.create(slider, {
          start: [dayStart, dayEnd],
          connect: true,
          behaviour: "drag-tap",
          range: {
            "min": 0,
            "max": totalDays
          },
          step: 1
        });
        const dateValues = document.getElementById("slider-values");
        slider.noUiSlider.on("update", (values, handle) => {
          const startDay = Math.round(Number(values[0]));
          const endDay = Math.round(Number(values[1]));
          const dStart = new Date(minDate + startDay * DAY_MS).toISOString().split("T")[0];
          const dEnd = new Date(minDate + endDay * DAY_MS).toISOString().split("T")[0];
          if (dateValues)
            dateValues.innerHTML = `${dStart}  \u2014  ${dEnd}`;
          if (handle === 0 && startInput)
            startInput.value = dStart;
          else if (endInput)
            endInput.value = dEnd;
        });
        slider.noUiSlider.on("change", () => {
          if (this.isInitializingSlider) {
            console.log("Slider changed during init. Skipping auto-filter.");
            return;
          }
          console.log("Slider released. Auto-applying filter...");
          this.applyDateFilter();
        });
        setTimeout(() => {
          this.isInitializingSlider = false;
          console.log("Slider initialization complete.");
        }, 100);
      } catch (err) {
        console.error("Slider creation failed:", err);
        this.isInitializingSlider = false;
      }
    }
  }
  // ═══════════════════════════════════════════════════════════════════════
  // FILE HANDLING
  // ═══════════════════════════════════════════════════════════════════════
  handleDragOver(e) {
    e.preventDefault();
    this.dom.dropZone.classList.add("drag-over");
  }
  handleDragLeave(e) {
    e.preventDefault();
    this.dom.dropZone.classList.remove("drag-over");
  }
  handleDrop(e) {
    e.preventDefault();
    this.dom.dropZone.classList.remove("drag-over");
    const files = e.dataTransfer?.files;
    if (files && files.length > 0) {
      this.processFile(files[0]);
    }
  }
  handleFileSelect(e) {
    const target = e.target;
    const files = target.files;
    if (files && files.length > 0) {
      this.processFile(files[0]);
    }
  }
  /**
   * Process uploaded Excel file
   */
  async processFile(file) {
    try {
      if (!file.name.match(/\.xlsx?$/i)) {
        errorUI.showError("Please upload an Excel file (.xlsx or .xls)");
        return;
      }
      this.hideError();
      this.showLoading(LOADING_MESSAGES.readingFile);
      const startInput = document.getElementById("filter-start-date");
      const endInput = document.getElementById("filter-end-date");
      if (startInput)
        startInput.value = "";
      if (endInput)
        endInput.value = "";
      const jsonData = await this.parseExcelFile(file);
      this.jsonData = jsonData;
      if (!jsonData || jsonData.length === 0) {
        errorUI.showError("Excel file appears to be empty");
        return;
      }
      this.showLoading(LOADING_MESSAGES.initPython);
      await this.pyodideService.initialize();
      this.showLoading(LOADING_MESSAGES.processing);
      const result = await this.pyodideService.processData(jsonData);
      if (!result.success) {
        errorUI.showError(result);
        this.hideLoading();
        return;
      }
      const output = result;
      const successResult = result;
      if (successResult.quality && (successResult.quality.warnings && successResult.quality.warnings.length > 0 || successResult.quality.info && successResult.quality.info.length > 0)) {
        errorUI.showWarnings(successResult.quality);
      }
      this.showLoading(LOADING_MESSAGES.rendering);
      this.processedData = successResult;
      this.renderResults();
      this.hideLoading();
      this.showResults();
      this.initializeDateFilters(successResult);
    } catch (error) {
      this.hideLoading();
      console.error("Processing error:", error);
      let msg = "Unknown error occurred";
      if (typeof error === "string") {
        msg = error;
      } else if (error instanceof Error) {
        msg = error.message;
      } else if (typeof error === "object" && error !== null) {
        const errObj = error;
        if (errObj.message)
          msg = errObj.message;
        else if (errObj.error)
          msg = errObj.error;
        else {
          try {
            msg = JSON.stringify(error);
          } catch (e) {
            msg = "Error object could not be stringified";
          }
        }
      }
      errorUI.showError(`Error processing file: ${msg}`);
    }
  }
  /**
   * Parse Excel file to JSON using SheetJS
   */
  async parseExcelFile(file) {
    const arrayBuffer = await file.arrayBuffer();
    const workbook = XLSX.read(arrayBuffer, { type: "array", cellDates: true });
    const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
    return XLSX.utils.sheet_to_json(firstSheet);
  }
  // ═══════════════════════════════════════════════════════════════════════════
  // UI STATE MANAGEMENT
  // ═══════════════════════════════════════════════════════════════════════════
  showLoading(message) {
    this.dom.loadingText.textContent = message;
    this.dom.loadingIndicator.classList.remove("hidden");
  }
  hideLoading() {
    this.dom.loadingIndicator.classList.add("hidden");
  }
  hideError() {
    this.dom.errorMessage.classList.add("hidden");
    errorUI.clearAll();
  }
  showResults() {
    this.dom.uploadSection.classList.add("hidden");
    this.dom.resultsSection.classList.remove("hidden");
  }
  resetToUpload() {
    this.dom.resultsSection.classList.add("hidden");
    this.dom.uploadSection.classList.remove("hidden");
    this.dom.fileInput.value = "";
    this.hideError();
    errorUI.clearAll();
  }
  // ═══════════════════════════════════════════════════════════════════════
  // RESULT RENDERING
  // ═══════════════════════════════════════════════════════════════════════
  renderResults() {
    if (!this.processedData)
      return;
    this.renderSummary();
    this.renderTables();
    this.renderCharts();
  }
  renderSummary() {
    if (!this.processedData)
      return;
    const summary = this.processedData.summary;
    document.getElementById("summary-rows").textContent = summary.record_count.toString();
    document.getElementById("summary-metrics").textContent = summary.metric_count.toString();
    document.getElementById("summary-missing").textContent = summary.missing_newscast.toString();
  }
  renderTables() {
    if (!this.processedData)
      return;
    const tables = this.processedData.tables;
    this.tableRenderer.render("table-overall", tables.overall, ["Question", "Yes %"], this.processedData.config);
    this.tableRenderer.render("table-quality", tables.data_quality, ["Question", "Complete %", "Missing"], this.processedData.config);
    const recentCard = document.getElementById("recent-week-card");
    if (tables.recent && recentCard) {
      recentCard.classList.remove("hidden");
      document.getElementById("recent-week-title").textContent = `Week of ${tables.recent_week_start}`;
      this.tableRenderer.render("table-recent", tables.recent, ["Question", "Yes %"], this.processedData.config);
    } else if (recentCard) {
      recentCard.classList.add("hidden");
    }
    if (tables.volume) {
      this.tableRenderer.render("table-volume", tables.volume, ["Newscast", "Responses"], this.processedData.config);
    }
  }
  renderCharts() {
    if (!this.processedData)
      return;
    const charts = this.processedData.charts;
    const config = this.processedData.config;
    this.chartRenderer.renderOverallChart("chart-overall", charts.overall, config);
    this.chartRenderer.renderPerNewscastCharts("charts-per-newscast", charts.per_newscast, config);
    if (charts.weekly) {
      this.chartRenderer.renderWeeklyChart("chart-weekly", charts.weekly, config);
    }
    if (charts.filter_options && charts.filter_options.length > 0) {
      const select = document.getElementById("weekly-chart-filter");
      if (select) {
        select.innerHTML = "";
        charts.filter_options.forEach((opt, index) => {
          const option = document.createElement("option");
          option.value = index.toString();
          option.textContent = opt.label;
          select.appendChild(option);
        });
        select.onchange = () => {
          const selectedIndex = parseInt(select.value);
          const selectedData = charts.filter_options[selectedIndex];
          if (selectedData) {
            try {
              const weeklyData = {
                dates: selectedData.dates,
                values: selectedData.values,
                full_dates: selectedData.dates,
                center_line: selectedData.center_line,
                ucl: selectedData.ucl,
                lcl: selectedData.lcl
              };
              this.chartRenderer.renderWeeklyChart("chart-weekly", weeklyData, config);
            } catch (e) {
              console.error("Error updating chart:", e);
            }
          }
        };
      }
    }
    if (charts.per_newscast && charts.per_newscast.length > 0) {
      this.chartRenderer.renderHeatmap("chart-heatmap", charts.per_newscast, config);
    }
    if (this.processedData.comments) {
      this.commentRenderer.renderComments("comments-feed", this.processedData.comments);
    }
  }
  // ═══════════════════════════════════════════════════════════════════════
  // EXPORT FUNCTIONALITY
  // ═══════════════════════════════════════════════════════════════════════
  async exportExcel() {
    if (!this.processedData)
      return;
    await this.exporter.exportToExcel(this.processedData);
  }
  async exportPowerPoint() {
    if (!this.processedData)
      return;
    await this.exporter.exportToPowerPoint(this.processedData, this.chartRenderer);
  }
}
export {
  NewscastAuditApp
};
//# sourceMappingURL=app.js.map
