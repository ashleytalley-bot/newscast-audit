import type { ProcessingResult } from '../types/output';
import type { ChartRenderer } from './ChartRenderer';

declare const XLSX: any;
declare const PptxGenJS: any;

export class DataExporter {
    /**
     * Export data to Excel workbook
     */
    async exportToExcel(processedData: ProcessingResult) {
        const workbook = XLSX.utils.book_new();

        // Overall metrics sheet
        this.addSheetFromData(workbook, processedData.export_data.overall, 'Overall Metrics');

        // Data quality sheet
        this.addSheetFromData(workbook, processedData.export_data.data_quality, 'Data Quality');

        // Recent week sheet (if available)
        if (processedData.export_data.recent && processedData.export_data.recent.length > 0) {
            this.addSheetFromData(workbook, processedData.export_data.recent, 'Recent Week');
        }

        // Volume sheet
        if (processedData.export_data.volume && processedData.export_data.volume.length > 0) {
            this.addSheetFromData(workbook, processedData.export_data.volume, 'Volume by Newscast');
        }

        // Normalized data sheet
        this.addSheetFromData(workbook, processedData.export_data.normalized, 'All Data');

        // Download file
        const timestamp = new Date().toISOString().split('T')[0];
        XLSX.writeFile(workbook, `newscast-audit-${timestamp}.xlsx`);
    }

    /**
     * Add a sheet to workbook from data
     */
    private addSheetFromData(workbook: any, data: any[], sheetName: string) {
        const worksheet = XLSX.utils.json_to_sheet(data);
        XLSX.utils.book_append_sheet(workbook, worksheet, sheetName);
    }

    /**
     * Export data to PowerPoint presentation
     */
    async exportToPowerPoint(processedData: ProcessingResult, chartRenderer: ChartRenderer) {
        const pptx = new PptxGenJS();
        pptx.layout = 'LAYOUT_16x9';
        pptx.author = 'Newscast Audit Tool';
        pptx.company = 'TEGNA';

        // Title slide
        let slide = pptx.addSlide();
        slide.addText('Newscast Audit Report', {
            x: 0.5, y: 2, w: 9, h: 1,
            fontSize: 44, bold: true, color: '045ea8'
        });
        slide.addText(`Generated: ${new Date().toLocaleDateString()}`, {
            x: 0.5, y: 3.5, w: 9, h: 0.5,
            fontSize: 18, color: '666666'
        });

        // Summary slide
        slide = pptx.addSlide();
        slide.addText('Summary', { x: 0.5, y: 0.5, w: 9, h: 0.5, fontSize: 32, bold: true });
        slide.addText([
            { text: `Total Responses: ${processedData.summary.record_count}\n`, options: { breakLine: true } },
            { text: `Metrics Tracked: ${processedData.summary.metric_count}\n`, options: { breakLine: true } },
            { text: `Missing Newscast: ${processedData.summary.missing_newscast}`, options: { breakLine: true } }
        ], { x: 0.5, y: 1.5, w: 9, h: 3, fontSize: 18 });

        // Overall chart slide
        const overallChart = await chartRenderer.captureChartAsImage('chart-overall');
        if (overallChart) {
            slide = pptx.addSlide();
            slide.addText('Overall Audit Metrics', { x: 0.5, y: 0.3, w: 9, h: 0.5, fontSize: 28, bold: true });
            slide.addImage({ data: overallChart, x: 0.5, y: 1, w: 9, h: 4.5 });
        }

        // Per-newscast charts
        const perNewscastCharts = processedData.charts.per_newscast;
        for (let i = 0; i < perNewscastCharts.length; i++) {
            const chartId = `chart-newscast-${i}`;
            const chartImg = await chartRenderer.captureChartAsImage(chartId);

            if (chartImg) {
                slide = pptx.addSlide();
                slide.addText(`${perNewscastCharts[i].newscast} (n=${perNewscastCharts[i].n})`, {
                    x: 0.5, y: 0.3, w: 9, h: 0.5, fontSize: 28, bold: true
                });
                slide.addImage({ data: chartImg, x: 0.5, y: 1, w: 9, h: 4.5 });
            }
        }

        // Download file
        const timestamp = new Date().toISOString().split('T')[0];
        pptx.writeFile({ fileName: `newscast-audit-${timestamp}.pptx` });
    }
}
