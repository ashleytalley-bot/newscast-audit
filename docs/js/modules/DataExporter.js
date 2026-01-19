class DataExporter {
  /**
   * Export data to Excel workbook
   */
  async exportToExcel(processedData) {
    const workbook = XLSX.utils.book_new();
    this.addSheetFromData(workbook, processedData.export_data.overall, "Overall Metrics");
    this.addSheetFromData(workbook, processedData.export_data.data_quality, "Data Quality");
    if (processedData.export_data.recent && processedData.export_data.recent.length > 0) {
      this.addSheetFromData(workbook, processedData.export_data.recent, "Recent Week");
    }
    if (processedData.export_data.volume && processedData.export_data.volume.length > 0) {
      this.addSheetFromData(workbook, processedData.export_data.volume, "Volume by Newscast");
    }
    this.addSheetFromData(workbook, processedData.export_data.normalized, "All Data");
    const timestamp = (/* @__PURE__ */ new Date()).toISOString().split("T")[0];
    XLSX.writeFile(workbook, `newscast-audit-${timestamp}.xlsx`);
  }
  /**
   * Add a sheet to workbook from data
   */
  addSheetFromData(workbook, data, sheetName) {
    const worksheet = XLSX.utils.json_to_sheet(data);
    XLSX.utils.book_append_sheet(workbook, worksheet, sheetName);
  }
  /**
   * Export data to PowerPoint presentation
   */
  async exportToPowerPoint(processedData, chartRenderer) {
    const pptx = new PptxGenJS();
    pptx.layout = "LAYOUT_16x9";
    pptx.author = "Newscast Audit Tool";
    pptx.company = "TEGNA";
    let slide = pptx.addSlide();
    slide.addText("Newscast Audit Report", {
      x: 0.5,
      y: 2,
      w: 9,
      h: 1,
      fontSize: 44,
      bold: true,
      color: "045ea8"
    });
    slide.addText(`Generated: ${(/* @__PURE__ */ new Date()).toLocaleDateString()}`, {
      x: 0.5,
      y: 3.5,
      w: 9,
      h: 0.5,
      fontSize: 18,
      color: "666666"
    });
    slide = pptx.addSlide();
    slide.addText("Summary", { x: 0.5, y: 0.5, w: 9, h: 0.5, fontSize: 32, bold: true });
    slide.addText([
      { text: `Total Responses: ${processedData.summary.record_count}
`, options: { breakLine: true } },
      { text: `Metrics Tracked: ${processedData.summary.metric_count}
`, options: { breakLine: true } },
      { text: `Missing Newscast: ${processedData.summary.missing_newscast}`, options: { breakLine: true } }
    ], { x: 0.5, y: 1.5, w: 9, h: 3, fontSize: 18 });
    const overallChart = await chartRenderer.captureChartAsImage("chart-overall");
    if (overallChart) {
      slide = pptx.addSlide();
      slide.addText("Overall Audit Metrics", { x: 0.5, y: 0.3, w: 9, h: 0.5, fontSize: 28, bold: true });
      slide.addImage({ data: overallChart, x: 0.5, y: 1, w: 9, h: 4.5 });
    }
    const perNewscastCharts = processedData.charts.per_newscast;
    for (let i = 0; i < perNewscastCharts.length; i++) {
      const chartId = `chart-newscast-${i}`;
      const chartImg = await chartRenderer.captureChartAsImage(chartId);
      if (chartImg) {
        slide = pptx.addSlide();
        slide.addText(`${perNewscastCharts[i].newscast} (n=${perNewscastCharts[i].n})`, {
          x: 0.5,
          y: 0.3,
          w: 9,
          h: 0.5,
          fontSize: 28,
          bold: true
        });
        slide.addImage({ data: chartImg, x: 0.5, y: 1, w: 9, h: 4.5 });
      }
    }
    const timestamp = (/* @__PURE__ */ new Date()).toISOString().split("T")[0];
    pptx.writeFile({ fileName: `newscast-audit-${timestamp}.pptx` });
  }
}
export {
  DataExporter
};
//# sourceMappingURL=DataExporter.js.map
